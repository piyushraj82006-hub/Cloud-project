"""
CloudGuard DR — PDF Report Generator Lambda (v2)
Generates branded PDF reports matching the UI/UX design spec.
Dark-tech aesthetic with weak-point highlighting for SEO, Competitor,
DR-Test, and Comparison reports.
Uses PDFBolt API for HTML-to-PDF conversion.
"""
import os
import json
import time
import uuid
import io
import html
import re
import urllib.request
import urllib.error
import boto3
from urllib.parse import urlparse
from root_cause_analyzer import analyze_report

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "llama3-70b-8192")
OPENROUTER_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
PDFBOLT_API_KEY = os.environ.get("PDFBOLT_API_KEY", "")
PDFBOLT_API_URL = "https://api.pdfbolt.com/v1/direct"


def get_api_key():
    """Get OpenRouter API key from env or SSM Parameter Store."""
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    try:
        ssm = boto3.client("ssm")
        param = ssm.get_parameter(
            Name=f"/cloudguard/{ENVIRONMENT}/openrouter-api-key",
            WithDecryption=True,
        )
        return param["Parameter"]["Value"]
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════
# AI WEAK POINTS ANALYSIS — OpenRouter
# ═══════════════════════════════════════════════════════════════════

AI_WEAK_POINTS_PROMPT = """Analyze this {report_type} report. For each failing check, provide severity, title, why it matters (1 sentence), root cause (1 sentence), and 2-3 fix steps. Also provide executive_summary (2 sentences) and quick_wins list.

Report data:
{report_data}

JSON only:
{{"executive_summary":"...","weak_points":[{{"check":"...","severity":"critical|high|medium","title":"...","why_it_matters":"...","root_cause":"...","fix_steps":["..."]}}],"quick_wins":["..."]}}"""


def call_openrouter(prompt, api_key):
    """Call OpenRouter API for AI analysis."""
    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert technical analyst. Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_BASE_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://cloudguard-dr.com",
            "X-Title": "CloudGuard DR",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[PDFReport] OpenRouter error: {e}")
        return None


def parse_ai_response(text):
    """Parse AI JSON response, handling markdown code fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def enrich_with_ai(report_type, report_data):
    """Call OpenRouter to analyze the report and attach AI weak points."""
    # Skip if AI insights already exist
    if report_data.get("ai_insights"):
        print("[PDFReport] AI insights already present — skipping")
        return report_data

    api_key = get_api_key()
    if not api_key:
        print("[PDFReport] No API key — skipping AI analysis")
        return report_data

    print(f"[PDFReport] Calling OpenRouter for {report_type} AI analysis...")
    prompt = AI_WEAK_POINTS_PROMPT.format(
        report_type=report_type,
        report_data=json.dumps(report_data, indent=2, default=str),
    )
    ai_text = call_openrouter(prompt, api_key)
    if not ai_text:
        return report_data

    insights = parse_ai_response(ai_text)
    if not insights:
        print("[PDFReport] Failed to parse AI response")
        return report_data

    report_data["ai_insights"] = insights
    print(f"[PDFReport] AI analysis complete: {len(insights.get('weak_points', []))} weak points found")
    return report_data


def _esc(text):
    """Escape text for safe HTML interpolation."""
    if text is None:
        return ""
    return html.escape(str(text))


def convert_html_to_pdf(html_content):
    """Convert HTML to PDF using PDFBolt API. Returns bytes or None."""
    api_key = PDFBOLT_API_KEY
    if not api_key:
        # Try SSM
        try:
            ssm = boto3.client("ssm")
            param = ssm.get_parameter(
                Name=f"/cloudguard/{ENVIRONMENT}/pdfbolt-api-key",
                WithDecryption=True,
            )
            api_key = param["Parameter"]["Value"]
        except Exception:
            pass

    if not api_key:
        print("[PDFReport] No PDFBolt API key — cannot generate PDF")
        return None

    import base64
    b64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")

    payload = json.dumps({
        "html": b64_html,
        "format": "A4",
        "printBackground": True,
        "margin": {"top": "0", "bottom": "0", "left": "0", "right": "0"},
    }).encode("utf-8")

    req = urllib.request.Request(
        PDFBOLT_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "API-KEY": api_key,
        },
        method="POST",
    )
    try:
        print("[PDFReport] Calling PDFBolt API...")
        resp = urllib.request.urlopen(req, timeout=30)
        pdf_bytes = resp.read()
        print(f"[PDFReport] PDF generated via PDFBolt ({len(pdf_bytes)} bytes)")
        return pdf_bytes
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[PDFReport] PDFBolt error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"[PDFReport] PDFBolt call failed: {e}")
        return None


def lambda_handler(event, context):
    """
    Generate a branded PDF report from an existing JSON report.

    Event input:
        {
            "report_type": "seo" | "competitor" | "dr-test" | "comparison",
            "report_id": "seo-abc12345" | "run-abc123" | "comp-abc12345",
            "agency_name": "Acme Agency"  // optional, for cover page
        }

    For comparison:
        {
            "report_type": "comparison",
            "report_id": "run-a1b2c3d4-run-e5f6g7h8",
            "run_id_a": "run-a1b2c3d4",
            "run_id_b": "run-e5f6g7h8",
            "agency_name": "Acme Agency"  // optional
        }

    Output:
        {
            "pdf_key": "pdf-reports/...",
            "pdf_url": "https://...",
            "report_type": "seo",
            "report_id": "..."
        }
    """
    print(f"[PDFReport] Starting. Event: {json.dumps(event)}")

    try:
        report_type = event.get("report_type", "seo")
        report_id = event.get("report_id", "")
        agency_name = event.get("agency_name", "CloudGuard DR")

        if not report_id:
            raise ValueError("report_id is required")

        # Handle comparison type specially (needs two runs)
        if report_type == "comparison":
            run_id_a = event.get("run_id_a", "")
            run_id_b = event.get("run_id_b", "")
            if not run_id_a or not run_id_b:
                raise ValueError("run_id_a and run_id_b are required for comparison")
            report_data = fetch_comparison_data(run_id_a, run_id_b)
        else:
            # Fetch the JSON report from S3
            json_key = find_report_json(report_type, report_id)
            if not json_key:
                raise ValueError(f"Report not found for {report_type}/{report_id}")

            report_data = fetch_json_report(json_key)

        # ── AI Weak Points Analysis (via OpenRouter) ──
        report_data = enrich_with_ai(report_type, report_data)

        # ── Generate HTML ──
        if report_type == "comparison":
            html_content = generate_comparison_pdf_html(report_data, agency_name)
        elif report_type == "seo":
            html_content = generate_seo_pdf_html(report_data, agency_name)
        elif report_type == "competitor":
            html_content = generate_competitor_pdf_html(report_data, agency_name)
        elif report_type == "dr-test":
            html_content = generate_dr_test_pdf_html(report_data, agency_name)
        else:
            raise ValueError(f"Unknown report_type: {report_type}")

        # Convert HTML to PDF using PDFBolt API
        pdf_bytes = convert_html_to_pdf(html_content)

        if pdf_bytes:
            # Upload PDF to S3
            pdf_key = f"pdf-reports/{report_id}/report.pdf"
            s3_client.put_object(
                Bucket=REPORTS_BUCKET,
                Key=pdf_key,
                Body=pdf_bytes,
                ContentType="application/pdf",
            )
        else:
            # Fallback: save HTML if PDFBolt unavailable
            print("[PDFReport] PDFBolt unavailable — returning HTML fallback")
            pdf_key = f"pdf-reports/{report_id}/report.html"
            s3_client.put_object(
                Bucket=REPORTS_BUCKET,
                Key=pdf_key,
                Body=html_content.encode("utf-8"),
                ContentType="text/html",
            )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": REPORTS_BUCKET, "Key": pdf_key},
            ExpiresIn=604800,  # 7 days
        )

        is_pdf = pdf_bytes is not None
        result = {
            "statusCode": 200,
            "pdf_key": pdf_key,
            "pdf_url": presigned_url,
            "report_type": report_type,
            "report_id": report_id,
            "format": "pdf" if is_pdf else "html_fallback",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        print(f"[PDFReport] Generated: {pdf_key} ({'PDF' if is_pdf else 'HTML fallback'})")
        return result

    except ValueError as e:
        print(f"[PDFReport] Validation error: {str(e)}")
        return {"statusCode": 400, "error": str(e)}
    except Exception as e:
        print(f"[PDFReport] Error: {str(e)}")
        raise


def find_report_json(report_type, report_id):
    """Find the JSON report key in S3 based on type and ID."""
    prefix_map = {
        "seo": "seo-reports",
        "competitor": "competitor-analysis",
        "dr-test": "reports",
    }
    prefix = prefix_map.get(report_type, "reports")
    key = f"{prefix}/{report_id}/report.json"

    # Verify it exists
    try:
        s3_client.head_object(Bucket=REPORTS_BUCKET, Key=key)
        return key
    except Exception:
        return None


def fetch_json_report(s3_key):
    """Fetch and parse a JSON report from S3."""
    response = s3_client.get_object(Bucket=REPORTS_BUCKET, Key=s3_key)
    return json.loads(response["Body"].read().decode("utf-8"))


def fetch_comparison_data(run_id_a, run_id_b):
    """Fetch two run records and their reports for comparison."""
    table = dynamodb.Table(f"cloudguard-{ENVIRONMENT}-test-runs")

    resp_a = table.get_item(Key={"run_id": run_id_a})
    resp_b = table.get_item(Key={"run_id": run_id_b})

    run_a = resp_a.get("Item", {})
    run_b = resp_b.get("Item", {})

    # Fetch reports if available
    report_a = None
    report_b = None
    if run_a.get("report_s3_key"):
        try:
            report_a = fetch_json_report(run_a["report_s3_key"])
        except Exception:
            pass
    if run_b.get("report_s3_key"):
        try:
            report_b = fetch_json_report(run_b["report_s3_key"])
        except Exception:
            pass

    return {
        "run_a": run_a,
        "run_b": run_b,
        "report_a": report_a,
        "report_b": report_b,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ═══════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Based on UI_UX_DESIGN.md
# ═══════════════════════════════════════════════════════════════════

def base_pdf_styles():
    """
    Design-system-aligned CSS for all PDF reports.
    Dark-tech aesthetic with weak-point highlighting.
    Optimized for browser viewing (scales up from print sizes).
    """
    return """
    @page {
        size: A4;
        margin: 18mm 16mm 22mm 16mm;
        @bottom-center {
            content: "CloudGuard DR — Confidential";
            font-size: 7.5px;
            color: #666666;
            font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
        }
        @bottom-right {
            content: counter(page) " / " counter(pages);
            font-size: 7.5px;
            color: #666666;
            font-family: 'JetBrains Mono', monospace;
        }
    }
    @page cover {
        margin: 0;
        @bottom-center { content: none; }
        @bottom-right { content: none; }
    }
    @page toc {
        @bottom-center { content: none; }
    }
    @page weak-points {
        @bottom-center {
            content: "\\26A0  CRITICAL \\2014 Review weak points";
            font-size: 7px;
            color: #EF4444;
            font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
            font-weight: 600;
        }
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
        font-size: 15px;
        line-height: 1.65;
        color: #E2E8F0;
        background: #070709;
        max-width: 960px;
        margin: 0 auto;
        padding: 40px 32px;
    }

    /* ─── Cover Page ─── */
    .cover {
        page: cover;
        width: 100%;
        min-height: 100vh;
        background: radial-gradient(circle at 10% 20%, rgba(34, 197, 94, 0.1) 0%, transparent 60%), 
                    radial-gradient(circle at 90% 80%, rgba(59, 130, 246, 0.08) 0%, transparent 60%),
                    #070709;
        color: #F8FAFC;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        page-break-after: always;
        padding: 100px 60px;
        margin: -40px -32px 40px -32px;
        border-radius: 0;
    }
    .cover-logo {
        font-size: 56px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-bottom: 12px;
        font-family: 'Plus Jakarta Sans', 'Outfit', sans-serif;
    }
    .cover-logo span {
        color: #22C55E;
    }
    .cover-subtitle {
        font-size: 18px;
        color: #94A3B8;
        margin-bottom: 40px;
        font-weight: 300;
        letter-spacing: 0.02em;
    }
    .cover-report-type {
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #F8FAFC;
    }
    .cover-client {
        font-size: 20px;
        color: #94A3B8;
        margin-bottom: 60px;
        word-break: break-all;
    }
    .cover-meta {
        font-size: 13px;
        color: #64748B;
        line-height: 2.2;
        font-family: 'JetBrains Mono', monospace;
    }
    .cover-bar {
        width: 80px;
        height: 3px;
        background: #22C55E;
        margin: 20px auto;
    }

    /* ─── Headings ─── */
    h1 {
        font-size: 28px;
        font-weight: 700;
        color: #F8FAFC;
        margin: 48px 0 20px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid #22C55E;
        letter-spacing: -0.02em;
    }
    h2 {
        font-size: 22px;
        font-weight: 600;
        color: #F8FAFC;
        margin: 32px 0 14px 0;
    }
    h3 {
        font-size: 18px;
        font-weight: 600;
        color: #E2E8F0;
        margin: 20px 0 10px 0;
    }
    p {
        margin-bottom: 14px;
        color: #94A3B8;
        font-size: 15px;
    }
    strong {
        color: #F8FAFC;
    }

    /* ─── Section ─── */
    .section {
        page-break-inside: avoid;
        margin-bottom: 24px;
    }

    /* ─── Executive Summary ─── */
    .exec-summary {
        background: rgba(37, 99, 235, 0.03);
        border: 1px solid rgba(37, 99, 235, 0.15);
        border-left: 4px solid #2563EB;
        border-radius: 12px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    /* ─── Stat Grid ─── */
    .stat-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin: 24px 0;
    }
    .stat-card {
        flex: 1;
        min-width: 160px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.08), 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .stat-value {
        font-size: 36px;
        font-weight: 700;
        color: #F8FAFC;
        font-family: 'JetBrains Mono', monospace;
    }
    .stat-value.good { color: #22C55E; }
    .stat-value.warn { color: #F59E0B; }
    .stat-value.bad { color: #EF4444; }
    .stat-value.info { color: #3B82F6; }
    .stat-label {
        font-size: 11px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 6px;
        font-weight: 600;
    }

    /* ─── Weak Points Banner ─── */
    .weak-points-banner {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.06) 0%, rgba(239, 68, 68, 0.02) 100%);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 5px solid #EF4444;
        border-radius: 16px;
        padding: 24px;
        margin: 24px 0;
        page-break-inside: avoid;
        page: weak-points;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    .weak-points-banner h2 {
        color: #EF4444;
        font-size: 20px;
        margin: 0 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .weak-points-banner .weak-count {
        background: #EF4444;
        color: white;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ─── Issue Card (within weak points) ─── */
    .issue-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(239, 68, 68, 0.15);
        border-left: 4px solid #EF4444;
        border-radius: 12px;
        padding: 18px;
        margin: 12px 0;
        page-break-inside: avoid;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .issue-card.warn {
        background: rgba(255, 255, 255, 0.02);
        border-color: rgba(245, 158, 11, 0.2);
        border-left-color: #F59E0B;
    }
    .issue-card-title {
        font-size: 16px;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 8px;
    }
    .issue-card-detail {
        font-size: 14px;
        color: #94A3B8;
        line-height: 1.6;
    }
    .issue-severity {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .severity-critical { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; }
    .severity-high { background: rgba(245, 158, 11, 0.15); color: #FCD34D; }
    .severity-medium { background: rgba(245, 158, 11, 0.1); color: #FDE68A; }

    /* ─── Tables ─── */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 14px;
    }
    th {
        background: #151515;
        font-weight: 600;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid #292929;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #888888;
    }
    td {
        padding: 12px 16px;
        border-bottom: 1px solid #1A1A1A;
        vertical-align: top;
        color: #D4D4D4;
    }
    tr:nth-child(even) { background: #0D0D0D; }
    tr:hover { background: #151515; }

    /* Row highlighting for failures */
    tr.row-fail { background: #1C0A0A !important; }
    tr.row-fail td { border-bottom-color: #3B1111; }
    tr.row-warn { background: #1A1408 !important; }
    tr.row-warn td { border-bottom-color: #78350F; }
    tr.row-pass { background: #0A1A0A !important; }

    /* ─── Badges ─── */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
    }
    .badge-pass { background: #052E16; color: #22C55E; }
    .badge-fail { background: #450A0A; color: #EF4444; }
    .badge-warn { background: #451A03; color: #F59E0B; }
    .badge-info { background: #172554; color: #3B82F6; }
    .badge-high { background: #450A0A; color: #EF4444; }
    .badge-medium { background: #451A03; color: #F59E0B; }
    .badge-low { background: #052E16; color: #22C55E; }
    .badge-critical { background: #7F1D1D; color: #FCA5A5; }

    /* ─── Delta Indicators (Comparison) ─── */
    .delta-good {
        color: #22C55E;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-weight: 600;
    }
    .delta-bad {
        color: #EF4444;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-weight: 600;
    }
    .delta-neutral {
        color: #888888;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
    }

    /* ─── Opportunity / Recommendation Card ─── */
    .opportunity {
        border: 1px solid #292929;
        border-left: 4px solid #22C55E;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
        page-break-inside: avoid;
        background: #0D0D0D;
    }
    .opportunity.critical {
        border-left-color: #EF4444;
        background: #1A0A0A;
    }
    .opportunity.high {
        border-left-color: #F59E0B;
        background: #1A1408;
    }
    .opportunity h3 {
        margin: 0 0 8px 0;
        font-size: 16px;
    }
    .opportunity p {
        font-size: 14px;
        color: #B0B0B0;
    }
    .opportunity ul {
        margin: 10px 0 0 20px;
        font-size: 14px;
        color: #B0B0B0;
    }
    .opportunity li { margin-bottom: 6px; }

    /* ─── TOC ─── */
    .toc {
        page: toc;
        page-break-after: always;
    }
    .toc h1 { border-bottom-color: #22C55E; }
    .toc-item {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px dotted #292929;
        font-size: 16px;
        color: #B0B0B0;
    }
    .toc-item span:first-child { font-weight: 500; color: #D4D4D4; }
    .toc-item span:last-child { color: #888888; font-family: 'JetBrains Mono', 'Courier New', monospace; }

    /* ─── Closing ─── */
    .closing {
        margin-top: 48px;
        padding-top: 20px;
        border-top: 2px solid #22C55E;
        text-align: center;
        color: #888888;
        font-size: 13px;
    }
    .closing strong { color: #B0B0B0; }

    /* ─── Utilities ─── */
    .page-break { page-break-before: always; }
    .text-muted { color: #888888; }
    .text-pass { color: #22C55E; }
    .text-fail { color: #EF4444; }
    .text-warn { color: #F59E0B; }
    .mono { font-family: 'JetBrains Mono', 'Courier New', monospace; }

    /* ─── Responsive ─── */
    @media (max-width: 640px) {
        body { padding: 20px 16px; }
        .stat-grid { flex-direction: column; }
        .stat-card { min-width: 100%; }
        h1 { font-size: 24px; }
        .cover-logo { font-size: 40px; }
    }
    """


# ═══════════════════════════════════════════════════════════════════
# AI INSIGHTS SECTION — Shared across all report types
# ═══════════════════════════════════════════════════════════════════

def generate_ai_insights_html(report):
    """Render the AI insights section if present in the report."""
    insights = report.get("ai_insights")
    if not insights:
        return ""

    sections = []

    # Executive Summary
    summary = insights.get("executive_summary", "")
    if summary:
        sections.append(f"""
        <div class="exec-summary" style="border-left-color: #8B5CF6;">
            <h3 style="color: #8B5CF6; margin-bottom: 10px;">AI Executive Summary</h3>
            <p style="color: #D4D4D4;">{summary}</p>
        </div>
        """)

    # Critical Actions
    actions = insights.get("critical_actions", [])
    if actions:
        action_cards = ""
        for i, action in enumerate(actions, 1):
            impact = action.get("impact", "medium")
            badge_class = "badge-critical" if impact == "high" else "badge-medium"
            impl = action.get("implementation", "")
            action_cards += f"""
            <div class="issue-card">
                <div class="issue-severity {badge_class}">{impact} impact</div>
                <div class="issue-card-title">{i}. {action.get('action', '')}</div>
                <div class="issue-card-detail">{impl}</div>
            </div>"""
        sections.append(f"""
        <div class="weak-points-banner" style="border-left-color: #8B5CF6; background: linear-gradient(135deg, #1A0A2E 0%, #0D1117 100%); border-color: #4C1D95;">
            <h2 style="color: #8B5CF6;">🤖 AI Critical Actions <span class="weak-count" style="background: #8B5CF6;">{len(actions)}</span></h2>
            {action_cards}
        </div>
        """)

    # Winning Strategies (competitor)
    strategies = insights.get("winning_strategies", [])
    if strategies:
        strat_cards = ""
        for i, s in enumerate(strategies, 1):
            strat_cards += f"""
            <div class="opportunity" style="border-left-color: #8B5CF6;">
                <h3>{i}. {s.get('strategy', '')}</h3>
                <p>Impact: {s.get('expected_impact', '')} | Timeline: {s.get('timeline', '')}</p>
            </div>"""
        sections.append(f"""
        <div style="margin: 4mm 0;">
            <h2 style="color: #8B5CF6; border-bottom-color: #8B5CF6;">🤖 AI Winning Strategies</h2>
            {strat_cards}
        </div>
        """)

    # Roadmap (SEO)
    roadmap = insights.get("roadmap", {})
    if roadmap:
        roadmap_html = ""
        for phase, items in roadmap.items():
            phase_label = phase.replace("_", " ").title()
            items_html = "\n".join(f"<li>{item}</li>" for item in items)
            roadmap_html += f"""
            <div style="margin-bottom: 16px;">
                <h3 style="color: #8B5CF6;">{phase_label}</h3>
                <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{items_html}</ul>
            </div>"""
        sections.append(f"""
        <div style="margin: 4mm 0; background: #111111; border: 1px solid #292929; border-radius: 4px; padding: 4mm;">
            <h2 style="color: #8B5CF6; border-bottom-color: #8B5CF6; margin-bottom: 16px;">🤖 AI 90-Day Roadmap</h2>
            {roadmap_html}
        </div>
        """)

    # Remediation Steps (DR)
    remediation = insights.get("remediation_steps", [])
    if remediation:
        rem_cards = ""
        for i, r in enumerate(remediation, 1):
            pri = r.get("priority", "medium")
            badge_class = "badge-critical" if pri == "critical" else "badge-high" if pri == "high" else "badge-medium"
            rem_cards += f"""
            <div class="issue-card">
                <div class="issue-severity {badge_class}">{pri}</div>
                <div class="issue-card-title">{i}. {r.get('step', '')}</div>
                <div class="issue-card-detail">Effort: {r.get('effort', 'N/A')}</div>
            </div>"""
        sections.append(f"""
        <div class="weak-points-banner" style="border-left-color: #8B5CF6; background: linear-gradient(135deg, #1A0A2E 0%, #0D1117 100%); border-color: #4C1D95;">
            <h2 style="color: #8B5CF6;">🤖 AI Remediation Steps <span class="weak-count" style="background: #8B5CF6;">{len(remediation)}</span></h2>
            {rem_cards}
        </div>
        """)

    # Root Cause Analysis (DR)
    root_causes = insights.get("root_cause_analysis", [])
    if root_causes:
        rc_items = "\n".join(f"<li>{rc}</li>" for rc in root_causes)
        sections.append(f"""
        <div style="margin: 4mm 0; background: #111111; border: 1px solid #292929; border-radius: 4px; padding: 4mm;">
            <h3 style="color: #8B5CF6; margin-bottom: 10px;">🤖 AI Root Cause Analysis</h3>
            <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{rc_items}</ul>
        </div>
        """)

    # Architecture Recommendations (DR)
    arch_recs = insights.get("architecture_recommendations", [])
    if arch_recs:
        arch_items = "\n".join(f"<li>{rec}</li>" for rec in arch_recs)
        sections.append(f"""
        <div style="margin: 4mm 0; background: #111111; border: 1px solid #292929; border-radius: 4px; padding: 4mm;">
            <h3 style="color: #8B5CF6; margin-bottom: 10px;">🤖 AI Architecture Recommendations</h3>
            <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{arch_items}</ul>
        </div>
        """)

    # Regression Analysis (Comparison)
    regressions = insights.get("regression_analysis", [])
    if regressions:
        reg_items = "\n".join(f"<li>{r}</li>" for r in regressions)
        sections.append(f"""
        <div class="weak-points-banner" style="border-left-color: #8B5CF6; background: linear-gradient(135deg, #1A0A2E 0%, #0D1117 100%); border-color: #4C1D95;">
            <h2 style="color: #8B5CF6;">🤖 AI Regression Analysis</h2>
            <ul style="margin: 6px 0 0 20px; color: #FCA5A5; font-size: 14px;">{reg_items}</ul>
        </div>
        """)

    # Improvement Actions (Comparison)
    improvements = insights.get("improvement_actions", [])
    if improvements:
        imp_cards = ""
        for i, imp in enumerate(improvements, 1):
            pri = imp.get("priority", "medium")
            badge_class = "badge-critical" if pri == "critical" else "badge-high" if pri == "high" else "badge-medium"
            imp_cards += f"""
            <div class="issue-card">
                <div class="issue-severity {badge_class}">{pri}</div>
                <div class="issue-card-title">{i}. {imp.get('action', '')}</div>
            </div>"""
        sections.append(f"""
        <div style="margin: 4mm 0;">
            <h3 style="color: #8B5CF6;">🤖 AI Improvement Actions</h3>
            {imp_cards}
        </div>
        """)

    # Opportunities (generic)
    opportunities = insights.get("opportunities", [])
    if opportunities:
        opp_cards = ""
        for i, opp in enumerate(opportunities, 1):
            opp_cards += f"""
            <div class="opportunity" style="border-left-color: #8B5CF6;">
                <h3>{i}. {opp.get('title', '')}</h3>
                <p>{opp.get('description', '')}</p>
                <span class="badge badge-info">{opp.get('effort', 'medium')} effort</span>
            </div>"""
        sections.append(f"""
        <div style="margin: 4mm 0;">
            <h2 style="color: #8B5CF6; border-bottom-color: #8B5CF6;">🤖 AI Opportunities</h2>
            {opp_cards}
        </div>
        """)

    # Defensive Measures (Competitor)
    defensive = insights.get("defensive_measures", [])
    if defensive:
        def_cards = ""
        for d in defensive:
            def_cards += f"""
            <div class="issue-card warn">
                <div class="issue-card-title">⚠ {d.get('threat', '')}</div>
                <div class="issue-card-detail">Mitigation: {d.get('mitigation', '')}</div>
            </div>"""
        sections.append(f"""
        <div style="margin: 4mm 0;">
            <h3 style="color: #F59E0B;">🤖 AI Defensive Measures</h3>
            {def_cards}
        </div>
        """)

    # Failure Analysis (detailed per-failure breakdown)
    failure_analysis = insights.get("failure_analysis", [])
    if failure_analysis:
        fa_cards = ""
        for i, fa in enumerate(failure_analysis, 1):
            check_name = fa.get("check", fa.get("gap", fa.get("issue", fa.get("regression", ""))))
            why = fa.get("why_it_matters", "")
            cause = fa.get("root_cause", fa.get("likely_cause", ""))
            fix_steps = fa.get("fix_steps", [])
            scope = fa.get("scope", "")
            impact = fa.get("estimated_impact", "")

            scope_badge = {
                "quick_win": "badge-pass",
                "medium_project": "badge-warn",
                "major_initiative": "badge-critical",
            }.get(scope, "badge-info")
            scope_label = scope.replace("_", " ").title() if scope else ""

            fix_html = "\n".join(f"<li>{s}</li>" for s in fix_steps)

            fa_cards += f"""
            <div class="issue-card" style="border-left-color: #8B5CF6; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #666; font-family: 'JetBrains Mono', monospace;">#{i}</span>
                    <span class="badge {scope_badge}">{scope_label}</span>
                    {f'<span class="badge badge-info">{impact}</span>' if impact else ''}
                </div>
                <div class="issue-card-title" style="color: #8B5CF6;">{check_name}</div>
                <div style="margin-bottom: 8px;">
                    <strong style="color: #EF4444; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;">Why It Matters</strong>
                    <p style="color: #A1A1A1; font-size: 14px; margin-top: 4px;">{why}</p>
                </div>
                {f'<div style="margin-bottom: 8px;"><strong style="color: #F59E0B; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;">Root Cause</strong><p style="color: #A1A1A1; font-size: 14px; margin-top: 4px;">{cause}</p></div>' if cause else ''}
                {f'<div><strong style="color: #22C55E; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em;">How To Fix</strong><ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{fix_html}</ul></div>' if fix_steps else ''}
            </div>"""

        sections.append(f"""
        <div class="weak-points-banner" style="border-left-color: #8B5CF6; background: linear-gradient(135deg, #1A0A2E 0%, #0D1117 100%); border-color: #4C1D95;">
            <h2 style="color: #8B5CF6;">🤖 AI Failure Analysis <span class="weak-count" style="background: #8B5CF6;">{len(failure_analysis)}</span></h2>
            <p style="color: #C4B5FD; font-size: 14px; margin-bottom: 10px;">Detailed breakdown of each failure with root cause, impact, and fix steps.</p>
            {fa_cards}
        </div>
        """)

    # Improvement Scopes (quick wins, medium, major)
    scopes = insights.get("improvement_scopes", {})
    if scopes:
        quick_wins = scopes.get("quick_wins", [])
        medium_projects = scopes.get("medium_projects", [])
        major_initiatives = scopes.get("major_initiatives", [])

        if quick_wins or medium_projects or major_initiatives:
            scope_html = ""
            if quick_wins:
                qw_items = "\n".join(f"<li>{q}</li>" for q in quick_wins)
                scope_html += f"""
                <div style="margin-bottom: 16px;">
                    <h3 style="color: #22C55E; font-size: 9pt;">⚡ Quick Wins <span style="color: #666; font-weight: 400;">(do this week)</span></h3>
                    <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{qw_items}</ul>
                </div>"""
            if medium_projects:
                mp_items = "\n".join(f"<li>{m}</li>" for m in medium_projects)
                scope_html += f"""
                <div style="margin-bottom: 16px;">
                    <h3 style="color: #F59E0B; font-size: 9pt;">🔧 Medium Projects <span style="color: #666; font-weight: 400;">(1-4 weeks)</span></h3>
                    <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{mp_items}</ul>
                </div>"""
            if major_initiatives:
                mi_items = "\n".join(f"<li>{m}</li>" for m in major_initiatives)
                scope_html += f"""
                <div style="margin-bottom: 16px;">
                    <h3 style="color: #EF4444; font-size: 9pt;">🏗 Major Initiatives <span style="color: #666; font-weight: 400;">(1-3 months)</span></h3>
                    <ul style="margin: 6px 0 0 20px; color: #A1A1A1; font-size: 14px;">{mi_items}</ul>
                </div>"""

            sections.append(f"""
            <div style="margin: 4mm 0; background: #111111; border: 1px solid #292929; border-radius: 4px; padding: 4mm;">
                <h2 style="color: #8B5CF6; border-bottom-color: #8B5CF6; margin-bottom: 16px;">🎯 AI Improvement Scopes</h2>
                <p style="color: #A1A1A1; font-size: 14px; margin-bottom: 10px;">Actions grouped by effort and timeline:</p>
                {scope_html}
            </div>
            """)

    if not sections:
        return ""

    return f"""
    <div class="page-break"></div>
    <h1 style="border-bottom-color: #8B5CF6;">AI-Powered Insights</h1>
    <p style="color: #8B5CF6; font-size: 14px; margin-bottom: 16px;">Generated by Claude via OpenRouter — strategic analysis based on your report data</p>
    {''.join(sections)}
    """


# ═══════════════════════════════════════════════════════════════════
# ROOT CAUSE ANALYSIS SECTION — Explains WHY failures happened
# ═══════════════════════════════════════════════════════════════════

def generate_root_cause_html(report_type, report_data):
    """Render root cause analysis section with WHY + HOW TO FIX for each failure."""
    findings = analyze_report(report_type, report_data)
    if not findings:
        return ""

    severity_order = {"critical": 0, "high": 1, "medium": 2}
    findings.sort(key=lambda f: severity_order.get(f.get("severity", "medium"), 3))

    cards = ""
    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "medium")
        sev_class = f"severity-{severity}"
        badge_class = f"badge-{severity}"

        fix_steps_html = "\n".join(
            f"<li>{step}</li>" for step in f.get("fix_steps", [])
        )

        prevention = f.get("prevention", "")
        prevention_html = f"""
        <div style="margin-top: 2mm; padding: 2.5mm; background: #0A1A0A; border: 1px solid #166534; border-radius: 3px;">
            <strong style="color: #22C55E; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em;">🛡 Prevention</strong>
            <p style="color: #A1A1A1; font-size: 14px; margin-top: 6px;">{prevention}</p>
        </div>""" if prevention else ""

        effort = f.get("estimated_effort", "")
        effort_html = f'<span class="badge badge-info" style="margin-left: 2mm;">⏱ {effort}</span>' if effort else ""

        cards += f"""
        <div class="issue-card" style="border-left-width: 4px; padding: 4mm; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span class="issue-severity {sev_class}">{severity}</span>
                <span style="font-size: 12px; color: #666; font-family: 'JetBrains Mono', monospace;">#{i}</span>
                {effort_html}
            </div>
            <div class="issue-card-title" style="font-size: 16px; margin-bottom: 10px;">{f.get('title', '')}</div>

            <div style="margin-bottom: 2.5mm;">
                <strong style="color: #EF4444; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em;">Why It Matters</strong>
                <p style="color: #A1A1A1; font-size: 14px; margin-top: 6px;">{f.get('why_it_matters', '')}</p>
            </div>

            <div style="margin-bottom: 2.5mm;">
                <strong style="color: #F59E0B; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em;">Root Cause</strong>
                <p style="color: #A1A1A1; font-size: 14px; margin-top: 6px;">{f.get('root_cause', '')}</p>
            </div>

            <div style="margin-bottom: 8px;">
                <strong style="color: #22C55E; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em;">How To Fix</strong>
                <ul style="margin: 1.5mm 0 0 4mm; padding: 0; list-style: none;">
                    {fix_steps_html}
                </ul>
            </div>

            {prevention_html}
        </div>"""

    critical_count = sum(1 for f in findings if f.get("severity") == "critical")
    high_count = sum(1 for f in findings if f.get("severity") == "high")
    medium_count = sum(1 for f in findings if f.get("severity") == "medium")

    summary_parts = []
    if critical_count:
        summary_parts.append(f'<span style="color: #EF4444;">{critical_count} critical</span>')
    if high_count:
        summary_parts.append(f'<span style="color: #F59E0B;">{high_count} high</span>')
    if medium_count:
        summary_parts.append(f'<span style="color: #FDE68A;">{medium_count} medium</span>')
    summary_text = ", ".join(summary_parts)

    return f"""
    <div class="page-break"></div>
    <h1 style="border-bottom-color: #F59E0B;">Root Cause Analysis</h1>
    <p style="color: #A1A1A1; font-size: 14px; margin-bottom: 1mm;">
        Every failure has a root cause and a fix. Below is a detailed breakdown of each issue:
        <strong>{summary_text}</strong>
    </p>
    <p style="color: #666; font-size: 12px; margin-bottom: 20px;">
        Each finding explains WHY the failure matters, WHAT likely caused it, HOW to fix it, and HOW to prevent it from happening again.
    </p>
    {cards}
    """


# ═══════════════════════════════════════════════════════════════════
# SEO PDF — With Weak-Point Highlighting
# ═══════════════════════════════════════════════════════════════════

def generate_seo_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for an SEO audit report with weak-point highlighting."""
    checks = report.get("seo_checks", {})
    score = report.get("seo_score", 0)

    # Count issues
    total_issues = 0
    failing_checks = []
    passing_checks = []

    for key, label in [
        ("title", "Page Title"), ("meta_description", "Meta Description"),
        ("headings", "Heading Structure"), ("images", "Images & Alt Text"),
        ("links", "Links"), ("canonical", "Canonical URL"),
        ("open_graph", "Open Graph Tags"), ("twitter_card", "Twitter Card"),
        ("viewport", "Mobile Viewport"), ("robots", "Robots / Indexing"),
        ("structured_data", "Structured Data"), ("performance", "Performance"),
        ("https", "HTTPS / Security"),
    ]:
        check = checks.get(key, {})
        issues = check.get("issues", [])
        total_issues += len(issues)
        if issues:
            failing_checks.append((key, label, issues))
        else:
            passing_checks.append((key, label))

    total_checks = len(checks) if checks else 1
    passing_count = len(passing_checks)

    score_class = "good" if score >= 70 else "warn" if score >= 50 else "bad"

    # ── Build failing checks HTML (Weak Points Section) ──
    weak_points_html = ""
    if failing_checks:
        weak_cards = ""
        for key, label, issues in failing_checks:
            # Determine severity based on category importance
            critical_keys = {"title", "meta_description", "headings", "https", "viewport"}
            high_keys = {"canonical", "structured_data", "performance"}
            severity = "critical" if key in critical_keys else "high" if key in high_keys else "medium"
            severity_class = f"severity-{severity}"

            issues_list = "".join(f"<li>{issue}</li>" for issue in issues)
            weak_cards += f"""
            <div class="issue-card">
                <div class="issue-severity {severity_class}">{severity}</div>
                <div class="issue-card-title">{label}</div>
                <div class="issue-card-detail">
                    <ul style="margin: 6px 0 0 20px; padding: 0; list-style: disc;">
                        {issues_list}
                    </ul>
                </div>
            </div>"""

        weak_points_html = f"""
        <div class="weak-points-banner">
            <h2>⚠ Weak Points Identified <span class="weak-count">{len(failing_checks)} FAILING</span></h2>
            <p style="color: #FCA5A5; font-size: 14px; margin-bottom: 10px;">
                These checks are failing and require immediate attention to improve your SEO score.
            </p>
            {weak_cards}
        </div>"""

    # ── Build check rows (full audit table) ──
    check_rows = ""
    for key, label in [
        ("title", "Page Title"), ("meta_description", "Meta Description"),
        ("headings", "Heading Structure"), ("images", "Images & Alt Text"),
        ("links", "Links"), ("canonical", "Canonical URL"),
        ("open_graph", "Open Graph Tags"), ("twitter_card", "Twitter Card"),
        ("viewport", "Mobile Viewport"), ("robots", "Robots / Indexing"),
        ("structured_data", "Structured Data"), ("performance", "Performance"),
        ("https", "HTTPS / Security"),
    ]:
        check = checks.get(key, {})
        issues = check.get("issues", [])
        status = "PASS" if not issues else "FAIL"
        badge_class = "badge-pass" if status == "PASS" else "badge-fail"
        row_class = "row-pass" if status == "PASS" else "row-fail"
        issues_text = "; ".join(issues) if issues else "No issues found"
        check_rows += f"""
        <tr class="{row_class}">
            <td>{label}</td>
            <td><span class="badge {badge_class}">{status}</span></td>
            <td style="color: {'#666' if status == 'PASS' else '#FCA5A5'};">{issues_text}</td>
        </tr>"""

    # ── Build recommendations ──
    recommendations_html = generate_seo_recommendations(checks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{base_pdf_styles()}</style></head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">Cloud<span>Guard</span> DR</div>
    <div class="cover-subtitle">Automated Resilience & SEO Platform</div>
    <div class="cover-bar"></div>
    <div class="cover-report-type">SEO Audit Report</div>
    <div class="cover-client">{_esc(report.get('target_url', 'Unknown'))}</div>
    <div class="cover-meta">
        Generated: {_esc(report.get('generated_at', 'N/A'))}<br>
        Prepared by: {_esc(agency_name)}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>⚠ Weak Points</span><span>3</span></div>
    <div class="toc-item"><span>Technical SEO Audit</span><span>4</span></div>
    <div class="toc-item"><span>Recommendations</span><span>5</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report presents the results of an automated SEO audit for <strong>{_esc(report.get('target_url', 'N/A'))}</strong>. The analysis covers technical SEO factors, on-page optimization, content structure, and performance metrics.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {score_class}">{score}</div>
        <div class="stat-label">Overall SEO Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'good' if passing_count == total_checks else 'warn'}">{passing_count}/{total_checks}</div>
        <div class="stat-label">Checks Passing</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'good' if total_issues == 0 else 'bad'}">{total_issues}</div>
        <div class="stat-label">Issues Found</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono">{report.get('response_time_ms', 'N/A')}ms</div>
        <div class="stat-label">Response Time</div>
    </div>
</div>

<!-- Weak Points Section -->
{weak_points_html}

<!-- Technical SEO Audit -->
<h1 class="page-break">Technical SEO Audit</h1>
<p>Each check is rated as <span class="badge badge-pass">PASS</span> or <span class="badge badge-fail">FAIL</span> based on industry best practices.</p>

<table>
    <thead>
        <tr><th>Check</th><th>Status</th><th>Details</th></tr>
    </thead>
    <tbody>
        {check_rows}
    </tbody>
</table>

<!-- Recommendations -->
<h1 class="page-break">Recommendations</h1>
<p>Prioritized list of improvements based on the audit findings. Issues are ranked by severity.</p>

{recommendations_html}

<!-- Root Cause Analysis -->
{generate_root_cause_html('seo', report)}

<!-- AI Insights -->
{generate_ai_insights_html(report)}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {_esc(report.get('generated_at', 'N/A'))} by {_esc(agency_name)}</p>
</div>

</body></html>"""


def generate_seo_recommendations(checks):
    """Generate prioritized recommendations from SEO check results, with severity weighting."""
    recs = []
    priority = 1

    rec_map = [
        ("title", "Page Title", "Critical", "Rewrite the page title to be 30-60 characters, including the primary keyword. This is the single most important on-page SEO factor."),
        ("meta_description", "Meta Description", "Critical", "Add a compelling meta description of 120-160 characters. This appears in search results and directly impacts click-through rate."),
        ("headings", "Heading Structure", "Critical", "Ensure exactly one H1 tag containing the primary keyword, with proper H2-H6 hierarchy. Search engines use headings to understand page structure."),
        ("https", "HTTPS / Security", "Critical", "Migrate to HTTPS immediately. Sites without valid SSL certificates are penalized by Google and flagged as insecure by browsers."),
        ("viewport", "Mobile Viewport", "Critical", "Add the viewport meta tag for mobile responsiveness. Google uses mobile-first indexing — without this, your mobile ranking is severely impacted."),
        ("canonical", "Canonical URL", "High", "Add a canonical tag to prevent duplicate content issues. This tells search engines which version of the page to index."),
        ("structured_data", "Structured Data", "High", "Add JSON-LD structured data (LocalBusiness, FAQ, etc.) for rich results. Structured data can increase visibility in search results by 30%."),
        ("performance", "Performance", "High", "Optimize page load time — compress images, minify CSS/JS, use CDN. Page speed is a direct ranking factor and affects user experience."),
        ("images", "Image Alt Text", "Medium", "Add descriptive alt text to all images for accessibility and image search. Alt text helps Google understand image content."),
        ("open_graph", "Open Graph Tags", "Medium", "Add og:title, og:description, og:image, and og:url for social sharing. These control how your page appears when shared on social media."),
        ("twitter_card", "Twitter Card Tags", "Medium", "Add twitter:card, twitter:title, and twitter:description for proper Twitter/X sharing."),
        ("links", "Link Analysis", "Medium", "Review internal/external link structure. Ensure a healthy mix of internal links and quality external references."),
        ("robots", "Robots / Indexing", "Medium", "Verify robots.txt and meta robots tags allow search engine crawling. Incorrect directives can prevent indexing."),
    ]

    # Sort by severity: critical first, then high, then medium
    severity_order = {"Critical": 0, "High": 1, "Medium": 2}
    rec_map_sorted = sorted(
        [(k, l, s, r) for k, l, s, r in rec_map if checks.get(k, {}).get("issues", [])],
        key=lambda x: severity_order.get(x[2], 3)
    )

    for key, label, severity, default_rec in rec_map_sorted:
        check = checks.get(key, {})
        issues = check.get("issues", [])
        card_class = "critical" if severity == "Critical" else "high" if severity == "High" else ""
        badge_class = "badge-critical" if severity == "Critical" else "badge-high" if severity == "High" else "badge-medium"

        recs.append(f"""
        <div class="opportunity {card_class}">
            <h3>
                <span class="badge {badge_class}">{severity}</span>
                &nbsp; {priority}. {label}
            </h3>
            <p>{default_rec}</p>
            <ul>{''.join(f'<li style="color: #FCA5A5;">{issue}</li>' for issue in issues)}</ul>
        </div>""")
        priority += 1

    if not recs:
        return '<div class="exec-summary"><p>No critical issues found. The site is well-optimized.</p></div>'
    return "\n".join(recs)


# ═══════════════════════════════════════════════════════════════════
# COMPETITOR PDF — With Weak-Point Highlighting
# ═══════════════════════════════════════════════════════════════════

def generate_competitor_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for a competitor analysis with weak-point highlighting."""
    ga = report.get("gap_analysis", {})
    client_score = ga.get("client_score", 0)
    rank = ga.get("client_rank", 0)
    total = ga.get("total_sites", 1)
    opps = report.get("strategic_opportunities", [])
    site_analyses = report.get("site_analyses", {})
    feature_gaps = ga.get("feature_gaps", [])

    score_class = "good" if client_score >= 70 else "warn" if client_score >= 50 else "bad"

    # ── Identify client weaknesses ──
    target_url = report.get("target_url", "")
    target = site_analyses.get(target_url, {})
    weaknesses = []
    if not target.get("has_h1"):
        weaknesses.append(("Missing H1 Tag", "critical", "Your site has no H1 heading. All competitors have one."))
    if not target.get("has_blog"):
        weaknesses.append(("No Blog / Content Hub", "high", "Competitors with blogs rank for more keywords."))
    if not target.get("has_pricing"):
        weaknesses.append(("No Pricing Page", "medium", "Pricing transparency builds trust and captures high-intent traffic."))
    if not target.get("has_schema"):
        weaknesses.append(("No Structured Data", "high", "Competitors use schema markup for rich search results."))
    if not target.get("has_og_tags"):
        weaknesses.append(("No Open Graph Tags", "medium", "Your social sharing previews are unoptimized."))
    if target.get("alt_text_ratio", 100) < 50:
        weaknesses.append(("Low Image Alt Text Coverage", "high", f"Only {target.get('alt_text_ratio', 0)}% of images have alt text."))
    if (target.get("response_time_ms") or 0) > 2000:
        weaknesses.append(("Slow Response Time", "critical", f"Your site loads in {target.get('response_time_ms')}ms. Competitors average {ga.get('average_competitor_score', 0)}ms faster."))

    # Build weakness cards
    weakness_cards = ""
    for label, severity, detail in weaknesses:
        severity_class = f"severity-{severity}"
        weakness_cards += f"""
        <div class="issue-card">
            <div class="issue-severity {severity_class}">{severity}</div>
            <div class="issue-card-title">{label}</div>
            <div class="issue-card-detail">{detail}</div>
        </div>"""

    weakness_section = ""
    if weaknesses:
        weakness_section = f"""
        <div class="weak-points-banner">
            <h2>⚠ Your Weaknesses <span class="weak-count">{len(weaknesses)} GAPS</span></h2>
            <p style="color: #FCA5A5; font-size: 14px; margin-bottom: 10px;">
                These are areas where competitors outperform you. Addressing them will improve your competitive position.
            </p>
            {weakness_cards}
        </div>"""

    # ── Build competitor comparison table ──
    comp_rows = ""
    for url, analysis in site_analyses.items():
        if url == target_url:
            continue
        domain = urlparse(url).netloc.replace("www.", "")
        comp_rows += f"""
        <tr>
            <td>{domain}</td>
            <td class="mono">{analysis.get('title_length', '—')}</td>
            <td>{'<span class="text-pass">✓</span>' if analysis.get('has_h1') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if analysis.get('has_blog') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if analysis.get('has_pricing') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if analysis.get('has_schema') else '<span class="text-fail">✗</span>'}</td>
            <td class="mono">{analysis.get('alt_text_ratio', 0)}%</td>
            <td class="mono">{analysis.get('response_time_ms', '—')}ms</td>
        </tr>"""

    # ── Build opportunities ──
    opps_html = ""
    for i, opp in enumerate(opps, 1):
        details = "\n".join(
            f"<li>{d.get('action', d.get('feature', ''))}</li>"
            for d in opp.get("details", [])
        )
        impact_class = "critical" if opp.get('impact') == 'high' else "high" if opp.get('impact') == 'medium' else ""
        opps_html += f"""
        <div class="opportunity {impact_class}">
            <h3>
                <span class="badge badge-{opp.get('impact', 'medium')}">{opp.get('impact', 'medium')} impact</span>
                &nbsp; <span class="badge badge-info">{opp.get('effort', 'medium')} effort</span>
                &nbsp; {i}. {opp['title']}
            </h3>
            <p>{opp['description']}</p>
            <ul>{details}</ul>
        </div>"""

    # ── Build feature gaps ──
    gaps_rows = ""
    for gap in feature_gaps:
        sev_class = f"badge-{gap['severity']}"
        row_class = "row-fail" if gap['severity'] == 'critical' else "row-warn" if gap['severity'] == 'important' else ""
        gaps_rows += f"""
        <tr class="{row_class}">
            <td>{gap['feature']}</td>
            <td><span class="badge {sev_class}">{gap['severity']}</span></td>
            <td class="mono">{gap['competitor_pct']}%</td>
            <td>{'✗ Missing' if not gap.get('client_has') else '<span class="text-pass">✓ Has</span>'}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{base_pdf_styles()}</style></head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">Cloud<span>Guard</span> DR</div>
    <div class="cover-subtitle">Automated Resilience & SEO Platform</div>
    <div class="cover-bar"></div>
    <div class="cover-report-type">Competitive Analysis Report</div>
    <div class="cover-client">{_esc(report.get('industry', '').title())} — {_esc(report.get('city', ''))}</div>
    <div class="cover-meta">
        Target: {_esc(report.get('target_url', 'N/A'))}<br>
        Competitors Analyzed: {report.get('competitor_count', 0)}<br>
        Generated: {_esc(report.get('generated_at', 'N/A'))}<br>
        Prepared by: {_esc(agency_name)}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>⚠ Your Weaknesses</span><span>3</span></div>
    <div class="toc-item"><span>Competitor Comparison</span><span>4</span></div>
    <div class="toc-item"><span>Feature Gaps</span><span>5</span></div>
    <div class="toc-item"><span>Strategic Opportunities</span><span>6</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report compares <strong>{_esc(report.get('target_url', 'N/A'))}</strong> against {report.get('competitor_count', 0)} competitors in the {_esc(report.get('industry', ''))} market in {_esc(report.get('city', ''))}.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {score_class}">{client_score}</div>
        <div class="stat-label">Your Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value info">#{rank}</div>
        <div class="stat-label">Rank of {total}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono">{ga.get('average_competitor_score', 0)}</div>
        <div class="stat-label">Avg Competitor</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'bad' if len(feature_gaps) > 3 else 'warn' if len(feature_gaps) > 0 else 'good'}">{len(feature_gaps)}</div>
        <div class="stat-label">Feature Gaps</div>
    </div>
</div>

<!-- Weaknesses Section -->
{weakness_section}

<!-- Competitor Comparison -->
<h1 class="page-break">Competitor Comparison</h1>
<table>
    <thead>
        <tr>
            <th>Competitor</th><th>Title Len</th><th>H1</th><th>Blog</th>
            <th>Pricing</th><th>Schema</th><th>Alt %</th><th>Speed</th>
        </tr>
    </thead>
    <tbody>
        <tr class="row-pass" style="font-weight:600;">
            <td><strong>YOU</strong></td>
            <td class="mono">{target.get('title_length', '—')}</td>
            <td>{'<span class="text-pass">✓</span>' if target.get('has_h1') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if target.get('has_blog') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if target.get('has_pricing') else '<span class="text-fail">✗</span>'}</td>
            <td>{'<span class="text-pass">✓</span>' if target.get('has_schema') else '<span class="text-fail">✗</span>'}</td>
            <td class="mono">{target.get('alt_text_ratio', 0)}%</td>
            <td class="mono">{target.get('response_time_ms', '—')}ms</td>
        </tr>
        {comp_rows}
    </tbody>
</table>

<!-- Feature Gaps -->
<h1 class="page-break">Feature Gaps</h1>
<p>Features that competitors have but you are missing. Gaps are sorted by severity.</p>
<table>
    <thead><tr><th>Feature</th><th>Severity</th><th>Competitor Adoption</th><th>Your Status</th></tr></thead>
    <tbody>{gaps_rows if gaps_rows else '<tr><td colspan="4">No critical gaps found</td></tr>'}</tbody>
</table>

<!-- Strategic Opportunities -->
<h1 class="page-break">Strategic Opportunities</h1>
<p>Top actionable recommendations based on competitive gaps:</p>
{opps_html if opps_html else '<p>No strategic opportunities identified.</p>'}

<!-- Root Cause Analysis -->
{generate_root_cause_html('competitor', report)}

<!-- AI Insights -->
{generate_ai_insights_html(report)}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {_esc(report.get('generated_at', 'N/A'))} by {_esc(agency_name)}</p>
</div>

</body></html>"""


# ═══════════════════════════════════════════════════════════════════
# DR TEST PDF — With Weak-Point Highlighting
# ═══════════════════════════════════════════════════════════════════

def generate_dr_test_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for a DR test report with weak-point highlighting."""
    score = report.get("resilience_score", 0)
    status = report.get("status", "Unknown")
    score_class = "good" if score >= 70 else "warn" if score >= 50 else "bad"
    health = report.get("health_checks", {})
    rto_actual = report.get("rto_seconds", -1)
    rto_target = report.get("rto_target", 300)
    rpo_actual = report.get("rpo_seconds", -1)
    rpo_target = report.get("rpo_target", 60)

    # ── Identify failures/weaknesses ──
    failures = []
    if score < 70:
        failures.append(("Low Resilience Score", "critical", f"Score {score}/100 is below the 70 threshold. System recovery is unreliable."))
    if rto_actual > rto_target:
        failures.append(("RTO Exceeded Target", "critical", f"Recovery took {rto_actual}s vs {rto_target}s target ({rto_actual - rto_target}s over)."))
    if rpo_actual > rpo_target:
        failures.append(("RPO Exceeded Target", "high", f"Data loss window was {rpo_actual}s vs {rpo_target}s target."))
    if not health.get("https_valid"):
        failures.append(("HTTPS Invalid", "critical", "SSL certificate is invalid or expired. Site may be unreachable."))
    if not health.get("dns_failover_ok"):
        failures.append(("DNS Failover Broken", "critical", "DNS failover routing is not operational. Traffic may not redirect during outages."))
    if (health.get("response_time_ms") or 9999) > 3000:
        failures.append(("Slow Response Time", "high", f"Response time {health.get('response_time_ms')}ms exceeds 3000ms threshold."))
    if health.get("http_status_code") and health.get("http_status_code") != 200:
        failures.append(("Non-200 HTTP Status", "high", f"Server returned HTTP {health.get('http_status_code')}. Expected 200 OK."))

    # Build failure cards
    failure_cards = ""
    for label, severity, detail in failures:
        severity_class = f"severity-{severity}"
        failure_cards += f"""
        <div class="issue-card">
            <div class="issue-severity {severity_class}">{severity}</div>
            <div class="issue-card-title">{label}</div>
            <div class="issue-card-detail">{detail}</div>
        </div>"""

    failure_section = ""
    if failures:
        failure_section = f"""
        <div class="weak-points-banner">
            <h2>⚠ Failures & Weaknesses <span class="weak-count">{len(failures)} ISSUES</span></h2>
            <p style="color: #FCA5A5; font-size: 14px; margin-bottom: 10px;">
                The following issues were detected during this disaster recovery test. Immediate remediation is recommended.
            </p>
            {failure_cards}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{base_pdf_styles()}</style></head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">Cloud<span>Guard</span> DR</div>
    <div class="cover-subtitle">Automated Resilience & SEO Platform</div>
    <div class="cover-bar"></div>
    <div class="cover-report-type">Disaster Recovery Test Report</div>
    <div class="cover-client">Run: {_esc(report.get('run_id', 'N/A'))}</div>
    <div class="cover-meta">
        Fault Type: {_esc(report.get('fault_type', 'N/A'))}<br>
        Target: {_esc(report.get('target_resource', 'N/A'))}<br>
        Generated: {_esc(report.get('generated_at', 'N/A'))}<br>
        Prepared by: {_esc(agency_name)}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>⚠ Failures & Weaknesses</span><span>3</span></div>
    <div class="toc-item"><span>Resilience Metrics</span><span>4</span></div>
    <div class="toc-item"><span>Site Health Checks</span><span>5</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report documents the results of a disaster recovery test performed on <strong>{_esc(report.get('target_resource', 'N/A'))}</strong> using AWS Fault Injection Simulator. The test simulated a {_esc(report.get('fault_type', 'ec2-termination'))} event and measured system recovery.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {score_class}">{score}</div>
        <div class="stat-label">Resilience Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'good' if status == 'Passed' else 'bad'}">{status}</div>
        <div class="stat-label">Test Result</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono {'good' if rto_actual <= rto_target else 'bad'}">{rto_actual}s</div>
        <div class="stat-label">RTO (Target: {rto_target}s)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono {'good' if rpo_actual <= rpo_target else 'bad'}">{rpo_actual}s</div>
        <div class="stat-label">RPO (Target: {rpo_target}s)</div>
    </div>
</div>

<!-- Failures Section -->
{failure_section}

<!-- Resilience Metrics -->
<h1 class="page-break">Resilience Metrics</h1>
<table>
    <thead><tr><th>Metric</th><th>Actual</th><th>Target</th><th>Status</th></tr></thead>
    <tbody>
        <tr class="{'row-fail' if rto_actual > rto_target else 'row-pass'}">
            <td>Recovery Time (RTO)</td>
            <td class="mono">{rto_actual}s</td>
            <td class="mono">{rto_target}s</td>
            <td><span class="badge {'badge-pass' if rto_actual <= rto_target else 'badge-fail'}">
                {'PASS' if rto_actual <= rto_target else 'FAIL'}
            </span></td>
        </tr>
        <tr class="{'row-fail' if rpo_actual > rpo_target else 'row-pass'}">
            <td>Recovery Point (RPO)</td>
            <td class="mono">{rpo_actual}s</td>
            <td class="mono">{rpo_target}s</td>
            <td><span class="badge {'badge-pass' if rpo_actual <= rpo_target else 'badge-fail'}">
                {'PASS' if rpo_actual <= rpo_target else 'FAIL'}
            </span></td>
        </tr>
        <tr class="{'row-fail' if score < 70 else 'row-pass'}">
            <td>Overall Score</td>
            <td class="mono">{score}/100</td>
            <td class="mono">70+</td>
            <td><span class="badge {'badge-pass' if score >= 70 else 'badge-fail'}">
                {'PASS' if score >= 70 else 'FAIL'}
            </span></td>
        </tr>
    </tbody>
</table>

<!-- Site Health Checks -->
<h1 class="page-break">Site Health Checks</h1>
<table>
    <thead><tr><th>Check</th><th>Status</th><th>Details</th></tr></thead>
    <tbody>
        <tr class="{'row-pass' if health.get('https_valid') else 'row-fail'}">
            <td>HTTPS Valid</td>
            <td><span class="badge {'badge-pass' if health.get('https_valid') else 'badge-fail'}">
                {'PASS' if health.get('https_valid') else 'FAIL'}
            </span></td>
            <td>SSL certificate is {'valid' if health.get('https_valid') else '<span class="text-fail">invalid or expired</span>'}</td>
        </tr>
        <tr class="{'row-pass' if health.get('dns_failover_ok') else 'row-fail'}">
            <td>DNS Failover</td>
            <td><span class="badge {'badge-pass' if health.get('dns_failover_ok') else 'badge-fail'}">
                {'PASS' if health.get('dns_failover_ok') else 'FAIL'}
            </span></td>
            <td>DNS failover routing is {'operational' if health.get('dns_failover_ok') else '<span class="text-fail">not working</span>'}</td>
        </tr>
        <tr class="{'row-pass' if (health.get('response_time_ms') or 9999) < 3000 else 'row-warn'}">
            <td>Response Time</td>
            <td><span class="badge {'badge-pass' if (health.get('response_time_ms') or 9999) < 3000 else 'badge-warn'}">
                {health.get('response_time_ms', 'N/A')}ms
            </span></td>
            <td>Page loaded in {health.get('response_time_ms', 'N/A')}ms</td>
        </tr>
        <tr class="{'row-pass' if health.get('http_status_code') == 200 else 'row-fail'}">
            <td>HTTP Status</td>
            <td><span class="badge {'badge-pass' if health.get('http_status_code') == 200 else 'badge-fail'}">
                {health.get('http_status_code', 'N/A')}
            </span></td>
            <td>Server returned HTTP {health.get('http_status_code', 'N/A')}</td>
        </tr>
    </tbody>
</table>

<!-- Root Cause Analysis -->
{generate_root_cause_html('dr-test', report)}

<!-- AI Insights -->
{generate_ai_insights_html(report)}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {_esc(report.get('generated_at', 'N/A'))} by {_esc(agency_name)}</p>
</div>

</body></html>"""


# ═══════════════════════════════════════════════════════════════════
# COMPARISON PDF — Side-by-Side with Delta Highlighting
# ═══════════════════════════════════════════════════════════════════

def generate_comparison_pdf_html(data, agency_name):
    """Generate a branded PDF HTML for a side-by-side run comparison with delta highlighting."""
    run_a = data.get("run_a", {})
    run_b = data.get("run_b", {})
    report_a = data.get("report_a") or {}
    report_b = data.get("report_b") or {}

    # Calculate deltas
    score_a = run_a.get("resilience_score", 0)
    score_b = run_b.get("resilience_score", 0)
    score_delta = score_b - score_a

    rto_a = run_a.get("rto_seconds", 0)
    rto_b = run_b.get("rto_seconds", 0)
    rto_delta = rto_b - rto_a

    rpo_a = run_a.get("rpo_seconds", 0)
    rpo_b = run_b.get("rpo_seconds", 0)
    rpo_delta = rpo_b - rpo_a

    # Health checks comparison
    health_a = report_a.get("health_checks", {})
    health_b = report_b.get("health_checks", {})

    # ── Identify weaknesses in run B ──
    weaknesses = []
    if score_delta < 0:
        weaknesses.append(("Score Regression", "critical", f"Resilience score dropped by {abs(score_delta)} points ({score_a} → {score_b})."))
    if rto_b > run_b.get("rto_target", 300):
        weaknesses.append(("RTO Target Exceeded", "critical", f"Run B recovery time ({rto_b}s) exceeds target ({run_b.get('rto_target', 300)}s)."))
    if rpo_b > run_b.get("rpo_target", 60):
        weaknesses.append(("RPO Target Exceeded", "high", f"Run B data loss window ({rpo_b}s) exceeds target ({run_b.get('rpo_target', 60)}s)."))
    if run_b.get("status") == "Failed" and run_a.get("status") == "Passed":
        weaknesses.append(("Status Regression", "critical", "Test went from PASSED to FAILED. System reliability degraded."))
    if not health_b.get("https_valid") and health_a.get("https_valid"):
        weaknesses.append(("HTTPS Regression", "critical", "HTTPS validity lost between runs."))
    if not health_b.get("dns_failover_ok") and health_a.get("dns_failover_ok"):
        weaknesses.append(("DNS Failover Regression", "critical", "DNS failover stopped working between runs."))
    rto_target = run_b.get("rto_target", 300)
    if rto_a <= rto_target and rto_b > rto_target:
        weaknesses.append(("RTO Breach", "critical", f"RTO went from within target ({rto_a}s ≤ {rto_target}s) to exceeding it ({rto_b}s > {rto_target}s)."))

    # Build weakness cards
    weakness_cards = ""
    for label, severity, detail in weaknesses:
        severity_class = f"severity-{severity}"
        weakness_cards += f"""
        <div class="issue-card">
            <div class="issue-severity {severity_class}">{severity}</div>
            <div class="issue-card-title">{label}</div>
            <div class="issue-card-detail">{detail}</div>
        </div>"""

    weakness_section = ""
    if weaknesses:
        weakness_section = f"""
        <div class="weak-points-banner">
            <h2>⚠ Weaknesses Identified <span class="weak-count">{len(weaknesses)} REGRESSIONS</span></h2>
            <p style="color: #FCA5A5; font-size: 14px; margin-bottom: 10px;">
                These metrics degraded between the two runs. Investigate what changed to cause these regressions.
            </p>
            {weakness_cards}
        </div>"""

    # ── Build comparison rows ──
    def delta_cell(delta, inverse=False):
        """Render a delta cell with color coding."""
        improved = (delta < 0) if inverse else (delta > 0)
        degraded = (delta > 0) if inverse else (delta < 0)
        if delta == 0:
            return '<td class="delta-neutral">—</td>'
        elif improved:
            return f'<td class="delta-good">▼ {abs(delta)}</td>'
        else:
            return f'<td class="delta-bad">▲ {abs(delta)}</td>'

    def format_seconds(s):
        """Format seconds into human-readable string."""
        if s is None:
            return "—"
        s = int(s)
        if s < 60:
            return f"{s}s"
        m, sec = divmod(s, 60)
        return f"{m}m {sec}s" if sec else f"{m}m"

    def bool_cell(val):
        if val:
            return '<span class="text-pass">✓</span>'
        return '<span class="text-fail">✗</span>'

    rto_target_a = run_a.get("rto_target", 300)
    rto_target_b = run_b.get("rto_target", 300)
    rpo_target_a = run_a.get("rpo_target", 60)
    rpo_target_b = run_b.get("rpo_target", 60)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><style>{base_pdf_styles()}</style></head>
<body>

<!-- Cover Page -->
<div class="cover">
    <div class="cover-logo">Cloud<span>Guard</span> DR</div>
    <div class="cover-subtitle">Automated Resilience & SEO Platform</div>
    <div class="cover-bar"></div>
    <div class="cover-report-type">Run Comparison Report</div>
    <div class="cover-client">{_esc(run_a.get('run_id', 'A'))} vs {_esc(run_b.get('run_id', 'B'))}</div>
    <div class="cover-meta">
        Run A: {_esc(run_a.get('run_id', 'N/A'))} ({_esc(run_a.get('timestamp', 'N/A'))})<br>
        Run B: {_esc(run_b.get('run_id', 'N/A'))} ({_esc(run_b.get('timestamp', 'N/A'))})<br>
        Generated: {_esc(data.get('generated_at', 'N/A'))}<br>
        Prepared by: {_esc(agency_name)}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>⚠ Weaknesses & Regressions</span><span>3</span></div>
    <div class="toc-item"><span>Side-by-Side Comparison</span><span>4</span></div>
    <div class="toc-item"><span>Health Check Comparison</span><span>5</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>Comparing <strong>{_esc(run_a.get('run_id', 'A'))}</strong> against <strong>{_esc(run_b.get('run_id', 'B'))}</strong>. This report highlights differences in resilience metrics, test outcomes, and site health between the two runs.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {'good' if score_delta >= 0 else 'bad'}">{score_delta:+d}</div>
        <div class="stat-label">Score Delta</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono {'bad' if rto_delta > 0 else 'good'}">{format_seconds(rto_delta)}</div>
        <div class="stat-label">RTO Delta</div>
    </div>
    <div class="stat-card">
        <div class="stat-value mono {'bad' if rpo_delta > 0 else 'good'}">{format_seconds(rpo_delta)}</div>
        <div class="stat-label">RPO Delta</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'bad' if len(weaknesses) > 0 else 'good'}">{len(weaknesses)}</div>
        <div class="stat-label">Regressions</div>
    </div>
</div>

<!-- Weaknesses Section -->
{weakness_section}

<!-- Side-by-Side Comparison -->
<h1 class="page-break">Side-by-Side Comparison</h1>
<table>
    <thead>
        <tr>
            <th style="width: 25%;">Metric</th>
            <th style="width: 28%;">Run A: {run_a.get('run_id', 'A')[:16]}</th>
            <th style="width: 28%;">Run B: {run_b.get('run_id', 'B')[:16]}</th>
            <th style="width: 19%; text-align: right;">Delta</th>
        </tr>
    </thead>
    <tbody>
        <tr class="{'row-fail' if score_delta < 0 else 'row-pass' if score_delta > 0 else ''}">
            <td style="font-weight: 500;">Score</td>
            <td class="mono" style="font-weight: 600; color: {'#22C55E' if score_a >= 70 else '#F59E0B' if score_a >= 50 else '#EF4444'};">{score_a}</td>
            <td class="mono" style="font-weight: 600; color: {'#22C55E' if score_b >= 70 else '#F59E0B' if score_b >= 50 else '#EF4444'};">{score_b}</td>
            {delta_cell(score_delta, inverse=False)}
        </tr>
        <tr class="{'row-fail' if rto_delta > 0 else 'row-pass' if rto_delta < 0 else ''}">
            <td style="font-weight: 500;">RTO</td>
            <td class="mono">{format_seconds(rto_a)} <span class="text-muted">/ {format_seconds(rto_target_a)}</span></td>
            <td class="mono">{format_seconds(rto_b)} <span class="text-muted">/ {format_seconds(rto_target_b)}</span></td>
            {delta_cell(rto_delta, inverse=True)}
        </tr>
        <tr class="{'row-fail' if rpo_delta > 0 else 'row-pass' if rpo_delta < 0 else ''}">
            <td style="font-weight: 500;">RPO</td>
            <td class="mono">{format_seconds(rpo_a)} <span class="text-muted">/ {format_seconds(rpo_target_a)}</span></td>
            <td class="mono">{format_seconds(rpo_b)} <span class="text-muted">/ {format_seconds(rpo_target_b)}</span></td>
            {delta_cell(rpo_delta, inverse=True)}
        </tr>
        <tr class="{'row-fail' if run_b.get('status') == 'Failed' and run_a.get('status') == 'Passed' else 'row-pass' if run_b.get('status') == 'Passed' and run_a.get('status') == 'Failed' else ''}">
            <td style="font-weight: 500;">Status</td>
            <td><span class="badge {'badge-pass' if run_a.get('status') == 'Passed' else 'badge-fail'}">{run_a.get('status', 'Unknown')}</span></td>
            <td><span class="badge {'badge-pass' if run_b.get('status') == 'Passed' else 'badge-fail'}">{run_b.get('status', 'Unknown')}</span></td>
            <td class="delta-neutral">{'—' if run_a.get('status') == run_b.get('status') else '▼ Changed' if run_b.get('status') == 'Passed' else '▲ REGRESSION'}</td>
        </tr>
        <tr>
            <td style="font-weight: 500;">Fault Type</td>
            <td class="mono">{run_a.get('fault_type', 'N/A')}</td>
            <td class="mono">{run_b.get('fault_type', 'N/A')}</td>
            <td class="delta-neutral">{'—' if run_a.get('fault_type') == run_b.get('fault_type') else 'Changed'}</td>
        </tr>
        <tr>
            <td style="font-weight: 500;">Target</td>
            <td class="mono">{run_a.get('target_resource', 'N/A')}</td>
            <td class="mono">{run_b.get('target_resource', 'N/A')}</td>
            <td class="delta-neutral">{'—' if run_a.get('target_resource') == run_b.get('target_resource') else 'Changed'}</td>
        </tr>
    </tbody>
</table>

<!-- Health Check Comparison -->
<h1 class="page-break">Health Check Comparison</h1>
<table>
    <thead>
        <tr>
            <th style="width: 25%;">Check</th>
            <th style="width: 28%;">Run A</th>
            <th style="width: 28%;">Run B</th>
            <th style="width: 19%; text-align: right;">Delta</th>
        </tr>
    </thead>
    <tbody>
        <tr class="{'row-fail' if not health_b.get('https_valid') and health_a.get('https_valid') else 'row-pass' if health_b.get('https_valid') and not health_a.get('https_valid') else ''}">
            <td style="font-weight: 500;">HTTPS Valid</td>
            <td>{bool_cell(health_a.get('https_valid'))}</td>
            <td>{bool_cell(health_b.get('https_valid'))}</td>
            <td class="delta-neutral">{'—' if health_a.get('https_valid') == health_b.get('https_valid') else '▼ REGRESSION' if not health_b.get('https_valid') else '▲ Fixed'}</td>
        </tr>
        <tr class="{'row-fail' if not health_b.get('dns_failover_ok') and health_a.get('dns_failover_ok') else 'row-pass' if health_b.get('dns_failover_ok') and not health_a.get('dns_failover_ok') else ''}">
            <td style="font-weight: 500;">DNS Failover</td>
            <td>{bool_cell(health_a.get('dns_failover_ok'))}</td>
            <td>{bool_cell(health_b.get('dns_failover_ok'))}</td>
            <td class="delta-neutral">{'—' if health_a.get('dns_failover_ok') == health_b.get('dns_failover_ok') else '▼ REGRESSION' if not health_b.get('dns_failover_ok') else '▲ Fixed'}</td>
        </tr>
        <tr class="{'row-warn' if (health_b.get('response_time_ms') or 0) > (health_a.get('response_time_ms') or 0) * 1.5 else 'row-pass' if (health_b.get('response_time_ms') or 0) < (health_a.get('response_time_ms') or 0) * 0.7 else ''}">
            <td style="font-weight: 500;">Response Time</td>
            <td class="mono">{health_a.get('response_time_ms', 'N/A')}ms</td>
            <td class="mono">{health_b.get('response_time_ms', 'N/A')}ms</td>
            {delta_cell((health_b.get('response_time_ms') or 0) - (health_a.get('response_time_ms') or 0), inverse=True) if health_a.get('response_time_ms') and health_b.get('response_time_ms') else '<td class="delta-neutral">—</td>'}
        </tr>
        <tr>
            <td style="font-weight: 500;">HTTP Status</td>
            <td class="mono">{health_a.get('http_status_code', 'N/A')}</td>
            <td class="mono">{health_b.get('http_status_code', 'N/A')}</td>
            <td class="delta-neutral">{'—' if health_a.get('http_status_code') == health_b.get('http_status_code') else 'Changed'}</td>
        </tr>
    </tbody>
</table>

<!-- Root Cause Analysis -->
{generate_root_cause_html('comparison', data)}

<!-- AI Insights -->
{generate_ai_insights_html(data)}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {_esc(data.get('generated_at', 'N/A'))} by {_esc(agency_name)}</p>
</div>

</body></html>"""
