"""
CloudGuard DR — API Lambda
Handles all API Gateway endpoints:
  GET /runs              — List all test runs
  GET /runs/{run_id}     — Get a specific test run
  GET /runs/{run_id}/report — Get the audit report for a run
  POST /compare          — Compare two runs side by side
  POST /compare-sites    — Compare two external sites by URL
  POST /dr-test          — Trigger a DR test (fault injection)
  GET /health            — Health check endpoint
"""
import os
import json
import sys
import time
import ssl
import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError

# Add pdf-report lambda to path so we can import root_cause_analyzer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pdf-report'))
try:
    from root_cause_analyzer import analyze_report
except ImportError:
    analyze_report = None

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
TEST_RUNS_TABLE = os.environ.get("TEST_RUNS_TABLE", f"cloudguard-{ENVIRONMENT}-test-runs")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")
COMPARISONS_TABLE = os.environ.get("COMPARISONS_TABLE", f"cloudguard-{ENVIRONMENT}-comparisons")
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

    if path == "/compare-sites" and http_method == "POST":
        return compare_sites(event)

    if path == "/comparisons" and http_method == "GET":
        return list_comparisons(event)

    if path.startswith("/comparisons/") and http_method == "GET":
        comparison_id = path.split("/")[2]
        return get_comparison(comparison_id)

    if path == "/recommendations" and http_method == "GET":
        return get_recommendations(event)

    if path == "/dr-test" and http_method == "POST":
        return trigger_dr_test(event)

    if path == "/report/pdf" and http_method == "POST":
        return generate_pdf(event)

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
    """Get the audit report for a specific run.
    
    Checks both test-runs table (DR reports) and audit-reports table
    (SEO, competitor reports) to find the correct report.
    """
    try:
        # First get the run to find the report S3 key
        run_table = dynamodb.Table(TEST_RUNS_TABLE)
        run_response = run_table.get_item(Key={"run_id": run_id})
        run = run_response.get("Item")
        
        report_key = None
        fault_type = None
        
        if run:
            report_key = run.get("report_s3_key")
            fault_type = run.get("fault_type", "ec2-termination")
        
        # If not found in test-runs, check audit-reports table
        # (SEO, competitor reports are stored there)
        if not report_key:
            audit_table = dynamodb.Table(AUDIT_REPORTS_TABLE)
            audit_response = audit_table.query(
                IndexName="run_id-index",
                KeyConditionExpression=boto3.dynamodb.conditions.Key("run_id").eq(run_id)
            )
            items = audit_response.get("Items", [])
            if items:
                report_key = items[0].get("s3_report_key")
                fault_type = items[0].get("fault_type", "ec2-termination")
        
        if not report_key:
            # Also try to get report_id from the run_id (for SEO reports where report_id = seo-xxx)
            # Try direct lookup in audit-reports by report_id
            try:
                audit_table = dynamodb.Table(AUDIT_REPORTS_TABLE)
                audit_response = audit_table.get_item(Key={"report_id": run_id})
                item = audit_response.get("Item")
                if item:
                    report_key = item.get("s3_report_key")
                    fault_type = item.get("fault_type", "ec2-termination")
            except Exception:
                pass
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
        report_body = json.loads(s3_response["Body"].read().decode("utf-8"))

        # Detect report type and attach weak points analysis
        report_type = _detect_report_type(report_body)
        weak_points = []
        if analyze_report and report_type:
            try:
                weak_points = analyze_report(report_type, report_body) or []
            except Exception as e:
                print(f"[API] Root cause analysis failed: {str(e)}")

        report_body["weak_points"] = weak_points
        report_body["report_type"] = report_type

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(report_body),
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


def _detect_report_type(report_data):
    """Detect report type from content."""
    if report_data.get("seo_score") is not None or report_data.get("seo_checks"):
        return "seo"
    if report_data.get("site_analyses") or report_data.get("gap_analysis") or report_data.get("feature_matrix"):
        return "competitor"
    if report_data.get("resilience_score") is not None:
        return "dr-test"
    return None


def generate_pdf(event):
    """Invoke the PDF report Lambda to generate a PDF."""
    try:
        body = json.loads(event.get("body", "{}"))
        report_type = body.get("report_type")
        report_id = body.get("report_id")

        if not report_type or not report_id:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "report_type and report_id are required"}),
            }

        lambda_client = boto3.client("lambda")
        pdf_function_name = f"cloudguard-{ENVIRONMENT}-pdf-report"

        response = lambda_client.invoke(
            FunctionName=pdf_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(body),
        )

        payload = json.loads(response["Payload"].read().decode("utf-8"))
        status_code = payload.get("statusCode", 500)

        return {
            "statusCode": status_code,
            "headers": cors_headers(),
            "body": json.dumps(payload),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        print(f"[API] Error generating PDF: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def get_comparison_warning(run_a, run_b):
    """Generate a warning if the comparison may not be apples-to-apples."""
    if run_a.get("fault_type") != run_b.get("fault_type"):
        return "Warning: These runs have different fault types. Comparison may not be apples-to-apples."
    return None


# ──────────────────────────────────────────
#  Compare Sites  (POST /compare-sites)
# ──────────────────────────────────────────

def compare_sites(event):
    """Compare two external sites by URL.

    Input:
        {
            "url_a": "https://example.com",
            "url_b": "https://competitor.com",
            "parameters": ["https_valid", "response_time_ms", ...]  // optional
        }

    Output:
        {
            "site_a": { ...metrics },
            "site_b": { ...metrics },
            "comparison": {
                "https_valid": { "a": true, "b": true, "winner": "tie" },
                "response_time_ms": { "a": 230, "b": 890, "winner": "a" },
                ...
            },
            "summary": {
                "a_wins": 3,
                "b_wins": 1,
                "ties": 2
            }
        }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        url_a = body.get("url_a", "").strip()
        url_b = body.get("url_b", "").strip()
        parameters = body.get("parameters")  # optional filter

        if not url_a or not url_b:
            return {
                "statusCode": 400,
                "headers": cors_headers(),
                "body": json.dumps({"error": "Both url_a and url_b are required"}),
            }

        # Normalize URLs
        url_a = _normalize_url(url_a)
        url_b = _normalize_url(url_b)

        print(f"[CompareSites] Comparing: {url_a} vs {url_b}")

        # Run health checks on both sites
        start = time.time()
        metrics_a = _site_health_checks(url_a)
        metrics_b = _site_health_checks(url_b)
        duration_ms = int((time.time() - start) * 1000)

        # Compare the metrics
        comparison = _compare_metrics(metrics_a, metrics_b, parameters)

        # Calculate summary
        a_wins = sum(1 for v in comparison.values() if v.get("winner") == "a")
        b_wins = sum(1 for v in comparison.values() if v.get("winner") == "b")
        ties = sum(1 for v in comparison.values() if v.get("winner") == "tie")

        result = {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "site_a": metrics_a,
                "site_b": metrics_b,
                "comparison": comparison,
                "summary": {
                    "a_wins": a_wins,
                    "b_wins": b_wins,
                    "ties": ties,
                },
                "duration_ms": duration_ms,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }),
        }

        # Save to DynamoDB for history
        comparison_id = f"cmp-{uuid.uuid4().hex[:8]}"
        _save_comparison(comparison_id, url_a, url_b, metrics_a, metrics_b, comparison, a_wins, b_wins, ties)

        # Add comparison_id to response
        result_body = json.loads(result["body"])
        result_body["comparison_id"] = comparison_id
        result["body"] = json.dumps(result_body)

        print(f"[CompareSites] Done in {duration_ms}ms — A:{a_wins} T:{ties} B:{b_wins} ({comparison_id})")
        return result

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        print(f"[CompareSites] Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def _normalize_url(url):
    """Ensure URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme == "http":
        url = url.replace("http://", "https://", 1)
    return url


def _site_health_checks(url):
    """Run comprehensive health checks on a single site."""
    result = {
        "url": url,
        "https_valid": False,
        "ssl_expiry_days": None,
        "dns_resolves": False,
        "status_code": 0,
        "response_time_ms": None,
        "content_length": None,
        # SEO — meta
        "title": None,
        "title_length": 0,
        "meta_description": None,
        "meta_desc_length": 0,
        # SEO — headings
        "has_h1": False,
        "h1_count": 0,
        "h2_count": 0,
        "h3_count": 0,
        # SEO — images
        "total_images": 0,
        "images_with_alt": 0,
        "alt_text_ratio": 0.0,
        # SEO — links
        "total_links": 0,
        "internal_links": 0,
        "external_links": 0,
        # SEO — technical
        "has_viewport": False,
        "has_og_tags": False,
        "og_tag_count": 0,
        "has_twitter_card": False,
        "has_canonical": False,
        "has_schema": False,
        "has_robots": False,
        "has_robots_noindex": False,
    }

    parsed = urlparse(url)
    ctx = ssl.create_default_context()

    # DNS check
    try:
        socket.getaddrinfo(parsed.hostname, 443)
        result["dns_resolves"] = True
    except socket.gaierror:
        print(f"[CompareSites] DNS failed for {parsed.hostname}")
        return result

    # SSL check
    try:
        import ssl as ssl_mod
        cert_info = ssl_mod.get_server_certificate((parsed.hostname, 443))
        # Simple check — if we got a cert, SSL is valid
        result["https_valid"] = True
        result["ssl_expiry_days"] = 30  # Placeholder — real impl would parse cert
    except Exception as e:
        print(f"[CompareSites] SSL check failed: {e}")

    # HTTP request
    start = time.time()
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CloudGuardDR/2.0")
        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        response_time_ms = int((time.time() - start) * 1000)

        result["status_code"] = response.status
        result["response_time_ms"] = response_time_ms
        result["https_valid"] = True

        # Content length
        content_length = response.headers.get("Content-Length")
        if content_length:
            result["content_length"] = int(content_length)

        # Read body for SEO checks
        body = response.read().decode("utf-8", errors="ignore")[:100_000]  # max 100KB

        import re

        # Title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = title_match.group(1).strip()[:200]
            result["title"] = title_text
            result["title_length"] = len(title_text)

        # Headings
        h1_matches = re.findall(r"<h1[\s>]", body, re.IGNORECASE)
        result["has_h1"] = len(h1_matches) > 0
        result["h1_count"] = len(h1_matches)
        result["h2_count"] = len(re.findall(r"<h2[\s>]", body, re.IGNORECASE))
        result["h3_count"] = len(re.findall(r"<h3[\s>]", body, re.IGNORECASE))

        # Meta description
        meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\'>]*)["\']', body, re.IGNORECASE)
        if not meta_match:
            meta_match = re.search(r'<meta[^>]*content=["\']([^"\'>]*)["\'][^>]*name=["\']description["\']', body, re.IGNORECASE)
        if meta_match:
            meta_text = meta_match.group(1).strip()[:500]
            result["meta_description"] = meta_text
            result["meta_desc_length"] = len(meta_text)

        # Images — alt text ratio
        img_tags = re.findall(r"<img\s[^>]*>", body, re.IGNORECASE | re.DOTALL)
        result["total_images"] = len(img_tags)
        images_with_alt = 0
        for img in img_tags:
            if re.search(r'alt=["\'][^"\'>]+["\']', img, re.IGNORECASE):
                images_with_alt += 1
        result["images_with_alt"] = images_with_alt
        result["alt_text_ratio"] = round(images_with_alt / len(img_tags), 2) if img_tags else 0.0

        # Links — internal vs external
        parsed_url = urlparse(url)
        base_domain = parsed_url.hostname or ""
        link_tags = re.findall(r'<a\s[^>]*href=["\']([^"\'>]+)["\']', body, re.IGNORECASE)
        result["total_links"] = len(link_tags)
        internal = 0
        external = 0
        for href in link_tags:
            if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue
            try:
                if href.startswith("/") or base_domain in href:
                    internal += 1
                else:
                    external += 1
            except Exception:
                external += 1
        result["internal_links"] = internal
        result["external_links"] = external

        # Viewport
        result["has_viewport"] = bool(re.search(r'<meta[^>]*name=["\']viewport["\']', body, re.IGNORECASE))

        # Open Graph
        og_tags = re.findall(r'<meta[^>]*property=["\']og:([^"\'>]*)["\']', body, re.IGNORECASE)
        result["has_og_tags"] = len(og_tags) > 0
        result["og_tag_count"] = len(og_tags)

        # Twitter Card
        result["has_twitter_card"] = bool(re.search(r'<meta[^>]*name=["\']twitter:', body, re.IGNORECASE))

        # Canonical URL
        canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\'>]+)["\']', body, re.IGNORECASE)
        result["has_canonical"] = canonical_match is not None

        # Structured data (JSON-LD)
        schema_count = len(re.findall(r'<script[^>]*type=["\']application/ld\+json["\']', body, re.IGNORECASE))
        result["has_schema"] = schema_count > 0

        # Robots / indexing
        robots_meta = re.search(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\'>]*)["\']', body, re.IGNORECASE)
        result["has_robots"] = robots_meta is not None
        if robots_meta:
            result["has_robots_noindex"] = "noindex" in robots_meta.group(1).lower()

    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["response_time_ms"] = int((time.time() - start) * 1000)
        print(f"[CompareSites] HTTP error for {url}: {e.code}")
    except Exception as e:
        print(f"[CompareSites] Request failed for {url}: {e}")

    return result


def _compare_metrics(metrics_a, metrics_b, parameters=None):
    """Compare two sets of site metrics.

    Returns a dict like:
        {
            "https_valid": { "a": true, "b": true, "winner": "tie" },
            "response_time_ms": { "a": 230, "b": 890, "winner": "a", "better": "lower" },
            ...
        }
    """
    # Parameter definitions
    param_defs = {
        # Health / Performance
        "https_valid":         {"type": "boolean"},
        "ssl_expiry_days":     {"type": "number", "higher_better": True},
        "dns_resolves":        {"type": "boolean"},
        "status_code":         {"type": "number", "higher_better": None},
        "response_time_ms":    {"type": "number", "higher_better": False},
        "content_length":      {"type": "number", "higher_better": True},
        # SEO — meta
        "title_length":        {"type": "number", "higher_better": None},  # 50-60 optimal
        "meta_desc_length":    {"type": "number", "higher_better": None},  # 150-160 optimal
        # SEO — headings
        "has_h1":              {"type": "boolean"},
        "h1_count":            {"type": "number", "higher_better": None},  # exactly 1 is best
        "h2_count":            {"type": "number", "higher_better": True},
        "h3_count":            {"type": "number", "higher_better": True},
        # SEO — images
        "total_images":        {"type": "number", "higher_better": True},
        "images_with_alt":     {"type": "number", "higher_better": True},
        "alt_text_ratio":      {"type": "number", "higher_better": True},
        # SEO — links
        "total_links":         {"type": "number", "higher_better": True},
        "internal_links":      {"type": "number", "higher_better": True},
        "external_links":      {"type": "number", "higher_better": None},
        # SEO — technical
        "has_viewport":        {"type": "boolean"},
        "has_og_tags":         {"type": "boolean"},
        "og_tag_count":        {"type": "number", "higher_better": True},
        "has_twitter_card":    {"type": "boolean"},
        "has_canonical":       {"type": "boolean"},
        "has_schema":          {"type": "boolean"},
        "has_robots":          {"type": "boolean"},
        "has_robots_noindex":  {"type": "boolean", "invert": True},  # noindex is bad
    }

    # Filter to requested parameters
    if parameters:
        param_defs = {k: v for k, v in param_defs.items() if k in parameters}

    comparison = {}

    for key, defn in param_defs.items():
        val_a = metrics_a.get(key)
        val_b = metrics_b.get(key)

        entry = {"a": val_a, "b": val_b}

        if defn["type"] == "boolean":
            if val_a == val_b:
                entry["winner"] = "tie"
            elif val_a is True:
                entry["winner"] = "a"
            elif val_b is True:
                entry["winner"] = "b"
            else:
                entry["winner"] = "tie"  # both false

        elif defn["type"] == "number":
            higher_better = defn.get("higher_better")

            if val_a is None and val_b is None:
                entry["winner"] = "tie"
            elif val_a is None:
                entry["winner"] = "b"
            elif val_b is None:
                entry["winner"] = "a"
            elif val_a == val_b:
                entry["winner"] = "tie"
            elif higher_better is None:
                # No clear winner direction (e.g., status code)
                entry["winner"] = "tie"
            elif higher_better:
                entry["winner"] = "a" if val_a > val_b else "b"
            else:
                entry["winner"] = "a" if val_a < val_b else "b"

            # Special case: status code — 2xx is best
            if key == "status_code":
                a_ok = 200 <= (val_a or 0) < 300
                b_ok = 200 <= (val_b or 0) < 300
                if a_ok and not b_ok:
                    entry["winner"] = "a"
                elif b_ok and not a_ok:
                    entry["winner"] = "b"
                else:
                    entry["winner"] = "tie"

            # Special case: title_length — closer to 50-60 is optimal
            if key == "title_length":
                entry["winner"] = _closer_to_range(val_a, val_b, 50, 60)

            # Special case: meta_desc_length — closer to 150-160 is optimal
            if key == "meta_desc_length":
                entry["winner"] = _closer_to_range(val_a, val_b, 150, 160)

            # Special case: h1_count — exactly 1 is best
            if key == "h1_count":
                a_dist = abs((val_a or 0) - 1)
                b_dist = abs((val_b or 0) - 1)
                if a_dist == b_dist:
                    entry["winner"] = "tie"
                else:
                    entry["winner"] = "a" if a_dist < b_dist else "b"

        # Invert boolean winner if param says so (e.g., has_robots_noindex)
        if defn.get("invert") and entry.get("winner") in ("a", "b"):
            entry["winner"] = "b" if entry["winner"] == "a" else "a"

        comparison[key] = entry

    return comparison


def _closer_to_range(val_a, val_b, low, high):
    """Determine which value is closer to the optimal range [low, high]."""
    if val_a is None and val_b is None:
        return "tie"
    if val_a is None:
        return "b"
    if val_b is None:
        return "a"

    def distance(v):
        if v < low:
            return low - v
        if v > high:
            return v - high
        return 0  # inside optimal range

    d_a = distance(val_a)
    d_b = distance(val_b)
    if d_a == d_b:
        return "tie"
    return "a" if d_a < d_b else "b"


# ──────────────────────────────────────────
#  Comparison History
# ──────────────────────────────────────────

import uuid


def _save_comparison(comparison_id, url_a, url_b, metrics_a, metrics_b, comparison, a_wins, b_wins, ties):
    """Save a site comparison to DynamoDB for history."""
    try:
        table = dynamodb.Table(COMPARISONS_TABLE)
        table.put_item(Item={
            "comparison_id": comparison_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "url_a": url_a,
            "url_b": url_b,
            "domain_a": urlparse(url_a).hostname or url_a,
            "domain_b": urlparse(url_b).hostname or url_b,
            "parameters_compared": list(comparison.keys()),
            "summary": {
                "a_wins": a_wins,
                "b_wins": b_wins,
                "ties": ties,
            },
            # Store metrics for re-comparison
            "site_a": metrics_a,
            "site_b": metrics_b,
            "comparison": comparison,
        })
        print(f"[CompareSites] Saved comparison {comparison_id}")
    except Exception as e:
        # Don't fail the request if saving history fails
        print(f"[CompareSites] Failed to save comparison: {e}")


def list_comparisons(event):
    """List past site comparisons, newest first."""
    try:
        table = dynamodb.Table(COMPARISONS_TABLE)
        params = event.get("queryStringParameters") or {}
        limit = int(params.get("limit", 20))

        response = table.scan()
        items = response.get("Items", [])

        # Sort by created_at descending
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # Slim down items for listing (don't send full metrics)
        slimmed = []
        for item in items[:limit]:
            slimmed.append({
                "comparison_id": item["comparison_id"],
                "created_at": item["created_at"],
                "url_a": item["url_a"],
                "url_b": item["url_b"],
                "domain_a": item.get("domain_a"),
                "domain_b": item.get("domain_b"),
                "summary": item.get("summary"),
                "parameters_compared": item.get("parameters_compared"),
            })

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "comparisons": slimmed,
                "count": len(slimmed),
            }),
        }

    except Exception as e:
        print(f"[API] Error listing comparisons: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def get_comparison(comparison_id):
    """Get a single comparison by ID with full metrics."""
    try:
        table = dynamodb.Table(COMPARISONS_TABLE)
        response = table.get_item(Key={"comparison_id": comparison_id})
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "headers": cors_headers(),
                "body": json.dumps({"error": f"Comparison {comparison_id} not found"}),
            }

        return {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps(item),
        }

    except Exception as e:
        print(f"[API] Error getting comparison: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


# ──────────────────────────────────────────
#  DR Recommendations  (GET /recommendations)
# ──────────────────────────────────────────

import statistics


def get_recommendations(event):
    """Analyze DR test history and generate actionable recommendations.

    Returns:
        {
            "summary": { ... },
            "recommendations": [
                {
                    "id": "rec-001",
                    "severity": "critical" | "high" | "medium" | "info",
                    "category": "rto" | "rpo" | "scoring" | "reliability" | "fault-type",
                    "title": "...",
                    "description": "...",
                    "action": "...",
                    "based_on": { ... }   // supporting data
                }
            ],
            "trends": { ... },
            "analyzed_runs": 12,
            "generated_at": "..."
        }
    """
    try:
        table = dynamodb.Table(TEST_RUNS_TABLE)
        params = event.get("queryStringParameters") or {}
        limit = int(params.get("limit", 50))

        response = table.scan()
        runs = response.get("Items", [])

        # Sort by timestamp descending
        runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        runs = runs[:limit]

        if not runs:
            return {
                "statusCode": 200,
                "headers": cors_headers(),
                "body": json.dumps({
                    "summary": {"total_runs": 0, "message": "No DR test runs found"},
                    "recommendations": [],
                    "trends": {},
                    "analyzed_runs": 0,
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }),
            }

        # Extract metrics
        scores = [r.get("resilience_score", 0) for r in runs if r.get("resilience_score") is not None]
        rtos = [r.get("rto_seconds", 0) for r in runs if r.get("rto_seconds") is not None]
        rpos = [r.get("rpo_seconds", 0) for r in runs if r.get("rpo_seconds") is not None]
        statuses = [r.get("status", "") for r in runs]
        fault_types = [r.get("fault_type", "unknown") for r in runs]

        passed = sum(1 for s in statuses if s == "Passed")
        failed = sum(1 for s in statuses if s == "Failed")
        total = len(runs)

        # Trends (compare first half vs second half)
        half = max(len(runs) // 2, 1)
        recent = runs[:half]
        older = runs[half:]

        recent_scores = [r.get("resilience_score", 0) for r in recent if r.get("resilience_score") is not None]
        older_scores = [r.get("resilience_score", 0) for r in older if r.get("resilience_score") is not None]
        recent_avg_score = statistics.mean(recent_scores) if recent_scores else 0
        older_avg_score = statistics.mean(older_scores) if older_scores else 0
        score_trend = "improving" if recent_avg_score > older_avg_score else "declining" if recent_avg_score < older_avg_score else "stable"

        recent_rtos = [r.get("rto_seconds", 0) for r in recent if r.get("rto_seconds") is not None]
        older_rtos = [r.get("rto_seconds", 0) for r in older if r.get("rto_seconds") is not None]
        recent_avg_rto = statistics.mean(recent_rtos) if recent_rtos else 0
        older_avg_rto = statistics.mean(older_rtos) if older_rtos else 0
        rto_trend = "improving" if recent_avg_rto < older_avg_rto else "degrading" if recent_avg_rto > older_avg_rto else "stable"

        # Failure rate by fault type
        fault_failures = {}
        fault_totals = {}
        for r in runs:
            ft = r.get("fault_type", "unknown")
            fault_totals[ft] = fault_totals.get(ft, 0) + 1
            if r.get("status") == "Failed":
                fault_failures[ft] = fault_failures.get(ft, 0) + 1

        # Build summary
        summary = {
            "total_runs": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "avg_score": round(statistics.mean(scores), 1) if scores else 0,
            "avg_rto": round(statistics.mean(rtos), 1) if rtos else 0,
            "avg_rpo": round(statistics.mean(rpos), 1) if rpos else 0,
            "worst_score": min(scores) if scores else 0,
            "best_score": max(scores) if scores else 0,
        }

        trends = {
            "score": score_trend,
            "rto": rto_trend,
            "recent_avg_score": round(recent_avg_score, 1),
            "older_avg_score": round(older_avg_score, 1),
            "recent_avg_rto": round(recent_avg_rto, 1),
            "older_avg_rto": round(older_avg_rto, 1),
        }

        # Generate recommendations
        recommendations = []
        rec_id = 0

        def add_rec(severity, category, title, description, action, based_on=None):
            nonlocal rec_id
            rec_id += 1
            recommendations.append({
                "id": f"rec-{rec_id:03d}",
                "severity": severity,
                "category": category,
                "title": title,
                "description": description,
                "action": action,
                "based_on": based_on or {},
            })

        # 1. Low pass rate
        if total >= 3:
            pass_rate = round(passed / total * 100, 1)
            if pass_rate < 50:
                add_rec("critical", "reliability",
                    "DR pass rate below 50%",
                    f"Only {pass_rate}% of {total} tests passed. Your disaster recovery is unreliable.",
                    "Review failed runs and fix the root cause before the next scheduled test.",
                    {"pass_rate": pass_rate, "total": total, "failed": failed})
            elif pass_rate < 80:
                add_rec("high", "reliability",
                    "DR pass rate below 80%",
                    f"{pass_rate}% pass rate across {total} tests. Some failure scenarios are not being handled.",
                    "Investigate patterns in failed runs — look for common fault types or resources.",
                    {"pass_rate": pass_rate, "total": total})

        # 2. RTO consistently exceeds target
        rto_targets = [r.get("rto_target", 300) for r in runs if r.get("rto_target")]
        if rtos and rto_targets:
            avg_rto = statistics.mean(rtos)
            avg_target = statistics.mean(rto_targets)
            if avg_rto > avg_target * 1.2:
                add_rec("critical", "rto",
                    "Average RTO exceeds target by 20%+",
                    f"Average RTO is {round(avg_rto)}s but target is {round(avg_target)}s.",
                    "Scale out your recovery infrastructure — add auto-scaling, warm standbys, or reduce deployment complexity.",
                    {"avg_rto": round(avg_rto, 1), "target": round(avg_target, 1)})
            elif avg_rto > avg_target:
                add_rec("high", "rto",
                    "Average RTO slightly above target",
                    f"Average RTO is {round(avg_rto)}s vs target of {round(avg_target)}s.",
                    "Monitor closely. Consider pre-warming resources or optimizing startup scripts.",
                    {"avg_rto": round(avg_rto, 1), "target": round(avg_target, 1)})

        # 3. RPO issues
        if rpos:
            avg_rpo = statistics.mean(rpos)
            rpo_targets = [r.get("rpo_target", 60) for r in runs if r.get("rpo_target")]
            if rpo_targets:
                avg_rpo_target = statistics.mean(rpo_targets)
                if avg_rpo > avg_rpo_target * 1.5:
                    add_rec("high", "rpo",
                        "Average RPO significantly exceeds target",
                        f"Average RPO is {round(avg_rpo)}s vs target of {round(avg_rpo_target)}s.",
                        "Increase backup frequency, enable continuous replication, or reduce data write latency.",
                        {"avg_rpo": round(avg_rpo, 1), "target": round(avg_rpo_target, 1)})

        # 4. Score declining trend
        if score_trend == "declining" and len(runs) >= 4:
            add_rec("high", "scoring",
                "Resilience score is declining",
                f"Recent avg score: {round(recent_avg_score)} vs earlier: {round(older_avg_score)}.",
                "Something has changed — check for new deployments, config drift, or infrastructure changes.",
                {"recent_avg": round(recent_avg_score, 1), "older_avg": round(older_avg_score, 1)})

        # 5. RTO degrading trend
        if rto_trend == "degrading" and len(runs) >= 4:
            add_rec("medium", "rto",
                "Recovery time is getting worse",
                f"Recent avg RTO: {round(recent_avg_rto)}s vs earlier: {round(older_avg_rto)}s.",
                "Check for resource sprawl, increased load, or new dependencies slowing recovery.",
                {"recent_avg_rto": round(recent_avg_rto, 1), "older_avg_rto": round(older_avg_rto, 1)})

        # 6. Specific fault type always fails
        for ft, fails in fault_failures.items():
            ft_total = fault_totals.get(ft, 1)
            if fails == ft_total and ft_total >= 2:
                add_rec("critical", "fault-type",
                    f"Always fails: {ft}",
                    f"Every {ft} test has failed ({fails}/{ft_total}).",
                    f"This fault type is not being handled. Fix the recovery path for {ft} scenarios.",
                    {"fault_type": ft, "failures": fails, "total": ft_total})
            elif fails / ft_total > 0.6 and ft_total >= 3:
                add_rec("high", "fault-type",
                    f"Frequently fails: {ft}",
                    f"{ft} fails {round(fails/ft_total*100)}% of the time ({fails}/{ft_total}).",
                    f"Review the {ft} recovery path — it has a systematic weakness.",
                    {"fault_type": ft, "failures": fails, "total": ft_total, "fail_rate": round(fails/ft_total*100, 1)})

        # 7. No tests run recently
        if runs:
            latest_ts = runs[0].get("timestamp", "")
            if latest_ts:
                try:
                    from datetime import datetime, timezone
                    latest_dt = datetime.fromisoformat(latest_ts.replace("Z", "+00:00"))
                    days_since = (datetime.now(timezone.utc) - latest_dt).days
                    if days_since > 14:
                        add_rec("medium", "reliability",
                            f"No DR test in {days_since} days",
                            f"Last test was on {latest_ts[:10]}. DR testing should run at least weekly.",
                            "Check your EventBridge schedule and ensure the Step Function is triggering.",
                            {"last_test": latest_ts, "days_since": days_since})
                except Exception:
                    pass

        # 8. High variance in scores (unpredictable recovery)
        if len(scores) >= 4:
            stdev = statistics.stdev(scores)
            if stdev > 15:
                add_rec("medium", "scoring",
                    "Highly variable recovery scores",
                    f"Score standard deviation is {round(stdev, 1)} — recovery is unpredictable.",
                    "Inconsistent recovery suggests environment dependencies. Check for race conditions or shared resource contention.",
                    {"stdev": round(stdev, 1), "min": min(scores), "max": max(scores)})

        # 9. Positive reinforcement
        if score_trend == "improving" and pass_rate >= 80 and len(runs) >= 4:
            add_rec("info", "scoring",
                "DR resilience is improving",
                f"Scores trending up ({round(older_avg_score)} -> {round(recent_avg_score)}) with {round(passed/total*100)}% pass rate.",
                "Keep it up. Consider tightening RTO/RPO targets or adding more fault types.",
                {"trend": "improving", "pass_rate": round(passed/total*100, 1)})

        # Sort: critical first, then high, medium, info
        severity_order = {"critical": 0, "high": 1, "medium": 2, "info": 3}
        recommendations.sort(key=lambda r: severity_order.get(r["severity"], 99))

        result = {
            "statusCode": 200,
            "headers": cors_headers(),
            "body": json.dumps({
                "summary": summary,
                "recommendations": recommendations,
                "trends": trends,
                "analyzed_runs": total,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }),
        }

        print(f"[Recommendations] Generated {len(recommendations)} recommendations from {total} runs")
        return result

    except Exception as e:
        print(f"[Recommendations] Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def trigger_dr_test(event):
    """Trigger a DR test via Step Functions.

    Input:
        {
            "fault_type": "ec2-termination" | "dns-failover" | "s3-origin-block" | "security-group",
            "target_url": "https://example.com",  // optional
            "port": 443,                            // optional
            "security_group_id": "sg-...",          // optional
            "bucket_name": "my-bucket",              // optional
        }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        fault_type = body.get("fault_type", "ec2-termination")

        # Build Step Function input
        sfn_input = {
            "fault_type": fault_type,
            "target_url": body.get("target_url"),
            "target_resource": body.get("target_resource", "auto"),
        }

        # Pass resource-specific params
        if fault_type == "security-group":
            sfn_input["port"] = body.get("port", 443)
            sfn_input["security_group_id"] = body.get("security_group_id")
            sfn_input["vpc_id"] = body.get("vpc_id")
        elif fault_type == "s3-origin-block":
            sfn_input["bucket_name"] = body.get("bucket_name")
        elif fault_type == "dns-failover":
            sfn_input["health_check_id"] = body.get("health_check_id")

        # Start Step Function execution
        sfn_client = boto3.client("stepfunctions")
        state_machine_name = f"cloudguard-{ENVIRONMENT}-dr-test"

        execution_name = f"dr-test-{fault_type}-{int(time.time())}"
        # Execution name must be alphanumeric + hyphens, max 80 chars
        execution_name = execution_name[:80]

        response = sfn_client.start_execution(
            stateMachineArn=f"arn:aws:states:{AWS_REGION}:{_get_account_id()}:stateMachine:{state_machine_name}",
            name=execution_name,
            input=json.dumps(sfn_input),
        )

        execution_arn = response["executionArn"]
        print(f"[DRTest] Started execution: {execution_arn}")

        return {
            "statusCode": 202,
            "headers": cors_headers(),
            "body": json.dumps({
                "message": f"DR test started with fault type: {fault_type}",
                "execution_arn": execution_arn,
                "execution_name": execution_name,
                "fault_type": fault_type,
                "target_url": sfn_input.get("target_url"),
            }),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        print(f"[DRTest] Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers(),
            "body": json.dumps({"error": str(e)}),
        }


def _get_account_id():
    """Get the current AWS account ID."""
    sts_client = boto3.client("sts")
    return sts_client.get_caller_identity()["Account"]
