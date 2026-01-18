FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx redis

# Copy common module for latency tracking
COPY common /app/common

# Copy gateway service
COPY gateway/gateway.py .

CMD ["python", "gateway.py"]
