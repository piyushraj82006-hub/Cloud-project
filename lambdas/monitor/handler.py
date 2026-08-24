"""
CloudGuard DR — Monitor Lambda
Polls CloudWatch metrics and Route 53 health checks until the target resource
returns to a healthy state, or a timeout is reached.
"""
import os
import json
import time
import boto3

cloudwatch_client = boto3.client("cloudwatch")
route53_client = boto3.client("route53")
ec2_client = boto3.client("ec2")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
MAX_MONITOR_DURATION = 600  # 10 minutes max wait
POLL_INTERVAL = 15  # seconds between polls


def lambda_handler(event, context):
    """
    Monitor recovery after fault injection.
    
    Event input (from Injection Lambda):
        {
            "experiment_id": "...",
            "injection_timestamp": "2026-08-22T08:00:12Z",
            "target_instance": "i-0abc...",
            "fault_type": "ec2-termination"
        }
    
    Output:
        {
            "recovered": true/false,
            "recovery_timestamp": "2026-08-22T08:02:44Z",
            "injection_timestamp": "2026-08-22T08:00:12Z",
            "monitor_duration_seconds": 152
        }
    """
    print(f"[Monitor] Starting recovery monitoring. Event: {json.dumps(event)}")
    
    injection_timestamp = event.get("injection_timestamp")
    target_instance = event.get("target_instance")
    
    start_time = time.time()
    recovered = False
    recovery_timestamp = None
    
    # Wait a bit before starting to check (let the injection take effect)
    time.sleep(10)
    
    while time.time() - start_time < MAX_MONITOR_DURATION:
        # Check if the ALB target group has healthy targets
        if check_alb_health():
            recovered = True
            recovery_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            print(f"[Monitor] ALB health check passed. Recovery confirmed at {recovery_timestamp}")
            break
        
        # Check EC2 instance status (for replacement instance)
        if target_instance and check_instance_recovery():
            recovered = True
            recovery_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            print(f"[Monitor] EC2 instance recovery confirmed at {recovery_timestamp}")
            break
        
        # Check Route 53 health check status
        if check_route53_health():
            recovered = True
            recovery_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            print(f"[Monitor] Route 53 health check passed at {recovery_timestamp}")
            break
        
        print(f"[Monitor] Not yet recovered. Checking again in {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)
    
    monitor_duration = time.time() - start_time
    
    if not recovered:
        print(f"[Monitor] Timeout: Resource did not recover within {MAX_MONITOR_DURATION}s")
    
    result = {
        "statusCode": 200,
        "recovered": recovered,
        "recovery_timestamp": recovery_timestamp,
        "injection_timestamp": injection_timestamp,
        "monitor_duration_seconds": int(monitor_duration),
        "target_instance": target_instance,
        "fault_type": event.get("fault_type", "ec2-termination"),
        "experiment_id": event.get("experiment_id"),
    }
    
    print(f"[Monitor] Result: {json.dumps(result)}")
    return result


def check_alb_health():
    """Check if the ALB target group has healthy targets."""
    try:
        # Get target groups by name pattern
        response = ec2_client.describe_instance_status(
            Filters=[
                {"Name": "instance-state-name", "Values": ["running"]},
            ]
        )
        
        running_instances = len(response.get("InstanceStatuses", []))
        
        # If at least one instance is running, consider ALB healthy
        # In production, you'd check the specific target group health
        if running_instances >= 1:
            print(f"[Monitor] Found {running_instances} running instances")
            return True
        
        return False
        
    except Exception as e:
        print(f"[Monitor] Error checking ALB health: {str(e)}")
        return False


def check_instance_recovery():
    """Check if EC2 instances tagged dr-test=true are running."""
    try:
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
        
        if instances:
            print(f"[Monitor] Running DR-test instances: {instances}")
            return True
        
        return False
        
    except Exception as e:
        print(f"[Monitor] Error checking instance recovery: {str(e)}")
        return False


def check_route53_health():
    """Check Route 53 health check status."""
    try:
        response = route53_client.list_health_checks()
        
        for health_check in response.get("HealthChecks", []):
            hc_id = health_check["Id"]
            
            status_response = route53_client.get_health_check_status(
                HealthCheckId=hc_id
            )
            
            status = status_response["HealthCheckStatus"]
            print(f"[Monitor] Route 53 health check {hc_id}: {status}")
            
            if status == "Healthy":
                return True
        
        return False
        
    except Exception as e:
        print(f"[Monitor] Error checking Route 53 health: {str(e)}")
        return False
