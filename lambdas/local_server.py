#!/usr/bin/env python3
"""
Local API Server — mimics API Gateway + Lambda for local testing.
Run:  python local_server.py
Then: Set VITE_API_URL=http://localhost:3001/prod in frontend/.env
"""
import os
import sys
from unittest.mock import MagicMock
boto3_mock = MagicMock()
sys.modules['boto3'] = boto3_mock

import json
import time
import uuid
import urllib.request
import urllib.error
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

pdf_report_path = os.path.join(os.path.dirname(__file__), "pdf-report")
sys.path.append(pdf_report_path)

try:
    import handler
    HAS_PDF_HANDLER = True
except Exception as e:
    print(f"WARNING: failed to import pdf-report handler: {e}")
    HAS_PDF_HANDLER = False


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs

PORT = 3001
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


# ═══════════════════════════════════════════════════════════════════
# SEO ANALYSIS (simplified from seo-report/handler.py)
# ═══════════════════════════════════════════════════════════════════

class SimpleSEOAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_desc = ""
        self.has_viewport = False
        self.h1_count = 0
        self.images = 0
        self.images_with_alt = 0
        self.links = 0
        self.canonical = None
        self.og_tags = {}
        self._in_title = False
        self._title_data = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._title_data = []
        elif tag == "meta":
            name = d.get("name", "").lower()
            prop = d.get("property", "").lower()
            content = d.get("content", "")
            if name == "description":
                self.meta_desc = content
            elif name == "viewport":
                self.has_viewport = True
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
        elif tag == "link" and d.get("rel", "").lower() == "canonical":
            self.canonical = d.get("href", "")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "img":
            self.images += 1
            if d.get("alt", "").strip():
                self.images_with_alt += 1
        elif tag == "a":
            self.links += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_data).strip()

    def handle_data(self, data):
        if self._in_title:
            self._title_data.append(data)

    def analyze(self, url):
        checks = {}

        if not self.title:
            ti = ["Missing page title"]
        elif len(self.title) < 30:
            ti = [f"Title too short ({len(self.title)} chars)"]
        elif len(self.title) > 60:
            ti = [f"Title too long ({len(self.title)} chars)"]
        else:
            ti = []
        checks["title"] = {"present": bool(self.title), "issues": ti, "value": self.title}

        if not self.meta_desc:
            mi = ["Missing meta description"]
        elif len(self.meta_desc) < 120:
            mi = [f"Meta desc too short ({len(self.meta_desc)} chars)"]
        else:
            mi = []
        checks["meta_description"] = {"present": bool(self.meta_desc), "issues": mi, "value": self.meta_desc}

        hi = []
        if self.h1_count == 0:
            hi.append("Missing H1 tag")
        elif self.h1_count > 1:
            hi.append(f"Multiple H1 tags ({self.h1_count})")
        checks["headings"] = {"issues": hi, "h1_count": self.h1_count, "has_h1": self.h1_count > 0}

        ii = []
        if self.images > 0 and self.images_with_alt < self.images:
            ii.append(f"{self.images - self.images_with_alt}/{self.images} images missing alt text")
        checks["images"] = {"issues": ii, "total": self.images, "with_alt": self.images_with_alt}

        checks["canonical"] = {"present": bool(self.canonical), "issues": [] if self.canonical else ["Missing canonical URL"]}

        og_missing = [t for t in ["og:title", "og:description", "og:image"] if t not in self.og_tags]
        checks["open_graph"] = {"issues": [f"Missing: {', '.join(og_missing)}"] if og_missing else [], "tags_missing": og_missing}

        checks["viewport"] = {"present": self.has_viewport, "issues": [] if self.has_viewport else ["Missing viewport"]}

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
        return {"report_id": f"seo-{uuid.uuid4().hex[:8]}", "target_url": url, "seo_score": 0, "seo_checks": {}, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "page_fetched": False, "status_code": 0, "response_time_ms": 0, "content_length": 0}


# ═══════════════════════════════════════════════════════════════════
# OPENROUTER AI
# ═══════════════════════════════════════════════════════════════════

AI_PROMPT = """Analyze this SEO audit. For each failing check provide severity, title, why it matters (1 sentence), root cause (1 sentence), and 2-3 fix steps. Also provide executive_summary (2 sentences) and quick_wins.

SEO data:
{report_data}

JSON only:
{{"executive_summary":"...","weak_points":[{{"check":"...","severity":"critical|high|medium","title":"...","why_it_matters":"...","root_cause":"...","fix_steps":["..."]}}],"quick_wins":["..."]}}"""


def get_ai_insights(report):
    api_key = OPENROUTER_API_KEY
    if not api_key:
        print("[AI] No API key — skipping")
        return report
    print("[AI] Calling OpenRouter...")
    prompt = AI_PROMPT.format(report_data=json.dumps(report, indent=2, default=str))
    payload = json.dumps({"model": OPENROUTER_MODEL, "messages": [{"role": "system", "content": "Respond with valid JSON only."}, {"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 1024}).encode()
    req = urllib.request.Request(OPENROUTER_BASE_URL, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://cloudguard-dr.com"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        text = json.loads(resp.read())["choices"][0]["message"]["content"]
        try:
            insights = json.loads(text)
        except json.JSONDecodeError:
            import re
            m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            insights = json.loads(m.group(1)) if m else {"raw": text}
        report["ai_insights"] = insights
        print(f"[AI] {len(insights.get('weak_points', []))} weak points found")
    except Exception as e:
        print(f"[AI] Failed: {e}")
    return report


# ═══════════════════════════════════════════════════════════════════
# MOCK DATA STORE
# ═══════════════════════════════════════════════════════════════════

RUNS = {}
REPORTS = {}
CLIENTS = {}
COMPARISONS = {}

# Seed some mock runs
for i in range(5):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    score = 50 + (i * 8)
    RUNS[run_id] = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fault_type": "ec2-termination",
        "target_resource": f"i-0abc{i}def{i+1}23",
        "rto_seconds": 120 + i * 30,
        "rpo_seconds": 30 + i * 10,
        "resilience_score": score,
        "status": "Passed" if score >= 70 else "Failed",
        "rto_target": 300,
        "rpo_target": 60,
        "report_s3_key": f"reports/{run_id}/report.json",
    }


# ═══════════════════════════════════════════════════════════════════
# HTTP HANDLER
# ═══════════════════════════════════════════════════════════════════

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html_content, status=200):
        body = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_html_report(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        report_id = params.get("id", [None])[0]
        report_type = params.get("type", ["seo"])[0]

        if not report_id:
            return self.send_html("<h1>Error: Report ID is required</h1>", 400)

        # Look in REPORTS or RUNS
        report = REPORTS.get(report_id)
        if not report and report_id in RUNS:
            run = RUNS[report_id]
            report = {
                "report_id": report_id,
                "target_url": run.get("target_resource", "i-0abc123"),
                "generated_at": run.get("timestamp"),
                "resilience_score": run.get("resilience_score"),
                "status": run.get("status"),
                "rto_seconds": run.get("rto_seconds"),
                "rto_target": run.get("rto_target"),
                "rpo_seconds": run.get("rpo_seconds"),
                "rpo_target": run.get("rpo_target"),
                "fault_type": run.get("fault_type"),
                "report_type": "dr-test"
            }

        if not report:
            # Generate mock SEO report if not found to prevent empty screens
            report = {
                "report_id": report_id,
                "target_url": "https://example.com",
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "seo_score": 85,
                "seo_checks": {
                    "title": {"present": True, "issues": []},
                    "meta_description": {"present": True, "issues": []},
                    "headings": {"issues": [], "h1_count": 1, "has_h1": True},
                    "images": {"issues": [], "total": 0, "with_alt": 0},
                    "canonical": {"present": True, "issues": []},
                    "open_graph": {"issues": [], "tags_missing": []},
                    "viewport": {"present": True, "issues": []}
                }
            }

        html_content = self.render_html_template(report, report_type)
        return self.send_html(html_content)

    def render_html_template(self, report, report_type):
        if HAS_PDF_HANDLER:
            try:
                agency_name = "CloudGuard DR"
                if report_type == "seo":
                    # Fix keys if missing
                    if "seo_checks" not in report:
                        report["seo_checks"] = {
                            "title": {"present": True, "issues": []},
                            "meta_description": {"present": True, "issues": []},
                            "headings": {"issues": [], "h1_count": 1, "has_h1": True},
                            "images": {"issues": [], "total": 0, "with_alt": 0},
                            "canonical": {"present": True, "issues": []},
                            "open_graph": {"issues": [], "tags_missing": []},
                            "viewport": {"present": True, "issues": []}
                        }
                    return handler.generate_seo_pdf_html(report, agency_name)
                elif report_type == "competitor":
                    return handler.generate_competitor_pdf_html(report, agency_name)
                elif report_type == "dr-test" or report_type == "dr_test":
                    return handler.generate_dr_test_pdf_html(report, agency_name)
                elif report_type == "comparison":
                    return handler.generate_comparison_pdf_html(report, agency_name)
            except Exception as e:
                print(f"[API] Error generating HTML from pdf-report handler: {e}")

        # Fallback custom template if import failed or threw an error
        title = report.get("target_url", "CloudGuard Report")
        score = report.get("seo_score", report.get("resilience_score", 0))
        generated_at = report.get("generated_at", "N/A")
        
        score_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#f43f5e"
        
        ai_summary = ""
        ai_insights = report.get("ai_insights", {})
        if ai_insights and isinstance(ai_insights, dict):
            summary_text = ai_insights.get("executive_summary", "")
            if summary_text:
                ai_summary = f"""
                <div class="ai-summary-card">
                    <h3>💡 AI Insights</h3>
                    <p>{summary_text}</p>
                </div>
                """

        details_html = ""
        if "seo_checks" in report:
            details_html += "<h2>SEO Checks Detail</h2>"
            for check_name, check_data in report["seo_checks"].items():
                if not isinstance(check_data, dict):
                    continue
                issues = check_data.get("issues", [])
                status_icon = "❌" if issues else "✅"
                issues_html = ""
                if issues:
                    issues_html = "<ul class='issues-list'>" + "".join(f"<li>⚠️ {issue}</li>" for issue in issues) + "</ul>"
                
                details_html += f"""
                <div class="check-card {'has-issues' if issues else 'no-issues'}">
                    <div class="check-header">
                        <span class="status-icon">{status_icon}</span>
                        <strong class="check-title">{check_name.replace('_', ' ').upper()}</strong>
                    </div>
                    {issues_html}
                </div>
                """
        elif "rto_seconds" in report:
            details_html += "<h2>Resilience Metrics</h2>"
            rto = report.get("rto_seconds")
            rto_target = report.get("rto_target")
            rpo = report.get("rpo_seconds")
            rpo_target = report.get("rpo_target")
            
            details_html += f"""
            <div class="metrics-grid">
                <div class="metric-card {'pass' if rto <= rto_target else 'fail'}">
                    <div class="metric-label">RTO (Recovery Time Objective)</div>
                    <div class="metric-value">{rto}s <span class="target">target: {rto_target}s</span></div>
                    <div class="metric-status">{"✅ PASSED" if rto <= rto_target else "❌ FAILED"}</div>
                </div>
                <div class="metric-card {'pass' if rpo <= rpo_target else 'fail'}">
                    <div class="metric-label">RPO (Recovery Point Objective)</div>
                    <div class="metric-value">{rpo}s <span class="target">target: {rpo_target}s</span></div>
                    <div class="metric-status">{"✅ PASSED" if rpo <= rpo_target else "❌ FAILED"}</div>
                </div>
            </div>
            """
            
        return f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CloudGuard DR Report — {title}</title>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg-primary: #050508;
                    --bg-secondary: #0c0c10;
                    --bg-card: rgba(15, 15, 20, 0.7);
                    --border-primary: rgba(255, 255, 255, 0.06);
                    --text-primary: #e8e8ec;
                    --text-secondary: #8a8a95;
                    --text-muted: #505060;
                }}
                body {{
                    font-family: 'Outfit', sans-serif;
                    background-color: var(--bg-primary);
                    background-image: 
                        radial-gradient(ellipse 80% 50% at 20% 0%, rgba(16, 185, 129, 0.04) 0%, transparent 60%),
                        radial-gradient(ellipse 60% 40% at 80% 10%, rgba(99, 102, 241, 0.03) 0%, transparent 50%);
                    color: var(--text-primary);
                    margin: 0;
                    padding: 40px 20px;
                    display: flex;
                    justify-content: center;
                }}
                .container {{
                    max-width: 800px;
                    width: 100%;
                }}
                header {{
                    margin-bottom: 40px;
                }}
                h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    margin: 0 0 8px 0;
                    letter-spacing: -0.02em;
                }}
                .meta {{
                    font-size: 13px;
                    color: var(--text-muted);
                    font-family: 'JetBrains Mono', monospace;
                }}
                .score-section {{
                    display: flex;
                    align-items: center;
                    gap: 24px;
                    padding: 32px;
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    border-radius: 20px;
                    margin-bottom: 32px;
                    backdrop-filter: blur(24px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                }}
                .score-circle {{
                    width: 100px;
                    height: 100px;
                    border-radius: 50%;
                    border: 4px solid {score_color};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 36px;
                    font-weight: 800;
                    font-family: 'JetBrains Mono', monospace;
                    color: {score_color};
                    box-shadow: 0 0 20px rgba(16, 185, 129, 0.1);
                }}
                .score-label {{
                    font-size: 14px;
                    color: var(--text-secondary);
                    margin-bottom: 4px;
                }}
                .target-url {{
                    font-size: 18px;
                    font-weight: 600;
                }}
                .ai-summary-card {{
                    padding: 24px;
                    background: rgba(99, 102, 241, 0.05);
                    border: 1px solid rgba(99, 102, 241, 0.15);
                    border-radius: 16px;
                    margin-bottom: 32px;
                    line-height: 1.6;
                }}
                .ai-summary-card h3 {{
                    margin: 0 0 8px 0;
                    font-size: 14px;
                    color: #818cf8;
                }}
                .check-card {{
                    padding: 20px;
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    border-radius: 12px;
                    margin-bottom: 16px;
                    backdrop-filter: blur(12px);
                }}
                .check-card.has-issues {{
                    border-left: 3px solid #f43f5e;
                }}
                .check-card.no-issues {{
                    border-left: 3px solid #10b981;
                }}
                .check-header {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .status-icon {{
                    font-size: 16px;
                }}
                .check-title {{
                    font-size: 13px;
                    letter-spacing: 0.05em;
                }}
                .issues-list {{
                    margin: 12px 0 0 0;
                    padding-left: 28px;
                    font-size: 13px;
                    color: var(--text-secondary);
                }}
                .issues-list li {{
                    margin-bottom: 6px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 16px;
                }}
                .metric-card {{
                    padding: 20px;
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    border-radius: 12px;
                }}
                .metric-card.pass {{
                    border-top: 3px solid #10b981;
                }}
                .metric-card.fail {{
                    border-top: 3px solid #f43f5e;
                }}
                .metric-label {{
                    font-size: 11px;
                    color: var(--text-muted);
                    text-transform: uppercase;
                    margin-bottom: 8px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: 700;
                    font-family: 'JetBrains Mono', monospace;
                    margin-bottom: 4px;
                }}
                .metric-value .target {{
                    font-size: 12px;
                    color: var(--text-muted);
                    font-weight: 400;
                }}
                .metric-status {{
                    font-size: 12px;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Disaster Recovery & Audit Report</h1>
                    <div class="meta">Report ID: {report.get("report_id")} | Generated at: {generated_at}</div>
                </header>
                <div class="score-section">
                    <div class="score-circle">{score}</div>
                    <div>
                        <div class="score-label">OVERALL PERFORMANCE SCORE</div>
                        <div class="target-url">{title}</div>
                    </div>
                </div>
                {ai_summary}
                {details_html}
            </div>
        </body>
        </html>
        """

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        # Strip /prod prefix if present
        if path.startswith("/prod"):
            path = path[5:]

        if path == "/health":
            return self.send_json({"status": "healthy", "service": "CloudGuard DR (local)"})

        if path == "/report/html":
            return self.handle_html_report()

        if path == "/runs":
            items = sorted(RUNS.values(), key=lambda x: x.get("timestamp", ""), reverse=True)
            return self.send_json({"runs": items, "count": len(items)})

        if path.startswith("/runs/") and path.endswith("/report"):
            run_id = path.split("/")[2]
            run = RUNS.get(run_id)
            if not run:
                return self.send_json({"error": "Run not found"}, 404)
            report = REPORTS.get(run_id, {"resilience_score": run.get("resilience_score", 0), "status": run.get("status"), "health_checks": {"https_valid": True, "dns_failover_ok": True, "response_time_ms": 250, "http_status_code": 200}})
            return self.send_json(report)

        if path.startswith("/runs/"):
            run_id = path.split("/")[2]
            run = RUNS.get(run_id)
            if not run:
                return self.send_json({"error": "Run not found"}, 404)
            return self.send_json(run)

        if path == "/clients":
            items = list(CLIENTS.values())
            return self.send_json({"clients": items, "count": len(items)})

        if path.startswith("/clients/"):
            client_id = path.split("/")[2]
            client = CLIENTS.get(client_id)
            if not client:
                return self.send_json({"error": "Client not found"}, 404)
            return self.send_json(client)

        if path == "/comparisons":
            items = sorted(COMPARISONS.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            list_items = []
            for item in items:
                list_items.append({
                    "comparison_id": item["comparison_id"],
                    "created_at": item["created_at"],
                    "url_a": item["url_a"],
                    "url_b": item["url_b"],
                    "domain_a": item["domain_a"],
                    "domain_b": item["domain_b"],
                    "summary": item["summary"],
                    "parameters_compared": item["parameters_compared"]
                })
            return self.send_json({"comparisons": list_items})

        if path.startswith("/comparisons/"):
            comp_id = path.split("/")[2]
            item = COMPARISONS.get(comp_id)
            if not item:
                return self.send_json({"error": "Comparison not found"}, 404)
            return self.send_json(item)

        if path == "/recommendations":
            return self.send_json({
                "summary": {
                    "total_runs": len(RUNS),
                    "pass_rate": int(sum(1 for r in RUNS.values() if r.get("status") == "Passed") * 100 / max(len(RUNS), 1)),
                    "avg_score": int(sum(r.get("resilience_score", 0) for r in RUNS.values()) / max(len(RUNS), 1)),
                    "avg_rto": int(sum(r.get("rto_seconds", 0) for r in RUNS.values()) / max(len(RUNS), 1))
                },
                "recommendations": [
                    {
                        "id": "rec-1",
                        "severity": "critical",
                        "title": "Enable Multi-AZ RDS Failover",
                        "description": "The current RDS instances do not have Multi-AZ failover enabled, exposing the system to database service outages.",
                        "action": "Enable Multi-AZ replication in your RDS settings."
                    },
                    {
                        "id": "rec-2",
                        "severity": "high",
                        "title": "Reduce Route 53 TTL for DNS Failover",
                        "description": "Failover latency is high because the Route 53 TTL value is set to 300 seconds.",
                        "action": "Set Route 53 records TTL to 60 seconds."
                    },
                    {
                        "id": "rec-3",
                        "severity": "medium",
                        "title": "Configure S3 Bucket Versioning & Replication",
                        "description": "Production S3 bucket does not replicate to a backup region.",
                        "action": "Set up Cross-Region Replication for the production bucket."
                    },
                    {
                        "id": "rec-4",
                        "severity": "info",
                        "title": "Optimize Auto-Scaling Group Launch Templates",
                        "description": "Bootstrapping speed can be optimized by using pre-warmed AMIs.",
                        "action": "Update launch template to use a pre-built AMI."
                    }
                ]
            })

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        if path.startswith("/prod"):
            path = path[5:]

        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length > 0 else {}

        if path == "/audit/seo":
            return self.handle_seo_audit(body)

        if path == "/dr-test":
            return self.handle_dr_test(body)

        if path == "/audit/external":
            return self.handle_external_audit(body)

        if path == "/audit/competitors":
            return self.handle_competitor_analysis(body)

        if path == "/compare":
            return self.handle_compare(body)

        if path == "/report/pdf":
            report_id = body.get("report_id")
            report_type = body.get("report_type", "seo")
            pdf_url = f"http://localhost:3001/prod/report/html?id={report_id}&type={report_type}"
            return self.send_json({
                "statusCode": 200,
                "pdf_key": f"reports/{report_id}/report.html",
                "pdf_url": pdf_url,
                "report_type": report_type,
                "report_id": report_id,
                "format": "html_fallback"
            })

        if path == "/clients":
            return self.handle_create_client(body)

        if path == "/compare-sites":
            return self.handle_compare_sites(body)

        self.send_json({"error": "Not found"}, 404)

    def handle_seo_audit(self, body):
        url = body.get("target_url", "").strip()
        if not url:
            return self.send_json({"error": "target_url is required"}, 400)

        if not url.startswith("http"):
            url = "https://" + url

        # Step 1: Fetch + SEO analysis
        report = fetch_and_analyze(url)

        # Step 2: AI insights
        report = get_ai_insights(report)

        # Step 3: Store
        report_id = report["report_id"]
        report["pdf_url"] = f"http://localhost:3001/prod/report/html?id={report_id}"
        REPORTS[report_id] = report

        print(f"[API] SEO audit complete: {report_id} (score: {report['seo_score']})")
        self.send_json(report)

    def handle_dr_test(self, body):
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        fault_type = body.get("fault_type", "ec2-termination")
        target = body.get("target_url", "i-0abc123")
        
        RUNS[run_id] = {
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fault_type": fault_type,
            "target_resource": target,
            "rto_seconds": 145,
            "rpo_seconds": 32,
            "resilience_score": 88,
            "status": "Passed",
            "rto_target": 300,
            "rpo_target": 60,
            "report_s3_key": f"reports/{run_id}/report.json",
        }
        
        print(f"[API] DR test run initiated: {run_id}")
        return self.send_json({"status": "initiated", "run_id": run_id})

    def handle_external_audit(self, body):
        url = body.get("target_url", "").strip()
        if not url:
            return self.send_json({"error": "target_url is required"}, 400)
            
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        RUNS[run_id] = {
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fault_type": "external-audit",
            "target_resource": url,
            "rto_seconds": 12,
            "rpo_seconds": 0,
            "resilience_score": 95,
            "status": "Passed",
            "rto_target": 30,
            "rpo_target": 5,
            "report_s3_key": f"reports/{run_id}/report.json",
        }
        
        print(f"[API] External audit complete: {run_id}")
        return self.send_json({"status": "complete", "run_id": run_id})

    def handle_competitor_analysis(self, body):
        url = body.get("target_url", "").strip()
        if not url:
            return self.send_json({"error": "target_url is required"}, 400)
            
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        RUNS[run_id] = {
            "run_id": run_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fault_type": "competitor-analysis",
            "target_resource": url,
            "rto_seconds": 150,
            "rpo_seconds": 40,
            "resilience_score": 75,
            "status": "Passed",
            "rto_target": 300,
            "rpo_target": 60,
            "report_s3_key": f"reports/{run_id}/report.json",
        }
        
        REPORTS[run_id] = {
            "report_id": run_id,
            "target_url": url,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "gap_analysis": {
                "client_score": 75,
                "client_rank": 2,
                "total_sites": 4,
                "average_competitor_score": 80,
                "max_competitor_score": 90,
                "min_competitor_score": 60,
                "feature_gaps": [],
                "content_gaps": []
            },
            "strategic_opportunities": [],
            "site_analyses": {
                url: {
                    "url": url,
                    "has_h1": True,
                    "has_blog": False,
                    "has_pricing": True,
                    "has_schema": False,
                    "has_og_tags": True,
                    "alt_text_ratio": 70,
                    "response_time_ms": 1200
                }
            }
        }
        
        print(f"[API] Competitor analysis complete: {run_id}")
        return self.send_json({"status": "complete", "run_id": run_id})

    def handle_compare(self, body):
        run_id_a = body.get("run_id_a")
        run_id_b = body.get("run_id_b")
        run_a = RUNS.get(run_id_a)
        run_b = RUNS.get(run_id_b)
        
        if not run_a or not run_b:
            return self.send_json({"error": "One or both runs not found"}, 404)
            
        score_a = run_a["resilience_score"]
        score_b = run_b["resilience_score"]
        rto_a = run_a["rto_seconds"]
        rto_b = run_b["rto_seconds"]
        rpo_a = run_a["rpo_seconds"]
        rpo_b = run_b["rpo_seconds"]
        
        res = {
            "run_a": run_a,
            "run_b": run_b,
            "deltas": {
                "score": {
                    "value_a": score_a,
                    "value_b": score_b,
                    "delta": score_b - score_a,
                    "improved": score_b >= score_a
                },
                "rto": {
                    "value_a": rto_a,
                    "value_b": rto_b,
                    "delta": rto_b - rto_a,
                    "improved": rto_b <= rto_a
                },
                "rpo": {
                    "value_a": rpo_a,
                    "value_b": rpo_b,
                    "delta": rpo_b - rpo_a,
                    "improved": rpo_b <= rpo_a
                }
            },
            "reports": {
                "a": None,
                "b": None
            },
            "warning": None
        }
        return self.send_json(res)

    def handle_create_client(self, body):
        client_id = f"client-{uuid.uuid4().hex[:8]}"
        client = {
            "client_id": client_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "business_name": body.get("business_name", ""),
            "url": body.get("url", ""),
            "industry": body.get("industry", ""),
            "primary_city": body.get("primary_city", ""),
            "state": body.get("state", ""),
            "neighborhoods": body.get("neighborhoods", []),
            "service_radius_miles": body.get("service_radius_miles", 10),
            "geographic_scope": body.get("geographic_scope", "city"),
            "business_type": body.get("business_type", "b2c"),
            "classification": {
                "business_type": body.get("business_type", "b2c"),
                "geographic_scope": body.get("geographic_scope", "city"),
                "classification": "Local Service Provider",
                "signals": [],
                "location_page_strategy": "Create city-specific landing pages",
                "keyword_tier_strategy": "Target geo-modified service keywords"
            },
            "seo_strategy": {
                "keyword_tiers": [],
                "content_priorities": [],
                "location_page_plan": [],
                "technical_priorities": []
            },
            "agency_name": body.get("agency_name", "CloudGuard Agency"),
            "client_email": body.get("client_email", ""),
            "known_competitors": body.get("known_competitors", []),
            "has_gbp": body.get("has_gbp", False),
            "gbp_review_count": body.get("gbp_review_count", 0),
            "launch_status": body.get("launch_status", "intake"),
            "notes": body.get("notes", "")
        }
        CLIENTS[client_id] = client
        print(f"[API] Client intake complete: {client_id}")
        return self.send_json(client)

    def handle_compare_sites(self, body):
        from urllib.parse import urlparse
        url_a = body.get("url_a", "").strip()
        url_b = body.get("url_b", "").strip()
        params = body.get("parameters", [])

        if not url_a or not url_b:
            return self.send_json({"error": "Both url_a and url_b are required"}, 400)

        site_a = self.generate_mock_site_metrics(url_a)
        site_b = self.generate_mock_site_metrics(url_b)

        comparison = {}
        for p in params:
            val_a = site_a.get(p)
            val_b = site_b.get(p)
            
            winner = "tie"
            if val_a is not None and val_b is not None and val_a != val_b:
                if isinstance(val_a, bool):
                    winner = "a" if val_a else "b"
                elif isinstance(val_a, (int, float)):
                    if p == "response_time_ms":
                        winner = "a" if val_a < val_b else "b"
                    else:
                        winner = "a" if val_a > val_b else "b"
                        
            comparison[p] = {"a": val_a, "b": val_b, "winner": winner}

        res = {
            "site_a": site_a,
            "site_b": site_b,
            "comparison": comparison
        }

        comp_id = f"comp-{uuid.uuid4().hex[:8]}"
        a_wins = sum(1 for v in comparison.values() if v["winner"] == "a")
        b_wins = sum(1 for v in comparison.values() if v["winner"] == "b")
        ties = sum(1 for v in comparison.values() if v["winner"] == "tie")

        COMPARISONS[comp_id] = {
            "comparison_id": comp_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "url_a": url_a,
            "url_b": url_b,
            "domain_a": urlparse(url_a).netloc or url_a,
            "domain_b": urlparse(url_b).netloc or url_b,
            "summary": {"a_wins": a_wins, "b_wins": b_wins, "ties": ties},
            "parameters_compared": params,
            "site_a": site_a,
            "site_b": site_b,
            "comparison": comparison
        }

        print(f"[API] Site comparison complete: {url_a} vs {url_b}")
        return self.send_json(res)

    def generate_mock_site_metrics(self, url):
        from urllib.parse import urlparse
        import random
        # deterministic random based on url to make it feel consistent
        seed = sum(ord(c) for c in url)
        random.seed(seed)
        
        parsed = urlparse(url)
        netloc = parsed.netloc or url
        
        return {
            "url": url,
            "status_code": 200 if random.random() > 0.05 else 500,
            "response_time_ms": random.randint(150, 1800),
            "content_length": random.randint(15000, 250000),
            "https_valid": url.startswith("https"),
            "ssl_expiry_days": random.randint(10, 365) if url.startswith("https") else None,
            "dns_resolves": True,
            "title": f"Home Page | {netloc}",
            "title_length": random.randint(10, 80),
            "meta_description": "Mock description of the website to test meta tags checks.",
            "meta_desc_length": random.randint(50, 200),
            "has_h1": random.random() > 0.1,
            "h1_count": random.randint(0, 3),
            "h2_count": random.randint(2, 18),
            "h3_count": random.randint(0, 30),
            "total_images": random.randint(5, 60),
            "images_with_alt": random.randint(2, 50),
            "alt_text_ratio": random.randint(20, 100),
            "total_links": random.randint(10, 150),
            "internal_links": random.randint(5, 100),
            "external_links": random.randint(0, 50),
            "has_viewport": True,
            "has_og_tags": random.random() > 0.2,
            "og_tag_count": random.randint(0, 8),
            "has_twitter_card": random.random() > 0.3,
            "has_canonical": random.random() > 0.1,
            "has_schema": random.random() > 0.4,
            "has_robots": True,
            "has_robots_noindex": False
        }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    if not OPENROUTER_API_KEY:
        print("WARNING: OPENROUTER_API_KEY not set — AI insights disabled")
        print("  export OPENROUTER_API_KEY='sk-or-v1-...'")

    server = HTTPServer(("0.0.0.0", PORT), APIHandler)
    print(f"\n{'='*60}")
    print(f"  CloudGuard DR — Local API Server")
    print(f"  Running on: http://localhost:{PORT}")
    print(f"  API base:   http://localhost:{PORT}/prod")
    print(f"  AI:         {'enabled' if OPENROUTER_API_KEY else 'disabled'}")
    print(f"{'='*60}\n")
    print("  Frontend .env:")
    print(f"    VITE_API_URL=http://localhost:{PORT}/prod")
    print(f"\n  Test:")
    print(f"    curl http://localhost:{PORT}/health")
    print(f"    curl -X POST http://localhost:{PORT}/audit/seo -H 'Content-Type: application/json' -d '{{\"target_url\":\"https://example.com\"}}'")
    print(f"{'='*60}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
