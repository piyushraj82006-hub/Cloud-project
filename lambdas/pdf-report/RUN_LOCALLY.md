# Run PDF Generation Locally (No Lambda)

Generate SEO audit PDFs with AI-powered weak points analysis on your machine.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-local.txt

# 2. Set your OpenRouter API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# 3. Run it
python generate_pdf.py https://example.com
```

## What It Does

```
URL → Fetch page → SEO analysis → OpenRouter AI → PDF with weak points
```

1. Fetches the target URL and runs SEO checks (title, meta, headings, images, OG tags, etc.)
2. Sends the report to Claude via OpenRouter for AI-powered weak point analysis
3. Generates a branded PDF with:
   - Cover page (dark gradient, green accent)
   - Executive summary with stat cards
   - ⚠ Weak points section (AI-generated, severity-coded)
   - Full audit table (PASS/FAIL badges)
   - Prioritized recommendations
   - Root cause analysis per failure

## Output

```
lambdas/pdf-report/output/
├── seo-a1b2c3d4.pdf    ← branded PDF report
└── seo-a1b2c3d4.json   ← raw report data + AI insights
```

## Options

```bash
# Custom output directory
python generate_pdf.py https://example.com /tmp/reports

# Use different model
export OPENROUTER_MODEL="anthropic/claude-sonnet-4"
python generate_pdf.py https://example.com

# Without AI (rule-based only)
unset OPENROUTER_API_KEY
python generate_pdf.py https://example.com
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | (none) | OpenRouter API key for AI analysis |
| `OPENROUTER_MODEL` | `anthropic/claude-sonnet-4` | AI model to use |
| `PDF_OUTPUT_DIR` | `./output` | Where to save generated PDFs |
