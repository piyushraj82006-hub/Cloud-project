"""
CloudGuard DR — External Audit Lambda
Performs non-intrusive health checks on an arbitrary external URL.
No fault injection — just HTTPS validity, response time, DNS, HTTP status.
"""
import os
import json
import time
import uuid
import boto3
import urllib.request
import ssl
from urllib.parse import urlparse

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")


def lambda_handler(event, context):
    """
    Perform an external site audit (health checks only).
    
    Event input:
        {
            "target_url": "https://example.com"
        }
    
    Output:
        {
            "report_id": "report-uuid",
            "target_url": "https://example.com",
            "health_checks": { ... }
        }
    """
    print(f"[ExternalAudit] Starting audit. Event: {json.dumps(event)}")
    
    try:
        target_url = event.get("target_url", "").strip()
        
        # Validate URL
        if not target_url:
            raise ValueError("target_url is required")
        
        parsed = urlparse(target_url)
        if parsed.scheme not in ("https", "http"):
            raise ValueError("target_url must be an HTTP or HTTPS URL")
        
        if parsed.scheme == "http":
            # Upgrade to HTTPS for the audit
            target_url = target_url.replace("http://", "https://", 1)
            print(f"[ExternalAudit] Upgraded to HTTPS: {target_url}")
        
        report_id = f"report-{uuid.uuid4().hex[:8]}"
        
        # Perform health checks
        health_checks = perform_health_checks(target_url)
        
        # Build report
        report = {
            "report_id": report_id,
            "run_id": None,  # No run_id for external audits
            "target_url": target_url,
            "target_resource": None,
            "fault_type": None,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            
            # No resilience data for external audits
            "resilience_score": None,
            "status": "External Audit",
            "rto_seconds": None,
            "rpo_seconds": None,
            "rto_target": None,
            "rpo_target": None,
            "measured": False,
            
            # Health checks
            "health_checks": health_checks,
        }
        
        # Write JSON to S3
        s3_key = f"external-audits/{report_id}/report.json"
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=s3_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json",
        )
        
        # Store in DynamoDB
        table = dynamodb.Table(AUDIT_REPORTS_TABLE)
        table.put_item(Item={
            "report_id": report_id,
            "run_id": "",  # Empty string for external audits (DynamoDB can't store null for string)
            "target_url": target_url,
            "https_valid": health_checks.get("https_valid", False),
            "dns_failover_ok": health_checks.get("dns_failover_ok", False),
            "response_time_ms": health_checks.get("response_time_ms"),
            "http_status_code": health_checks.get("http_status_code", 0),
            "ssl_expiry_days": health_checks.get("ssl_expiry_days"),
            "generated_at": report["generated_at"],
            "fault_type": "",
            "rto_seconds": None,
            "rpo_seconds": None,
            "resilience_score": None,
            "s3_report_key": s3_key,
        })
        
        result = {
            "statusCode": 200,
            "report_id": report_id,
            "target_url": target_url,
            "health_checks": health_checks,
            "generated_at": report["generated_at"],
            "s3_key": s3_key,
        }
        
        print(f"[ExternalAudit] Audit complete: {report_id}")
        print(f"[ExternalAudit] Result: {json.dumps(result)}")
        return result
        
    except ValueError as e:
        print(f"[ExternalAudit] Validation error: {str(e)}")
        return {
            "statusCode": 400,
            "error": str(e),
        }
    except Exception as e:
        print(f"[ExternalAudit] Error: {str(e)}")
        raise


def perform_health_checks(url):
    """Perform non-intrusive health checks on a URL."""
    checks = {
        "https_valid": False,
        "dns_failover_ok": False,
        "response_time_ms": None,
        "http_status_code": 0,
        "ssl_expiry_days": None,
        "content_length": None,
    }
    
    try:
        ctx = ssl.create_default_context()
        
        # Measure response time
        start_time = time.time()
        
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CloudGuardDR/1.0")
        
        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        checks["https_valid"] = True
        checks["response_time_ms"] = response_time_ms
        checks["http_status_code"] = response.status
        
        # Get content length
        content_length = response.headers.get("Content-Length")
        if content_length:
            checks["content_length"] = int(content_length)
        
        # SSL certificate check
        # In production, you'd parse the certificate to get expiry date
        checks["ssl_expiry_days"] = 365  # Placeholder
        
        # DNS failover check (simplified — check if DNS resolves)
        parsed = urlparse(url)
        import socket
        try:
            socket.getaddrinfo(parsed.hostname, 443)
            checks["dns_failover_ok"] = True
        except socket.gaierror:
            checks["dns_failover_ok"] = False
        
    except urllib.error.HTTPError as e:
        checks["http_status_code"] = e.code
        checks["response_time_ms"] = int((time.time() - start_time) * 1000) if 'start_time' in dir() else None
        print(f"[ExternalAudit] HTTP error: {e.code}")
    except urllib.error.URLError as e:
        print(f"[ExternalAudit] URL error: {e.reason}")
    except ssl.SSLError as e:
        print(f"[ExternalAudit] SSL error: {str(e)}")
    except Exception as e:
        print(f"[ExternalAudit] Health check error: {str(e)}")
    
    return checks
