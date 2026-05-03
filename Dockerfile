# ═══════════════════════════════════════════════════════════════════════════
# WasteWise AI — Multi-stage Dockerfile
# Stage 1: builder (installs heavy ML deps)
# Stage 2: runtime (slim production image)
# ═══════════════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps for Pillow & PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="WasteWise AI Project"
LABEL description="AI-Based Waste Detection with Generative AI — SDG 11, 12, 13"
LABEL version="1.0.0"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# System runtime libs only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY app/         ./app/
COPY templates/   ./templates/
COPY static/      ./static/
COPY main.py      .

# Create directories
RUN mkdir -p models uploads

# Non-root user for security
RUN useradd -m -u 1001 wastewise && chown -R wastewise:wastewise /app
USER wastewise

# Environment defaults
ENV FLASK_ENV=production \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Production server via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", \
     "--timeout", "120", "--access-logfile", "-", "main:create_app()"]
