# TaskPulse - AI Assistant - Backend Dockerfile
# Multi-stage build for optimized production image

# ==================== Build Stage ====================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ==================== Production Stage ====================
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r taskpulse && useradd -r -g taskpulse taskpulse

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=taskpulse:taskpulse app/ ./app/
COPY --chown=taskpulse:taskpulse scripts/ ./scripts/
COPY --chown=taskpulse:taskpulse run.py .

# Create data directory for SQLite
RUN mkdir -p /app/data && chown taskpulse:taskpulse /app/data

# Switch to non-root user
USER taskpulse

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
