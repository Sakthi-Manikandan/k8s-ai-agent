# ─────────────────────────────────────
# Stage 1: Builder
# Install dependencies and build
# ─────────────────────────────────────
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────────
# Stage 2: Runtime
# Only copy what's needed to run!
# ─────────────────────────────────────
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production
ENV PATH=/root/.local/bin:$PATH

# Install ONLY runtime dependencies
# kubectl is needed to talk to K8s
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s \
    https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
# This is the magic of multi-stage!
# We get the installed packages
# WITHOUT the build tools!
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
# Running as root in containers = bad practice!
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports
EXPOSE 8000
EXPOSE 8501

# Health check
# Docker will ping this to know
# if container is healthy!
HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Default command
CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000"]