"""Configuración de gunicorn, el servidor WSGI de producción (dentro del contenedor).

Un solo proceso con varios hilos por contenedor: las métricas de Prometheus
viven en memoria del proceso, así que con un único worker son coherentes. Para
atender más carga se agregan réplicas del contenedor (HPA en Kubernetes,
réplicas en Azure Container Apps).
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"  # nosec B104 - dentro del contenedor
workers = 1
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = 30
graceful_timeout = 20
# Cada petición ya se registra en JSON desde la app: sin access log duplicado.
accesslog = None
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "warning")
