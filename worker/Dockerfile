
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/model-cache \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install CPU-only PyTorch to avoid downloading NVIDIA CUDA libraries
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.4.1+cpu

# Install application dependencies
RUN pip install --no-cache-dir \
    pika==1.3.2 \
    transformers==4.44.2

COPY worker.py .

# Run as a non-root user
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/model-cache \
    && chown -R appuser:appuser /app

USER 10001

CMD ["python", "-u", "worker.py"]

