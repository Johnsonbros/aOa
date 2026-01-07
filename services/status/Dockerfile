FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask redis requests

COPY status_service.py .

ENV REDIS_URL=redis://localhost:6379/0
ENV STATUS_PORT=9998

EXPOSE 9998

CMD ["python", "status_service.py"]
