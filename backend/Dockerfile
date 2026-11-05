FROM python:3.13-slim-bookworm@sha256:281d39ff02e3b389401586134ff9e6572954687822a58055ec07a60ded4e0b7f
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/opt/reckon/backend
WORKDIR /opt/reckon
COPY deploy/requirements-server.lock /tmp/requirements-server.lock
RUN pip install --no-cache-dir -r /tmp/requirements-server.lock \
    && groupadd --gid 10001 reckon \
    && useradd --uid 10001 --gid 10001 --no-create-home reckon \
    && mkdir /state && chown 10001:10001 /state
COPY backend/app/ backend/app/
USER 10001:10001
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).close()"
CMD ["python", "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--no-access-log", "--limit-concurrency", "16", "--timeout-keep-alive", "5", "--timeout-graceful-shutdown", "30"]
