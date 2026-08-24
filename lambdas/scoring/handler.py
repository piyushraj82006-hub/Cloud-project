"""
CloudGuard DR — Scoring Lambda
Converts RTO and RPO measurements into a single 0-100 resilience score,
checks against configured thresholds, and stores the result in DynamoDB.
"""
import os
import json
import time
import uuid
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
ssm_client = boto3.client("ssm")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
TEST_RUNS_TABLE = os.environ.get("TEST_RUNS_TABLE", f"cloudguard-{ENVIRONMENT}-test-runs")
RTO_TARGET_SSM_ARN = os.environ.get("RTO_TARGET_SSM_ARN", "")
RPO_TARGET_SSM_ARN = os.environ.get("RPO_TARGET_SSM_ARN", "")
SCORE_THRESHOLD_SSM_ARN = os.environ.get("SCORE_THRESHOLD_SSM_ARN", "")


def lambda_handler(event, context):
    """
    Compute resilience score and store in DynamoDB.
    
    Event input (from Measurement Lambda):
        {
            "rto_seconds": 152,
            "rpo_seconds": 0,
            "injection_timestamp": "...",
            "recovery_timestamp": "...",
            "target_instance": "i-0abc...",
            "fault_type": "ec2-termination",
            "experiment_id": "...",
            "measured": true
        }
    
    Output:
        {
            "run_id": "run-uuid",
            "resilience_score": 82,
            "status": "Passed",
            "rto_seconds": 152,
            "rpo_seconds": 0,
            "rto_target": 300,
            "rpo_target": 60,
            "score_threshold": 70
        }
    """
    print(f"[Scoring] Computing resilience score. Event: {json.dumps(event)}")
    
    try:
        # Get configured targets
        rto_target = get_ssm_param(RTO_TARGET_SSM_ARN, default=300)
        rpo_target = get_ssm_param(RPO_TARGET_SSM_ARN, default=60)
        score_threshold = get_ssm_param(SCORE_THRESHOLD_SSM_ARN, default=70)
        
        rto_seconds = event.get("rto_seconds", -1)
        rpo_seconds = event.get("rpo_seconds", -1)
        measured = event.get("measured", False)
        
        # Calculate resilience score
        if measured and rto_seconds >= 0 and rpo_seconds >= 0:
            resilience_score = calculate_score(rto_seconds, rpo_seconds, rto_target, rpo_target)
        else:
            # Measurement failed — score is 0
            resilience_score = 0
        
        # Determine pass/fail
        status = "Passed" if resilience_score >= score_threshold else "Failed"
        
        # Generate run ID
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        
        # Store in DynamoDB
        table = dynamodb.Table(TEST_RUNS_TABLE)
        
        item = {
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fault_type": event.get("fault_type", "ec2-termination"),
            "target_resource": event.get("target_instance", "unknown"),
            "rto_seconds": rto_seconds,
            "rpo_seconds": rpo_seconds,
            "resilience_score": resilience_score,
            "status": status,
            "rto_target": rto_target,
            "rpo_target": rpo_target,
            "report_s3_key": "",  # Will be set by Audit Report Lambda
            "stage_timestamps": {
                "inject": event.get("injection_timestamp"),
                "recover": event.get("recovery_timestamp"),
            },
        }
        
        table.put_item(Item=item)
        
        result = {
            "statusCode": 200,
            "run_id": run_id,
            "resilience_score": resilience_score,
            "status": status,
            "rto_seconds": rto_seconds,
            "rpo_seconds": rpo_seconds,
            "rto_target": rto_target,
            "rpo_target": rpo_target,
            "score_threshold": score_threshold,
            "measured": measured,
            "timestamp": item["timestamp"],
            "fault_type": item["fault_type"],
            "target_resource": item["target_resource"],
        }
        
        print(f"[Scoring] Score: {resilience_score}/100 ({status})")
        print(f"[Scoring] Run ID: {run_id}")
        print(f"[Scoring] Result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        print(f"[Scoring] Error: {str(e)}")
        raise


def calculate_score(rto_seconds, rpo_seconds, rto_target, rpo_target):
    """
    Calculate resilience score (0-100) from RTO and RPO.
    
    Formula:
        RTO Score = max(0, 100 - (rto_seconds / rto_target * 50))
        RPO Score = max(0, 100 - (rpo_seconds / rpo_target * 50))
        Final Score = (RTO Score * 0.6) + (RPO Score * 0.4)
    
    This weights RTO more heavily than RPO since recovery time is
    typically the primary concern in disaster recovery.
    """
    # RTO component (60% weight)
    if rto_target > 0:
        rto_ratio = rto_seconds / rto_target
        rto_score = max(0, 100 - (rto_ratio * 50))
    else:
        rto_score = 100 if rto_seconds == 0 else 0
    
    # RPO component (40% weight)
    if rpo_target > 0:
        rpo_ratio = rpo_seconds / rpo_target
        rpo_score = max(0, 100 - (rpo_ratio * 50))
    else:
        rpo_score = 100 if rpo_seconds == 0 else 0
    
    # Weighted average
    final_score = round((rto_score * 0.6) + (rpo_score * 0.4))
    
    print(f"[Scoring] RTO: {rto_seconds}s / {rto_target}s = {rto_ratio:.2f} → {rto_score:.1f}")
    print(f"[Scoring] RPO: {rpo_seconds}s / {rpo_target}s = {rpo_ratio:.2f} → {rpo_score:.1f}")
    print(f"[Scoring] Final: ({rto_score:.1f} * 0.6) + ({rpo_score:.1f} * 0.4) = {final_score}")
    
    return max(0, min(100, final_score))


def get_ssm_param(arn, default=None):
    """Get a parameter value from SSM Parameter Store."""
    if not arn:
        return default
    
    try:
        # Extract parameter name from ARN
        param_name = arn.split(":")[-1]
        response = ssm_client.get_parameter(Name=param_name)
        return int(response["Parameter"]["Value"])
    except (ClientError, ValueError, IndexError) as e:
        print(f"[Scoring] Warning: Could not get SSM param {arn}: {e}")
        return default
