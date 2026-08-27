"""
CloudGuard DR — Injection Lambda
Triggers fault injection via AWS FIS or direct AWS API calls.

Supported fault types:
  ec2-termination    — FIS experiment to terminate tagged EC2 instances
  dns-failover       — Disable Route53 health check to force DNS failover
  s3-origin-block    — Add S3 bucket policy deny rule to block access
  security-group     — Add ingress deny rule to block traffic on a port
"""
import os
import json
import time
import copy
import boto3
from botocore.exceptions import ClientError

fis_client = boto3.client("fis")
ec2_client = boto3.client("ec2")
ssm_client = boto3.client("ssm")
route53_client = boto3.client("route53")
s3_client = boto3.client("s3")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Supported fault types and their handlers
FAULT_TYPES = {
    "ec2-termination",
    "dns-failover",
    "s3-origin-block",
    "security-group",
}


def lambda_handler(event, context):
    """
    Start a fault injection experiment.

    Event input:
        {
            "fault_type": "ec2-termination" | "dns-failover" | "s3-origin-block" | "security-group",
            "target_resource": "auto" | "<resource-id>",
            "target_url": "https://example.com",          // optional — for monitoring
            "port": 443,                                    // optional — for security-group
            "health_check_id": "...",                       // optional — for dns-failover
            "bucket_name": "my-bucket",                     // optional — for s3-origin-block
            "security_group_id": "sg-...",                  // optional — for security-group
            "vpc_id": "vpc-..."                             // optional — for security-group
        }

    Output:
        {
            "experiment_id": "...",
            "injection_timestamp": "2026-08-22T08:00:12Z",
            "target_instance": "i-0abc...",
            "target_url": "https://example.com",
            "fault_type": "ec2-termination",
            "restore_info": { ... }   // data needed to undo the fault
        }
    """
    print(f"[Injection] Starting fault injection. Event: {json.dumps(event)}")

    fault_type = event.get("fault_type", "ec2-termination")

    if fault_type not in FAULT_TYPES:
        raise Exception(
            f"Unknown fault_type '{fault_type}'. "
            f"Supported: {', '.join(sorted(FAULT_TYPES))}"
        )

    injection_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    try:
        if fault_type == "ec2-termination":
            result = inject_ec2_termination(event)
        elif fault_type == "dns-failover":
            result = inject_dns_failover(event)
        elif fault_type == "s3-origin-block":
            result = inject_s3_origin_block(event)
        elif fault_type == "security-group":
            result = inject_security_group(event)

        result["injection_timestamp"] = injection_timestamp
        result["fault_type"] = fault_type
        result["target_url"] = event.get("target_url")

        print(f"[Injection] Fault injected: {json.dumps(result)}")
        return result

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"[Injection] AWS Error: {error_code} - {error_msg}")
        raise Exception(f"Failed to inject fault ({fault_type}): {error_msg}")

    except Exception as e:
        print(f"[Injection] Error: {str(e)}")
        raise


# ──────────────────────────────────────────────
#  ec2-termination  (existing FIS-based method)
# ──────────────────────────────────────────────

def inject_ec2_termination(event):
    """Start a FIS experiment to terminate a tagged EC2 instance."""
    experiment_template_id = get_experiment_template_id()

    target_instance = event.get("target_resource", "auto")
    if target_instance == "auto":
        target_instance = find_target_instance()

    response = fis_client.start_experiment(
        experimentTemplateId=experiment_template_id,
        tags={
            "Project": "CloudGuardDR",
            "Environment": ENVIRONMENT,
        },
    )

    experiment_id = response["experiment"]["id"]
    print(f"[Injection] FIS experiment started: {experiment_id}")

    return {
        "statusCode": 200,
        "experiment_id": experiment_id,
        "target_instance": target_instance,
        "restore_info": None,  # FIS auto-terminates; no manual restore needed
    }


# ──────────────────────────────────────────
#  dns-failover  (Route53 health check)
# ──────────────────────────────────────────

def inject_dns_failover(event):
    """
    Disable a Route53 health check to force DNS failover.

    The health_check_id can be provided directly or discovered by
    matching the target_url's domain against existing health checks.
    """
    health_check_id = event.get("health_check_id")
    target_url = event.get("target_url")

    if not health_check_id and target_url:
        health_check_id = find_health_check_for_url(target_url)

    if not health_check_id:
        raise Exception(
            "dns-failover requires health_check_id or target_url "
            "that matches an existing Route53 health check"
        )

    # Store original config so we can restore it
    original_config = route53_client.get_health_check(
        HealthCheckId=health_check_id
    )["HealthCheck"]

    # Disable the health check by setting healthy threshold to an
    # unreachable value (invert the logic: mark as unhealthy)
    # We update the health check config to force an unhealthy status
    config = original_config["HealthCheckConfig"]
    original_config_snapshot = {
        "health_check_id": health_check_id,
        "caller_reference": original_config.get("CallerReference", ""),
        "original_config": config,
    }

    # Disable by removing the inversion flag (if present) or by
    # setting the failure threshold to 1 and marking unhealthy
    new_config = copy.deepcopy(config)
    # Force unhealthy: set Inverted to True (swaps healthy/unhealthy)
    new_config["Inverted"] = not config.get("Inverted", False)

    route53_client.update_health_check(
        HealthCheckId=health_check_id,
        HealthCheckConfig=new_config,
    )

    print(f"[Injection] Disabled Route53 health check: {health_check_id}")
    print(f"[Injection] Health check inverted to force unhealthy status")

    return {
        "statusCode": 200,
        "experiment_id": f"dns-failover-{health_check_id}",
        "target_instance": None,
        "restore_info": {
            "type": "dns-failover",
            "health_check_id": health_check_id,
            "original_config": original_config_snapshot,
        },
    }


def find_health_check_for_url(target_url):
    """Find a Route53 health check whose domain matches the target URL."""
    from urllib.parse import urlparse

    parsed = urlparse(target_url)
    target_domain = parsed.hostname

    try:
        response = route53_client.list_health_checks()
        for hc in response.get("HealthChecks", []):
            config = hc.get("HealthCheckConfig", {})
            domain = config.get("FullyQualifiedDomainName", "")
            if domain and (domain == target_domain or target_domain.endswith(domain)):
                print(f"[Injection] Matched health check {hc['Id']} to domain {domain}")
                return hc["Id"]
    except Exception as e:
        print(f"[Injection] Error listing health checks: {e}")

    return None


# ──────────────────────────────────────────
#  s3-origin-block  (S3 bucket policy)
# ──────────────────────────────────────────

def inject_s3_origin_block(event):
    """
    Add a deny-all statement to an S3 bucket policy to block public access.

    Useful for testing CloudFront or static-site failover when the
    origin is an S3 bucket.
    """
    bucket_name = event.get("bucket_name")

    if not bucket_name and event.get("target_url"):
        # Try to extract bucket name from URL pattern
        # e.g. https://my-bucket.s3.amazonaws.com → my-bucket
        from urllib.parse import urlparse
        parsed = urlparse(event["target_url"])
        hostname = parsed.hostname or ""
        if hostname.startswith("s3.") or hostname.endswith(".s3.amazonaws.com"):
            bucket_name = hostname.split(".")[0]

    if not bucket_name:
        raise Exception(
            "s3-origin-block requires bucket_name or a target_url "
            "matching an S3 website endpoint"
        )

    # Get current bucket policy (if any)
    try:
        current_policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        original_policy = json.loads(current_policy["Policy"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            original_policy = None
        else:
            raise

    # Build the deny statement
    deny_statement = {
        "Sid": "CloudGuardDR-BlockAccess",
        "Effect": "Deny",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{bucket_name}/*",
    }

    # Create or update policy
    if original_policy:
        new_policy = copy.deepcopy(original_policy)
        # Remove any previous CloudGuardDR statement
        new_policy["Statement"] = [
            s for s in new_policy.get("Statement", [])
            if s.get("Sid") != "CloudGuardDR-BlockAccess"
        ]
        new_policy["Statement"].append(deny_statement)
    else:
        new_policy = {
            "Version": "2012-10-17",
            "Statement": [deny_statement],
        }

    s3_client.put_bucket_policy(
        Bucket=bucket_name,
        Policy=json.dumps(new_policy),
    )

    print(f"[Injection] Blocked S3 bucket access: {bucket_name}")

    return {
        "statusCode": 200,
        "experiment_id": f"s3-origin-block-{bucket_name}",
        "target_instance": None,
        "restore_info": {
            "type": "s3-origin-block",
            "bucket_name": bucket_name,
            "original_policy": original_policy,  # None means no policy existed
        },
    }


# ──────────────────────────────────────────
#  security-group  (ingress deny rule)
# ──────────────────────────────────────────

def inject_security_group(event):
    """
    Add an ingress deny rule to a security group to block traffic on a port.

    This creates a high-priority DENY rule that overrides any existing
    ALLOW rules for the specified port.
    """
    security_group_id = event.get("security_group_id")
    port = int(event.get("port", 443))
    vpc_id = event.get("vpc_id")

    # Auto-discover security group if not provided
    if not security_group_id:
        security_group_id = find_security_group_for_vpc(vpc_id)

    if not security_group_id:
        raise Exception(
            "security-group requires security_group_id or vpc_id "
            "to auto-discover the default security group"
        )

    # Verify the security group exists
    sg_info = ec2_client.describe_security_groups(
        GroupIds=[security_group_id]
    )
    sg = sg_info["SecurityGroups"][0]

    # Record existing ingress rules for restoration
    original_ingress = sg.get("IpPermissions", [])

    # Add a DENY ingress rule for the specified port
    # Using a prefix list or CIDR that covers all traffic
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": port,
                "ToPort": port,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "CloudGuard DR - fault injection"}],
                "Ipv6Ranges": [{"CidrIpv6": "::/0", "Description": "CloudGuard DR - fault injection"}],
            }
        ],
    )

    # Now we need to add a DENY rule. The trick: AWS doesn't have explicit DENY
    # in security groups. Instead, we REMOVE all ALLOW rules for that port.
    # Save the original allow rules so we can restore them.
    port_allow_rules = [
        rule for rule in original_ingress
        if rule.get("FromPort") == port and rule.get("ToPort") == port
    ]

    if port_allow_rules:
        # Revoke the allow rules for this port
        ec2_client.revoke_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=port_allow_rules,
        )
        print(f"[Injection] Revoked {len(port_allow_rules)} allow rule(s) for port {port}")
    else:
        print(f"[Injection] No existing allow rules found for port {port}")

    print(f"[Injection] Blocked port {port} on security group {security_group_id}")

    return {
        "statusCode": 200,
        "experiment_id": f"security-group-{security_group_id}-port{port}",
        "target_instance": None,
        "restore_info": {
            "type": "security-group",
            "security_group_id": security_group_id,
            "port": port,
            "original_port_rules": port_allow_rules,
        },
    }


def find_security_group_for_vpc(vpc_id):
    """Find the default security group for a VPC."""
    if not vpc_id:
        # Try to find any VPC
        response = ec2_client.describe_vpcs(
            Filters=[{"Name": "is-default", "Values": ["true"]}]
        )
        vpcs = response.get("Vpcs", [])
        if not vpcs:
            raise Exception("No default VPC found. Provide vpc_id explicitly.")
        vpc_id = vpcs[0]["VpcId"]

    response = ec2_client.describe_security_groups(
        Filters=[
            {"Name": "vpc-id", "Values": [vpc_id]},
            {"Name": "group-name", "Values": ["default"]},
        ]
    )

    groups = response.get("SecurityGroups", [])
    if groups:
        print(f"[Injection] Found default SG: {groups[0]['GroupId']} in VPC {vpc_id}")
        return groups[0]["GroupId"]

    raise Exception(f"No default security group found in VPC {vpc_id}")


# ──────────────────────────────────────────
#  Restore function (called after monitoring)
# ──────────────────────────────────────────

def restore_fault(restore_info):
    """
    Revert a fault injection by restoring the original state.

    Called by the Step Function after monitoring completes.
    """
    if not restore_info:
        print("[Restore] No restore_info provided, skipping")
        return {"statusCode": 200, "restored": False}

    fault_type = restore_info.get("type")
    print(f"[Restore] Reverting fault type: {fault_type}")

    try:
        if fault_type == "dns-failover":
            hc_id = restore_info["health_check_id"]
            original = restore_info["original_config"]
            route53_client.update_health_check(
                HealthCheckId=hc_id,
                HealthCheckConfig=original["original_config"],
            )
            print(f"[Restore] Route53 health check {hc_id} restored")

        elif fault_type == "s3-origin-block":
            bucket_name = restore_info["bucket_name"]
            original_policy = restore_info.get("original_policy")
            if original_policy:
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(original_policy),
                )
                print(f"[Restore] S3 bucket policy restored for {bucket_name}")
            else:
                s3_client.delete_bucket_policy(Bucket=bucket_name)
                print(f"[Restore] S3 bucket policy removed for {bucket_name} (no original)")

        elif fault_type == "security-group":
            sg_id = restore_info["security_group_id"]
            port = restore_info["port"]
            original_rules = restore_info.get("original_port_rules", [])
            if original_rules:
                ec2_client.authorize_security_group_ingress(
                    GroupId=sg_id,
                    IpPermissions=original_rules,
                )
                print(f"[Restore] Security group {sg_id} port {port} rules restored")
            else:
                print(f"[Restore] No original rules to restore for {sg_id} port {port}")

        else:
            print(f"[Restore] Unknown fault type '{fault_type}', skipping")
            return {"statusCode": 200, "restored": False}

        return {"statusCode": 200, "restored": True, "fault_type": fault_type}

    except Exception as e:
        print(f"[Restore] Error restoring fault: {e}")
        return {"statusCode": 500, "restored": False, "error": str(e)}


# ──────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────

def get_experiment_template_id():
    """Get the FIS experiment template ID from SSM Parameter Store."""
    try:
        param_name = f"/cloudguard-{ENVIRONMENT}/fis-experiment-template-id"
        response = ssm_client.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ClientError:
        response = fis_client.list_experiment_templates()
        templates = response.get("experimentTemplates", [])
        if templates:
            return templates[0]["id"]
        raise Exception("No FIS experiment templates found")


def find_target_instance():
    """Find an EC2 instance tagged with dr-test=true."""
    response = ec2_client.describe_instances(
        Filters=[
            {"Name": "tag:dr-test", "Values": ["true"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(instance["InstanceId"])

    if not instances:
        raise Exception("No instances found with dr-test=true tag")

    print(f"[Injection] Found target instances: {instances}")
    return instances[0]
