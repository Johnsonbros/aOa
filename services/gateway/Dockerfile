FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx

COPY gateway.py .

CMD ["python", "gateway.py"]
