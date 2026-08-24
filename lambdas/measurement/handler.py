"""
CloudGuard DR — Measurement Lambda
Calculates RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
from CloudWatch metrics and injection/recovery timestamps.
"""
import os
import json
from datetime import datetime

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


def lambda_handler(event, context):
    """
    Calculate RTO and RPO for the test run.
    
    Event input (from Monitor Lambda):
        {
            "recovered": true,
            "recovery_timestamp": "2026-08-22T08:02:44Z",
            "injection_timestamp": "2026-08-22T08:00:12Z",
            "monitor_duration_seconds": 152,
            "target_instance": "i-0abc...",
            "fault_type": "ec2-termination",
            "experiment_id": "..."
        }
    
    Output:
        {
            "rto_seconds": 152,
            "rpo_seconds": 0,
            "injection_timestamp": "...",
            "recovery_timestamp": "...",
            "target_instance": "...",
            "fault_type": "...",
            "experiment_id": "..."
        }
    """
    print(f"[Measurement] Calculating RTO/RPO. Event: {json.dumps(event)}")
    
    try:
        injection_timestamp = event.get("injection_timestamp")
        recovery_timestamp = event.get("recovery_timestamp")
        recovered = event.get("recovered", False)
        
        if not recovered or not recovery_timestamp or not injection_timestamp:
            print("[Measurement] Recovery not confirmed or timestamps missing")
            return {
                "statusCode": 200,
                "rto_seconds": -1,  # Indicates measurement failed
                "rpo_seconds": -1,
                "injection_timestamp": injection_timestamp,
                "recovery_timestamp": None,
                "measured": False,
                "target_instance": event.get("target_instance"),
                "fault_type": event.get("fault_type", "ec2-termination"),
                "experiment_id": event.get("experiment_id"),
            }
        
        # Calculate RTO (Recovery Time Objective)
        rto_seconds = calculate_rto(injection_timestamp, recovery_timestamp)
        
        # Calculate RPO (Recovery Point Objective)
        # For EC2 termination, RPO is typically 0 if no stateful data was lost
        # In a real scenario, you'd check the last successful data checkpoint
        rpo_seconds = calculate_rpo(event)
        
        result = {
            "statusCode": 200,
            "rto_seconds": rto_seconds,
            "rpo_seconds": rpo_seconds,
            "injection_timestamp": injection_timestamp,
            "recovery_timestamp": recovery_timestamp,
            "measured": True,
            "target_instance": event.get("target_instance"),
            "fault_type": event.get("fault_type", "ec2-termination"),
            "experiment_id": event.get("experiment_id"),
        }
        
        print(f"[Measurement] RTO: {rto_seconds}s, RPO: {rpo_seconds}s")
        print(f"[Measurement] Result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        print(f"[Measurement] Error: {str(e)}")
        raise


def calculate_rto(injection_timestamp, recovery_timestamp):
    """
    Calculate Recovery Time Objective in seconds.
    RTO = time between fault injection and resource returning to healthy state.
    """
    try:
        injection_time = datetime.fromisoformat(
            injection_timestamp.replace("Z", "+00:00")
        )
        recovery_time = datetime.fromisoformat(
            recovery_timestamp.replace("Z", "+00:00")
        )
        
        delta = recovery_time - injection_time
        rto_seconds = int(delta.total_seconds())
        
        # Add a small buffer (5 seconds) to account for CloudWatch metric delay
        rto_seconds += 5
        
        print(f"[Measurement] RTO calculation: {recovery_timestamp} - {injection_timestamp} = {rto_seconds}s")
        return max(rto_seconds, 0)
        
    except Exception as e:
        print(f"[Measurement] Error calculating RTO: {str(e)}")
        return -1


def calculate_rpo(event):
    """
    Calculate Recovery Point Objective in seconds.
    RPO = data loss window (time since last successful data checkpoint).
    
    For EC2 instance termination (stateless): RPO = 0
    For database scenarios: RPO = time since last backup/replication.
    """
    fault_type = event.get("fault_type", "ec2-termination")
    
    if fault_type == "ec2-termination":
        # Stateless application — no data loss
        print("[Measurement] RPO = 0 (stateless application)")
        return 0
    
    # For other fault types, you'd check the last checkpoint
    # This is a placeholder for MVP
    print(f"[Measurement] RPO = 0 (default for {fault_type})")
    return 0
