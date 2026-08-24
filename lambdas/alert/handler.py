"""
CloudGuard DR — Alert Lambda
Publishes an SNS notification when a test run misses its RTO/RPO target
or falls below the resilience score threshold.
"""
import os
import json
import boto3
import time

sns_client = boto3.client("sns")
ssm_client = boto3.client("ssm")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
SCORE_THRESHOLD_SSM_ARN = os.environ.get("SCORE_THRESHOLD_SSM_ARN", "")


def lambda_handler(event, context):
    """
    Check if the run missed its target and send alert if needed.
    
    Event input (from Scoring Lambda):
        {
            "run_id": "run-abc123",
            "resilience_score": 45,
            "status": "Failed",
            "rto_seconds": 492,
            "rpo_seconds": 150,
            "rto_target": 300,
            "rpo_target": 60,
            "score_threshold": 70
        }
    
    Output:
        {
            "alert_sent": true/false,
            "reason": "..."
        }
    """
    print(f"[Alert] Checking run. Event: {json.dumps(event)}")
    
    try:
        score = event.get("resilience_score", 0)
        status = event.get("status", "Failed")
        rto_seconds = event.get("rto_seconds", 0)
        rpo_seconds = event.get("rpo_seconds", 0)
        rto_target = event.get("rto_target", 300)
        rpo_target = event.get("rpo_target", 60)
        score_threshold = event.get("score_threshold", 70)
        
        # Determine if alert should be sent
        alert_reasons = []
        
        if status == "Failed":
            alert_reasons.append(f"Score {score} is below threshold {score_threshold}")
        
        if rto_seconds > rto_target:
            alert_reasons.append(
                f"RTO exceeded target: {format_time(rto_seconds)} > {format_time(rto_target)}"
            )
        
        if rpo_seconds > rpo_target:
            alert_reasons.append(
                f"RPO exceeded target: {format_time(rpo_seconds)} > {format_time(rpo_target)}"
            )
        
        if not event.get("measured", False):
            alert_reasons.append("Measurement failed — run could not be scored")
        
        # Send alert if there are any reasons
        alert_sent = False
        if alert_reasons:
            alert_sent = send_sns_alert(event, alert_reasons)
        
        result = {
            "statusCode": 200,
            "alert_sent": alert_sent,
            "reasons": alert_reasons,
            "run_id": event.get("run_id"),
            "resilience_score": score,
            "status": status,
        }
        
        print(f"[Alert] Alert sent: {alert_sent}")
        print(f"[Alert] Reasons: {alert_reasons}")
        print(f"[Alert] Result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        print(f"[Alert] Error: {str(e)}")
        raise


def send_sns_alert(event, reasons):
    """Publish an SNS notification with the alert details."""
    try:
        run_id = event.get("run_id", "unknown")
        score = event.get("resilience_score", 0)
        status = event.get("status", "Unknown")
        
        subject = f"CloudGuard DR Alert: Run {run_id} — {status}"
        
        body = f"""CloudGuard DR Test Run Alert
{'=' * 50}

Run ID:       {run_id}
Status:       {status}
Score:        {score}/100
Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

Alert Reasons:
{chr(10).join(f'  • {reason}' for reason in reasons)}

Metrics:
  RTO: {format_time(event.get('rto_seconds', 0))} (target: {format_time(event.get('rto_target', 300))})
  RPO: {format_time(event.get('rpo_seconds', 0))} (target: {format_time(event.get('rpo_target', 60))})

Dashboard: https://cloudguard-{ENVIRONMENT}.s3.amazonaws.com/index.html
{'=' * 50}
"""
        
        # Publish to SNS
        topic_arn = SNS_TOPIC_ARN
        if not topic_arn:
            # Try to get from SSM
            topic_arn = get_ssm_param(SCORE_THRESHOLD_SSM_ARN)
        
        if topic_arn:
            sns_client.publish(
                TopicArn=topic_arn,
                Subject=subject[:100],  # SNS subject max 100 chars
                Message=body,
            )
            print(f"[Alert] SNS published to {topic_arn}")
            return True
        else:
            print("[Alert] Warning: No SNS topic ARN configured")
            return False
            
    except Exception as e:
        print(f"[Alert] Error publishing SNS: {str(e)}")
        return False


def format_time(seconds):
    """Format seconds into human-readable time string."""
    if seconds < 0:
        return "N/A"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def get_ssm_param(arn):
    """Get a parameter value from SSM Parameter Store."""
    if not arn:
        return None
    try:
        param_name = arn.split(":")[-1]
        response = ssm_client.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except Exception:
        return None
