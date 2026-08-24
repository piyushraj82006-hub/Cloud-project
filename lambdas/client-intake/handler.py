"""
CloudGuard DR — Client Intake Lambda
Accepts client business information, classifies the business model
(B2C Local, B2C Regional, B2B Multi-State), determines SEO strategy,
and stores everything in DynamoDB for use by other audit lambdas.
"""
import os
import json
import time
import uuid
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
CLIENTS_TABLE = os.environ.get("CLIENTS_TABLE", f"cloudguard-{ENVIRONMENT}-clients")


def lambda_handler(event, context):
    """
    Handle client intake: create, get, or list clients.

    POST /clients         — Create new client intake
    GET  /clients/{id}    — Get client by ID
    GET  /clients         — List all clients

    Event input (POST):
        {
            "business_name": "Acme Plumbing",
            "url": "https://acmeplumbing.com",
            "industry": "plumbing",
            "primary_city": "Austin",
            "state": "TX",
            "neighborhoods": ["Downtown", "East Austin", "South Austin"],
            "service_radius_miles": 25,
            "geographic_scope": "city",
            "business_type": "b2c",
            "agency_name": "Growth Agency",
            "client_email": "client@example.com",
            "known_competitors": ["https://competitor1.com"],
            "has_gbp": true,
            "gbp_review_count": 127,
            "launch_status": "live",
            "old_domain": null,
            "notes": "Fast-growing local plumbing company"
        }
    """
    print(f"[ClientIntake] Event: {json.dumps(event)}")

    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/clients")
    body = event.get("body")
    if body and isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            body = {}

    table = dynamodb.Table(CLIENTS_TABLE)

    try:
        if http_method == "POST" and body:
            return create_client(table, body)
        elif http_method == "GET" and "{client_id}" in path:
            client_id = event.get("pathParameters", {}).get("client_id", "")
            return get_client(table, client_id)
        elif http_method == "GET":
            return list_clients(table)
        else:
            return response(400, {"error": "Invalid request"})
    except Exception as e:
        print(f"[ClientIntake] Error: {str(e)}")
        raise


def create_client(table, data):
    """Create a new client intake record with business classification."""
    client_id = f"client-{uuid.uuid4().hex[:8]}"

    # Validate required fields
    url = data.get("url", "").strip()
    business_name = data.get("business_name", "").strip()
    industry = data.get("industry", "").strip()
    primary_city = data.get("primary_city", "").strip()

    if not url:
        return response(400, {"error": "url is required"})
    if not business_name:
        return response(400, {"error": "business_name is required"})

    # Upgrade HTTP to HTTPS
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)

    # Classify business model
    classification = classify_business(data)

    # Determine SEO strategy based on classification
    seo_strategy = determine_seo_strategy(classification, data)

    # Build client record
    client = {
        "client_id": client_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "business_name": business_name,
        "url": url,
        "industry": industry,
        "primary_city": primary_city,
        "state": data.get("state", ""),
        "neighborhoods": data.get("neighborhoods", []),
        "service_radius_miles": data.get("service_radius_miles", 0),
        "geographic_scope": classification["geographic_scope"],
        "business_type": classification["business_type"],
        "classification": classification,
        "seo_strategy": seo_strategy,
        "agency_name": data.get("agency_name", ""),
        "client_email": data.get("client_email", ""),
        "known_competitors": data.get("known_competitors", []),
        "has_gbp": data.get("has_gbp", False),
        "gbp_review_count": data.get("gbp_review_count", 0),
        "launch_status": data.get("launch_status", "live"),
        "old_domain": data.get("old_domain"),
        "notes": data.get("notes", ""),
    }

    # Store in DynamoDB
    table.put_item(Item=client)

    print(f"[ClientIntake] Created client: {client_id} ({classification['business_type']}/{classification['geographic_scope']})")

    return response(201, {
        "client_id": client_id,
        "business_name": business_name,
        "classification": classification,
        "seo_strategy": seo_strategy,
        "created_at": client["created_at"],
    })


def get_client(table, client_id):
    """Get a client by ID."""
    result = table.get_item(Key={"client_id": client_id})
    item = result.get("Item")
    if not item:
        return response(404, {"error": "Client not found"})
    return response(200, item)


def list_clients(table):
    """List all clients."""
    result = table.scan()
    items = result.get("Items", [])
    # Sort by created_at descending
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return response(200, {"clients": items, "count": len(items)})


def classify_business(data):
    """
    Classify the business into a model based on intake answers.

    Returns:
        {
            "business_type": "b2c" | "b2b",
            "geographic_scope": "city" | "regional" | "multi-state",
            "classification": "B2C Local" | "B2C Regional" | "B2B Multi-State",
            "signals": [...],
            "location_page_strategy": "...",
            "keyword_tier_strategy": "..."
        }
    """
    industry = data.get("industry", "").lower()
    city = data.get("primary_city", "")
    state = data.get("state", "")
    neighborhoods = data.get("neighborhoods", [])
    radius = data.get("service_radius_miles", 0)
    geo_scope = data.get("geographic_scope", "").lower()
    known_competitors = data.get("known_competitors", [])

    signals = []

    # Determine geographic scope
    if geo_scope == "multi-state" or geo_scope == "national":
        scope = "multi-state"
        signals.append("Multi-state geographic scope selected")
    elif geo_scope == "regional" or radius > 50:
        scope = "regional"
        signals.append(f"Regional scope (radius: {radius} miles)")
    else:
        scope = "city"
        signals.append(f"City-level scope ({city})")

    # Determine business type from signals
    b2b_signals = [
        "property management" in industry,
        "commercial" in industry,
        "contractor" in industry and "residential" not in industry,
        "B2B" in data.get("business_type", "").upper(),
        scope == "multi-state",
    ]

    b2b_count = sum(1 for s in b2b_signals if s)
    is_b2b = b2b_count >= 2 or scope == "multi-state"

    if is_b2b:
        business_type = "b2b"
        if scope == "multi-state":
            classification = "B2B Multi-State"
            location_strategy = "One page per major market city"
            keyword_strategy = "National + state-level service keywords"
        else:
            classification = "B2B Regional"
            location_strategy = "City pages for each service area"
            keyword_strategy = "Regional service + industry keywords"
        signals.append("Classified as B2B based on industry/scope signals")
    else:
        business_type = "b2c"
        if scope == "regional":
            classification = "B2C Regional"
            location_strategy = "City pages + neighborhood pages"
            keyword_strategy = "City-level + neighborhood keywords"
        else:
            classification = "B2C Local"
            if neighborhoods:
                location_strategy = f"Neighborhood pages for: {', '.join(neighborhoods)}"
                keyword_strategy = "City + neighborhood long-tail keywords"
            else:
                location_strategy = "City page + suburb discovery during recon"
                keyword_strategy = "City-level service keywords"
        signals.append("Classified as B2C local service business")

    # Add neighborhood signals
    if neighborhoods:
        signals.append(f"Neighborhoods identified: {', '.join(neighborhoods)}")

    # Add competitor signals
    if known_competitors:
        signals.append(f"{len(known_competitors)} known competitors provided")
    else:
        signals.append("No known competitors — auto-discovery will be used")

    return {
        "business_type": business_type,
        "geographic_scope": scope,
        "classification": classification,
        "signals": signals,
        "location_page_strategy": location_strategy,
        "keyword_tier_strategy": keyword_strategy,
    }


def determine_seo_strategy(classification, data):
    """
    Determine the recommended SEO strategy based on business classification.

    Returns specific, actionable recommendations based on the skill framework.
    """
    biz_type = classification["business_type"]
    scope = classification["geographic_scope"]
    city = data.get("primary_city", "")
    industry = data.get("industry", "")
    neighborhoods = data.get("neighborhoods", [])
    has_gbp = data.get("has_gbp", False)

    strategy = {
        "keyword_tiers": [],
        "content_priorities": [],
        "location_page_plan": [],
        "technical_priorities": [],
    }

    # ─── Keyword Tiers ─────────────────────────────────────────────

    # Tier 1: Core service + city
    strategy["keyword_tiers"].append({
        "tier": 1,
        "name": "Core Local",
        "intent": "Mixed",
        "examples": [
            f"{industry} {city}",
            f"{industry} services {city}",
            f"best {industry} {city}",
            f"{industry} near me",
        ],
        "target_page": "Homepage / main service page",
    })

    # Tier 2: Neighborhood / suburb keywords
    tier2_keywords = []
    if neighborhoods:
        for hood in neighborhoods:
            tier2_keywords.extend([
                f"{industry} {hood}",
                f"{industry} in {hood} {city}",
            ])
    tier2_keywords.extend([
        f"{industry} {city} area",
        f"affordable {industry} {city}",
    ])
    strategy["keyword_tiers"].append({
        "tier": 2,
        "name": "Local/Neighborhood",
        "intent": "Transactional",
        "examples": tier2_keywords[:6],
        "target_page": "Location / neighborhood pages",
    })

    # Tier 3: Long-tail high-intent
    strategy["keyword_tiers"].append({
        "tier": 3,
        "name": "Long-Tail High-Intent",
        "intent": "Transactional",
        "examples": [
            f"{industry} cost {city}",
            f"{industry} prices near me",
            f"emergency {industry} {city}",
            f"{industry} reviews {city}",
            f"how much does {industry} cost {city}",
        ],
        "target_page": "Pricing page, service pages, blog",
    })

    # Tier 4: Informational / blog
    strategy["keyword_tiers"].append({
        "tier": 4,
        "name": "Informational / Blog",
        "intent": "Informational",
        "examples": [
            f"how to choose a {industry} in {city}",
            f"{industry} tips for {city} homeowners",
            f"signs you need a {industry}",
            f"{industry} maintenance guide",
        ],
        "target_page": "Blog posts",
    })

    # ─── Content Priorities ────────────────────────────────────────

    strategy["content_priorities"] = [
        {"priority": 1, "action": "Ensure service pages exist for each core service"},
        {"priority": 2, "action": f"Build location pages for {city} and surrounding areas"},
    ]

    if not has_gbp:
        strategy["content_priorities"].append(
            {"priority": 3, "action": "Set up and optimize Google Business Profile"}
        )

    if not data.get("has_pricing"):
        strategy["content_priorities"].append(
            {"priority": 4, "action": "Create a pricing page or cost estimator"}
        )

    strategy["content_priorities"].extend([
        {"priority": 5, "action": "Add testimonials with customer locations"},
        {"priority": 6, "action": "Launch blog with 2-4 posts per month"},
        {"priority": 7, "action": "Build FAQ pages for common customer questions"},
    ])

    # ─── Location Page Plan ────────────────────────────────────────

    if neighborhoods:
        for hood in neighborhoods:
            strategy["location_page_plan"].append({
                "page": f"{hood} {industry.title()}",
                "url": f"/locations/{hood.lower().replace(' ', '-')}",
                "keywords": [f"{industry} {hood}", f"{industry} in {hood}"],
            })

    strategy["location_page_plan"].append({
        "page": f"{city} {industry.title()}",
        "url": f"/locations/{city.lower().replace(' ', '-')}",
        "keywords": [f"{industry} {city}", f"best {industry} {city}"],
    })

    # ─── Technical Priorities ──────────────────────────────────────

    strategy["technical_priorities"] = [
        "Add LocalBusiness JSON-LD schema to homepage",
        "Ensure mobile viewport meta tag is present",
        "Add canonical URLs to all pages",
        "Create and submit XML sitemap",
        "Set up Google Search Console",
    ]

    if not has_gbp:
        strategy["technical_priorities"].append(
            "Verify Google Business Profile and ensure NAP consistency"
        )

    return strategy


def response(status_code, body):
    """Build an API Gateway-compatible response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }
