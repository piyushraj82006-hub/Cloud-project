"""
CloudGuard DR — API Lambda
Handles all API Gateway endpoints:
  GET /runs              — List all test runs
  GET /runs/{run_id}     — Get a specific test run
  GET /runs/{run_id}/report — Get the audit report for a run
  POST /compare          — Compare two runs side by side
  GET /health            — Health check endpoint
"""
import os
import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
TEST_RUNS_TABLE = os.environ.get("TEST_RUNS_TABLE", f"cloudguard-{ENVIRONMENT}-test-runs")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")


def lambda_handler(event, context):
    """Route API requests to the appropriate handler."""
    print(f"[API] Event: {json.dumps(event)}")
    
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    
    # Route requests
    if path == "/health" and http_method == "GET":
        return health_check()
    
    if path == "/runs" and http_method == "GET":
        return list_runs(event)
    
    if path.startswith("/runs/") and path.endswith("/report") and http_method == "GET":
        run_id = path.split("/")[2]
        return get_run_report(run_id)
    
    if path.startswith("/runs/") and http_method == "GET":
        run_id = path.split("/")[2]
        return get_run(run_id)
    
    if path == "/compare" and http_method == "POST":
        return compare_runs(event)
    
    return {
        "statusCode": 404,
        "headers": cors_headers(),
        "body": json.dumps({"error": "Not found"}),
    }


def cors_headers():
    """Return CORS headers."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }


def health_check():
    """Health check endpoint (no auth required)."""
    return {
        "statusCode": 200,
        "headers": cors_headers(),
        "body": json.dumps({
            "status": "healthy",
            "service": "CloudGuard DR API",
            "environment": ENVIRONMENT,
        }),
    }


def list_runs(event):
    """List all test runs, optionally filtered."""
    try:
        table = dynamodb.Table(TEST_RUNS_TABLE)
        
        # Parse query parameters
        params = event.get("queryStringParameters") or {}
        limit = int(params.get("limit", 20))
        status_filter = params.get("status")
        fault_type_filter = params.get("fault_type")
        
        # Scan the table (for MVP; use Query with GSI for production)
        response = table.scan()
        items = response.get("Items", [])
        
        # Apply filters
        if status_filter:
            items = [i for i in items if i.get("status") == status_filter]
        if fault_type_filter:
            items = [i for i in items if i.get("fault_type") == fault_type_filter]
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit results
        items = items[:limit]
        
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "runs": items,
                "count": len(items),
            }),
        }
        
    except Exception as e:
        print(f"[API] Error listing runs: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def get_run(run_id):
    """Get a specific test run by ID."""
    try:
        table = dynamodb.Table(TEST_RUNS_TABLE)
        
        response = table.get_item(Key={"run_id": run_id})
        item = response.get("Item")
        
        if not item:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": f"Run {run_id} not found"}),
            }
        
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(item),
        }
        
    except Exception as e:
        print(f"[API] Error getting run: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def get_run_report(run_id):
    """Get the audit report for a specific run."""
    try:
        # First get the run to find the report S3 key
        run_table = dynamodb.Table(TEST_RUNS_TABLE)
        run_response = run_table.get_item(Key={"run_id": run_id})
        run = run_response.get("Item")
        
        if not run:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": f"Run {run_id} not found"}),
            }
        
        report_key = run.get("report_s3_key")
        if not report_key:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": "No report available for this run"}),
            }
        
        # Get the report from S3
        s3_response = s3_client.get_object(
            Bucket=REPORTS_BUCKET,
            Key=report_key,
        )
        report_body = s3_response["Body"].read().decode("utf-8")
        
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": report_body,
        }
        
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Report file not found in S3"}),
            }
        raise
    except Exception as e:
        print(f"[API] Error getting report: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def compare_runs(event):
    """Compare two runs side by side."""
    try:
        body = json.loads(event.get("body", "{}"))
        run_id_a = body.get("run_id_a")
        run_id_b = body.get("run_id_b")
        
        if not run_id_a or not run_id_b:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Both run_id_a and run_id_b are required"}),
            }
        
        table = dynamodb.Table(TEST_RUNS_TABLE)
        
        # Get both runs
        response_a = table.get_item(Key={"run_id": run_id_a})
        response_b = table.get_item(Key={"run_id": run_id_b})
        
        run_a = response_a.get("Item")
        run_b = response_b.get("Item")
        
        if not run_a:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": f"Run {run_id_a} not found"}),
            }
        
        if not run_b:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": f"Run {run_id_b} not found"}),
            }
        
        # Calculate deltas
        deltas = calculate_deltas(run_a, run_b)
        
        # Get audit reports for both runs
        reports = get_audit_reports(run_a, run_b)
        
        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "run_a": run_a,
                "run_b": run_b,
                "deltas": deltas,
                "reports": reports,
                "warning": get_comparison_warning(run_a, run_b),
            }),
        }
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        print(f"[API] Error comparing runs: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def calculate_deltas(run_a, run_b):
    """Calculate deltas between two runs."""
    deltas = {}
    
    # Score delta
    score_a = run_a.get("resilience_score", 0)
    score_b = run_b.get("resilience_score", 0)
    deltas["score"] = {
        "value_a": score_a,
        "value_b": score_b,
        "delta": score_b - score_a,
        "improved": score_b > score_a,
    }
    
    # RTO delta
    rto_a = run_a.get("rto_seconds", 0)
    rto_b = run_b.get("rto_seconds", 0)
    deltas["rto"] = {
        "value_a": rto_a,
        "value_b": rto_b,
        "delta": rto_b - rto_a,
        "improved": rto_b < rto_a,  # Lower RTO is better
    }
    
    # RPO delta
    rpo_a = run_a.get("rpo_seconds", 0)
    rpo_b = run_b.get("rpo_seconds", 0)
    deltas["rpo"] = {
        "value_a": rpo_a,
        "value_b": rpo_b,
        "delta": rpo_b - rpo_a,
        "improved": rpo_b < rpo_a,  # Lower RPO is better
    }
    
    return deltas


def get_audit_reports(run_a, run_b):
    """Get audit reports for both runs."""
    reports = {}
    
    for label, run in [("a", run_a), ("b", run_b)]:
        report_key = run.get("report_s3_key")
        if report_key:
            try:
                s3_response = s3_client.get_object(
                    Bucket=REPORTS_BUCKET,
                    Key=report_key,
                )
                reports[label] = json.loads(s3_response["Body"].read().decode("utf-8"))
            except Exception:
                reports[label] = None
        else:
            reports[label] = None
    
    return reports


def get_comparison_warning(run_a, run_b):
    """Generate a warning if the comparison may not be apples-to-apples."""
    if run_a.get("fault_type") != run_b.get("fault_type"):
        return "Warning: These runs have different fault types. Comparison may not be apples-to-apples."
    return None
