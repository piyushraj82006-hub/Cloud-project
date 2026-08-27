"""
CloudGuard DR — Root Cause Analyzer
Rule-based failure diagnosis that explains WHY something failed
and HOW to fix it. Works without any AI API key.

Each analyzer returns a list of findings:
{
    "category": "rto_breach" | "seo_missing_title" | ...,
    "severity": "critical" | "high" | "medium",
    "title": "Short description",
    "why_it_matters": "Explanation of impact",
    "root_cause": "What likely caused this",
    "fix_steps": ["Step 1", "Step 2", ...],
    "estimated_effort": "minutes" | "hours" | "days",
    "prevention": "How to prevent this in the future"
}
"""


# ═══════════════════════════════════════════════════════════════════
# DR TEST Root Cause Analysis
# ═══════════════════════════════════════════════════════════════════

def analyze_dr_test(report):
    """Analyze a DR test report and return root causes for all failures."""
    findings = []

    score = report.get("resilience_score", 0)
    rto = report.get("rto_seconds", -1)
    rto_target = report.get("rto_target", 300)
    rpo = report.get("rpo_seconds", -1)
    rpo_target = report.get("rpo_target", 60)
    health = report.get("health_checks", {})
    fault_type = report.get("fault_type", "ec2-termination")

    # ── RTO Analysis ──
    if rto > rto_target:
        ratio = rto / rto_target if rto_target > 0 else 999
        if ratio > 2.0:
            findings.append({
                "category": "rto_critical_breach",
                "severity": "critical",
                "title": f"Recovery took {rto}s — {ratio:.1f}x over target ({rto_target}s)",
                "why_it_matters": "Your system took more than twice the acceptable time to recover. During this window, users experienced downtime or degraded service, potentially causing revenue loss and SLA violations.",
                "root_cause": "The most common causes for severe RTO breaches are: (1) No Auto Scaling group — EC2 instances must be manually replaced instead of auto-launched. (2) Missing AMI — the replacement instance uses a slow-to-configure base image instead of a pre-baked application AMI. (3) Slow health checks — ALB health check intervals are too long (e.g., 60s instead of 15s), delaying detection of the new healthy instance. (4) No load balancer deregistration delay — old dead instances stay in the target group, routing traffic to unhealthy endpoints.",
                "fix_steps": [
                    "1. Enable Auto Scaling group with min/max/max-size matching your capacity needs. Set desired capacity to your running instance count.",
                    "2. Create a launch template with your application pre-installed. Use a golden AMI built with Packer or EC2 Image Builder — not a UserData script that installs packages on boot.",
                    "3. Reduce ALB health check interval to 15 seconds and healthy threshold to 2. This means recovery is detected in ~30s instead of 2-3 minutes.",
                    "4. Set ALB deregistration delay to 10 seconds (default is 300s). This removes dead instances from the target group faster.",
                    "5. Enable instance protection on launch template to prevent accidental termination of running instances.",
                    "6. Test: Run the DR test again after changes. Target RTO should drop below 120s."
                ],
                "estimated_effort": "hours",
                "prevention": "Schedule weekly DR tests to catch regressions early. Monitor RTO trend line in the dashboard — any upward trend means infrastructure is drifting."
            })
        elif ratio > 1.2:
            findings.append({
                "category": "rto_moderate_breach",
                "severity": "high",
                "title": f"Recovery took {rto}s — {rto - rto_target}s over target ({rto_target}s)",
                "why_it_matters": "Your recovery time is slightly above target. While not critical, this indicates your infrastructure is not fully optimized for fast recovery and may degrade further under load.",
                "root_cause": "Moderate RTO breaches are typically caused by: (1) AMI that requires post-launch configuration (package installs, config downloads). (2) DNS TTL set too high — Route 53 continues routing to the dead instance. (3) Missing connection draining configuration on the ALB. (4) Cold start on replacement instance — no warm pool configured.",
                "fix_steps": [
                    "1. Audit your AMI — ensure all application code, dependencies, and configuration are baked in at build time, not installed at launch.",
                    "2. Reduce Route 53 DNS TTL to 60 seconds for the application record.",
                    "3. Configure ALB connection draining timeout to 10 seconds.",
                    "4. Consider EC2 Warm Pool — keeps stopped instances ready for near-instant launch.",
                    "5. Run the DR test again to verify improvement."
                ],
                "estimated_effort": "hours",
                "prevention": "Keep AMI updated weekly. Set up CloudWatch alarm on RTO trend."
            })

    # ── RPO Analysis ──
    if rpo > rpo_target:
        findings.append({
            "category": "rpo_breach",
            "severity": "critical" if rpo > rpo_target * 3 else "high",
            "title": f"Data loss window was {rpo}s — {rpo - rpo_target}s over target ({rpo_target}s)",
            "why_it_matters": f"During the {rpo}s recovery window, any data written to the system may have been lost. For a {rpo_target}s RPO target, this means your backup/replication strategy is not meeting your business requirements.",
            "root_cause": "RPO breaches happen when: (1) No real-time replication — data is only backed up periodically (e.g., hourly snapshots), so recent writes are lost. (2) EBS snapshots are not being taken frequently enough. (3) Database replication lag — if using RDS, the read replica is behind the primary. (4) No point-in-time recovery enabled on databases.",
            "fix_steps": [
                "1. Enable EBS snapshots with 5-minute intervals for all data volumes.",
                "2. If using RDS, enable automated backups with point-in-time recovery (RPO = seconds).",
                "3. If using DynamoDB, enable Point-in-Time Recovery (PITR) — it provides continuous backups with RPO of 1 second.",
                "4. For application state, consider using ElastiCache or a distributed cache that survives instance termination.",
                "5. Verify: After enabling, run a test write, terminate the instance, and confirm the write is recoverable."
            ],
            "estimated_effort": "hours",
            "prevention": "Enable automated backups on all stateful resources. Set CloudWatch alarms on replication lag."
        })

    # ── Health Check Failures ──
    if not health.get("https_valid"):
        findings.append({
            "category": "https_invalid",
            "severity": "critical",
            "title": "SSL certificate is invalid or expired",
            "why_it_matters": "Browsers will show a security warning, blocking most users. Search engines may de-index the page. API clients using strict SSL verification will fail entirely.",
            "root_cause": "SSL certificates expire after 90-365 days. This typically happens when: (1) Certificate was not set up for auto-renewal. (2) Using a self-signed certificate that wasn't properly configured. (3) The certificate was issued for a different domain than the one being tested. (4) AWS Certificate Manager (ACM) certificate renewal failed due to DNS validation not completing.",
            "fix_steps": [
                "1. Check certificate expiry: `aws acm list-certificates --region us-east-1`",
                "2. If expired, request a new certificate via ACM with DNS validation.",
                "3. For auto-renewal: Ensure the CNAME validation record exists in Route 53. ACM sends renewal requests 60 days before expiry.",
                "4. Update the ALB/CloudFront listener to use the new certificate ARN.",
                "5. Verify: `openssl s_client -connect yourdomain.com:443 -servername yourdomain.com` should show a valid cert chain.",
                "6. Set up a CloudWatch alarm on certificate expiry — alert at 30 days."
            ],
            "estimated_effort": "minutes",
            "prevention": "Use ACM with DNS validation — it auto-renews. Set up monitoring for cert expiry."
        })

    if not health.get("dns_failover_ok"):
        findings.append({
            "category": "dns_failover_broken",
            "severity": "critical",
            "title": "DNS failover routing is not operational",
            "why_it_matters": "When the primary instance fails, traffic is NOT being redirected to the standby. Users will see errors instead of being routed to the healthy instance. This defeats the entire purpose of having a DR setup.",
            "root_cause": "DNS failover breaks when: (1) Route 53 health checks are not configured on the record. (2) The health check is pointing to the wrong port or path. (3) Failover routing policy is not set — using simple routing instead. (4) Secondary record (standby) is missing or points to a non-existent resource. (5) Health check timeout is too aggressive — marking healthy instances as unhealthy.",
            "fix_steps": [
                "1. Open Route 53 console → Hosted Zones → your domain",
                "2. Verify the primary A/AAAA record uses 'Failover' routing policy with 'Primary' designation",
                "3. Verify a Route 53 health check exists and is associated with the primary record",
                "4. Create a secondary record with 'Failover' → 'Secondary' pointing to your standby instance/ALB",
                "5. Set health check: Protocol=HTTPS, Port=443, Path=/health, Interval=30s, Failure threshold=3",
                "6. Test: Manually stop the primary instance and verify DNS resolves to the secondary within 60s"
            ],
            "estimated_effort": "minutes",
            "prevention": "Test failover monthly. Set up Route 53 health check CloudWatch alarms."
        })

    if (health.get("response_time_ms") or 9999) > 3000:
        findings.append({
            "category": "slow_response",
            "severity": "high",
            "title": f"Response time {health.get('response_time_ms')}ms exceeds 3000ms threshold",
            "why_it_matters": "Slow response times directly impact user experience and SEO rankings. Google penalizes pages that take over 3 seconds to load. Users abandon sites after 3 seconds.",
            "root_cause": "Slow responses after recovery are caused by: (1) Cold start — the replacement instance hasn't warmed up caches yet. (2) Missing CloudFront distribution — all requests hit the origin directly. (3) Unoptimized application — no connection pooling, missing indexes, synchronous external API calls. (4) Instance type too small for the traffic load.",
            "fix_steps": [
                "1. Add a CloudFront distribution in front of your ALB. CloudFront edge caching absorbs cold-start latency.",
                "2. Configure ALB to use connection keep-alive to backend instances.",
                "3. Add application-level caching (ElastiCache Redis) for frequent database queries.",
                "4. Implement health check warm-up — after instance launch, run a warm-up script that pre-populates caches.",
                "5. Consider a larger instance type if the application is CPU/memory bound.",
                "6. Profile the application — use X-Ray to find the slowest endpoints."
            ],
            "estimated_effort": "days",
            "prevention": "Use CloudFront for all public endpoints. Monitor response time trend."
        })

    if health.get("http_status_code") and health.get("http_status_code") != 200:
        findings.append({
            "category": "non_200_status",
            "severity": "high",
            "title": f"Server returned HTTP {health.get('http_status_code')} instead of 200",
            "why_it_matters": f"HTTP {health.get('http_status_code')} indicates the server is responding but something is wrong — the application isn't ready to serve traffic after recovery.",
            "root_cause": "Common causes: (1) Application not fully started — returns 503 during boot. (2) Missing environment variables — application starts but can't connect to database/cache. (3) Dependency failure — external service (database, S3, API) is unreachable from the new instance's network. (4) Security group misconfiguration — instance can't reach required services.",
            "fix_steps": [
                "1. Check application logs: `aws logs tail /aws/lambda/your-app --since 10m`",
                "2. Verify environment variables are set correctly in the launch template.",
                "3. Test database connectivity from the instance: `telnet your-rds-endpoint 5432`",
                "4. Verify security groups allow outbound traffic to required services.",
                "5. Add a post-launch initialization script that waits for all dependencies before marking instance healthy.",
                "6. Set ALB health check to match the application's readiness endpoint (e.g., /health that checks DB + cache connectivity)."
            ],
            "estimated_effort": "hours",
            "prevention": "Use a readiness probe that checks all dependencies, not just HTTP 200."
        })

    # ── Score Analysis ──
    if score < 50:
        findings.append({
            "category": "very_low_score",
            "severity": "critical",
            "title": f"Resilience score {score}/100 indicates system is not disaster-ready",
            "why_it_matters": "A score below 50 means your DR setup has fundamental gaps. In a real disaster, recovery is unlikely to succeed within acceptable timeframes, and data loss is probable.",
            "root_cause": "Very low scores are caused by multiple compounding failures — typically RTO AND RPO both exceeding targets, plus health check failures. This indicates the DR infrastructure was never properly set up or has severely degraded.",
            "fix_steps": [
                "1. Address all critical findings above first (RTO, RPO, health checks).",
                "2. Run the full DR test checklist: Auto Scaling, AMI, health checks, DNS failover, backups.",
                "3. Consider engaging a DR consultant for a one-time infrastructure audit.",
                "4. Implement infrastructure-as-code (Terraform) to prevent configuration drift.",
                "5. Schedule DR tests bi-weekly until score is consistently above 70."
            ],
            "estimated_effort": "days",
            "prevention": "Implement DR-as-code. Never manually modify infrastructure that affects recovery."
        })

    return findings


# ═══════════════════════════════════════════════════════════════════
# SEO AUDIT Root Cause Analysis
# ═══════════════════════════════════════════════════════════════════

def analyze_seo(report):
    """Analyze an SEO report and return root causes with specific fix instructions."""
    findings = []
    checks = report.get("seo_checks", {})
    score = report.get("seo_score", 0)

    # ── Title Tag ──
    title_check = checks.get("title", {})
    title_issues = title_check.get("issues", [])
    if title_issues:
        has_title = title_check.get("present", True)
        if not has_title or "Missing page title" in str(title_issues):
            findings.append({
                "category": "missing_title",
                "severity": "critical",
                "title": "Page title is missing",
                "why_it_matters": "The title tag is the single most important on-page SEO factor. It appears in search results as the clickable headline (blue link). Without it, Google doesn't know what the page is about, and click-through rates drop 30-50%.",
                "root_cause": "Missing titles are caused by: (1) Developer forgot to add <title> tag in the HTML <head>. (2) CMS/template doesn't set a default title. (3) JavaScript-rendered pages that don't set document.title. (4) Single-page app (SPA) that doesn't update the title on route changes.",
                "fix_steps": [
                    "1. Open your page's HTML source (right-click → View Page Source).",
                    "2. Find the <head> section and add: <title>Your Primary Keyword — Brand Name</title>",
                    "3. Keep title between 30-60 characters. Put the most important keyword first.",
                    "4. If using a CMS (WordPress, Shopify), check SEO plugin settings (Yoast, RankMath).",
                    "5. For SPAs: Use React Helmet or equivalent to set title per route.",
                    "6. Verify: Search 'site:yourdomain.com' in Google — the title should appear in results."
                ],
                "estimated_effort": "minutes",
                "prevention": "Add title validation to your CI/CD pipeline. Use a template: '{Page Name} | {Brand}'"
            })
        else:
            # Title exists but has issues
            for issue in title_issues:
                if "too short" in issue.lower():
                    findings.append({
                        "category": "title_too_short",
                        "severity": "high",
                        "title": "Page title is too short",
                        "why_it_matters": "Short titles waste valuable search result real estate. Google may auto-generate a longer title from your content, which you can't control and may not be compelling.",
                        "root_cause": "The title is set but doesn't contain enough descriptive text. This often happens when the title is just the brand name without a page description.",
                        "fix_steps": [
                            "1. Rewrite the title to be 30-60 characters.",
                            "2. Format: 'Primary Keyword — Secondary Keyword | Brand Name'",
                            "3. Example: 'Emergency Plumbing Austin TX | Acme Plumbing' (46 chars)",
                            "4. Make it compelling — think of it as a headline that earns clicks."
                        ],
                        "estimated_effort": "minutes",
                        "prevention": "Use a title template for all pages."
                    })
                elif "too long" in issue.lower():
                    findings.append({
                        "category": "title_too_long",
                        "severity": "medium",
                        "title": "Page title is too long and will be truncated",
                        "why_it_matters": "Google truncates titles after ~60 characters. Your carefully crafted message gets cut off, and the visible title may not make sense.",
                        "root_cause": "The title exceeds 60 characters. Common in pages that try to stuff too many keywords into the title.",
                        "fix_steps": [
                            "1. Trim the title to under 60 characters.",
                            "2. Prioritize the most important keyword — put it first.",
                            "3. Remove filler words (the, and, a, or) and redundant keywords.",
                            "4. Use Google's SERP preview tool to see how it will appear."
                        ],
                        "estimated_effort": "minutes",
                        "prevention": "Use a character counter when writing titles."
                    })

    # ── Meta Description ──
    meta_check = checks.get("meta_description", {})
    meta_issues = meta_check.get("issues", [])
    if meta_issues:
        has_meta = meta_check.get("present", True)
        if not has_meta or "Missing meta description" in str(meta_issues):
            findings.append({
                "category": "missing_meta_desc",
                "severity": "critical",
                "title": "Meta description is missing",
                "why_it_matters": "The meta description appears below the title in search results. It's your elevator pitch — a compelling 155-character ad that convinces users to click. Missing it means Google auto-generates one from your page content, which is often irrelevant.",
                "root_cause": "Same causes as missing title — developer oversight, CMS misconfiguration, or SPA routing issues.",
                "fix_steps": [
                    "1. Add to <head>: <meta name=\"description\" content=\"Your compelling 120-160 character description here.\">",
                    "2. Include your primary keyword naturally in the first sentence.",
                    "3. Write it like ad copy — address the user's pain point and offer a solution.",
                    "4. End with a call-to-action: 'Call now for a free estimate' or 'Learn more'.",
                    "5. Example for a plumber: 'Emergency plumbing services in Austin, TX. 24/7 response, licensed & insured. Call (512) 555-0123 for immediate help.'"
                ],
                "estimated_effort": "minutes",
                "prevention": "Write meta descriptions for every page as part of content creation."
            })

    # ── Headings ──
    heading_check = checks.get("headings", {})
    heading_issues = heading_check.get("issues", [])
    if heading_issues:
        for issue in heading_issues:
            if "Missing H1" in issue:
                findings.append({
                    "category": "missing_h1",
                    "severity": "critical",
                    "title": "No H1 heading tag found on the page",
                    "why_it_matters": "The H1 tag tells Google (and users) what the page is about. It's the second most important on-page SEO element after the title. Pages without an H1 rank lower because Google can't determine the page's topic.",
                    "root_cause": "Caused by: (1) Developer used a <div> or <span> for the main heading instead of <h1>. (2) The main heading is inside a JavaScript component that renders after SEO crawlers read the page. (3) CSS styled a non-heading element to look like a heading.",
                    "fix_steps": [
                        "1. Identify the main heading on the page (the largest, most prominent text at the top).",
                        "2. Wrap it in an <h1> tag: <h1>Your Primary Keyword Here</h1>",
                        "3. There should be exactly ONE H1 per page — multiple H1s confuse search engines.",
                        "4. Include your primary keyword naturally in the H1.",
                        "5. For JavaScript-rendered pages: ensure the H1 is in the initial HTML, not just added by JS."
                    ],
                    "estimated_effort": "minutes",
                    "prevention": "Use semantic HTML5 elements. Add H1 validation to your linting rules."
                })
            elif "Multiple H1" in issue:
                findings.append({
                    "category": "multiple_h1",
                    "severity": "high",
                    "title": "Page has multiple H1 tags",
                    "why_it_matters": "Multiple H1s dilute the page's topical focus. Google can't determine which H1 is the 'main' topic, so it may rank for the wrong keywords or not rank at all.",
                    "root_cause": "Common in: (1) Pages built with page builders that add H1s to each section. (2) Blog posts where the title and a section header both use H1. (3) Navigation elements accidentally using H1.",
                    "fix_steps": [
                        "1. Keep exactly ONE H1 — the main page title.",
                        "2. Convert all other H1s to H2s or H3s.",
                        "3. Use the heading hierarchy: H1 → H2 → H3 → H4 (never skip levels).",
                        "4. If using a CMS, check theme settings for heading defaults."
                    ],
                    "estimated_effort": "minutes",
                    "prevention": "Set heading rules in your style guide: H1 = page title, H2 = sections, H3 = subsections."
                })

    # ── Images ──
    image_check = checks.get("images", {})
    image_issues = image_check.get("issues", [])
    if image_issues:
        findings.append({
            "category": "missing_alt_text",
            "severity": "high",
            "title": f"{image_issues[0]}",
            "why_it_matters": "Alt text helps Google understand image content (images appear in Google Images search). It's also a legal accessibility requirement (ADA/WCAG) — screen readers can't describe images without alt text.",
            "root_cause": "Images added via CMS drag-and-drop often don't require alt text, so content editors skip it. Developer-added images (hero banners, icons) frequently omit alt attributes.",
            "fix_steps": [
                "1. For each image, ask: 'What would I tell someone on the phone about this image?' — that's your alt text.",
                "2. Add alt attribute: <img src=\"...\" alt=\"Plumber fixing a burst pipe in Austin kitchen\">",
                "3. Be descriptive but concise (under 125 characters).",
                "4. Include keywords naturally — don't stuff them.",
                "5. Decorative images (purely visual, no information): use alt=\"\" (empty).",
                "6. For CMS images: go to Media Library → click image → add Alt Text."
            ],
            "estimated_effort": "minutes",
            "prevention": "Make alt text required in your CMS upload workflow."
        })

    # ── Canonical URL ──
    canonical_check = checks.get("canonical", {})
    canonical_issues = canonical_check.get("issues", [])
    if canonical_issues:
        findings.append({
            "category": "missing_canonical",
            "severity": "high",
            "title": "Canonical URL tag is missing",
            "why_it_matters": "Without a canonical tag, Google may index multiple versions of the same page (http/https, www/non-www, with/without trailing slash). This splits your SEO authority across duplicate pages.",
            "root_cause": "Caused by: (1) Developer didn't add the canonical tag. (2) CMS doesn't output canonical tags by default. (3) URL parameters create duplicate pages that aren't consolidated.",
            "fix_steps": [
                "1. Add to <head>: <link rel=\"canonical\" href=\"https://yourdomain.com/this-page\">",
                "2. The canonical URL should be the 'master' version — use HTTPS, with or without www (pick one and be consistent).",
                "3. For CMS sites: Install an SEO plugin that auto-generates canonical tags.",
                "4. For parameterized URLs (e.g., /products?color=red): canonical should point to /products (the base URL).",
                "5. Verify: View page source and search for 'canonical' — the tag should be there."
            ],
            "estimated_effort": "minutes",
            "prevention": "Use a CMS SEO plugin that auto-generates canonical tags."
        })

    # ── Open Graph ──
    og_check = checks.get("open_graph", {})
    og_issues = og_check.get("issues", [])
    if og_issues:
        missing_tags = og_check.get("tags_missing", [])
        findings.append({
            "category": "missing_og_tags",
            "severity": "medium",
            "title": f"Missing Open Graph tags: {', '.join(missing_tags[:3])}",
            "why_it_matters": "Open Graph tags control how your page appears when shared on Facebook, LinkedIn, Slack, and other social platforms. Without them, shares show a generic preview with no image, title, or description.",
            "root_cause": "OG tags are often forgotten because they don't affect Google ranking directly — they affect social media sharing. Developers focused on Google SEO may skip them.",
            "fix_steps": [
                "1. Add these tags to <head>:",
                "   <meta property=\"og:title\" content=\"Page Title\">",
                "   <meta property=\"og:description\" content=\"Page description\">",
                "   <meta property=\"og:image\" content=\"https://yourdomain.com/image.jpg\">",
                "   <meta property=\"og:url\" content=\"https://yourdomain.com/page\">",
                "   <meta property=\"og:type\" content=\"website\">",
                "2. Image should be 1200x630 pixels (optimal for social sharing).",
                "3. Test: Use Facebook's Sharing Debugger (developers.facebook.com/tools/debug) to preview.",
                "4. For CMS: Most SEO plugins auto-generate OG tags from the title/description."
            ],
            "estimated_effort": "minutes",
            "prevention": "Add OG tags to your base HTML template so all pages inherit them."
        })

    # ── Structured Data ──
    schema_check = checks.get("structured_data", {})
    schema_issues = schema_check.get("issues", [])
    if schema_issues:
        findings.append({
            "category": "missing_structured_data",
            "severity": "high",
            "title": "No structured data (JSON-LD) found",
            "why_it_matters": "Structured data tells Google exactly what your content is — a business, product, FAQ, recipe, etc. Without it, you miss out on rich results (star ratings, FAQ dropdowns, business info panels) that can increase click-through rates by 30%.",
            "root_cause": "JSON-LD structured data requires manual implementation or a plugin. Most developers don't add it unless specifically asked.",
            "fix_steps": [
                "1. Identify your content type: LocalBusiness, Product, FAQ, Article, etc.",
                "2. Use Google's Structured Data Markup Helper (search.google.com/structured-data/testing-tool) to generate JSON-LD.",
                "3. For a local business, add this to <head>:",
                "   <script type=\"application/ld+json\">",
                "   {\"@context\": \"https://schema.org\", \"@type\": \"LocalBusiness\", \"name\": \"Your Business\", ...}",
                "   </script>",
                "4. Test with Google's Rich Results Test tool.",
                "5. For CMS: Install a structured data plugin."
            ],
            "estimated_effort": "hours",
            "prevention": "Add structured data to your page templates. Update when business info changes."
        })

    # ── Performance ──
    perf_check = checks.get("performance", {})
    perf_issues = perf_check.get("issues", [])
    if perf_issues:
        for issue in perf_issues:
            if "slow" in issue.lower() or "response time" in issue.lower():
                findings.append({
                    "category": "slow_page_load",
                    "severity": "high",
                    "title": f"Page load time is slow: {perf_check.get('response_time_ms', 'unknown')}ms",
                    "why_it_matters": "Page speed is a direct Google ranking factor (Core Web Vitals). Slow pages also have 32% higher bounce rates — users leave before your content loads.",
                    "root_cause": "Slow page loads are caused by: (1) Uncompressed images — large files served without optimization. (2) No CDN — all traffic hits your origin server. (3) Render-blocking CSS/JS in the <head>. (4) No browser caching — every visit re-downloads everything. (5) Too many HTTP requests — many small files instead of bundled ones.",
                    "fix_steps": [
                        "1. Compress images: Use WebP format, or run through TinyPNG/Squoosh. Target under 200KB per image.",
                        "2. Add CloudFront CDN — caches content at edge locations worldwide.",
                        "3. Add cache headers: Cache-Control: max-age=31536000 for static assets.",
                        "4. Minify CSS and JS files. Use build tools (Webpack, Vite) that do this automatically.",
                        "5. Defer non-critical JS: <script src=\"...\" defer>",
                        "6. Use Google PageSpeed Insights (pagespeed.web.dev) for specific recommendations."
                    ],
                    "estimated_effort": "hours",
                    "prevention": "Run PageSpeed Insights before every deployment. Set a performance budget."
                })

    # ── Viewport ──
    viewport_check = checks.get("viewport", {})
    viewport_issues = viewport_check.get("issues", [])
    if viewport_issues:
        findings.append({
            "category": "missing_viewport",
            "severity": "critical",
            "title": "Viewport meta tag is missing — site is not mobile-friendly",
            "why_it_matters": "Google uses mobile-first indexing — it primarily crawls and ranks the mobile version of your site. Without a viewport tag, your site renders at desktop width on mobile, making it unusable. Google will penalize or de-index it.",
            "root_cause": "Missing viewport tag means the HTML <head> doesn't include: <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">. Common in legacy sites built before mobile was important.",
            "fix_steps": [
                "1. Add to <head>: <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
                "2. This tells browsers to render the page at the device's width, not at 980px.",
                "3. After adding the tag, test your site on a mobile device — content should fit the screen.",
                "4. If content overflows or is too small, add responsive CSS: @media (max-width: 768px) { ... }",
                "5. Verify: Use Google's Mobile-Friendly Test tool (search.google.com/test/mobile-friendly)."
            ],
            "estimated_effort": "minutes",
            "prevention": "Always include the viewport tag in your base HTML template."
        })

    return findings


# ═══════════════════════════════════════════════════════════════════
# COMPETITOR ANALYSIS Root Cause
# ═══════════════════════════════════════════════════════════════════

def analyze_competitor(report):
    """Analyze competitor report and explain why gaps exist and how to close them."""
    findings = []
    ga = report.get("gap_analysis", {})
    feature_gaps = ga.get("feature_gaps", [])
    content_gaps = ga.get("content_gaps", [])
    site_analyses = report.get("site_analyses", {})
    target_url = report.get("target_url", "")
    target = site_analyses.get(target_url, {})

    # ── Feature Gaps ──
    gap_fix_map = {
        "Blog / Content Marketing": {
            "why": "Competitors with blogs rank for long-tail keywords that drive 60-70% of organic traffic. Without a blog, you're invisible for informational searches like 'how to fix a leaky faucet' that your customers are Googling.",
            "root_cause": "No content strategy — the site was built as a brochure without ongoing content investment.",
            "fix_steps": [
                "1. Start with 4 foundational pages: 'Services', 'About', 'FAQ', 'Contact'.",
                "2. Add 2 blog posts per month targeting long-tail keywords (e.g., 'signs you need a water heater replacement').",
                "3. Each post: 800-1500 words, includes images, targets one specific keyword.",
                "4. Share posts on social media and Google Business Profile.",
                "5. Track rankings in Google Search Console — organic traffic should grow within 3-6 months."
            ]
        },
        "Pricing Page": {
            "why": "Pricing pages capture high-intent traffic — people searching 'plumbing cost Austin' are ready to buy. Competitors with pricing pages rank for these money keywords and convert visitors faster.",
            "root_cause": "Business owners often avoid publishing prices thinking competitors will undercut them. In reality, 70% of consumers prefer to see pricing upfront.",
            "fix_steps": [
                "1. Create a pricing page with ranges (e.g., 'Drain cleaning: $150-$350 depending on complexity').",
                "2. Include a 'Get a Free Quote' CTA for custom jobs.",
                "3. Add a pricing FAQ section addressing common cost questions.",
                "4. Target keywords: '{service} cost {city}', '{service} price {city}'.",
                "5. Update pricing quarterly — it doesn't need to be exact, ranges work fine."
            ]
        },
        "Schema / Structured Data": {
            "why": "Competitors with schema markup get rich search results — star ratings, business hours, and service areas displayed directly in Google. This increases click-through rates by 30%.",
            "root_cause": "Schema markup requires adding JSON-LD code to the page. Most developers don't add it unless asked.",
            "fix_steps": [
                "1. Add LocalBusiness schema: {\"@type\": \"LocalBusiness\", \"name\": \"...\", \"address\": {...}, \"priceRange\": \"$$\"}",
                "2. Add Service schema for each service you offer.",
                "3. Add FAQ schema to your FAQ page for FAQ rich results.",
                "4. Test with Google's Rich Results Test.",
                "5. Update schema when business info changes (hours, phone, services)."
            ]
        },
        "Testimonials / Reviews": {
            "why": "Social proof is the #1 factor in local service decisions. Competitors with testimonials build trust faster and convert more visitors into customers.",
            "root_cause": "Reviews exist on Google/Yelp but aren't displayed on the website.",
            "fix_steps": [
                "1. Add a testimonials section to your homepage and services pages.",
                "2. Feature 3-5 of your best Google reviews with the reviewer's name.",
                "3. Add a 'Reviews' page that aggregates Google/Yelp reviews.",
                "4. After every job, send a review request link to the customer.",
                "5. Respond to all reviews — positive and negative."
            ]
        },
        "H1 Tag": {
            "why": "Without an H1, Google can't determine the page's main topic. Competitors with proper heading structure rank higher because their pages are topically clear.",
            "root_cause": "Developer used a <div> or <span> styled to look like a heading instead of a semantic <h1> tag.",
            "fix_steps": [
                "1. Find the main heading on your homepage.",
                "2. Wrap it in <h1> tags: <h1>Austin's Trusted Emergency Plumbing Service</h1>",
                "3. Include your primary keyword and city in the H1.",
                "4. Only ONE H1 per page — convert others to H2."
            ]
        },
        "OG Tags": {
            "why": "When your site is shared on social media without OG tags, it shows a generic preview with no image or description. Competitors with OG tags look professional and get more social clicks.",
            "root_cause": "OG tags are invisible to site visitors, so developers often skip them.",
            "fix_steps": [
                "1. Add to <head>: <meta property=\"og:title\" content=\"...\"><meta property=\"og:image\" content=\"...\">",
                "2. Create a 1200x630px social sharing image with your brand and key message.",
                "3. Test with Facebook Sharing Debugger.",
                "4. Add OG tags to your base HTML template so all pages inherit them."
            ]
        },
        "Blog": {
            "why": "Blogs drive 67% more leads than non-blogging websites. Competitors with blogs capture informational searches that lead to service inquiries.",
            "root_cause": "Content creation requires ongoing effort that most small businesses deprioritize.",
            "fix_steps": [
                "1. Write 1 post per week answering a common customer question.",
                "2. Target keywords with 'how to', 'what is', 'best' + your service + city.",
                "3. Each post should be 800+ words with images.",
                "4. Share on Google Business Profile for local visibility."
            ]
        }
    }

    for gap in feature_gaps:
        feature = gap.get("feature", "")
        severity = gap.get("severity", "medium")
        competitor_pct = gap.get("competitor_pct", 0)

        fix_info = gap_fix_map.get(feature, {})
        why = fix_info.get("why", f"Competitors have {feature} but you don't. This puts you at a competitive disadvantage.")
        root_cause = fix_info.get("root_cause", f"The feature was never implemented or was removed during a site redesign.")
        fix_steps = fix_info.get("fix_steps", [f"Implement {feature} on your website."])

        findings.append({
            "category": f"feature_gap_{feature.lower().replace(' ', '_').replace('/', '_')}",
            "severity": severity,
            "title": f"Missing: {feature} ({competitor_pct}% of competitors have it)",
            "why_it_matters": why,
            "root_cause": root_cause,
            "fix_steps": fix_steps,
            "estimated_effort": "hours" if feature in ["Blog / Content Marketing", "Pricing Page"] else "minutes",
            "prevention": f"Audit quarterly — check if competitors have added {feature}."
        })

    # ── Content Gaps ──
    for gap in content_gaps:
        findings.append({
            "category": "content_gap",
            "severity": "high",
            "title": f"Content gap: {gap.get('gap', '')}",
            "why_it_matters": gap.get("impact", "Competitors are ranking for keywords you're not targeting."),
            "root_cause": "No content exists to target these keywords.",
            "fix_steps": [
                f"Create content targeting: {gap.get('gap', '')}",
                f"Detail: {gap.get('detail', '')}",
                "Write 800-1500 words with proper H1/H2 structure, internal links, and a clear CTA."
            ],
            "estimated_effort": "hours",
            "prevention": "Run keyword gap analysis quarterly using Google Search Console."
        })

    return findings


# ═══════════════════════════════════════════════════════════════════
# COMPARISON Root Cause Analysis
# ═══════════════════════════════════════════════════════════════════

def analyze_comparison(data):
    """Analyze a run comparison and explain what changed and why."""
    findings = []
    run_a = data.get("run_a", {})
    run_b = data.get("run_b", {})

    score_a = run_a.get("resilience_score", 0)
    score_b = run_b.get("resilience_score", 0)
    rto_a = run_a.get("rto_seconds", 0)
    rto_b = run_b.get("rto_seconds", 0)
    rpo_a = run_a.get("rpo_seconds", 0)
    rpo_b = run_b.get("rpo_seconds", 0)
    rto_target = run_b.get("rto_target", 300)

    report_a = data.get("report_a") or {}
    report_b = data.get("report_b") or {}
    health_a = report_a.get("health_checks", {})
    health_b = report_b.get("health_checks", {})

    # ── Score Regression ──
    if score_b < score_a:
        delta = score_a - score_b
        severity = "critical" if delta > 30 else "high" if delta > 15 else "medium"
        findings.append({
            "category": "score_regression",
            "severity": severity,
            "title": f"Resilience score dropped by {delta} points ({score_a} → {score_b})",
            "why_it_matters": f"A {delta}-point drop means your system's ability to recover from failures has significantly degraded. What worked before may not work now.",
            "root_cause": "Score regressions are caused by: (1) Infrastructure changes that broke Auto Scaling or health checks. (2) New application code that increases startup time. (3) Configuration drift — manual changes to security groups, subnets, or ALB settings. (4) Dependency changes — database or cache moved to a different region/AZ.",
            "fix_steps": [
                "1. Compare infrastructure between runs: Check CloudTrail for any changes between run_a and run_b timestamps.",
                "2. Review Auto Scaling group settings — verify desired/min/max haven't changed.",
                "3. Check ALB target group health — are all targets healthy?",
                "4. Review recent code deployments — did startup time increase?",
                "5. Check security groups — are outbound rules still correct?",
                "6. Run 'terraform plan' to detect infrastructure drift."
            ],
            "estimated_effort": "hours",
            "prevention": "Use infrastructure-as-code. Never make manual changes to production infrastructure."
        })

    # ── RTO Regression ──
    if rto_b > rto_a and rto_b > rto_target:
        findings.append({
            "category": "rto_regression",
            "severity": "critical",
            "title": f"Recovery time regressed: {rto_a}s → {rto_b}s (target: {rto_target}s)",
            "why_it_matters": f"Recovery now takes {rto_b - rto_a}s longer than before. If this trend continues, recovery may eventually exceed the target by a dangerous margin.",
            "root_cause": "RTO increases over time are typically caused by: (1) Application growing — more dependencies to initialize on startup. (2) Database getting larger — backup/restore takes longer. (3) AMI not updated — packages need updating on launch. (4) Network latency increasing — new AZ or region added.",
            "fix_steps": [
                "1. Compare startup logs between runs — identify what takes longer now.",
                "2. Profile application startup — which dependency is slowest?",
                "3. Update the AMI — rebuild with current packages.",
                "4. Check if database size has grown significantly.",
                "5. Consider a warm pool to eliminate cold start time."
            ],
            "estimated_effort": "hours",
            "prevention": "Monitor RTO trend monthly. Set alert if RTO increases by >20%."
        })

    # ── Status Regression (Passed → Failed) ──
    if run_a.get("status") == "Passed" and run_b.get("status") == "Failed":
        findings.append({
            "category": "status_regression",
            "severity": "critical",
            "title": "Test went from PASSED to FAILED — system reliability degraded",
            "why_it_matters": "Your DR setup was working and now it's broken. This means a real disaster right now would result in extended downtime.",
            "root_cause": "This is the most critical finding — something changed that broke your disaster recovery capability. Common causes: (1) Auto Scaling group was modified or deleted. (2) AMI was deregistered or became unavailable. (3) Security group rules changed, blocking recovery traffic. (4) IAM role lost permissions needed for instance launch. (5) AWS service limit was reached.",
            "fix_steps": [
                "1. This is URGENT — treat it as a production incident.",
                "2. Check CloudTrail for any IAM, EC2, or Auto Scaling changes between runs.",
                "3. Verify Auto Scaling group exists and has correct launch template.",
                "4. Test manual instance launch from the AMI — does it work?",
                "5. Check IAM role permissions — can the Auto Scaling service assume the role?",
                "6. Check AWS service limits — have you hit the EC2 instance limit for your account?",
                "7. Fix the issue and run the test again IMMEDIATELY."
            ],
            "estimated_effort": "hours",
            "prevention": "Set up AWS Config rules to alert on Auto Scaling or security group changes."
        })

    # ── Health Check Regressions ──
    if not health_b.get("https_valid") and health_a.get("https_valid"):
        findings.append({
            "category": "https_regression",
            "severity": "critical",
            "title": "HTTPS validity lost between runs",
            "why_it_matters": "The SSL certificate was valid during run_a but is now invalid. This means users are currently seeing security warnings.",
            "root_cause": "SSL certificate expired. ACM certificates auto-renew, but renewal can fail if DNS validation records are missing.",
            "fix_steps": [
                "1. Check ACM certificate status: aws acm list-certificates",
                "2. If pending validation, add the CNAME record to Route 53.",
                "3. If expired, request a new certificate.",
                "4. Update the ALB/CloudFront listener with the new certificate ARN.",
                "5. Set up CloudWatch alarm for certificate expiry at 30 days."
            ],
            "estimated_effort": "minutes",
            "prevention": "Monitor certificate expiry. Use ACM with DNS validation."
        })

    if not health_b.get("dns_failover_ok") and health_a.get("dns_failover_ok"):
        findings.append({
            "category": "dns_failover_regression",
            "severity": "critical",
            "title": "DNS failover stopped working between runs",
            "why_it_matters": "Your DNS failover was routing traffic to a healthy instance during failures. Now it's broken — traffic will go to a dead instance.",
            "root_cause": "DNS failover breaks when: (1) Route 53 health check was deleted. (2) Secondary record was removed. (3) Health check is marking healthy instances as unhealthy (too aggressive thresholds).",
            "fix_steps": [
                "1. Check Route 53 health check status in the console.",
                "2. Verify the failover routing policy is still set on the primary record.",
                "3. Verify the secondary record exists and points to the standby.",
                "4. Test failover manually by stopping the primary instance.",
                "5. Check health check logs in CloudWatch."
            ],
            "estimated_effort": "minutes",
            "prevention": "Test failover monthly. Set up Route 53 health check alarms."
        })

    return findings


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def analyze_report(report_type, report_data):
    """Main entry point — dispatches to the correct analyzer."""
    if report_type == "dr-test":
        return analyze_dr_test(report_data)
    elif report_type == "seo":
        return analyze_seo(report_data)
    elif report_type == "competitor":
        return analyze_competitor(report_data)
    elif report_type == "comparison":
        return analyze_comparison(report_data)
    return []
