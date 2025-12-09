FROM python:3.14-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    "fastapi>=0.124.0,<0.125.0" \
    "uvicorn[standard]>=0.38.0,<0.39.0" \
    "sqlalchemy[asyncio]>=2.0.0,<3.0.0" \
    "asyncpg>=0.29.0,<0.32.0" \
    "minio>=7.2.7,<8.0.0" \
    "aio-pika>=9.4.1,<10.0.0" \
    "python-multipart>=0.0.9,<0.1.0" \
    "pydantic-settings>=2.6.1,<3.0.0"

COPY storage ./storage

EXPOSE 8000

CMD ["uvicorn", "storage.main:app", "--host", "0.0.0.0", "--port", "8000"]
