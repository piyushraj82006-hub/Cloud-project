#!/bin/bash
# Build weasyprint Lambda layer using Docker (Amazon Linux 2)
set -e

LAYER_DIR="layer"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python/lib/python3.12/site-packages

echo "Building weasyprint layer in Docker..."

docker run --rm -v "$(pwd):/build" -w /build \
  public.ecr.aws/lambda/python:3.12 \
  bash -c "
    # Install system deps
    yum install -y pango cairo gdk-pixbuf2 libffi libjpeg-turbo zlib

    # Install weasyprint + deps into layer directory
    pip install \
      --target /build/layer/python/lib/python3.12/site-packages \
      weasyprint==62.3

    # Copy system libraries needed by weasyprint
    mkdir -p /build/layer/python/lib
    cp /usr/lib64/libpango-1.0.so.0 /build/layer/python/lib/ 2>/dev/null || true
    cp /usr/lib64/libpangocairo-1.0.so.0 /build/layer/python/lib/ 2>/dev/null || true
    cp /usr/lib64/libcairo.so.2 /build/layer/python/lib/ 2>/dev/null || true
    cp /usr/lib64/libgdk_pixbuf-2.0.so.0 /build/layer/python/lib/ 2>/dev/null || true
    cp /usr/lib64/libffi.so.6 /build/layer/python/lib/ 2>/dev/null || true
  "

# Package
echo "Packaging layer..."
cd $LAYER_DIR
zip -r ../weasyprint-layer.zip python/
cd ..

echo "Layer built: weasyprint-layer.zip ($(du -h weasyprint-layer.zip | cut -f1))"

# Publish to AWS (optional — pass --publish to upload)
if [ "$1" = "--publish" ]; then
  echo "Publishing to AWS Lambda..."
  aws lambda publish-layer-version \
    --layer-name cloudguard-weasyprint \
    --zip-file fileb://weasyprint-layer.zip \
    --compatible-runtimes python3.12 \
    --description "Weasyprint 62.3 with cairo/pango for PDF generation"

  LAYER_ARN=$(aws lambda list-layer-versions \
    --layer-name cloudguard-weasyprint \
    --query 'LayerVersions[0].LayerVersionArn' \
    --output text)

  echo "Layer published: $LAYER_ARN"
  echo "Add to terraform.tfvars:"
  echo "  pdf_report_layer_arn = \"$LAYER_ARN\""
else
  echo "Skipping publish. Run with --publish to upload to AWS."
fi
