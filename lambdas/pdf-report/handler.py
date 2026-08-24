"""
CloudGuard DR — PDF Report Generator Lambda
Fetches existing JSON audit reports from S3, generates a branded PDF
with cover page, executive summary, and detailed sections.
Uses weasyprint for HTML-to-PDF conversion.
"""
import os
import json
import time
import uuid
import io
import boto3

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")


def lambda_handler(event, context):
    """
    Generate a branded PDF report from an existing JSON report.

    Event input:
        {
            "report_type": "seo" | "competitor" | "dr-test",
            "report_id": "seo-abc12345" or "comp-abc12345" or "report-abc12345",
            "agency_name": "Acme Agency"  // optional, for cover page
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

        # Fetch the JSON report from S3
        json_key = find_report_json(report_type, report_id)
        if not json_key:
            raise ValueError(f"Report not found for {report_type}/{report_id}")

        report_data = fetch_json_report(json_key)

        # Generate branded HTML based on report type
        if report_type == "seo":
            html = generate_seo_pdf_html(report_data, agency_name)
        elif report_type == "competitor":
            html = generate_competitor_pdf_html(report_data, agency_name)
        elif report_type == "dr-test":
            html = generate_dr_test_pdf_html(report_data, agency_name)
        else:
            raise ValueError(f"Unknown report_type: {report_type}")

        # Convert HTML to PDF using weasyprint
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html).write_pdf()
        except ImportError:
            # Fallback: if weasyprint is not available (e.g., no layer),
            # return the HTML as a "PDF" with a note
            print("[PDFReport] weasyprint not available — returning HTML fallback")
            pdf_key = f"pdf-reports/{report_id}/report.html"
            s3_client.put_object(
                Bucket=REPORTS_BUCKET,
                Key=pdf_key,
                Body=html.encode("utf-8"),
                ContentType="text/html",
            )
            return {
                "statusCode": 200,
                "pdf_key": pdf_key,
                "pdf_url": f"s3://{REPORTS_BUCKET}/{pdf_key}",
                "report_type": report_type,
                "report_id": report_id,
                "format": "html_fallback",
                "message": "weasyprint not available — HTML report generated instead of PDF",
            }

        # Upload PDF to S3
        pdf_key = f"pdf-reports/{report_id}/report.pdf"
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=pdf_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )

        result = {
            "statusCode": 200,
            "pdf_key": pdf_key,
            "pdf_url": f"s3://{REPORTS_BUCKET}/{pdf_key}",
            "report_type": report_type,
            "report_id": report_id,
            "format": "pdf",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        print(f"[PDFReport] PDF generated: {pdf_key} ({len(pdf_bytes)} bytes)")
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


# ─── Base Styles ────────────────────────────────────────────────────

def base_pdf_styles():
    """Return the base CSS for all PDF reports with print @page rules."""
    return """
    @page {
        size: A4;
        margin: 20mm 18mm 25mm 18mm;
        @bottom-center {
            content: "CloudGuard DR — Confidential";
            font-size: 8px;
            color: #666;
        }
        @bottom-right {
            content: counter(page) " / " counter(pages);
            font-size: 8px;
            color: #666;
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
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.5;
        color: #1a1a1a;
        background: white;
    }
    .cover {
        page: cover;
        width: 210mm;
        height: 297mm;
        background: linear-gradient(135deg, #0A0A0A 0%, #1a1a2e 50%, #16213e 100%);
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        page-break-after: always;
        padding: 40mm;
    }
    .cover-logo {
        font-size: 36pt;
        font-weight: 700;
        letter-spacing: -1px;
        margin-bottom: 8mm;
    }
    .cover-logo span {
        color: #22C55E;
    }
    .cover-subtitle {
        font-size: 14pt;
        color: #A1A1A1;
        margin-bottom: 20mm;
        font-weight: 300;
    }
    .cover-report-type {
        font-size: 20pt;
        font-weight: 600;
        margin-bottom: 6mm;
        color: #F5F5F5;
    }
    .cover-client {
        font-size: 16pt;
        color: #A1A1A1;
        margin-bottom: 30mm;
    }
    .cover-meta {
        font-size: 9pt;
        color: #666;
        line-height: 2;
    }
    .cover-bar {
        width: 60mm;
        height: 3px;
        background: #22C55E;
        margin: 10mm auto;
    }
    h1 {
        font-size: 18pt;
        font-weight: 700;
        color: #0A0A0A;
        margin: 8mm 0 4mm 0;
        padding-bottom: 2mm;
        border-bottom: 2px solid #22C55E;
    }
    h2 {
        font-size: 13pt;
        font-weight: 600;
        color: #1a1a1a;
        margin: 6mm 0 3mm 0;
    }
    h3 {
        font-size: 11pt;
        font-weight: 600;
        color: #333;
        margin: 4mm 0 2mm 0;
    }
    p {
        margin-bottom: 3mm;
        color: #333;
    }
    .section {
        page-break-inside: avoid;
        margin-bottom: 6mm;
    }
    .exec-summary {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 5mm;
        margin: 5mm 0;
    }
    .stat-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 4mm;
        margin: 4mm 0;
    }
    .stat-card {
        flex: 1;
        min-width: 35mm;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 4mm;
        text-align: center;
    }
    .stat-value {
        font-size: 20pt;
        font-weight: 700;
        color: #0A0A0A;
    }
    .stat-value.good { color: #16a34a; }
    .stat-value.warn { color: #d97706; }
    .stat-value.bad { color: #dc2626; }
    .stat-label {
        font-size: 8pt;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 1mm;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 3mm 0;
        font-size: 9pt;
    }
    th {
        background: #f1f3f5;
        font-weight: 600;
        text-align: left;
        padding: 2.5mm 3mm;
        border-bottom: 2px solid #dee2e6;
        font-size: 8pt;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #495057;
    }
    td {
        padding: 2mm 3mm;
        border-bottom: 1px solid #e9ecef;
        vertical-align: top;
    }
    tr:nth-child(even) { background: #f8f9fa; }
    .badge {
        display: inline-block;
        padding: 1mm 3mm;
        border-radius: 2px;
        font-size: 7pt;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-pass { background: #dcfce7; color: #166534; }
    .badge-fail { background: #fee2e2; color: #991b1b; }
    .badge-warn { background: #fef3c7; color: #92400e; }
    .badge-info { background: #dbeafe; color: #1e40af; }
    .badge-high { background: #fee2e2; color: #991b1b; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #dcfce7; color: #166534; }
    .opportunity {
        border: 1px solid #e9ecef;
        border-left: 3px solid #22C55E;
        border-radius: 4px;
        padding: 4mm;
        margin: 3mm 0;
        page-break-inside: avoid;
    }
    .opportunity h3 {
        margin: 0 0 2mm 0;
    }
    .opportunity p {
        font-size: 9pt;
        color: #555;
    }
    .opportunity ul {
        margin: 2mm 0 0 5mm;
        font-size: 9pt;
        color: #555;
    }
    .opportunity li { margin-bottom: 1mm; }
    .toc {
        page: toc;
        page-break-after: always;
    }
    .toc h1 { border-bottom-color: #22C55E; }
    .toc-item {
        display: flex;
        justify-content: space-between;
        padding: 2mm 0;
        border-bottom: 1px dotted #ccc;
        font-size: 10pt;
    }
    .toc-item span:first-child { font-weight: 500; }
    .toc-item span:last-child { color: #666; }
    .closing {
        margin-top: 15mm;
        padding-top: 5mm;
        border-top: 2px solid #22C55E;
        text-align: center;
        color: #666;
        font-size: 9pt;
    }
    .closing strong { color: #0A0A0A; }
    .page-break { page-break-before: always; }
    """


# ─── SEO PDF ────────────────────────────────────────────────────────

def generate_seo_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for an SEO audit report."""
    checks = report.get("seo_checks", {})
    score = report.get("seo_score", 0)

    # Count issues
    total_issues = sum(
        len(checks.get(k, {}).get("issues", []))
        for k in checks
    )
    passing_checks = sum(
        1 for k in checks
        if not checks.get(k, {}).get("issues", [])
    )
    total_checks = len(checks) if checks else 1

    # Score class
    score_class = "good" if score >= 70 else "warn" if score >= 50 else "bad"

    # Build check rows
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
        issues_text = "; ".join(issues) if issues else "No issues found"
        check_rows += f"""
        <tr>
            <td>{label}</td>
            <td><span class="badge {badge_class}">{status}</span></td>
            <td>{issues_text}</td>
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
    <div class="cover-report-type">SEO Audit Report</div>
    <div class="cover-client">{report.get('target_url', 'Unknown')}</div>
    <div class="cover-meta">
        Generated: {report.get('generated_at', 'N/A')}<br>
        Prepared by: {agency_name}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>Technical SEO Audit</span><span>3</span></div>
    <div class="toc-item"><span>Detailed Findings</span><span>4</span></div>
    <div class="toc-item"><span>Recommendations</span><span>5</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report presents the results of an automated SEO audit for <strong>{report.get('target_url', 'N/A')}</strong>. The analysis covers technical SEO factors, on-page optimization, content structure, and performance metrics.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {score_class}">{score}</div>
        <div class="stat-label">Overall SEO Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'good' if passing_checks == total_checks else 'warn'}">{passing_checks}/{total_checks}</div>
        <div class="stat-label">Checks Passing</div>
    </div>
    <div class="stat-card">
        <div class="stat-value {'good' if total_issues == 0 else 'bad'}">{total_issues}</div>
        <div class="stat-label">Issues Found</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{report.get('response_time_ms', 'N/A')}ms</div>
        <div class="stat-label">Response Time</div>
    </div>
</div>

<!-- Technical SEO Audit -->
<h1 class="page-break">Technical SEO Audit</h1>
<p>Each check below is rated as <span class="badge badge-pass">PASS</span> or <span class="badge badge-fail">FAIL</span> based on industry best practices.</p>

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
<p>Prioritized list of improvements based on the audit findings:</p>

{generate_seo_recommendations(checks)}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {report.get('generated_at', 'N/A')} by {agency_name}</p>
</div>

</body></html>"""


def generate_seo_recommendations(checks):
    """Generate prioritized recommendations from SEO check results."""
    recs = []
    priority = 1

    rec_map = [
        ("title", "Page Title", "Rewrite the page title to be 30-60 characters, including the primary keyword."),
        ("meta_description", "Meta Description", "Add a compelling meta description of 120-160 characters."),
        ("headings", "Heading Structure", "Ensure exactly one H1 tag containing the primary keyword, with proper H2-H6 hierarchy."),
        ("images", "Image Alt Text", "Add descriptive alt text to all images for accessibility and image search."),
        ("canonical", "Canonical URL", "Add a canonical tag to prevent duplicate content issues."),
        ("open_graph", "Open Graph Tags", "Add og:title, og:description, og:image, and og:url for social sharing."),
        ("twitter_card", "Twitter Card Tags", "Add twitter:card, twitter:title, and twitter:description."),
        ("viewport", "Mobile Viewport", "Add the viewport meta tag for mobile responsiveness."),
        ("structured_data", "Structured Data", "Add JSON-LD structured data (LocalBusiness, FAQ, etc.) for rich results."),
        ("performance", "Performance", "Optimize page load time — compress images, minify CSS/JS, use CDN."),
    ]

    for key, label, default_rec in rec_map:
        check = checks.get(key, {})
        issues = check.get("issues", [])
        if issues:
            recs.append(f"""
            <div class="opportunity">
                <h3>{priority}. {label}</h3>
                <p>{default_rec}</p>
                <ul>{''.join(f'<li>{issue}</li>' for issue in issues)}</ul>
            </div>""")
            priority += 1

    if not recs:
        return '<p>No critical issues found. The site is well-optimized.</p>'
    return "\n".join(recs)


# ─── Competitor PDF ─────────────────────────────────────────────────

def generate_competitor_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for a competitor analysis report."""
    ga = report.get("gap_analysis", {})
    client_score = ga.get("client_score", 0)
    rank = ga.get("client_rank", 0)
    total = ga.get("total_sites", 1)
    opps = report.get("strategic_opportunities", [])
    site_analyses = report.get("site_analyses", {})

    score_class = "good" if client_score >= 70 else "warn" if client_score >= 50 else "bad"

    # Build competitor comparison table
    comp_rows = ""
    target = site_analyses.get(report.get("target_url", ""), {})
    for url, analysis in site_analyses.items():
        if url == report.get("target_url"):
            continue
        from urllib.parse import urlparse as _urlparse
        domain = _urlparse(url).netloc.replace("www.", "")
        comp_rows += f"""
        <tr>
            <td>{domain}</td>
            <td>{analysis.get('title_length', '—')}</td>
            <td>{'✓' if analysis.get('has_h1') else '✗'}</td>
            <td>{'✓' if analysis.get('has_blog') else '✗'}</td>
            <td>{'✓' if analysis.get('has_pricing') else '✗'}</td>
            <td>{'✓' if analysis.get('has_schema') else '✗'}</td>
            <td>{analysis.get('alt_text_ratio', 0)}%</td>
            <td>{analysis.get('response_time_ms', '—')}ms</td>
        </tr>"""

    # Build opportunities
    opps_html = ""
    for i, opp in enumerate(opps, 1):
        details = "\n".join(
            f"<li>{d.get('action', d.get('feature', ''))}</li>"
            for d in opp.get("details", [])
        )
        opps_html += f"""
        <div class="opportunity">
            <h3>{i}. {opp['title']}</h3>
            <p><span class="badge badge-{opp.get('impact', 'medium')}">{opp.get('impact', 'medium')} impact</span>
            &nbsp; <span class="badge badge-info">{opp.get('effort', 'medium')} effort</span></p>
            <p>{opp['description']}</p>
            <ul>{details}</ul>
        </div>"""

    # Feature gaps
    gaps_rows = ""
    for gap in ga.get("feature_gaps", []):
        sev_class = f"badge-{gap['severity']}"
        gaps_rows += f"""
        <tr>
            <td>{gap['feature']}</td>
            <td><span class="badge {sev_class}">{gap['severity']}</span></td>
            <td>{gap['competitor_pct']}%</td>
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
    <div class="cover-client">{report.get('industry', '').title()} — {report.get('city', '')}</div>
    <div class="cover-meta">
        Target: {report.get('target_url', 'N/A')}<br>
        Competitors Analyzed: {report.get('competitor_count', 0)}<br>
        Generated: {report.get('generated_at', 'N/A')}<br>
        Prepared by: {agency_name}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>Competitor Comparison</span><span>3</span></div>
    <div class="toc-item"><span>Feature Gaps</span><span>4</span></div>
    <div class="toc-item"><span>Strategic Opportunities</span><span>5</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report compares <strong>{report.get('target_url', 'N/A')}</strong> against {report.get('competitor_count', 0)} competitors in the {report.get('industry', '')} market in {report.get('city', '')}.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-value {score_class}">{client_score}</div>
        <div class="stat-label">Client SEO Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">#{rank}</div>
        <div class="stat-label">Rank out of {total}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{ga.get('average_competitor_score', 0)}</div>
        <div class="stat-label">Avg Competitor Score</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{len(ga.get('feature_gaps', []))}</div>
        <div class="stat-label">Feature Gaps</div>
    </div>
</div>

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
        <tr style="font-weight:600;background:#f0fdf4;">
            <td>CLIENT</td>
            <td>{target.get('title_length', '—')}</td>
            <td>{'✓' if target.get('has_h1') else '✗'}</td>
            <td>{'✓' if target.get('has_blog') else '✗'}</td>
            <td>{'✓' if target.get('has_pricing') else '✗'}</td>
            <td>{'✓' if target.get('has_schema') else '✗'}</td>
            <td>{target.get('alt_text_ratio', 0)}%</td>
            <td>{target.get('response_time_ms', '—')}ms</td>
        </tr>
        {comp_rows}
    </tbody>
</table>

<!-- Feature Gaps -->
<h1 class="page-break">Feature Gaps</h1>
<p>Features that competitors have but the client is missing:</p>
<table>
    <thead><tr><th>Feature</th><th>Severity</th><th>Competitor Adoption</th></tr></thead>
    <tbody>{gaps_rows if gaps_rows else '<tr><td colspan="3">No critical gaps found</td></tr>'}</tbody>
</table>

<!-- Strategic Opportunities -->
<h1 class="page-break">Strategic Opportunities</h1>
<p>Top 3 actionable recommendations based on competitive analysis:</p>
{opps_html if opps_html else '<p>No strategic opportunities identified.</p>'}

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {report.get('generated_at', 'N/A')} by {agency_name}</p>
</div>

</body></html>"""


# ─── DR Test PDF ────────────────────────────────────────────────────

def generate_dr_test_pdf_html(report, agency_name):
    """Generate a branded PDF HTML for a DR test audit report."""
    score = report.get("resilience_score", 0)
    status = report.get("status", "Unknown")
    score_class = "good" if score >= 70 else "warn" if score >= 50 else "bad"
    health = report.get("health_checks", {})

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
    <div class="cover-client">Run: {report.get('run_id', 'N/A')}</div>
    <div class="cover-meta">
        Fault Type: {report.get('fault_type', 'N/A')}<br>
        Target: {report.get('target_resource', 'N/A')}<br>
        Generated: {report.get('generated_at', 'N/A')}<br>
        Prepared by: {agency_name}
    </div>
</div>

<!-- Table of Contents -->
<div class="toc">
    <h1>Table of Contents</h1>
    <div class="toc-item"><span>Executive Summary</span><span>2</span></div>
    <div class="toc-item"><span>Resilience Metrics</span><span>3</span></div>
    <div class="toc-item"><span>Site Health Checks</span><span>4</span></div>
</div>

<!-- Executive Summary -->
<h1>Executive Summary</h1>
<div class="exec-summary">
    <p>This report documents the results of a disaster recovery test performed on <strong>{report.get('target_resource', 'N/A')}</strong> using AWS Fault Injection Simulator. The test simulated a {report.get('fault_type', 'ec2-termination')} event and measured system recovery.</p>
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
        <div class="stat-value">{report.get('rto_seconds', '—')}s</div>
        <div class="stat-label">RTO (Target: {report.get('rto_target', 300)}s)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{report.get('rpo_seconds', '—')}s</div>
        <div class="stat-label">RPO (Target: {report.get('rpo_target', 60)}s)</div>
    </div>
</div>

<!-- Resilience Metrics -->
<h1 class="page-break">Resilience Metrics</h1>
<table>
    <thead><tr><th>Metric</th><th>Actual</th><th>Target</th><th>Status</th></tr></thead>
    <tbody>
        <tr>
            <td>Recovery Time (RTO)</td>
            <td>{report.get('rto_seconds', '—')}s</td>
            <td>{report.get('rto_target', 300)}s</td>
            <td><span class="badge {'badge-pass' if report.get('rto_seconds', 999) <= report.get('rto_target', 300) else 'badge-fail'}">
                {'PASS' if report.get('rto_seconds', 999) <= report.get('rto_target', 300) else 'FAIL'}
            </span></td>
        </tr>
        <tr>
            <td>Recovery Point (RPO)</td>
            <td>{report.get('rpo_seconds', '—')}s</td>
            <td>{report.get('rpo_target', 60)}s</td>
            <td><span class="badge {'badge-pass' if report.get('rpo_seconds', 999) <= report.get('rpo_target', 60) else 'badge-fail'}">
                {'PASS' if report.get('rpo_seconds', 999) <= report.get('rpo_target', 60) else 'FAIL'}
            </span></td>
        </tr>
        <tr>
            <td>Overall Score</td>
            <td>{score}/100</td>
            <td>70+</td>
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
        <tr>
            <td>HTTPS Valid</td>
            <td><span class="badge {'badge-pass' if health.get('https_valid') else 'badge-fail'}">
                {'PASS' if health.get('https_valid') else 'FAIL'}
            </span></td>
            <td>SSL certificate is {'valid' if health.get('https_valid') else 'invalid or expired'}</td>
        </tr>
        <tr>
            <td>DNS Failover</td>
            <td><span class="badge {'badge-pass' if health.get('dns_failover_ok') else 'badge-fail'}">
                {'PASS' if health.get('dns_failover_ok') else 'FAIL'}
            </span></td>
            <td>DNS failover routing is {'operational' if health.get('dns_failover_ok') else 'not working'}</td>
        </tr>
        <tr>
            <td>Response Time</td>
            <td><span class="badge {'badge-pass' if (health.get('response_time_ms') or 9999) < 3000 else 'badge-warn'}">
                {health.get('response_time_ms', 'N/A')}ms
            </span></td>
            <td>Page loaded in {health.get('response_time_ms', 'N/A')}ms</td>
        </tr>
        <tr>
            <td>HTTP Status</td>
            <td><span class="badge {'badge-pass' if health.get('http_status_code') == 200 else 'badge-fail'}">
                {health.get('http_status_code', 'N/A')}
            </span></td>
            <td>Server returned HTTP {health.get('http_status_code', 'N/A')}</td>
        </tr>
    </tbody>
</table>

<!-- Closing -->
<div class="closing">
    <p><strong>CloudGuard DR</strong> — Automated Resilience & SEO Platform</p>
    <p>Report generated on {report.get('generated_at', 'N/A')} by {agency_name}</p>
</div>

</body></html>"""
