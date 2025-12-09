FROM python:3.14-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    "fastapi>=0.124.0,<0.125.0" \
    "uvicorn[standard]>=0.38.0,<0.39.0" \
    "httpx>=0.27.0,<0.28.0" \
    "pydantic-settings>=2.6.1,<3.0.0" \
    "python-multipart>=0.0.20,<0.0.21"

COPY gateway ./gateway

EXPOSE 8080

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
