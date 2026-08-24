"""
CloudGuard DR — Competitor Analysis Lambda
Fetches target + competitor sites, analyzes SEO features for each,
builds a feature matrix, calculates competitive gap scores, and
generates strategic recommendations.
Stores JSON/HTML reports in S3 and pointers in DynamoDB.
"""
import os
import json
import time
import uuid
import ssl
import re
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse, quote_plus

import boto3

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")


# ─── HTML Parser ────────────────────────────────────────────────────

class SiteAnalyzer(HTMLParser):
    """Parse HTML and extract SEO-relevant features for competitive comparison."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_desc = ""
        self.meta_keywords = ""
        self.meta_robots = ""
        self.has_viewport = False
        self.has_charset = False
        self.canonical = None
        self.og_tags = {}
        self.twitter_tags = {}
        self.headings = {f"h{i}": [] for i in range(1, 7)}
        self.images = []
        self.links = []
        self.schemas = []
        self.has_blog = False
        self.has_pricing = False
        self.has_testimonials = False
        self.has_contact_page = False
        self.has_about_page = False
        self.nav_links = []
        self._in_title = False
        self._title_data = []
        self._in_nav = False
        self._in_script = False
        self._script_data = []
        self._current_tag = None
        self._current_attrs = {}
        self.phone_numbers = []
        self.addresses = []
        self.cta_count = 0

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        self._current_attrs = dict(attrs)

        if tag == "title":
            self._in_title = True
            self._title_data = []

        elif tag == "meta":
            name = (self._current_attrs.get("name") or "").lower()
            prop = (self._current_attrs.get("property") or "").lower()
            content = self._current_attrs.get("content", "")
            charset = self._current_attrs.get("charset", "")

            if charset:
                self.has_charset = True
            if name == "description":
                self.meta_desc = content
            elif name == "keywords":
                self.meta_keywords = content
            elif name == "robots":
                self.meta_robots = content
            elif name == "viewport":
                self.has_viewport = True
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
            elif name.startswith("twitter:"):
                self.twitter_tags[name] = content

        elif tag == "link":
            rel = self._current_attrs.get("rel", "").lower()
            href = self._current_attrs.get("href", "").lower()
            if rel == "canonical":
                self.canonical = self._current_attrs.get("href")
            # Detect nav links
            if self._in_nav and href:
                self.nav_links.append(href)

        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings[tag].append("")

        elif tag == "img":
            alt = self._current_attrs.get("alt", "")
            self.images.append({"has_alt": bool(alt)})

        elif tag == "a":
            href = self._current_attrs.get("href", "")
            text = ""  # Will be filled by handle_data
            self.links.append({"href": href})
            # Count CTAs (buttons, prominent links)
            cls = self._current_attrs.get("class", "").lower()
            if any(kw in cls for kw in ["btn", "button", "cta", "call"]):
                self.cta_count += 1

        elif tag == "nav":
            self._in_nav = True

        elif tag == "script":
            script_type = self._current_attrs.get("type", "")
            if script_type == "application/ld+json":
                self._in_script = True
                self._script_data = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = "".join(self._title_data).strip()

        if tag in self.headings and self.headings[tag]:
            self.headings[tag][-1] = self.headings[tag][-1].strip()

        if tag == "nav":
            self._in_nav = False

        if tag == "script" and self._in_script:
            self._in_script = False
            try:
                data = json.loads("".join(self._script_data))
                self.schemas.append(data)
            except (json.JSONDecodeError, Exception):
                pass

    def handle_data(self, data):
        if self._in_title:
            self._title_data.append(data)

        if self._in_script:
            self._script_data.append(data)

        if self._current_tag in self.headings and self.headings[self._current_tag]:
            self.headings[self._current_tag][-1] += data

        lower = data.lower().strip()
        # Detect content signals
        if "blog" in lower or "article" in lower or "news" in lower:
            self.has_blog = True
        if "pricing" in lower or "price" in lower or "cost" in lower or "plans" in lower:
            self.has_pricing = True
        if "testimonial" in lower or "review" in lower or "what our" in lower:
            self.has_testimonials = True
        if "contact" in lower:
            self.has_contact_page = True
        if "about" in lower:
            self.has_about_page = True
        # Phone pattern
        phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', data)
        self.phone_numbers.extend(phones)


def discover_competitors(target_url, industry, city, max_competitors=8):
    """
    Auto-discover competitors using DuckDuckGo HTML search.
    Searches for "[industry] [city]" and extracts competitor URLs.
    """
    target_domain = urlparse(target_url).netloc.replace("www.", "")
    discovered = []

    # Build search queries — try multiple variations
    queries = []
    if industry and city:
        queries.append(f"{industry} {city}")
        queries.append(f"{industry} services {city}")
        queries.append(f"best {industry} {city}")
    elif industry:
        queries.append(f"{industry} services")
        queries.append(f"best {industry} companies")
    elif city:
        queries.append(f"local services {city}")
    else:
        return discovered[:max_competitors]

    for query in queries:
        if len(discovered) >= max_competitors:
            break

        try:
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            req = urllib.request.Request(search_url)
            req.add_header("User-Agent", "Mozilla/5.0 (compatible; CloudGuardDR/1.0)")

            ctx = ssl.create_default_context()
            response = urllib.request.urlopen(req, timeout=10, context=ctx)
            html = response.read().decode("utf-8", errors="replace")

            # Extract URLs from DuckDuckGo results
            # DuckDuckGo HTML wraps results in <a class="result__a" href="...">
            url_pattern = re.compile(
                r'class="result__a"[^>]*href="([^"]+)"', re.IGNORECASE
            )
            # Also try the redirect URL pattern
            redirect_pattern = re.compile(
                r'class="result__url"[^>]*>\s*([^<]+)', re.IGNORECASE
            )
            # Try direct link pattern
            direct_pattern = re.compile(
                r'uddg=([^&"]+)', re.IGNORECASE
            )

            matches = url_pattern.findall(html)
            redirects = redirect_pattern.findall(html)
            directs = direct_pattern.findall(html)

            all_found = matches + redirects + directs

            for raw_url in all_found:
                if len(discovered) >= max_competitors:
                    break

                # Decode URL-encoded strings
                try:
                    decoded = urllib.request.unquote(raw_url.strip())
                except Exception:
                    decoded = raw_url.strip()

                # Ensure it's a valid HTTP(S) URL
                if not decoded.startswith("http"):
                    decoded = "https://" + decoded

                try:
                    parsed = urlparse(decoded)
                    if parsed.scheme not in ("http", "https"):
                        continue
                    domain = parsed.netloc.replace("www.", "")
                except Exception:
                    continue

                # Skip the target site itself
                if domain == target_domain:
                    continue

                # Skip search engines, social media, directories, etc.
                skip_domains = [
                    "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
                    "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
                    "yelp.com", "bbb.org", "yellowpages.com", "angi.com",
                    "thumbtack.com", "homeadvisor.com", "nextdoor.com",
                    "wikipedia.org", "youtube.com", "reddit.com",
                    "apple.com", "microsoft.com", "amazon.com",
                ]
                if any(skip in domain for skip in skip_domains):
                    continue

                # Skip if already discovered
                if any(d["domain"] == domain for d in discovered):
                    continue

                discovered.append({
                    "url": parsed.scheme + "://" + parsed.netloc,
                    "domain": domain,
                })

        except Exception as e:
            print(f"[CompetitorAnalysis] Search error for '{query}': {str(e)}")
            continue

    print(f"[CompetitorAnalysis] Discovered {len(discovered)} competitors")
    return [d["url"] for d in discovered[:max_competitors]]


def lambda_handler(event, context):
    """
    Run competitive analysis on a target site vs. competitors.

    Event input:
        {
            "target_url": "https://example.com",
            "industry": "plumbing",
            "city": "Austin",
            "geographic_scope": "city",
            "competitor_urls": []  // optional — auto-discovers if empty
        }

    Output:
        {
            "analysis_id": "comp-uuid",
            "target_url": "https://example.com",
            "competitors_analyzed": 6,
            "feature_matrix": { ... },
            "gap_analysis": { ... },
            "strategic_opportunities": [ ... ]
        }
    """
    print(f"[CompetitorAnalysis] Starting. Event: {json.dumps(event)}")

    try:
        target_url = event.get("target_url", "").strip()
        industry = event.get("industry", "general")
        city = event.get("city", "")
        geo_scope = event.get("geographic_scope", "city")
        competitor_urls = event.get("competitor_urls", [])

        if not target_url:
            raise ValueError("target_url is required")

        # Upgrade HTTP to HTTPS
        if target_url.startswith("http://"):
            target_url = target_url.replace("http://", "https://", 1)

        # Clean manually-provided competitor URLs
        clean_competitors = []
        for url in competitor_urls:
            url = url.strip()
            if url and url.startswith("http"):
                if url.startswith("http://"):
                    url = url.replace("http://", "https://", 1)
                clean_competitors.append(url)

        # Auto-discover competitors if none provided
        if not clean_competitors and (industry or city):
            print(f"[CompetitorAnalysis] No competitors provided — auto-discovering...")
            discovered = discover_competitors(target_url, industry, city)
            clean_competitors = discovered
            print(f"[CompetitorAnalysis] Auto-discovered {len(clean_competitors)} competitors: {clean_competitors}")

        analysis_id = f"comp-{uuid.uuid4().hex[:8]}"
        all_urls = [target_url] + clean_competitors

        # Analyze each site
        site_analyses = {}
        for url in all_urls:
            print(f"[CompetitorAnalysis] Analyzing: {url}")
            analysis = analyze_site(url)
            site_analyses[url] = analysis

        # Build feature matrix
        feature_matrix = build_feature_matrix(target_url, clean_competitors, site_analyses)

        # Calculate gap analysis
        gap_analysis = calculate_gaps(target_url, clean_competitors, site_analyses, industry, city)

        # Generate strategic opportunities
        opportunities = generate_opportunities(
            target_url, industry, city, geo_scope,
            site_analyses, feature_matrix, gap_analysis
        )

        # Build full report
        report = {
            "analysis_id": analysis_id,
            "target_url": target_url,
            "industry": industry,
            "city": city,
            "geographic_scope": geo_scope,
            "competitor_count": len(clean_competitors),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "site_analyses": site_analyses,
            "feature_matrix": feature_matrix,
            "gap_analysis": gap_analysis,
            "strategic_opportunities": opportunities,
        }

        # Write JSON to S3
        json_key = f"competitor-analysis/{analysis_id}/report.json"
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=json_key,
            Body=json.dumps(report, indent=2),
            ContentType="application/json",
        )

        # Write HTML to S3
        html_key = f"competitor-analysis/{analysis_id}/report.html"
        html_content = generate_html_report(report)
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=html_key,
            Body=html_content,
            ContentType="text/html",
        )

        # Store in DynamoDB
        table = dynamodb.Table(AUDIT_REPORTS_TABLE)
        table.put_item(Item={
            "report_id": analysis_id,
            "run_id": "",
            "target_url": target_url,
            "https_valid": True,
            "dns_failover_ok": True,
            "response_time_ms": None,
            "http_status_code": 200,
            "ssl_expiry_days": None,
            "generated_at": report["generated_at"],
            "fault_type": "competitor-analysis",
            "rto_seconds": None,
            "rpo_seconds": None,
            "resilience_score": gap_analysis.get("client_score", 0),
            "s3_report_key": json_key,
        })

        result = {
            "statusCode": 200,
            "analysis_id": analysis_id,
            "target_url": target_url,
            "competitor_count": len(clean_competitors),
            "feature_matrix": feature_matrix,
            "gap_analysis": gap_analysis,
            "strategic_opportunities": opportunities,
            "generated_at": report["generated_at"],
            "s3_key": json_key,
            "html_key": html_key,
        }

        print(f"[CompetitorAnalysis] Complete: {analysis_id} ({len(clean_competitors)} competitors)")
        return result

    except ValueError as e:
        print(f"[CompetitorAnalysis] Validation error: {str(e)}")
        return {"statusCode": 400, "error": str(e)}
    except Exception as e:
        print(f"[CompetitorAnalysis] Error: {str(e)}")
        raise


def fetch_page(url):
    """Fetch a page and return status, content, and timing."""
    result = {
        "status_code": 0,
        "content": "",
        "response_time_ms": 0,
        "content_length": 0,
        "https_valid": False,
    }
    try:
        ctx = ssl.create_default_context()
        start_time = time.time()
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "CloudGuardDR-Competitor/1.0")
        response = urllib.request.urlopen(req, timeout=15, context=ctx)
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        result["status_code"] = response.status
        result["https_valid"] = True
        content = response.read().decode("utf-8", errors="replace")
        result["content"] = content
        result["content_length"] = len(content)
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
    except Exception as e:
        print(f"[CompetitorAnalysis] Fetch error for {url}: {str(e)}")
    return result


def analyze_site(url):
    """Fetch a site and extract SEO features."""
    page = fetch_page(url)
    analyzer = SiteAnalyzer()

    try:
        analyzer.feed(page["content"])
    except Exception as e:
        print(f"[CompetitorAnalysis] Parse error for {url}: {str(e)}")

    parsed = urlparse(url)

    return {
        "url": url,
        "domain": parsed.netloc,
        "status_code": page["status_code"],
        "response_time_ms": page["response_time_ms"],
        "content_length": page["content_length"],
        "https_valid": page["https_valid"],

        # Identity
        "title": analyzer.title,
        "title_length": len(analyzer.title),
        "meta_description": analyzer.meta_desc,
        "meta_desc_length": len(analyzer.meta_desc),
        "has_viewport": analyzer.has_viewport,
        "canonical": analyzer.canonical is not None,

        # Social
        "has_og_tags": bool(analyzer.og_tags),
        "og_tag_count": len(analyzer.og_tags),
        "has_twitter_tags": bool(analyzer.twitter_tags),

        # Headings
        "h1_count": len(analyzer.headings["h1"]),
        "has_h1": len(analyzer.headings["h1"]) > 0,
        "has_h2": len(analyzer.headings["h2"]) > 0,
        "heading_depth": max(
            (int(k[1]) for k, v in analyzer.headings.items() if v),
            default=0
        ),

        # Content signals
        "has_blog": analyzer.has_blog,
        "has_pricing": analyzer.has_pricing,
        "has_testimonials": analyzer.has_testimonials,
        "has_contact_page": analyzer.has_contact_page,
        "has_about_page": analyzer.has_about_page,

        # Images
        "total_images": len(analyzer.images),
        "images_with_alt": sum(1 for img in analyzer.images if img["has_alt"]),
        "alt_text_ratio": (
            round(sum(1 for img in analyzer.images if img["has_alt"]) / len(analyzer.images) * 100)
            if analyzer.images else 0
        ),

        # Links
        "total_links": len(analyzer.links),
        "cta_count": analyzer.cta_count,

        # Schema / structured data
        "has_schema": bool(analyzer.schemas),
        "schema_types": [
            s.get("@type", "unknown") for s in analyzer.schemas if isinstance(s, dict)
        ],
        "schema_count": len(analyzer.schemas),

        # Contact signals
        "has_phone": bool(analyzer.phone_numbers),
        "phone_numbers": analyzer.phone_numbers[:3],

        # Navigation
        "nav_link_count": len(analyzer.nav_links),
    }


def build_feature_matrix(target_url, competitor_urls, site_analyses):
    """Build a feature comparison matrix across all sites."""
    features = [
        "title", "meta_desc_length", "has_viewport", "canonical",
        "has_og_tags", "has_twitter_tags", "has_h1", "has_h2",
        "has_blog", "has_pricing", "has_testimonials",
        "has_schema", "schema_count", "alt_text_ratio",
        "total_images", "total_links", "cta_count",
        "response_time_ms", "content_length",
    ]

    matrix = {}
    for feature in features:
        matrix[feature] = {}
        for url in [target_url] + competitor_urls:
            analysis = site_analyses.get(url, {})
            matrix[feature][url] = analysis.get(feature)

    return matrix


def calculate_gaps(target_url, competitor_urls, site_analyses, industry, city):
    """Calculate competitive gaps and scores."""
    target = site_analyses.get(target_url, {})

    # Score each site on SEO features (0-100)
    all_scores = {}
    for url, analysis in site_analyses.items():
        score = 0

        # Title (15 pts)
        if analysis.get("title"):
            tl = analysis.get("title_length", 0)
            if 30 <= tl <= 60:
                score += 15
            elif tl > 0:
                score += 8

        # Meta description (15 pts)
        if analysis.get("meta_desc_length", 0) > 0:
            ml = analysis["meta_desc_length"]
            if 120 <= ml <= 160:
                score += 15
            elif ml > 0:
                score += 8

        # H1 (10 pts)
        if analysis.get("has_h1"):
            score += 10

        # H2 (5 pts)
        if analysis.get("has_h2"):
            score += 5

        # Viewport (8 pts)
        if analysis.get("has_viewport"):
            score += 8

        # Canonical (7 pts)
        if analysis.get("canonical"):
            score += 7

        # Open Graph (10 pts)
        if analysis.get("has_og_tags"):
            score += min(analysis.get("og_tag_count", 0) * 3, 10)

        # Schema (8 pts)
        if analysis.get("has_schema"):
            score += min(analysis.get("schema_count", 0) * 4, 8)

        # Blog (5 pts)
        if analysis.get("has_blog"):
            score += 5

        # Pricing (5 pts)
        if analysis.get("has_pricing"):
            score += 5

        # Testimonials (5 pts)
        if analysis.get("has_testimonials"):
            score += 5

        # Alt text (5 pts)
        ratio = analysis.get("alt_text_ratio", 0)
        if ratio >= 90:
            score += 5
        elif ratio >= 50:
            score += 3

        # Performance (7 pts)
        rt = analysis.get("response_time_ms", 5000)
        if rt < 1000:
            score += 7
        elif rt < 2000:
            score += 4
        elif rt < 3000:
            score += 2

        all_scores[url] = score

    target_score = all_scores.get(target_url, 0)
    competitor_scores = {url: all_scores[url] for url in competitor_urls if url in all_scores}

    avg_competitor = (
        round(sum(competitor_scores.values()) / len(competitor_scores))
        if competitor_scores else 0
    )
    max_competitor = max(competitor_scores.values()) if competitor_scores else 0
    min_competitor = min(competitor_scores.values()) if competitor_scores else 0

    # Feature gaps — what competitors have that the client doesn't
    feature_gaps = []
    check_features = [
        ("has_blog", "Blog / Content Marketing"),
        ("has_pricing", "Pricing Transparency"),
        ("has_testimonials", "Testimonials / Reviews"),
        ("has_schema", "Schema Markup"),
        ("has_og_tags", "Open Graph / Social Tags"),
        ("has_twitter_tags", "Twitter Card Tags"),
        ("canonical", "Canonical URL"),
        ("has_viewport", "Mobile Viewport"),
    ]

    for key, label in check_features:
        target_has = target.get(key, False)
        competitor_has_count = sum(
            1 for url in competitor_urls
            if site_analyses.get(url, {}).get(key, False)
        )
        competitor_total = len(competitor_urls) if competitor_urls else 1
        pct = round(competitor_has_count / competitor_total * 100)

        if not target_has and competitor_has_count > 0:
            feature_gaps.append({
                "feature": label,
                "client_has": False,
                "competitors_with": competitor_has_count,
                "competitor_pct": pct,
                "severity": "critical" if pct >= 75 else "important" if pct >= 50 else "minor",
            })

    # Content gaps
    content_gaps = []
    competitors_with_blog = sum(
        1 for url in competitor_urls if site_analyses.get(url, {}).get("has_blog")
    )
    competitors_with_pricing = sum(
        1 for url in competitor_urls if site_analyses.get(url, {}).get("has_pricing")
    )
    competitors_with_testimonials = sum(
        1 for url in competitor_urls if site_analyses.get(url, {}).get("has_testimonials")
    )

    if not target.get("has_blog") and competitors_with_blog > 0:
        content_gaps.append({
            "gap": "No blog or content marketing",
            "impact": "high",
            "detail": f"{competitors_with_blog}/{len(competitor_urls)} competitors have blog content",
        })
    if not target.get("has_pricing") and competitors_with_pricing > 0:
        content_gaps.append({
            "gap": "No pricing information",
            "impact": "high",
            "detail": f"{competitors_with_pricing}/{len(competitor_urls)} competitors show pricing",
        })
    if not target.get("has_testimonials") and competitors_with_testimonials > 0:
        content_gaps.append({
            "gap": "No testimonials or reviews section",
            "impact": "medium",
            "detail": f"{competitors_with_testimonials}/{len(competitor_urls)} competitors showcase reviews",
        })

    return {
        "client_score": target_score,
        "competitor_scores": competitor_scores,
        "average_competitor_score": avg_competitor,
        "max_competitor_score": max_competitor,
        "min_competitor_score": min_competitor,
        "client_rank": _get_rank(target_score, all_scores),
        "total_sites": len(all_scores),
        "feature_gaps": feature_gaps,
        "content_gaps": content_gaps,
    }


def _get_rank(score, all_scores):
    """Get rank (1 = best) among all scored sites."""
    sorted_scores = sorted(all_scores.values(), reverse=True)
    for i, s in enumerate(sorted_scores):
        if s == score:
            return i + 1
    return len(sorted_scores)


def generate_opportunities(target_url, industry, city, geo_scope,
                           site_analyses, feature_matrix, gap_analysis):
    """Generate 3 specific strategic opportunities based on competitive gaps."""
    opportunities = []
    target = site_analyses.get(target_url, {})
    feature_gaps = gap_analysis.get("feature_gaps", [])
    content_gaps = gap_analysis.get("content_gaps", [])

    # Opportunity 1: Feature gap exploitation
    critical_gaps = [g for g in feature_gaps if g["severity"] == "critical"]
    if critical_gaps:
        gap_names = [g["feature"] for g in critical_gaps[:3]]
        opportunities.append({
            "title": f"Implement Missing Features: {', '.join(gap_names)}",
            "description": (
                f"The client is missing {len(critical_gaps)} key SEO features that "
                f"competitors already have. Implementing these would close the "
                f"competitive gap significantly."
            ),
            "impact": "high",
            "effort": "medium",
            "details": [
                {
                    "feature": g["feature"],
                    "action": f"Add {g['feature'].lower()} to the site",
                    "competitor_adoption": f"{g['competitor_pct']}% of competitors have this",
                }
                for g in critical_gaps
            ],
        })

    # Opportunity 2: Content marketing / blog
    if not target.get("has_blog"):
        competitors_with_blog = sum(
            1 for url, a in site_analyses.items()
            if url != target_url and a.get("has_blog")
        )
        if competitors_with_blog > 0:
            opportunities.append({
                "title": "Launch Content Marketing / Blog Strategy",
                "description": (
                    f"No competitor in this market has strong blog content. "
                    f"Publishing {industry}-specific articles targeting local search "
                    f"terms like \"{industry} tips {city}\" or "
                    f"\"best {industry} in {city}\" would create a significant "
                    f"content advantage."
                ),
                "impact": "high",
                "effort": "high",
                "details": [
                    {"action": f"Publish 2-4 blog posts per month targeting {city}-specific keywords"},
                    {"action": f"Create how-to guides and FAQs around {industry} services"},
                    {"action": "Add internal linking from blog posts to service pages"},
                ],
            })

    # Opportunity 3: Local SEO / schema / GBP
    if not target.get("has_schema"):
        opportunities.append({
            "title": "Add LocalBusiness Schema Markup",
            "description": (
                f"Schema markup helps search engines understand the business and "
                f"can generate rich results. Adding LocalBusiness JSON-LD with "
                f"correct NAP (Name, Address, Phone) data, service area, and "
                f"business hours will improve local search visibility in {city}."
            ),
            "impact": "medium",
            "effort": "low",
            "details": [
                {"action": "Add LocalBusiness JSON-LD schema to homepage"},
                {"action": "Include service area, hours, and contact info in schema"},
                {"action": "Validate with Google Rich Results Test"},
            ],
        })

    # Opportunity 4: Pricing transparency
    competitors_with_pricing = sum(
        1 for url, a in site_analyses.items()
        if url != target_url and a.get("has_pricing")
    )
    if not target.get("has_pricing") and competitors_with_pricing > 0:
        opportunities.append({
            "title": "Add Pricing Page / Transparent Pricing",
            "description": (
                f"{competitors_with_pricing} competitor(s) show pricing information. "
                f"A pricing page or cost estimator would capture high-intent "
                f"searchers looking for \"{industry} cost {city}\" and "
                f"\"{industry} prices near me\"."
            ),
            "impact": "high",
            "effort": "medium",
            "details": [
                {"action": f"Create a pricing page with ranges or starting prices"},
                {"action": f"Target keywords like \"{industry} cost {city}\" and \"{industry} prices\""},
                {"action": "Add FAQ schema to pricing page for rich results"},
            ],
        })

    # Opportunity 5: Testimonials / social proof
    competitors_with_testimonials = sum(
        1 for url, a in site_analyses.items()
        if url != target_url and a.get("has_testimonials")
    )
    if not target.get("has_testimonials") and competitors_with_testimonials > 0:
        opportunities.append({
            "title": "Build Testimonials & Review Showcase",
            "description": (
                f"Multiple competitors showcase customer reviews. Adding a "
                f"testimonials section with real customer names, locations, and "
                f"specific results builds trust and can include local keywords "
                f"naturally (e.g., \"great {industry} service in [neighborhood]\")."
            ),
            "impact": "medium",
            "effort": "low",
            "details": [
                {"action": "Add testimonials section to homepage and service pages"},
                {"action": "Collect reviews from Google Business Profile and display them"},
                {"action": "Include customer location (neighborhood/city) in testimonials"},
            ],
        })

    # Opportunity 6: Performance improvement
    target_rt = target.get("response_time_ms", 0)
    avg_rt = sum(
        a.get("response_time_ms", 0)
        for url, a in site_analyses.items()
        if url != target_url
    ) / max(len(site_analyses) - 1, 1)
    if target_rt > avg_rt * 1.5 and target_rt > 2000:
        opportunities.append({
            "title": "Improve Page Load Performance",
            "description": (
                f"The site loads in {target_rt}ms, which is slower than the "
                f"competitor average of {int(avg_rt)}ms. Faster sites rank "
                f"better and have lower bounce rates."
            ),
            "impact": "medium",
            "effort": "medium",
            "details": [
                {"action": "Optimize images (WebP format, lazy loading)"},
                {"action": "Minimize CSS and JavaScript bundles"},
                {"action": "Enable browser caching and CDN"},
            ],
        })

    # Limit to top 3 opportunities by impact
    impact_order = {"high": 0, "medium": 1, "low": 2}
    opportunities.sort(key=lambda o: impact_order.get(o.get("impact", "low"), 2))
    return opportunities[:3]


def generate_html_report(report):
    """Generate an HTML version of the competitor analysis."""
    ga = report["gap_analysis"]
    client_score = ga.get("client_score", 0)
    rank = ga.get("client_rank", 0)
    total = ga.get("total_sites", 1)
    opps = report.get("strategic_opportunities", [])
    matrix = report.get("feature_matrix", {})
    competitors = report.get("site_analyses", {})

    if client_score >= 70:
        score_color = "#22C55E"
    elif client_score >= 50:
        score_color = "#F59E0B"
    else:
        score_color = "#EF4444"

    # Build competitor rows for the matrix
    matrix_features = [
        ("Title Length", "title_length"),
        ("Meta Desc Length", "meta_desc_length"),
        ("Has H1", "has_h1"),
        ("Has Blog", "has_blog"),
        ("Has Pricing", "has_pricing"),
        ("Has Testimonials", "has_testimonials"),
        ("Has Schema", "has_schema"),
        ("Has OG Tags", "has_og_tags"),
        ("Has Twitter Tags", "has_twitter_tags"),
        ("Alt Text %", "alt_text_ratio"),
        ("Response (ms)", "response_time_ms"),
    ]

    matrix_rows = ""
    for label, key in matrix_features:
        values = matrix.get(key, {})
        cells = ""
        for url in [report["target_url"]] + list(report.get("site_analyses", {}).keys()):
            if url == report["target_url"]:
                continue
            val = values.get(url, "—")
            if isinstance(val, bool):
                cells += f'<td style="padding:8px 12px;text-align:center;font-family:var(--font-mono);font-size:12px;color:{"#22C55E" if val else "#EF4444"};">{"✓" if val else "✗"}</td>'
            elif isinstance(val, (int, float)):
                cells += f'<td style="padding:8px 12px;text-align:center;font-family:var(--font-mono);font-size:12px;">{val}</td>'
            else:
                cells += f'<td style="padding:8px 12px;text-align:center;font-size:12px;color:#666;">—</td>'

        # Client value
        client_val = values.get(report["target_url"], "—")
        if isinstance(client_val, bool):
            client_cell = f'<td style="padding:8px 12px;text-align:center;font-family:var(--font-mono);font-size:12px;color:{"#22C55E" if client_val else "#EF4444"};font-weight:600;">{"✓" if client_val else "✗"}</td>'
        elif isinstance(client_val, (int, float)):
            client_cell = f'<td style="padding:8px 12px;text-align:center;font-family:var(--font-mono);font-size:12px;font-weight:600;">{client_val}</td>'
        else:
            client_cell = f'<td style="padding:8px 12px;text-align:center;font-size:12px;color:#666;font-weight:600;">—</td>'

        matrix_rows += f"<tr><td style='padding:8px 12px;font-size:12px;color:#A1A1A1;border-bottom:1px solid #292929;'>{label}</td>{client_cell}{cells}</tr>\n"

    # Build competitor column headers
    comp_headers = ""
    for url, analysis in competitors.items():
        if url == report["target_url"]:
            continue
        domain = urlparse(url).netloc.replace("www.", "")
        comp_headers += f'<th style="padding:12px 16px;font-size:10px;font-weight:500;color:#A1A1A1;letter-spacing:0.1em;border-bottom:1px solid #292929;text-align:center;">{domain}</th>'

    # Build opportunities HTML
    opps_html = ""
    for i, opp in enumerate(opps, 1):
        impact_color = "#EF4444" if opp["impact"] == "high" else "#F59E0B" if opp["impact"] == "medium" else "#22C55E"
        details_list = "".join(
            f'<li style="padding:4px 0;font-size:13px;color:#A1A1A1;">{d.get("action", d.get("feature", ""))}</li>'
            for d in opp.get("details", [])
        )
        opps_html += f"""
        <div style="background:#151515;border:1px solid #292929;border-radius:8px;padding:24px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <span style="background:{impact_color};color:white;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;text-transform:uppercase;">{opp['impact']} impact</span>
                <span style="font-size:10px;color:#666;text-transform:uppercase;">{opp.get('effort', '')} effort</span>
            </div>
            <h3 style="font-size:16px;font-weight:600;color:#F5F5F5;margin-bottom:8px;">{i}. {opp['title']}</h3>
            <p style="font-size:13px;color:#A1A1A1;margin-bottom:12px;">{opp['description']}</p>
            <ul style="list-style:none;padding:0;">{details_list}</ul>
        </div>"""

    # Build gap items
    gaps_html = ""
    for gap in ga.get("feature_gaps", []):
        severity_color = "#EF4444" if gap["severity"] == "critical" else "#F59E0B" if gap["severity"] == "important" else "#666"
        gaps_html += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #292929;">
            <div>
                <span style="font-size:13px;color:#F5F5F5;">{gap['feature']}</span>
                <span style="font-size:11px;color:#666;margin-left:8px;">{gap['competitor_pct']}% of competitors have this</span>
            </div>
            <span style="font-size:10px;font-weight:600;color:{severity_color};text-transform:uppercase;">{gap['severity']}</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Competitive Analysis — {report['target_url']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', -apple-system, sans-serif; background: #0A0A0A; color: #F5F5F5; padding: 40px; }}
        .container {{ max-width: 960px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div style="margin-bottom:40px;">
            <h1 style="font-size:24px;font-weight:600;">Competitive Analysis</h1>
            <p style="color:#A1A1A1;font-size:14px;margin-top:4px;">{report['industry'].title()} — {report['city']} | Generated: {report['generated_at']}</p>
        </div>

        <!-- Score Card -->
        <div style="background:#151515;border:1px solid #292929;border-radius:8px;padding:32px;margin-bottom:24px;text-align:center;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:64px;font-weight:700;color:{score_color};">{client_score}</div>
            <div style="color:#A1A1A1;font-size:14px;margin-top:4px;">Client SEO Score</div>
            <div style="color:#666;font-size:13px;margin-top:8px;">Rank #{rank} out of {total} sites analyzed</div>
        </div>

        <!-- Feature Matrix -->
        <div style="background:#151515;border:1px solid #292929;border-radius:8px;padding:24px;margin-bottom:24px;overflow-x:auto;">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:16px;">Feature Matrix</h3>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr>
                        <th style="padding:12px 16px;text-align:left;font-size:10px;font-weight:500;color:#A1A1A1;letter-spacing:0.1em;border-bottom:1px solid #292929;width:20%;">FEATURE</th>
                        <th style="padding:12px 16px;text-align:center;font-size:10px;font-weight:500;color:#F5F5F5;letter-spacing:0.1em;border-bottom:1px solid #292929;border-left:2px solid #292929;">CLIENT</th>
                        {comp_headers}
                    </tr>
                </thead>
                <tbody>
                    {matrix_rows}
                </tbody>
            </table>
        </div>

        <!-- Feature Gaps -->
        <div style="background:#151515;border:1px solid #292929;border-radius:8px;padding:24px;margin-bottom:24px;">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:16px;">Feature Gaps</h3>
            {gaps_html if gaps_html else '<p style="color:#666;font-size:13px;">No critical feature gaps found.</p>'}
        </div>

        <!-- Strategic Opportunities -->
        <div style="margin-bottom:24px;">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:16px;">Strategic Opportunities</h3>
            {opps_html if opps_html else '<p style="color:#666;font-size:13px;">No strategic opportunities identified.</p>'}
        </div>

        <div style="text-align:center;color:#666;font-size:12px;margin-top:40px;">
            CloudGuard DR — Competitive Analysis Report
        </div>
    </div>
</body>
</html>"""
    return html
