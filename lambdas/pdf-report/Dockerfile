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

# Copy Lambda handler and analyzer
COPY handler.py root_cause_analyzer.py ${LAMBDA_TASK_ROOT}/

CMD ["handler.lambda_handler"]
