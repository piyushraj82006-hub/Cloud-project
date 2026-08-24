"""
CloudGuard DR — Injection Lambda
Triggers AWS Fault Injection Simulator experiment to terminate an EC2 instance.
"""
import os
import json
import time
import boto3
from botocore.exceptions import ClientError

fis_client = boto3.client("fis")
ec2_client = boto3.client("ec2")
ssm_client = boto3.client("ssm")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def lambda_handler(event, context):
    """
    Start a FIS experiment to terminate a tagged EC2 instance.
    
    Event input:
        {
            "fault_type": "ec2-termination",
            "target_resource": "auto" | "<instance-id>"
        }
    
    Output:
        {
            "experiment_id": "...",
            "injection_timestamp": "2026-08-22T08:00:12Z",
            "target_instance": "i-0abc..."
        }
    """
    print(f"[Injection] Starting fault injection. Event: {json.dumps(event)}")
    
    try:
        # Get the FIS experiment template ID from SSM or environment
        experiment_template_id = get_experiment_template_id()
        
        # If target_resource is "auto", find a tagged instance
        target_instance = event.get("target_resource", "auto")
        if target_instance == "auto":
            target_instance = find_target_instance()
        
        # Start the FIS experiment
        injection_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        response = fis_client.start_experiment(
            experimentTemplateId=experiment_template_id,
            tags={
                "Project": "CloudGuardDR",
                "Environment": ENVIRONMENT,
            }
        )
        
        experiment_id = response["experiment"]["id"]
        
        print(f"[Injection] FIS experiment started: {experiment_id}")
        print(f"[Injection] Target instance: {target_instance}")
        print(f"[Injection] Injection timestamp: {injection_timestamp}")
        
        return {
            "statusCode": 200,
            "experiment_id": experiment_id,
            "injection_timestamp": injection_timestamp,
            "target_instance": target_instance,
            "fault_type": event.get("fault_type", "ec2-termination"),
        }
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_msg = e.response["Error"]["Message"]
        print(f"[Injection] AWS Error: {error_code} - {error_msg}")
        raise Exception(f"Failed to start FIS experiment: {error_msg}")
    
    except Exception as e:
        print(f"[Injection] Error: {str(e)}")
        raise


def get_experiment_template_id():
    """Get the FIS experiment template ID from SSM Parameter Store."""
    try:
        param_name = f"/cloudguard-{ENVIRONMENT}/fis-experiment-template-id"
        response = ssm_client.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ClientError:
        # Fallback: list experiment templates
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
    
    # Pick the first one (for MVP)
    print(f"[Injection] Found target instances: {instances}")
    return instances[0]
