# syntax=docker/dockerfile:1
# Imagen de OrderHub (RNF-03.1): construcción multi-etapa.
#  - builder: instala las dependencias de ejecución en un entorno virtual.
#  - runtime: imagen final liviana con solo el entorno virtual y el código,
#    ejecutada con un usuario sin privilegios (nunca root).

FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home app \
    && mkdir /app \
    && chown app:app /app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app.py worker.py config.py gunicorn.conf.py ./
COPY --chown=app:app orderhub ./orderhub

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthcheck', timeout=2)"

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
