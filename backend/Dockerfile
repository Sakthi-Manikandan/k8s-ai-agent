# ─────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────
# Stage 2: Runtime
# ─────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PATH=/root/.local/bin:$PATH

# Install kubectl only in backend!
# Frontend doesn't need kubectl!
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s \
    https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy packages from builder
COPY --from=builder /root/.local /root/.local

# Copy ONLY backend code
# Not frontend, not k8s manifests!
COPY backend/ ./backend/
COPY main.py .

# Create logs and data directories
RUN mkdir -p logs data

# Non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000"]