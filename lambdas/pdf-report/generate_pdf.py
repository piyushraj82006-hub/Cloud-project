#!/usr/bin/env python3
"""
Standalone PDF Generator — no Lambda required.
Run directly:  python generate_pdf.py https://example.com

Generates a branded SEO/PDF report with AI-powered weak points analysis.
"""
import os
import sys
import json
import time
import uuid
import urllib.request
import urllib.error
import ssl

# ─── Config ─────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
OUTPUT_DIR = os.environ.get("PDF_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "output"))


def get_api_key():
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    try:
        import boto3
        ssm = boto3.client("ssm")
        param = ssm.get_parameter(
            Name="/cloudguard/dev/openrouter-api-key",
            WithDecryption=True,
        )
        return param["Parameter"]["Value"]
    except Exception:
        return ""


# ─── SEO Analysis (copied from seo-report/handler.py) ────────────────

from html.parser import HTMLParser
from urllib.parse import urlparse


class SimpleSEOAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_desc = ""
        self.has_viewport = False
        self.h1_count = 0
        self.h2_count = 0
        self.images = 0
        self.images_with_alt = 0
        self.links = 0
        self.canonical = None
        self.og_tags = {}
        self.structured_data = []
        self._in_title = False
        self._title_data = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._title_data = []
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta_desc = content
            elif name == "viewport":
                self.has_viewport = True
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
        elif tag == "link":
            if attrs_dict.get("rel", "").lower() == "canonical":
                self.canonical = attrs_dict.get("href", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "h2":
            self.h2_count += 1
        elif tag == "img":
            self.images += 1
            if attrs_dict.get("alt", "").strip():
                self.images_with_alt += 1
        elif tag == "a":
            self.links += 1
        elif tag == "script" and attrs_dict.get("type") == "application/ld+json":
            self._in_script = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_data).strip()
        if tag == "script":
            self._in_script = False

    def handle_data(self, data):
        if self._in_title:
            self._title_data.append(data)

    def analyze(self, url):
        checks = {}
        issues = []

        # Title
        if not self.title:
            issues = ["Missing page title"]
        elif len(self.title) < 30:
            issues = [f"Title too short ({len(self.title)} chars, aim for 30-60)"]
        elif len(self.title) > 60:
            issues = [f"Title too long ({len(self.title)} chars, will be truncated)"]
        else:
            issues = []
        checks["title"] = {"present": bool(self.title), "issues": issues, "value": self.title}

        # Meta description
        if not self.meta_desc:
            issues = ["Missing meta description"]
        elif len(self.meta_desc) < 120:
            issues = [f"Meta description too short ({len(self.meta_desc)} chars)"]
        elif len(self.meta_desc) > 160:
            issues = [f"Meta description too long ({len(self.meta_desc)} chars)"]
        else:
            issues = []
        checks["meta_description"] = {"present": bool(self.meta_desc), "issues": issues, "value": self.meta_desc}

        # Headings
        h_issues = []
        if self.h1_count == 0:
            h_issues.append("Missing H1 tag")
        elif self.h1_count > 1:
            h_issues.append(f"Multiple H1 tags ({self.h1_count})")
        checks["headings"] = {"issues": h_issues, "h1_count": self.h1_count, "has_h1": self.h1_count > 0}

        # Images
        img_issues = []
        if self.images > 0 and self.images_with_alt < self.images:
            img_issues.append(f"{self.images - self.images_with_alt}/{self.images} images missing alt text")
        checks["images"] = {"issues": img_issues, "total": self.images, "with_alt": self.images_with_alt}

        # Canonical
        checks["canonical"] = {"present": bool(self.canonical), "issues": [] if self.canonical else ["Missing canonical URL"]}

        # Open Graph
        og_missing = [t for t in ["og:title", "og:description", "og:image"] if t not in self.og_tags]
        checks["open_graph"] = {"issues": [f"Missing: {', '.join(og_missing)}"] if og_missing else [], "tags_missing": og_missing}

        # Viewport
        checks["viewport"] = {"present": self.has_viewport, "issues": [] if self.has_viewport else ["Missing viewport meta tag"]}

        # Calculate score
        total = len(checks)
        passing = sum(1 for c in checks.values() if not c.get("issues"))
        score = int((passing / total) * 100) if total > 0 else 0

        return {
            "report_id": f"seo-{uuid.uuid4().hex[:8]}",
            "target_url": url,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seo_score": score,
            "seo_checks": checks,
            "response_time_ms": 0,
            "page_fetched": True,
            "status_code": 200,
            "content_length": 0,
        }


def fetch_and_analyze(url):
    """Fetch a URL and run SEO analysis."""
    print(f"[SEO] Fetching {url}...")
    start = time.time()
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "CloudGuard-DR/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html_bytes = resp.read()
        elapsed = int((time.time() - start) * 1000)
        html_text = html_bytes.decode("utf-8", errors="replace")

        analyzer = SimpleSEOAnalyzer()
        analyzer.feed(html_text)
        report = analyzer.analyze(url)
        report["response_time_ms"] = elapsed
        report["content_length"] = len(html_bytes)
        report["status_code"] = resp.getcode()

        print(f"[SEO] Score: {report['seo_score']}/100 ({elapsed}ms)")
        return report

    except Exception as e:
        print(f"[SEO] Fetch failed: {e}")
        return {
            "report_id": f"seo-{uuid.uuid4().hex[:8]}",
            "target_url": url,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seo_score": 0,
            "seo_checks": {},
            "response_time_ms": 0,
            "page_fetched": False,
            "status_code": 0,
            "content_length": 0,
        }


# ─── OpenRouter AI ──────────────────────────────────────────────────

AI_PROMPT = """Analyze this SEO audit. For each failing check provide severity, title, why it matters (1 sentence), root cause (1 sentence), and 2-3 fix steps. Also provide executive_summary (2 sentences) and quick_wins.

SEO data:
{report_data}

JSON only:
{{"executive_summary":"...","weak_points":[{{"check":"...","severity":"critical|high|medium","title":"...","why_it_matters":"...","root_cause":"...","fix_steps":["..."]}}],"quick_wins":["..."]}}"""


def call_openrouter(prompt, api_key):
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
    resp = urllib.request.urlopen(req, timeout=60)
    body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def get_ai_insights(report):
    api_key = get_api_key()
    if not api_key:
        print("[AI] No API key — skipping AI insights")
        return report

    print("[AI] Calling OpenRouter for weak points analysis...")
    prompt = AI_PROMPT.format(report_data=json.dumps(report, indent=2, default=str))
    try:
        text = call_openrouter(prompt, api_key)
        # Parse JSON (handle markdown fences)
        try:
            insights = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            insights = json.loads(match.group(1)) if match else {"raw": text}

        report["ai_insights"] = insights
        wp = insights.get("weak_points", [])
        print(f"[AI] Found {len(wp)} weak points")
    except Exception as e:
        print(f"[AI] OpenRouter call failed: {e}")

    return report


# ─── PDF Generation (import from handler) ───────────────────────────

def convert_html_to_pdf(html_content):
    """Convert HTML to PDF using PDFBolt API."""
    import base64
    api_key = OPENROUTER_API_KEY  # reuse if same, otherwise check env
    pdfbolt_key = os.environ.get("PDFBOLT_API_KEY", "")
    if not pdfbolt_key:
        return None

    b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    payload = json.dumps({"html": b64, "format": "A4", "printBackground": True}).encode()
    req = urllib.request.Request(
        "https://api.pdfbolt.com/v1/direct",
        data=payload,
        headers={"Content-Type": "application/json", "API-KEY": pdfbolt_key},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read()
    except Exception as e:
        print(f"[PDF] PDFBolt error: {e}")
        return None


def generate_pdf(report):
    """Generate PDF using the handler's HTML templates."""
    # Import the template function from the handler (lazy to avoid boto3 init)
    import importlib
    import sys

    # Temporarily mock boto3 to prevent connection errors during import
    if 'boto3' not in sys.modules:
        import types
        mock_boto3 = types.ModuleType('boto3')
        mock_boto3.resource = lambda *a, **kw: None
        mock_boto3.client = lambda *a, **kw: None
        sys.modules['boto3'] = mock_boto3
        sys.modules['botocore'] = types.ModuleType('botocore')
        sys.modules['botocore.exceptions'] = types.ModuleType('botocore.exceptions')

    handler = importlib.import_module('handler')
    html_content = handler.generate_seo_pdf_html(report, "CloudGuard DR")

    # Try PDFBolt API
    pdf_bytes = convert_html_to_pdf(html_content)
    if pdf_bytes:
        return pdf_bytes, "pdf"

    # Fallback: save HTML
    print("[PDF] PDFBolt unavailable — saving HTML instead")
    return html_content.encode("utf-8"), "html"


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf.py <url> [output_dir]")
        print("Example: python generate_pdf.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Fetch and analyze
    report = fetch_and_analyze(url)

    # Step 2: AI insights
    report = get_ai_insights(report)

    # Step 3: Generate PDF
    print("[PDF] Generating PDF...")
    data, fmt = generate_pdf(report)

    # Step 4: Save
    report_id = report["report_id"]
    filename = f"{report_id}.{fmt}"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(data)

    # Also save the JSON report
    json_path = os.path.join(output_dir, f"{report_id}.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    size_kb = len(data) / 1024
    print(f"\n{'='*60}")
    print(f"  Report generated successfully!")
    print(f"  Score:  {report['seo_score']}/100")
    print(f"  Output: {filepath} ({size_kb:.1f} KB)")
    print(f"  JSON:   {json_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
