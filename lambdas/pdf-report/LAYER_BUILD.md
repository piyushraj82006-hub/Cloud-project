# PDF Report Lambda — Build Instructions

WeasyPrint requires system-level libraries (cairo, pango, gdk-pixbuf) that are **not** included in Lambda's Amazon Linux 2 runtime. You have two options:

## Option 1: Docker Container Image (Recommended)

This is the most reliable approach. Build a custom Lambda container with all dependencies.

### 1. Create Dockerfile

```dockerfile
# lambdas/pdf-report/Dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies for weasyprint
RUN yum install -y \
    pango \
    cairo \
    gdk-pixbuf2 \
    libffi \
    libjpeg-turbo \
    zlib \
    && yum clean all

# Install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda handler
COPY handler.py root_cause_analyzer.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.lambda_handler"]
```

### 2. Build and push to ECR

```bash
# From project root
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)
REPO_NAME="cloudguard-pdf-report"

# Create ECR repository (once)
aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $REGION

# Build image
docker build --platform linux/amd64 \
  -t $REPO_NAME \
  -f lambdas/pdf-report/Dockerfile \
  lambdas/pdf-report/

# Authenticate and push
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker tag $REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
```

### 3. Update Terraform

Change the pdf-report Lambda from zip-based to container image:

```hcl
# terraform/modules/lambda/main.tf — replace the pdf_report resource

resource "aws_ecr_repository" "pdf_report" {
  name                 = "cloudguard-pdf-report"
  image_tag_mutability = "MUTABLE"
}

resource "aws_lambda_function" "pdf_report" {
  function_name = "${local.name_prefix}-pdf-report"
  role          = var.pdf_report_role_arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.pdf_report.repository_url}:latest"
  timeout       = 120
  memory_size   = 512

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      AWS_REGION          = var.aws_region
      REPORTS_BUCKET      = var.reports_bucket_id
      AUDIT_REPORTS_TABLE = var.audit_reports_table_name
    }
  }
}
```

### 4. Update pipeline after each code change

```bash
# Rebuild and push
docker build --platform linux/amd64 -t cloudguard-pdf-report -f lambdas/pdf-report/Dockerfile lambdas/pdf-report/
docker tag cloudguard-pdf-report:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/cloudguard-pdf-report:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/cloudguard-pdf-report:latest

# Update Lambda to use new image
aws lambda update-function-code \
  --function-name cloudguard-dev-pdf-report \
  --image-uri $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/cloudguard-pdf-report:latest
```

---

## Option 2: Lambda Layer with Pre-built Binaries

More complex, but keeps the zip-based deployment.

### Build using Docker (Amazon Linux 2)

```bash
#!/bin/bash
# lambdas/pdf-report/build-layer.sh
set -e

LAYER_DIR="layer"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python/lib/python3.12/site-packages

# Use Amazon Linux 2 Docker image to build compatible binaries
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
cd $LAYER_DIR
zip -r ../weasyprint-layer.zip python/
cd ..

# Publish to AWS
aws lambda publish-layer-version \
  --layer-name cloudguard-weasyprint \
  --zip-file fileb://weasyprint-layer.zip \
  --compatible-runtimes python3.12 \
  --description "Weasyprint 62.3 with cairo/pango for PDF generation"

echo "Layer published. Update pdf_report_layer_arn in terraform.tfvars"
```

### Get the layer ARN

```bash
aws lambda list-layer-versions \
  --layer-name cloudguard-weasyprint \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text
```

### Set in terraform.tfvars

```hcl
pdf_report_layer_arn = "arn:aws:lambda:us-east-1:123456789:layer:cloudguard-weasyprint:1"
```

---

## Option 3: No Layer (HTML Fallback)

If you skip both options above, the Lambda **still works** — it returns a print-optimized HTML file instead of a PDF. Users can open it in a browser and print to PDF (Ctrl+P → Save as PDF).

The handler already handles this gracefully:

```python
try:
    from weasyprint import HTML
    pdf_bytes = HTML(string=html).write_pdf()
except ImportError:
    # Returns HTML fallback — no error
    return { "format": "html_fallback", ... }
```

**This is fine for MVP.** Add the container/layer when you need actual PDF files.

---

## Recommendation

| Approach | Effort | Reliability | Best For |
|----------|--------|-------------|----------|
| Docker container | Medium | High | Production |
| Lambda layer | High | Medium | If you need zip-based Lambda |
| HTML fallback | None | High | MVP / development |

**Start with Option 3 (HTML fallback).** Switch to Option 1 (Docker container) when you need branded PDFs in production.
