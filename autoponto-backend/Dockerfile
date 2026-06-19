FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/tmp
ENV XDG_CACHE_HOME=/tmp/.cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY autoponto /app/autoponto
COPY docker/backend-entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && addgroup --system autoponto \
    && adduser --system --ingroup autoponto autoponto \
    && chown -R autoponto:autoponto /app /entrypoint.sh

USER autoponto

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "autoponto.wsgi:application", "--chdir", "/app/autoponto", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-tmp-dir", "/tmp"]
