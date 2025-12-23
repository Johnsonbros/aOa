FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask watchdog redis

# Copy from src context (set in docker-compose)
COPY index/indexer.py .
COPY ranking /app/ranking

ENV CODEBASE_ROOT=/codebase
ENV PORT=9999

EXPOSE 9999

CMD ["python", "indexer.py"]
