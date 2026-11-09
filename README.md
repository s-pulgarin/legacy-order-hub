# OrderHub: modernización de un sistema legado

> **Asignatura:** Actualización y Mantenimiento de Software
> **Estado:** v2.0, modernizado y desplegado. Partió de *Legacy OrderHub v1.0*, un monolito con alta deuda técnica.
> **Demo en vivo:** https://orderhub-qcr5.onrender.com (plan gratuito: la primera carga puede tardar unos 30–60 s si el servicio está "dormido").

[![CI](https://github.com/s-pulgarin/legacy-order-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/s-pulgarin/legacy-order-hub/actions/workflows/ci.yml)
[![CD](https://github.com/s-pulgarin/legacy-order-hub/actions/workflows/cd.yml/badge.svg)](https://github.com/s-pulgarin/legacy-order-hub/actions/workflows/cd.yml)

---

## Descripción

**OrderHub** gestiona usuarios, un catálogo de productos con inventario y órdenes de compra.

El proyecto partió de **Legacy OrderHub**: un único `app.py` con inyección SQL, contraseñas en texto plano, secretos en el código, ninguna prueba y despliegue manual. A lo largo del curso se auditó, se documentó por ingeniería inversa y se transformó en una aplicación **cloud-native**: arquitectura hexagonal, seguridad DevSecOps, pruebas automatizadas, CI/CD, contenedores, Kubernetes con autoescalado, observabilidad y despliegue público en Render.

## Funcionalidades

- **Interfaz web corporativa:** login, registro, catálogo con compra, "Mis órdenes" y administración de productos (solo admin).
- **Autenticación segura:** contraseñas con **Argon2**, sesiones **JWT** con expiración y control de acceso por rol (`admin` / `client`).
- **Inventario transaccional:** el stock solo se descuenta si la orden se guarda; las compras sin stock se rechazan.
- **Notificaciones asíncronas:** cada orden se encola en **Redis** y un *worker* la procesa sin bloquear la respuesta.
- **Observabilidad:** logs **JSON** con `request_id` y endpoint `/metrics` para **Prometheus**, con un dashboard **Grafana** de métricas RED.

## Antes y después

| Componente | Legado (v1.0) | Actual (v2.0) |
| :--- | :--- | :--- |
| **Arquitectura** | Monolito en `app.py` | **Hexagonal**: dominio, puertos y adaptadores; Repository, Unit of Work, inyección de dependencias |
| **Base de datos** | SQLite con SQL concatenado | **PostgreSQL** (producción) o SQLite (desarrollo), siempre con consultas parametrizadas |
| **Seguridad** | SQL injection, contraseñas planas, secretos en código | **Argon2**, **JWT**, roles, cero secretos (`.env`), Bandit y pip-audit en el CI |
| **Pruebas** | 0 % | **219 pruebas** (unitarias e integración contra SQLite y PostgreSQL), cobertura mínima obligatoria del **80 %** |
| **Calidad** | Sin estándar | **PEP 8** con black y flake8 |
| **CI/CD** | Despliegue manual | **GitHub Actions**: CI en cada PR y CD que publica la imagen en ghcr.io |
| **Infraestructura** | Ejecución local | **Docker** multi-stage, **docker-compose**, **Kubernetes** (Minikube) con **HPA** de 2 a 5 réplicas |
| **Despliegue** | Manual | **Render** (Blueprint `render.yaml`) con auto-deploy; estrategia para **Azure** (Canary/Blue-Green) |
| **Observabilidad** | `print()` | Logs JSON, Prometheus y Grafana |

## Estructura

```
orderhub/
├── domain/                  Entidades y reglas de negocio (Python puro)
├── application/
│   ├── ports/               Interfaces: repositorios, Unit of Work, hasher, tokens, notificador
│   └── services/            Casos de uso: auth, órdenes, productos
├── adapters/
│   ├── inbound/web/         Flask: rutas, decoradores JWT, interfaz (templates/ y static/)
│   ├── inbound/queue/       Worker que consume la cola de Redis
│   └── outbound/            PostgreSQL, SQLite, Argon2, JWT, Redis, métricas
├── observability/           Logs JSON y métricas Prometheus
└── container.py             Composition root (inyección de dependencias)
tests/                       unit/ e integration/
k8s/                         Manifiestos de Kubernetes y HPA
monitoring/                  Prometheus y Grafana
docs/                        Documentación técnica (ver abajo)
app.py · worker.py · config.py · Dockerfile · docker-compose.yml · render.yaml
```

## Cómo ejecutar

Requisitos: Python 3.11+ y Git. Para el entorno completo: Docker Desktop. Para Kubernetes: Minikube.

### 1. Local (rápido, con SQLite)

```bash
git clone https://github.com/s-pulgarin/legacy-order-hub.git
cd legacy-order-hub
python -m venv venv
venv\Scripts\activate              # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements-dev.txt
cp .env.example .env               # completar SECRET_KEY y, opcional, SEED_ADMIN_PASSWORD / SEED_CLIENT_PASSWORD
python app.py                      # http://localhost:5000
```

Para generar una `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

### 2. Entorno completo con Docker

Con `POSTGRES_PASSWORD` y `GRAFANA_ADMIN_PASSWORD` definidas en el `.env`:

```bash
docker compose up -d --build
```

| Servicio | URL |
| :--- | :--- |
| Aplicación | http://localhost:8000 |
| Grafana (usuario `admin`) | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

Levanta la API (gunicorn), el worker, PostgreSQL, Redis, Prometheus y Grafana.

### 3. Kubernetes local (Minikube)

```bash
minikube start --driver=docker && minikube addons enable metrics-server
docker build -t orderhub:local . && minikube image load orderhub:local
python scripts/k8s_secret_from_env.py      # genera k8s/secret.yaml desde .env (no se versiona)
kubectl apply -k k8s/
kubectl -n orderhub port-forward service/api 8080:8000
```

Para ver el autoescalado: `kubectl apply -f k8s/tools/load-generator.yaml` y `kubectl -n orderhub get hpa api --watch`.

### 4. Nube (Render)

`render.yaml` define la app, PostgreSQL y Redis. Cada merge a `main` despliega automáticamente. Ver [`docs/RENDER_DEPLOYMENT.md`](docs/RENDER_DEPLOYMENT.md).

## Rutas principales

| Ruta | Descripción |
| :--- | :--- |
| `/login`, `/registro`, `/catalogo`, `/ordenes`, `/admin/productos` | Interfaz web |
| `/dev` | Panel técnico para probar la API (401/403, token manipulado) |
| `POST /login`, `POST /register` | Autenticación (devuelve un JWT) |
| `GET /products` · `POST /products` (admin) | Catálogo |
| `POST /create_order` · `GET /my_orders` · `GET /get_all_orders_legacy` (admin) | Órdenes |
| `GET /healthcheck` · `GET /metrics` | Salud y métricas |

## Calidad

```bash
python -m pytest                                              # pruebas + cobertura (falla si es < 80 %)
black --check . && flake8                                     # PEP 8
bandit -r orderhub app.py config.py --severity-level medium   # SAST
pip-audit -r requirements.txt                                 # dependencias vulnerables
```

Para correr también las pruebas contra PostgreSQL, define `TEST_DATABASE_URL`. El CI lo hace automáticamente en cada Pull Request.

## Documentación

| Documento | Contenido |
| :--- | :--- |
| [`docs/ANALYSIS_AND_REQUIREMENTS.md`](docs/ANALYSIS_AND_REQUIREMENTS.md) | Requisitos, historias de usuario y seguimiento de implementación (§5) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Arquitectura, patrones, flujos, configuración, observabilidad, contenedores, Kubernetes e interfaz, con diagramas |
| [`docs/REVERSE_ENGINEERING.md`](docs/REVERSE_ENGINEERING.md) | Ingeniería inversa del sistema legado (C4, funciones, patrones) |
| [`docs/TECHNICAL_DEBT_LOG.md`](docs/TECHNICAL_DEBT_LOG.md) | Bitácora de deuda técnica y su resolución |
| [`docs/RENDER_DEPLOYMENT.md`](docs/RENDER_DEPLOYMENT.md) | Despliegue público en Render |

La estrategia de despliegue en **Azure** (Container Apps + PostgreSQL, Canary/Blue-Green y rollback) está preparada en la rama `feature/azure`. No se ejecutó porque la suscripción de estudiante quedó bloqueada en el registro de proveedores de recursos.

## Reglas del proyecto

1. **Nada de push directo a `main`:** todo cambio entra por rama y Pull Request, con el CI en verde.
2. **Cero secretos:** ninguna clave, token o contraseña en el código. Todo se lee de variables de entorno (`.env`, secretos de Render o de Kubernetes).
3. **Documentación continua:** cada cambio de arquitectura se documenta en `/docs`.
