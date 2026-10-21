FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ /app/src/
COPY seeds/ /app/seeds/
COPY reports/ /app/reports/
COPY logs/ /app/logs/
COPY demo/ /app/demo/
COPY tests/ /app/tests/

ENV PYTHONUNBUFFERED=1
ENV API_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=5s --timeout=5s --retries=5 --start_period=5s \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
