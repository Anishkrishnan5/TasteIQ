FROM python:3.12-slim

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --gid "${APP_GID}" tasteiq \
    && useradd --uid "${APP_UID}" --gid tasteiq --no-create-home --shell /usr/sbin/nologin tasteiq

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=tasteiq:tasteiq . .
RUN chmod +x docker-entrypoint.sh

USER tasteiq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["./docker-entrypoint.sh"]
