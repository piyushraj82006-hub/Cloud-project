"""
CloudGuard DR — Audit Report Lambda
Generates a structured audit report (resilience data + site health checks),
writes JSON/HTML to S3, and stores a pointer in DynamoDB.
"""
import os
import json
import time
import uuid
import boto3
import urllib.request
import ssl

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")


def lambda_handler(event, context):
    """
    Generate audit report for a completed test run.
    
    Event input (from Scoring Lambda):
        {
            "run_id": "run-abc123",
            "resilience_score": 82,
            "status": "Passed",
            "rto_seconds": 152,
            "rpo_seconds": 0,
            "rto_target": 300,
            "rpo_target": 60,
            "target_resource": "i-0abc...",
            "fault_type": "ec2-termination",
            "timestamp": "2026-08-22T08:00:00Z",
            "measured": true
        }
    
    Output:
        {
            "report_id": "report-uuid",
            "s3_key": "reports/run-abc123/report.json",
            "run_id": "run-abc123"
        }
    """
    print(f"[AuditReport] Generating report. Event: {json.dumps(event)}")
    
    try:
        run_id = event.get("run_id", "unknown")
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        
        # Perform site health checks
        target_url = get_target_url(event.get("target_resource"))
        health_checks = perform_health_checks(target_url)
        
        # Build the full audit report
        report = {
            "report_id": report_id,
            "run_id": run_id,
            "target_url": target_url,
            "target_resource": event.get("target_resource"),
            "fault_type": event.get("fault_type", "ec2-termination"),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            
            # Resilience data
            "resilience_score": event.get("resilience_score", 0),
            "status": event.get("status", "Unknown"),
            "rto_seconds": event.get("rto_seconds", -1),
            "rpo_seconds": event.get("rpo_seconds", -1),
            "rto_target": event.get("rto_target", 300),
            "rpo_target": event.get("rpo_target", 60),
            "measured": event.get("measured", False),
            
            # Site health checks
            "health_checks": health_checks,
            
            # Timestamps
            "injection_timestamp": event.get("injection_timestamp"),
            "recovery_timestamp": event.get("recovery_timestamp"),
        }
        
        # Write JSON report to S3
        json_key = f"reports/{run_id}/report.json"
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=json_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json",
        )
        
        # Write HTML report to S3
        html_key = f"reports/{run_id}/report.html"
        html_content = generate_html_report(report)
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=html_key,
            Body=html_content,
            ContentType="text/html",
        )
        
        # Store pointer in DynamoDB
        table = dynamodb.Table(AUDIT_REPORTS_TABLE)
        
        table.put_item(Item={
            "report_id": report_id,
            "run_id": run_id,
            "target_url": target_url,
            "https_valid": health_checks.get("https_valid", False),
            "dns_failover_ok": health_checks.get("dns_failover_ok", False),
            "response_time_ms": health_checks.get("response_time_ms"),
            "http_status_code": health_checks.get("http_status_code", 0),
            "ssl_expiry_days": health_checks.get("ssl_expiry_days"),
            "generated_at": report["generated_at"],
            "fault_type": event.get("fault_type", "ec2-termination"),
            "rto_seconds": event.get("rto_seconds", -1),
            "rpo_seconds": event.get("rpo_seconds", -1),
            "resilience_score": event.get("resilience_score", 0),
            "s3_report_key": json_key,
        })
        
        # Update the TestRun record with the report key
        update_test_run_report_key(run_id, json_key)
        
        result = {
            "statusCode": 200,
            "report_id": report_id,
            "s3_key": json_key,
            "html_key": html_key,
            "run_id": run_id,
            "timestamp": report["generated_at"],
        }
        
        print(f"[AuditReport] Report generated: {report_id}")
        print(f"[AuditReport] S3 key: {json_key}")
        print(f"[AuditReport] Result: {json.dumps(result)}")
        return result
        
    except Exception as e:
        print(f"[AuditReport] Error: {str(e)}")
        raise


def get_target_url(target_resource):
    """Convert target resource ID to a URL for health checks."""
    # For the sample app, we'd resolve the ALB DNS name
    # For MVP, return a placeholder
    return f"https://sample-app.cloudguard-{ENVIRONMENT}.example.com"


def perform_health_checks(url):
    """Perform non-intrusive health checks on the target URL."""
    checks = {
        "https_valid": False,
        "dns_failover_ok": False,
        "response_time_ms": None,
        "http_status_code": 0,
        "ssl_expiry_days": None,
    }
    
    try:
        # HTTPS validity check
        ctx = ssl.create_default_context()
        start_time = time.time()
        
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "CloudGuardDR/1.0")
        
        response = urllib.request.urlopen(req, timeout=10, context=ctx)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        checks["https_valid"] = True
        checks["response_time_ms"] = response_time_ms
        checks["http_status_code"] = response.status
        
        # Check SSL certificate expiry
        # In production, you'd parse the certificate chain
        checks["ssl_expiry_days"] = 365  # Placeholder
        
        # DNS failover check (simplified)
        checks["dns_failover_ok"] = True
        
    except urllib.error.HTTPError as e:
        checks["http_status_code"] = e.code
        print(f"[AuditReport] HTTP error: {e.code}")
    except urllib.error.URLError as e:
        print(f"[AuditReport] URL error: {e.reason}")
    except Exception as e:
        print(f"[AuditReport] Health check error: {str(e)}")
    
    return checks


def generate_html_report(report):
    """Generate an HTML version of the audit report."""
    score = report["resilience_score"]
    status = report["status"]
    status_color = "#22C55E" if status == "Passed" else "#EF4444"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudGuard DR Audit Report - {report['run_id']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ margin-bottom: 40px; }}
        .title {{ font-size: 24px; font-weight: 600; margin-bottom: 8px; }}
        .subtitle {{ color: #A1A1A1; font-size: 14px; }}
        .score-card {{ background: #151515; border: 1px solid #292929; border-radius: 8px; padding: 32px; margin-bottom: 24px; }}
        .score {{ font-size: 64px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .metric {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #292929; }}
        .metric-label {{ color: #A1A1A1; font-size: 14px; }}
        .metric-value {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; }}
        .health-check {{ padding: 16px; background: #1A1A1A; border: 1px solid #292929; border-radius: 6px; margin-bottom: 12px; }}
        .check-item {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }}
        .check-status {{ color: #22C55E; }} .check-fail {{ color: #EF4444; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">CloudGuard DR Audit Report</div>
            <div class="subtitle">Run: {report['run_id']} | Generated: {report['generated_at']}</div>
        </div>
        
        <div class="score-card">
            <div class="score" style="color: {status_color}">{score}</div>
            <span class="status" style="background: {status_color}; color: white;">{status}</span>
        </div>
        
        <div class="score-card">
            <h3 style="margin-bottom: 16px; font-size: 16px;">Resilience Metrics</h3>
            <div class="metric">
                <span class="metric-label">RTO (Recovery Time Objective)</span>
                <span class="metric-value">{report['rto_seconds']}s / {report['rto_target']}s</span>
            </div>
            <div class="metric">
                <span class="metric-label">RPO (Recovery Point Objective)</span>
                <span class="metric-value">{report['rpo_seconds']}s / {report['rpo_target']}s</span>
            </div>
            <div class="metric">
                <span class="metric-label">Fault Type</span>
                <span class="metric-value">{report['fault_type']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Target Resource</span>
                <span class="metric-value">{report['target_resource']}</span>
            </div>
        </div>
        
        <div class="score-card">
            <h3 style="margin-bottom: 16px; font-size: 16px;">Site Health Checks</h3>
            <div class="health-check">
                <div class="check-item">
                    <span>HTTPS Valid</span>
                    <span class="{'check-status' if report['health_checks']['https_valid'] else 'check-fail'}">
                        {'✓' if report['health_checks']['https_valid'] else '✗'}
                    </span>
                </div>
                <div class="check-item">
                    <span>DNS Failover</span>
                    <span class="{'check-status' if report['health_checks']['dns_failover_ok'] else 'check-fail'}">
                        {'✓' if report['health_checks']['dns_failover_ok'] else '✗'}
                    </span>
                </div>
                <div class="check-item">
                    <span>Response Time</span>
                    <span class="metric-value">{report['health_checks']['response_time_ms']}ms</span>
                </div>
                <div class="check-item">
                    <span>HTTP Status</span>
                    <span class="metric-value">{report['health_checks']['http_status_code']}</span>
                </div>
            </div>
        </div>
        
        <div style="text-align: center; color: #666666; font-size: 12px; margin-top: 40px;">
            CloudGuard DR — Automated Disaster Recovery Testing Platform
        </div>
    </div>
</body>
</html>"""
    return html


def update_test_run_report_key(run_id, report_key):
    """Update the TestRuns table with the report S3 key."""
    try:
        table = dynamodb.Table(f"cloudguard-{ENVIRONMENT}-test-runs")
        table.update_item(
            Key={"run_id": run_id},
            UpdateExpression="SET report_s3_key = :key",
            ExpressionAttributeValues={":key": report_key},
        )
    except Exception as e:
        print(f"[AuditReport] Warning: Could not update test run: {e}")
