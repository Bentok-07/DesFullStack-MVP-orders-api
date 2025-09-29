# Orders API
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    API_PORT=5001

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5001


HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://localhost:5001/api/v1/health || exit 1

CMD ["python", "app.py"]
