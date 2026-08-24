"""
CloudGuard DR — SEO Report Lambda
Performs SEO analysis on a target URL: meta tags, headings, images,
links, performance, accessibility, social tags, and structured data.
Writes JSON report to S3 and stores a pointer in DynamoDB.
"""
import os
import json
import time
import uuid
import re
import ssl
import urllib.request
import boto3
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")


class SEOHTMLParser(HTMLParser):
    """Custom HTML parser to extract SEO-relevant elements."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_tags = {}
        self.headings = {f"h{i}": [] for i in range(1, 7)}
        self.images = []
        self.links = []
        self.current_tag = None
        self.current_attrs = {}
        self._in_title = False
        self._title_data = []
        self.canonical = None
        self.og_tags = {}
        self.twitter_tags = {}
        self.has_viewport = False
        self.has_charset = False
        self.has_robots = False
        self.structured_data = []
        self._in_script = False
        self._script_type = None
        self._script_data = []
        self.charset = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

        if tag == "title":
            self._in_title = True
            self._title_data = []

        elif tag == "meta":
            name = (self.current_attrs.get("name") or "").lower()
            prop = (self.current_attrs.get("property") or "").lower()
            content = self.current_attrs.get("content", "")
            charset = self.current_attrs.get("charset", "")

            if charset:
                self.has_charset = True
                self.charset = charset
            if name == "description":
                self.meta_tags["description"] = content
            elif name == "keywords":
                self.meta_tags["keywords"] = content
            elif name == "robots":
                self.meta_tags["robots"] = content
                self.has_robots = True
            elif name == "viewport":
                self.has_viewport = True
                self.meta_tags["viewport"] = content
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
            elif name.startswith("twitter:"):
                self.twitter_tags[name] = content

        elif tag == "link":
            rel = self.current_attrs.get("rel", "").lower()
            href = self.current_attrs.get("href", "")
            if rel == "canonical":
                self.canonical = href

        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings[tag].append("")

        elif tag == "img":
            src = self.current_attrs.get("src", "")
            alt = self.current_attrs.get("alt", "")
            self.images.append({"src": src, "alt": alt, "has_alt": bool(alt)})

        elif tag == "a":
            href = self.current_attrs.get("href", "")
            rel_attr = self.current_attrs.get("rel", "")
            self.links.append({
                "href": href,
                "is_external": href.startswith("http"),
                "has_nofollow": "nofollow" in rel_attr,
            })

        elif tag == "script":
            script_type = self.current_attrs.get("type", "")
            if script_type == "application/ld+json":
                self._in_script = True
                self._script_type = "ld+json"
                self._script_data = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_data).strip()

        if tag in self.headings and self.headings[tag]:
            self.headings[tag][-1] = self.headings[tag][-1].strip()

        if tag == "script" and self._in_script:
            self._in_script = False
            try:
                data = json.loads("".join(self._script_data))
                self.structured_data.append(data)
            except (json.JSONDecodeError, Exception):
                pass

    def handle_data(self, data):
        if self._in_title:
            self._title_data.append(data)

        if self._in_script:
            self._script_data.append(data)

        if self.current_tag in self.headings and self.headings[self.current_tag]:
            self.headings[self.current_tag][-1] += data


def lambda_handler(event, context):
    """
    Generate SEO report for a target URL.

    Event input:
        {
            "target_url": "https://example.com"
        }

    Output:
        {
            "report_id": "seo-uuid",
            "target_url": "https://example.com",
            "seo_score": 75,
            "seo_checks": { ... }
        }
    """
    print(f"[SEOR] Starting SEO analysis. Event: {json.dumps(event)}")

    try:
        target_url = event.get("target_url", "").strip()

        if not target_url:
            raise ValueError("target_url is required")

        parsed = urlparse(target_url)
        if parsed.scheme not in ("https", "http"):
            raise ValueError("target_url must be an HTTP or HTTPS URL")

        if parsed.scheme == "http":
            target_url = target_url.replace("http://", "https://", 1)
            print(f"[SEOR] Upgraded to HTTPS: {target_url}")

        report_id = f"seo-{uuid.uuid4().hex[:8]}"

        # Fetch and parse the page
        page_data = fetch_page(target_url)

        # Run SEO analysis
        seo_checks = analyze_seo(target_url, page_data)

        # Calculate overall SEO score
        seo_score = calculate_seo_score(seo_checks)

        # Build report
        report = {
            "report_id": report_id,
            "target_url": target_url,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "page_fetched": page_data["status_code"] == 200,
            "status_code": page_data["status_code"],
            "response_time_ms": page_data["response_time_ms"],
            "content_length": page_data["content_length"],
            "seo_score": seo_score,
            "seo_checks": seo_checks,
        }

        # Write JSON report to S3
        s3_key = f"seo-reports/{report_id}/report.json"
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=s3_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json",
        )

        # Write HTML report to S3
        html_key = f"seo-reports/{report_id}/report.html"
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
            "run_id": "",
            "target_url": target_url,
            "https_valid": page_data.get("https_valid", False),
            "dns_failover_ok": True,
            "response_time_ms": page_data.get("response_time_ms"),
            "http_status_code": page_data.get("status_code", 0),
            "ssl_expiry_days": None,
            "generated_at": report["generated_at"],
            "fault_type": "seo-audit",
            "rto_seconds": None,
            "rpo_seconds": None,
            "resilience_score": seo_score,
            "s3_report_key": s3_key,
        })

        result = {
            "statusCode": 200,
            "report_id": report_id,
            "target_url": target_url,
            "seo_score": seo_score,
            "seo_checks": seo_checks,
            "generated_at": report["generated_at"],
            "s3_key": s3_key,
            "html_key": html_key,
        }

        print(f"[SEOR] SEO report generated: {report_id} (score: {seo_score})")
        return result

    except ValueError as e:
        print(f"[SEOR] Validation error: {str(e)}")
        return {"statusCode": 400, "error": str(e)}
    except Exception as e:
        print(f"[SEOR] Error: {str(e)}")
        raise


def fetch_page(url):
    """Fetch a page and return status, content, and timing."""
    result = {
        "status_code": 0,
        "content": "",
        "response_time_ms": 0,
        "content_length": 0,
        "https_valid": False,
        "headers": {},
    }

    try:
        ctx = ssl.create_default_context()
        start_time = time.time()

        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CloudGuardDR-SEO/1.0")

        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        result["status_code"] = response.status
        result["https_valid"] = True
        result["headers"] = dict(response.headers)

        content = response.read().decode("utf-8", errors="replace")
        result["content"] = content
        result["content_length"] = len(content)

    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        print(f"[SEOR] HTTP error: {e.code}")
    except urllib.error.URLError as e:
        print(f"[SEOR] URL error: {e.reason}")
    except Exception as e:
        print(f"[SEOR] Fetch error: {str(e)}")

    return result


def analyze_seo(url, page_data):
    """Run all SEO checks and return structured results."""
    content = page_data["content"]
    parser = SEOHTMLParser()

    try:
        parser.feed(content)
    except Exception as e:
        print(f"[SEOR] Parse error: {str(e)}")

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Title checks
    title_len = len(parser.title)
    title_check = {
        "present": bool(parser.title),
        "length": title_len,
        "optimal": 30 <= title_len <= 60,
        "value": parser.title,
        "issues": [],
    }
    if not parser.title:
        title_check["issues"].append("Missing page title")
    elif title_len < 30:
        title_check["issues"].append(f"Title too short ({title_len} chars, recommended 30-60)")
    elif title_len > 60:
        title_check["issues"].append(f"Title too long ({title_len} chars, recommended 30-60)")

    # Meta description checks
    desc = parser.meta_tags.get("description", "")
    desc_len = len(desc)
    desc_check = {
        "present": bool(desc),
        "length": desc_len,
        "optimal": 120 <= desc_len <= 160,
        "value": desc,
        "issues": [],
    }
    if not desc:
        desc_check["issues"].append("Missing meta description")
    elif desc_len < 120:
        desc_check["issues"].append(f"Description too short ({desc_len} chars, recommended 120-160)")
    elif desc_len > 160:
        desc_check["issues"].append(f"Description too long ({desc_len} chars, recommended 120-160)")

    # Heading structure checks
    heading_check = {
        "h1_count": len(parser.headings["h1"]),
        "has_h1": len(parser.headings["h1"]) > 0,
        "has_h2": len(parser.headings["h2"]) > 0,
        "hierarchy_valid": True,
        "headings": {k: v for k, v in parser.headings.items() if v},
        "issues": [],
    }
    if not parser.headings["h1"]:
        heading_check["issues"].append("Missing H1 tag")
    elif len(parser.headings["h1"]) > 1:
        heading_check["issues"].append(f"Multiple H1 tags ({len(parser.headings['h1'])})")
    if not parser.headings["h2"]:
        heading_check["issues"].append("Missing H2 tags")

    # Check heading hierarchy
    non_empty = [k for k in ["h1", "h2", "h3", "h4", "h5", "h6"] if parser.headings[k]]
    for i in range(len(non_empty) - 1):
        current_level = int(non_empty[i][1])
        next_level = int(non_empty[i + 1][1])
        if next_level > current_level + 1:
            heading_check["hierarchy_valid"] = False
            heading_check["issues"].append(
                f"Heading hierarchy skip: {non_empty[i].upper()} → {non_empty[i+1].upper()}"
            )

    # Image checks
    images_without_alt = [img for img in parser.images if not img["has_alt"]]
    image_check = {
        "total": len(parser.images),
        "with_alt": len(parser.images) - len(images_without_alt),
        "without_alt": len(images_without_alt),
        "all_have_alt": len(images_without_alt) == 0,
        "issues": [],
    }
    if parser.images and images_without_alt:
        image_check["issues"].append(
            f"{len(images_without_alt)} image(s) missing alt text"
        )

    # Link checks
    external_links = [l for l in parser.links if l["is_external"]]
    internal_links = [l for l in parser.links if not l["is_external"]]
    nofollow_links = [l for l in parser.links if l["has_nofollow"]]
    link_check = {
        "total": len(parser.links),
        "internal": len(internal_links),
        "external": len(external_links),
        "nofollow": len(nofollow_links),
        "issues": [],
    }

    # Check for broken-looking links
    empty_hrefs = [l for l in parser.links if not l["href"] or l["href"] == "#"]
    if empty_hrefs:
        link_check["issues"].append(f"{len(empty_hrefs)} link(s) with empty or anchor-only href")

    # Canonical check
    canonical_check = {
        "present": parser.canonical is not None,
        "value": parser.canonical,
        "issues": [],
    }
    if not parser.canonical:
        canonical_check["issues"].append("Missing canonical tag")

    # Open Graph checks
    og_required = ["og:title", "og:description", "og:image", "og:url"]
    og_present = [tag for tag in og_required if tag in parser.og_tags]
    og_check = {
        "present": bool(parser.og_tags),
        "tags_found": list(parser.og_tags.keys()),
        "tags_missing": [tag for tag in og_required if tag not in parser.og_tags],
        "issues": [],
    }
    missing_og = [tag for tag in og_required if tag not in parser.og_tags]
    if missing_og:
        og_check["issues"].append(f"Missing Open Graph tags: {', '.join(missing_og)}")

    # Twitter Card checks
    twitter_required = ["twitter:card", "twitter:title", "twitter:description"]
    twitter_present = [tag for tag in twitter_required if tag in parser.twitter_tags]
    twitter_check = {
        "present": bool(parser.twitter_tags),
        "tags_found": list(parser.twitter_tags.keys()),
        "tags_missing": [tag for tag in twitter_required if tag not in parser.twitter_tags],
        "issues": [],
    }
    missing_twitter = [tag for tag in twitter_required if tag not in parser.twitter_tags]
    if missing_twitter:
        twitter_check["issues"].append(f"Missing Twitter tags: {', '.join(missing_twitter)}")

    # Viewport check
    viewport_check = {
        "present": parser.has_viewport,
        "value": parser.meta_tags.get("viewport"),
        "issues": [],
    }
    if not parser.has_viewport:
        viewport_check["issues"].append("Missing viewport meta tag (important for mobile)")

    # Robots check
    robots_check = {
        "present": parser.has_robots,
        "value": parser.meta_tags.get("robots"),
        "issues": [],
    }
    if parser.meta_tags.get("robots", "").lower() == "noindex":
        robots_check["issues"].append("Page is set to noindex — will not appear in search results")

    # Structured data check
    structured_check = {
        "present": bool(parser.structured_data),
        "types": [sd.get("@type", "unknown") for sd in parser.structured_data if isinstance(sd, dict)],
        "count": len(parser.structured_data),
        "issues": [],
    }
    if not parser.structured_data:
        structured_check["issues"].append("No structured data (JSON-LD) found")

    # Performance checks
    perf_check = {
        "response_time_ms": page_data["response_time_ms"],
        "fast": page_data["response_time_ms"] < 1000,
        "content_size_kb": round(page_data["content_length"] / 1024, 1),
        "issues": [],
    }
    if page_data["response_time_ms"] > 3000:
        perf_check["issues"].append(f"Slow response time ({page_data['response_time_ms']}ms)")
    elif page_data["response_time_ms"] > 1000:
        perf_check["issues"].append(f"Moderate response time ({page_data['response_time_ms']}ms)")

    if page_data["content_length"] > 500_000:
        perf_check["issues"].append("Large page size (>500KB)")

    # HTTPS check
    https_check = {
        "is_https": parsed_url.scheme == "https",
        "ssl_valid": page_data["https_valid"],
        "issues": [],
    }
    if not https_check["is_https"]:
        https_check["issues"].append("Page is not served over HTTPS")

    return {
        "title": title_check,
        "meta_description": desc_check,
        "headings": heading_check,
        "images": image_check,
        "links": link_check,
        "canonical": canonical_check,
        "open_graph": og_check,
        "twitter_card": twitter_check,
        "viewport": viewport_check,
        "robots": robots_check,
        "structured_data": structured_check,
        "performance": perf_check,
        "https": https_check,
    }


def calculate_seo_score(checks):
    """Calculate an overall SEO score (0-100) from the checks."""
    weights = {
        "title": 15,
        "meta_description": 15,
        "headings": 12,
        "images": 8,
        "links": 8,
        "canonical": 8,
        "open_graph": 10,
        "twitter_card": 5,
        "viewport": 7,
        "robots": 3,
        "structured_data": 5,
        "performance": 4,
    }

    total_score = 0
    total_weight = 0

    for check_name, weight in weights.items():
        check = checks.get(check_name, {})
        issues = check.get("issues", [])

        if not issues:
            total_score += weight
        else:
            # Deduct points based on number of issues (max deduction = weight)
            deduction = min(len(issues) * (weight / 2), weight)
            total_score += weight - deduction

        total_weight += weight

    return round((total_score / total_weight) * 100) if total_weight > 0 else 0


def generate_html_report(report):
    """Generate an HTML version of the SEO report."""
    score = report["seo_score"]
    if score >= 80:
        score_color = "#22C55E"
        grade = "A"
    elif score >= 60:
        score_color = "#F59E0B"
        grade = "B"
    elif score >= 40:
        score_color = "#F97316"
        grade = "C"
    else:
        score_color = "#EF4444"
        grade = "D"

    checks = report["seo_checks"]

    def render_issues(issues):
        if not issues:
            return '<span style="color: #22C55E;">✓ No issues</span>'
        return "".join(
            f'<div style="color: #EF4444; font-size: 13px; padding: 2px 0;">• {issue}</div>'
            for issue in issues
        )

    def render_check_section(title, check_data):
        return f"""
        <div class="score-card">
            <h3 style="margin-bottom: 12px; font-size: 14px; color: #F5F5F5;">{title}</h3>
            {render_issues(check_data.get('issues', []))}
        </div>"""

    sections = ""
    section_map = [
        ("Page Title", checks.get("title", {})),
        ("Meta Description", checks.get("meta_description", {})),
        ("Heading Structure", checks.get("headings", {})),
        ("Images", checks.get("images", {})),
        ("Links", checks.get("links", {})),
        ("Canonical URL", checks.get("canonical", {})),
        ("Open Graph Tags", checks.get("open_graph", {})),
        ("Twitter Card", checks.get("twitter_card", {})),
        ("Viewport (Mobile)", checks.get("viewport", {})),
        ("Robots / Indexing", checks.get("robots", {})),
        ("Structured Data", checks.get("structured_data", {})),
        ("Performance", checks.get("performance", {})),
        ("HTTPS / Security", checks.get("https", {})),
    ]

    for title, check_data in section_map:
        sections += render_check_section(title, check_data)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Report — {report['target_url']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        .header {{ margin-bottom: 40px; }}
        .title {{ font-size: 24px; font-weight: 600; margin-bottom: 8px; }}
        .subtitle {{ color: #A1A1A1; font-size: 14px; }}
        .score-card {{ background: #151515; border: 1px solid #292929; border-radius: 8px; padding: 24px; margin-bottom: 16px; }}
        .score {{ font-size: 64px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
        .grade {{ font-size: 32px; font-weight: 700; font-family: 'JetBrains Mono', monospace; margin-left: 16px; }}
        .url {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #A1A1A1; word-break: break-all; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">SEO Audit Report</div>
            <div class="subtitle">Generated: {report['generated_at']}</div>
        </div>

        <div class="score-card" style="text-align: center; padding: 40px;">
            <div class="url" style="margin-bottom: 24px;">{report['target_url']}</div>
            <div>
                <span class="score" style="color: {score_color}">{score}</span>
                <span class="grade" style="color: {score_color}">{grade}</span>
            </div>
            <div style="color: #A1A1A1; font-size: 14px; margin-top: 8px;">Overall SEO Score</div>
        </div>

        <div class="score-card">
            <h3 style="margin-bottom: 16px; font-size: 14px;">Page Info</h3>
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #292929;">
                <span style="color: #A1A1A1; font-size: 13px;">Status Code</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 13px;">{report['status_code']}</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #292929;">
                <span style="color: #A1A1A1; font-size: 13px;">Response Time</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 13px;">{report['response_time_ms']}ms</span>
            </div>
            <div style="display: flex; justify-content: space-between; padding: 8px 0;">
                <span style="color: #A1A1A1; font-size: 13px;">Content Size</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 13px;">{report['content_length']} bytes</span>
            </div>
        </div>

        {sections}

        <div style="text-align: center; color: #666666; font-size: 12px; margin-top: 40px;">
            CloudGuard DR — Automated SEO Audit Report
        </div>
    </div>
</body>
</html>"""
    return html
