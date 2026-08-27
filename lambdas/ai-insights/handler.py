"""
CloudGuard DR — AI Insights Lambda (OpenRouter)
Reads existing audit report JSON from S3, sends it to an AI model via OpenRouter
for strategic analysis, failure highlighting, and improvement scopes.
Writes enriched insights back to S3.
Optional — skips gracefully if no API key is set.
"""
import os
import json
import time
import urllib.request
import urllib.error
import boto3

s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")
dynamodb = boto3.resource("dynamodb")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
REPORTS_BUCKET = os.environ.get("REPORTS_BUCKET", f"cloudguard-{ENVIRONMENT}-reports")
AUDIT_REPORTS_TABLE = os.environ.get("AUDIT_REPORTS_TABLE", f"cloudguard-{ENVIRONMENT}-audit-reports")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "llama3-70b-8192")
OPENROUTER_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_api_key():
    """Get API key from env var or SSM Parameter Store."""
    if OPENROUTER_API_KEY:
        return OPENROUTER_API_KEY
    try:
        param = ssm_client.get_parameter(
            Name=f"/cloudguard/{ENVIRONMENT}/openrouter-api-key",
            WithDecryption=True
        )
        return param["Parameter"]["Value"]
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════════

SEO_INSIGHTS_PROMPT = """You are an expert SEO strategist. Analyze this SEO audit report data and provide actionable insights.

For each failing check, explain:
1. WHY it matters (business impact)
2. WHAT likely caused it (root cause)
3. HOW to fix it (specific steps)
4. SCOPE of improvement (quick win vs long-term project)

Also provide:
- Executive summary (2-3 sentences)
- Top 3 critical actions with implementation guidance
- 90-day roadmap (Week 1-2, Month 1, Month 2-3)
- Competitive advantage opportunities

Report data:
{report_data}

Respond in JSON format:
{{
  "executive_summary": "...",
  "critical_actions": [
    {{"action": "...", "impact": "high|medium", "implementation": "...", "effort": "minutes|hours|days"}}
  ],
  "failure_analysis": [
    {{
      "check": "...",
      "why_it_matters": "...",
      "root_cause": "...",
      "fix_steps": ["..."],
      "scope": "quick_win|medium_project|major_initiative",
      "estimated_impact": "..."
    }}
  ],
  "improvement_scopes": {{
    "quick_wins": ["..."],
    "medium_projects": ["..."],
    "major_initiatives": ["..."]
  }},
  "roadmap": {{
    "week_1_2": ["..."],
    "month_1": ["..."],
    "month_2_3": ["..."]
  }},
  "opportunities": [
    {{"title": "...", "description": "...", "effort": "low|medium|high"}}
  ]
}}"""

COMPETITOR_INSIGHTS_PROMPT = """You are an expert competitive analyst. Analyze this competitor data and provide strategic insights.

For each weakness/gap, explain:
1. WHY competitors with this feature outperform you
2. WHAT is the root cause of the gap
3. HOW to close the gap (specific steps)
4. SCOPE (quick win vs strategic initiative)

Also provide:
- Executive summary (2-3 sentences)
- Top 3 winning strategies
- Defensive measures against competitor moves
- Market opportunity analysis

Competitor data:
{report_data}

Respond in JSON format:
{{
  "executive_summary": "...",
  "winning_strategies": [
    {{"strategy": "...", "expected_impact": "...", "timeline": "...", "effort": "low|medium|high"}}
  ],
  "failure_analysis": [
    {{
      "gap": "...",
      "why_it_matters": "...",
      "root_cause": "...",
      "fix_steps": ["..."],
      "scope": "quick_win|medium_project|major_initiative"
    }}
  ],
  "improvement_scopes": {{
    "quick_wins": ["..."],
    "medium_projects": ["..."],
    "major_initiatives": ["..."]
  }},
  "defensive_measures": [
    {{"threat": "...", "mitigation": "..."}}
  ],
  "market_opportunity": "..."
}}"""

DR_INSIGHTS_PROMPT = """You are an expert in disaster recovery and infrastructure resilience. Analyze this DR test report and provide insights.

For each failure, explain:
1. WHY it matters (business impact, SLA risk)
2. WHAT likely caused it (infrastructure root cause)
3. HOW to fix it (specific AWS configuration steps)
4. SCOPE of the fix (quick config change vs architecture redesign)

Also provide:
- Executive summary (2-3 sentences)
- Root cause analysis for all failures
- Remediation steps prioritized by impact
- Architecture recommendations

DR test data:
{report_data}

Respond in JSON format:
{{
  "executive_summary": "...",
  "root_cause_analysis": ["..."],
  "failure_analysis": [
    {{
      "issue": "...",
      "why_it_matters": "...",
      "root_cause": "...",
      "fix_steps": ["..."],
      "scope": "quick_win|medium_project|major_initiative",
      "aws_services_involved": ["..."]
    }}
  ],
  "improvement_scopes": {{
    "quick_wins": ["..."],
    "medium_projects": ["..."],
    "major_initiatives": ["..."]
  }},
  "remediation_steps": [
    {{"step": "...", "priority": "critical|high|medium", "effort": "..."}}
  ],
  "architecture_recommendations": ["..."]
}}"""

COMPARISON_INSIGHTS_PROMPT = """You are an expert in infrastructure resilience. Analyze this run comparison and provide insights.

For each regression, explain:
1. WHY it degraded (what changed)
2. WHAT infrastructure or code change likely caused it
3. HOW to recover (specific steps)
4. SCOPE of the fix

Also provide:
- Executive summary (2-3 sentences)
- Regression analysis
- Improvement actions

Comparison data:
{report_data}

Respond in JSON format:
{{
  "executive_summary": "...",
  "failure_analysis": [
    {{
      "regression": "...",
      "why_it_matters": "...",
      "likely_cause": "...",
      "fix_steps": ["..."],
      "scope": "quick_win|medium_project|major_initiative"
    }}
  ],
  "improvement_scopes": {{
    "quick_wins": ["..."],
    "medium_projects": ["..."],
    "major_initiatives": ["..."]
  }},
  "regression_analysis": ["..."],
  "improvement_actions": [
    {{"action": "...", "priority": "critical|high|medium"}}
  ]
}}"""


def lambda_handler(event, context):
    """
    Generate AI-powered insights for an audit report via OpenRouter.

    Event input (from Step Functions, after Report step):
        {
            "run_id": "run-abc123",
            "report_id": "report-abc123",
            "statusCode": 200,
            "s3_key": "reports/run-abc123/report.json",
            ... (all fields from audit-report output)
        }
    """
    print(f"[AIInsights] Starting. Event: {json.dumps(event)}")

    api_key = get_api_key()
    if not api_key:
        print("[AIInsights] No API key set — skipping AI insights")
        return {
            **event,
            "ai_insights": None,
            "ai_enriched": False,
            "ai_skip_reason": "No API key configured",
        }

    try:
        run_id = event.get("run_id", "")
        report_type = event.get("report_type", "dr-test")

        # Determine S3 key for the report
        s3_key = event.get("s3_key", "")
        if not s3_key:
            s3_key = find_report_key(report_type, run_id, event)

        if not s3_key:
            print(f"[AIInsights] No report found for {report_type}/{run_id}")
            return {
                **event,
                "ai_insights": None,
                "ai_enriched": False,
                "ai_skip_reason": "Report not found",
            }

        # Fetch report JSON
        report_data = fetch_json_report(s3_key)
        if not report_data:
            return {
                **event,
                "ai_insights": None,
                "ai_enriched": False,
                "ai_skip_reason": "Could not parse report JSON",
            }

        # Select prompt based on report type
        prompt_template = {
            "seo": SEO_INSIGHTS_PROMPT,
            "competitor": COMPETITOR_INSIGHTS_PROMPT,
            "dr-test": DR_INSIGHTS_PROMPT,
            "comparison": COMPARISON_INSIGHTS_PROMPT,
        }.get(report_type)

        if not prompt_template:
            print(f"[AIInsights] Unknown report type: {report_type}")
            return {
                **event,
                "ai_insights": None,
                "ai_enriched": False,
                "ai_skip_reason": f"Unknown type: {report_type}",
            }

        # Call OpenRouter API
        prompt = prompt_template.format(report_data=json.dumps(report_data, indent=2))
        ai_response = call_openrouter(prompt, api_key)

        if not ai_response:
            return {
                **event,
                "ai_insights": None,
                "ai_enriched": False,
                "ai_skip_reason": "OpenRouter API call failed",
            }

        # Parse AI response
        insights = parse_ai_response(ai_response)

        # Write enriched report back to S3
        report_data["ai_insights"] = insights
        enriched_key = s3_key.replace("report.json", "report-enriched.json")
        s3_client.put_object(
            Bucket=REPORTS_BUCKET,
            Key=enriched_key,
            Body=json.dumps(report_data, indent=2),
            ContentType="application/json",
        )

        # Update DynamoDB with enriched key
        update_enriched_key(run_id, enriched_key)

        result = {
            **event,
            "ai_insights": insights,
            "ai_enriched": True,
            "ai_enriched_key": enriched_key,
        }

        print(f"[AIInsights] AI insights generated for {report_type}/{run_id}")
        return result

    except Exception as e:
        print(f"[AIInsights] Error: {str(e)}")
        return {
            **event,
            "ai_insights": None,
            "ai_enriched": False,
            "ai_skip_reason": str(e),
        }


def find_report_key(report_type, run_id, event):
    """Find the report JSON key in S3."""
    if report_type == "dr-test":
        return f"reports/{run_id}/report.json"
    elif report_type == "seo":
        report_id = event.get("report_id", run_id)
        return f"seo-reports/{report_id}/report.json"
    elif report_type == "competitor":
        report_id = event.get("report_id", run_id)
        return f"competitor-analysis/{report_id}/report.json"
    elif report_type == "comparison":
        return f"reports/{run_id}/report.json"
    return None


def fetch_json_report(s3_key):
    """Fetch and parse a JSON report from S3."""
    try:
        response = s3_client.get_object(Bucket=REPORTS_BUCKET, Key=s3_key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except Exception as e:
        print(f"[AIInsights] Failed to fetch {s3_key}: {e}")
        return None


def call_openrouter(prompt, api_key):
    """Call OpenRouter API (OpenAI-compatible format)."""
    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert technical analyst. Always respond with valid JSON only, no markdown code blocks."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
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
        response = urllib.request.urlopen(req, timeout=60)
        body = json.loads(response.read().decode("utf-8"))
        text = body["choices"][0]["message"]["content"]
        return text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[AIInsights] OpenRouter API error {e.code}: {error_body}")
        return None
    except Exception as e:
        print(f"[AIInsights] OpenRouter API call failed: {e}")
        return None


def parse_ai_response(text):
    """Parse AI response into structured insights."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    import re
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return {"raw_response": text}


def update_enriched_key(run_id, enriched_key):
    """Update DynamoDB with the enriched report key."""
    try:
        table = dynamodb.Table(AUDIT_REPORTS_TABLE)
        table.update_item(
            Key={"run_id": run_id},
            UpdateExpression="SET ai_enriched_key = :key",
            ExpressionAttributeValues={":key": enriched_key},
        )
    except Exception as e:
        print(f"[AIInsights] Warning: Could not update DynamoDB: {e}")
