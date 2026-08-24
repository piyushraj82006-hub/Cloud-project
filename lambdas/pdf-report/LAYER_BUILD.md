# PDF Report Lambda Layer

This Lambda requires a `weasyprint` layer for HTML-to-PDF conversion.

## Build the Layer (Amazon Linux 2)

```bash
# On Amazon Linux 2 or use Docker
mkdir -p layer/python/lib/python3.12/site-packages

# Install weasyprint and dependencies into the layer
pip install \
  --platform manylinux2014_x86_64 \
  --only-binary=:all: \
  --target layer/python/lib/python3.12/site-packages \
  --python-version 3.12 \
  weasyprint==62.3

# Package the layer
cd layer
zip -r ../weasyprint-layer.zip python/
cd ..

# Publish the layer (update ARN in terraform)
aws lambda publish-layer-version \
  --layer-name cloudguard-weasyprint \
  --zip-file fileb://weasyprint-layer.zip \
  --compatible-runtimes python3.12 \
  --description "Weasyprint 62.3 for PDF generation"
```

## Alternative: Pure HTML Fallback

If weasyprint is not available, the Lambda will automatically fall back to
returning an HTML file instead of a PDF. The HTML is print-optimized with
`@page` CSS rules, so users can open it in a browser and print to PDF.

## Dependencies

The layer includes:
- `weasyprint` (HTML/CSS to PDF renderer)
- `pydyf` (PDF generation library)
- `tinycss2` (CSS parser)
- `cssselect2` (CSS selector engine)
- `urllib3`, `certifi`, `charset-normalizer`

All are pure-Python or have manylinux wheels, so they work on Lambda's
Amazon Linux 2 runtime.
