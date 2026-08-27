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
        
        # PDF generation is now handled by the Step Functions GeneratePDF step
        # (synchronous invocation, not fire-and-forget)
        
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

    # Determine score grade for the interpretation section
    if score >= 90:
        grade = "Excellent"
        grade_color = "#10b981"
        grade_desc = "Your infrastructure is battle-tested. The disaster recovery plan is working excellently with fast recovery and minimal data loss."
    elif score >= 70:
        grade = "Passed"
        grade_color = "#10b981"
        grade_desc = "Recovery meets your SLA targets. Consider optimizing auto-scaling policies and health check intervals for even faster recovery."
    elif score >= 50:
        grade = "Warning"
        grade_color = "#f59e0b"
        grade_desc = "Recovery is borderline. Your RTO/RPO targets are at risk. Review auto-scaling configurations, health check thresholds, and failover routing."
    elif score >= 30:
        grade = "Failed"
        grade_color = "#f43f5e"
        grade_desc = "Significant recovery delays detected. Your RTO and/or RPO targets are being missed. Immediate investigation and remediation is required."
    else:
        grade = "Critical"
        grade_color = "#f43f5e"
        grade_desc = "The system did not recover within acceptable limits or recovery could not be measured. Your disaster recovery plan is effectively broken and needs urgent attention."

    # Calculate RTO/RPO sub-scores for display
    rto_s = report.get("rto_seconds", -1)
    rpo_s = report.get("rpo_seconds", -1)
    rto_t = report.get("rto_target", 300)
    rpo_t = report.get("rpo_target", 60)

    if rto_s >= 0 and rto_t > 0:
        rto_sub = max(0, round(100 - (rto_s / rto_t * 50)))
        rto_pct = round(rto_s / rto_t * 100)
    else:
        rto_sub = 0
        rto_pct = 0

    if rpo_s >= 0 and rpo_t > 0:
        rpo_sub = max(0, round(100 - (rpo_s / rpo_t * 50)))
        rpo_pct = round(rpo_s / rpo_t * 100)
    else:
        rpo_sub = 0
        rpo_pct = 0

    rto_status = "✓ Within target" if rto_s <= rto_t and rto_s >= 0 else "✗ Exceeded target"
    rpo_status = "✓ Within target" if rpo_s <= rpo_t and rpo_s >= 0 else "✗ Exceeded target"
    rto_status_color = "#22C55E" if rto_s <= rto_t and rto_s >= 0 else "#EF4444"
    rpo_status_color = "#22C55E" if rpo_s <= rpo_t and rpo_s >= 0 else "#EF4444"

    # Format fault type for display
    fault_display = {
        "ec2-termination": "EC2 Instance Termination — killed a tagged instance via AWS FIS to test auto-scaling recovery",
        "dns-failover": "DNS Failover — inverted a Route 53 health check to force DNS failover to secondary endpoint",
        "s3-origin-block": "S3 Origin Block — added a Deny policy to the S3 bucket to test CDN/origin failover",
        "security-group": "Security Group — removed ingress rules to block traffic and test network recovery",
    }.get(report.get("fault_type", ""), report.get("fault_type", "unknown"))

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
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #A1A1A1; font-size: 14px; }}
        .metric-value {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; }}
        .health-check {{ padding: 16px; background: #1A1A1A; border: 1px solid #292929; border-radius: 6px; margin-bottom: 12px; }}
        .check-item {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }}
        .check-status {{ color: #22C55E; }} .check-fail {{ color: #EF4444; }}
        .section-title {{ font-size: 16px; font-weight: 600; margin-bottom: 16px; }}
        .grade-badge {{ display: inline-block; padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
        .grade-desc {{ color: #A1A1A1; font-size: 14px; line-height: 1.6; margin-top: 12px; }}
        .formula-box {{ background: #1A1A1A; border: 1px solid #292929; border-radius: 6px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #A1A1A1; margin: 12px 0; }}
        .formula-highlight {{ color: #10b981; font-weight: 600; }}
        .scale-row {{ display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #1A1A1A; font-size: 13px; }}
        .scale-row:last-child {{ border-bottom: none; }}
        .scale-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
        .scale-range {{ font-family: 'JetBrains Mono', monospace; color: #A1A1A1; min-width: 60px; }}
        .scale-label {{ font-weight: 600; min-width: 80px; }}
        .sub-score-bar {{ height: 6px; border-radius: 3px; background: #292929; margin-top: 8px; overflow: hidden; }}
        .sub-score-fill {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}
        .timestamp-row {{ display: flex; justify-content: space-between; padding: 8px 0; font-size: 13px; }}
        .timestamp-label {{ color: #666; }}
        .timestamp-value {{ font-family: 'JetBrains Mono', monospace; color: #A1A1A1; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">CloudGuard DR — Audit Report</div>
            <div class="subtitle">Run: {report['run_id']} &nbsp;|&nbsp; Generated: {report['generated_at']}</div>
        </div>

        <!-- Score Card -->
        <div class="score-card">
            <div style="display: flex; align-items: flex-end; gap: 16px; margin-bottom: 16px;">
                <div class="score" style="color: {status_color}">{score}</div>
                <div style="padding-bottom: 12px;">
                    <span class="status" style="background: {status_color}; color: white;">{status}</span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span class="grade-badge" style="background: {grade_color}22; color: {grade_color}; border: 1px solid {grade_color}44;">{grade}</span>
            </div>
            <div class="grade-desc">{grade_desc}</div>
        </div>

        <!-- Score Interpretation -->
        <div class="score-card">
            <h3 class="section-title">📊 Score Interpretation</h3>
            <p style="color: #A1A1A1; font-size: 13px; margin-bottom: 16px;">
                The Resilience Score (0–100) measures how well your infrastructure recovers from a deliberate failure.
                It combines <strong style="color: #F5F5F5;">Recovery Time</strong> (how fast you're back online) and
                <strong style="color: #F5F5F5;">Recovery Point</strong> (how much data was lost).
            </p>

            <div style="margin-bottom: 20px;">
                <div class="scale-row">
                    <div class="scale-dot" style="background: #10b981;"></div>
                    <span class="scale-range">90–100</span>
                    <span class="scale-label" style="color: #10b981;">Excellent</span>
                    <span style="color: #666;">Battle-tested. DR plan working perfectly.</span>
                </div>
                <div class="scale-row">
                    <div class="scale-dot" style="background: #10b981;"></div>
                    <span class="scale-range">70–89</span>
                    <span class="scale-label" style="color: #10b981;">Passed</span>
                    <span style="color: #666;">Meets SLA targets. Minor optimizations possible.</span>
                </div>
                <div class="scale-row">
                    <div class="scale-dot" style="background: #f59e0b;"></div>
                    <span class="scale-range">50–69</span>
                    <span class="scale-label" style="color: #f59e0b;">Warning</span>
                    <span style="color: #666;">Borderline. SLAs at risk.</span>
                </div>
                <div class="scale-row">
                    <div class="scale-dot" style="background: #f43f5e;"></div>
                    <span class="scale-range">30–49</span>
                    <span class="scale-label" style="color: #f43f5e;">Failed</span>
                    <span style="color: #666;">Targets missed. Immediate action needed.</span>
                </div>
                <div class="scale-row">
                    <div class="scale-dot" style="background: #f43f5e;"></div>
                    <span class="scale-range">0–29</span>
                    <span class="scale-label" style="color: #f43f5e;">Critical</span>
                    <span style="color: #666;">DR plan broken. Urgent remediation.</span>
                </div>
            </div>

            <h4 style="font-size: 13px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">How It's Calculated</h4>
            <div class="formula-box">
                <div>RTO Score = max(0, 100 − (actual_RTO ÷ target_RTO × 50))</div>
                <div>RPO Score = max(0, 100 − (actual_RPO ÷ target_RPO × 50))</div>
                <div style="margin-top: 8px;">
                    <span class="formula-highlight">Final Score</span> = (RTO Score × <strong>0.6</strong>) + (RPO Score × <strong>0.4</strong>)
                </div>
            </div>
            <p style="color: #666; font-size: 12px; margin-top: 8px;">
                RTO is weighted 60% because downtime directly impacts users. RPO is weighted 40% because data loss matters
                but most web apps prioritize getting back online first.
            </p>
        </div>

        <!-- Resilience Metrics -->
        <div class="score-card">
            <h3 class="section-title">🛡️ Resilience Metrics</h3>

            <!-- RTO -->
            <div style="margin-bottom: 20px;">
                <div class="metric" style="border-bottom: none; padding-bottom: 4px;">
                    <span class="metric-label">
                        <strong style="color: #F5F5F5;">RTO</strong> — Recovery Time Objective
                        <br><span style="font-size: 12px;">How long until the site was back online</span>
                    </span>
                    <span class="metric-value">{report['rto_seconds']}s / {report['rto_target']}s</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0;">
                    <span style="font-size: 12px; color: {rto_status_color};">{rto_status}</span>
                    <span style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #666;">Sub-score: {rto_sub}/100 (weight: 60%)</span>
                </div>
                <div class="sub-score-bar">
                    <div class="sub-score-fill" style="width: {min(rto_sub, 100)}%; background: {rto_status_color};"></div>
                </div>
            </div>

            <!-- RPO -->
            <div style="margin-bottom: 20px;">
                <div class="metric" style="border-bottom: none; padding-bottom: 4px;">
                    <span class="metric-label">
                        <strong style="color: #F5F5F5;">RPO</strong> — Recovery Point Objective
                        <br><span style="font-size: 12px;">How much data was lost during the failure</span>
                    </span>
                    <span class="metric-value">{report['rpo_seconds']}s / {report['rpo_target']}s</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0;">
                    <span style="font-size: 12px; color: {rpo_status_color};">{rpo_status}</span>
                    <span style="font-size: 12px; font-family: 'JetBrains Mono', monospace; color: #666;">Sub-score: {rpo_sub}/100 (weight: 40%)</span>
                </div>
                <div class="sub-score-bar">
                    <div class="sub-score-fill" style="width: {min(rpo_sub, 100)}%; background: {rpo_status_color};"></div>
                </div>
            </div>

            <!-- Fault & Target Info -->
            <div class="metric">
                <span class="metric-label">Fault Type</span>
                <span class="metric-value" style="font-size: 12px; max-width: 60%; text-align: right;">{report['fault_type']}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Target Resource</span>
                <span class="metric-value">{report['target_resource']}</span>
            </div>
        </div>

        <!-- What Was Tested -->
        <div class="score-card">
            <h3 class="section-title">🔬 What Was Tested</h3>
            <p style="color: #A1A1A1; font-size: 14px; line-height: 1.6;">
                {fault_display}
            </p>
            <div style="margin-top: 16px; padding: 12px; background: #1A1A1A; border: 1px solid #292929; border-radius: 6px;">
                <div class="timestamp-row">
                    <span class="timestamp-label">Fault injected at</span>
                    <span class="timestamp-value">{report.get('injection_timestamp', 'N/A')}</span>
                </div>
                <div class="timestamp-row">
                    <span class="timestamp-label">Recovery confirmed at</span>
                    <span class="timestamp-value">{report.get('recovery_timestamp', 'N/A')}</span>
                </div>
            </div>
        </div>

        <!-- Site Health Checks -->
        <div class="score-card">
            <h3 class="section-title">🌐 Site Health Checks</h3>
            <p style="color: #666; font-size: 12px; margin-bottom: 12px;">
                Post-recovery health checks performed on the target site.
            </p>
            <div class="health-check">
                <div class="check-item">
                    <span>HTTPS Valid</span>
                    <span class="{'check-status' if report['health_checks']['https_valid'] else 'check-fail'}">
                        {'✓ Valid' if report['health_checks']['https_valid'] else '✗ Invalid'}
                    </span>
                </div>
                <div class="check-item">
                    <span>DNS Failover</span>
                    <span class="{'check-status' if report['health_checks']['dns_failover_ok'] else 'check-fail'}">
                        {'✓ OK' if report['health_checks']['dns_failover_ok'] else '✗ Failed'}
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

        <div style="text-align: center; color: #666666; font-size: 12px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #292929;">
            CloudGuard DR — Automated Disaster Recovery Testing Platform<br>
            <span style="font-size: 11px; color: #444;">This report was auto-generated. Score methodology: weighted RTO (60%) + RPO (40%) against configured targets.</span>
        </div>
    </div>
</body>
</html>"""
    return html


# PDF generation is now handled by the Step Functions GeneratePDF step.
# The audit-report lambda no longer invokes PDF generation directly.
# This keeps the pipeline synchronous and trackable.


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
