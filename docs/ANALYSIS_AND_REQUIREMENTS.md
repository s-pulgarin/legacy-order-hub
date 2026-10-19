# Documento de Análisis, Requisitos e Historias de Usuario (Backlog de Transformación)

> **Proyecto:** Legacy OrderHub  
> **Asignatura:** Actualización y Mantenimiento de Software  
> **Versión del Documento:** 1.0.0  
> **Estado:** Aprobado para Modernización  

---

## 1. Resumen Ejecutivo y Diagnóstico del Sistema Legado

El sistema **Legacy OrderHub (v1.0.0-legacy)** es un monolito desarrollado en Python (Flask) con persistencia en SQLite, encargado de gestionar usuarios, inventario y procesamiento de órdenes de compra. Aunque la aplicación cubre las operaciones de negocio esenciales, presenta un deterioro técnico crítico debido a malas prácticas acumuladas, falta de arquitectura por capas y ausencia total de automatización y pruebas.

### Matriz de Diagnóstico Actual

| Dimensión | Estado Actual (v1.0 - Legado) | Nivel de Riesgo | Observaciones Técnicas |
| :--- | :--- | :--- | :--- |
| **Arquitectura** | Monolítica en capa única (*Spaghetti Code*) | 🔴 Alto | Múltiples responsabilidades acopladas en los handlers HTTP (`app.py`). |
| **Seguridad** | Inyección SQL, datos en texto plano, secretos *hardcoded* | 🔴 Crítico | Endpoint `/login` vulnerable. Sin hash en contraseñas. Claves expuestas en `config.py`. |
| **Calidad de Código** | Cobertura del 0%, sin linters ni análisis estático | 🔴 Alto | Imposible hacer cambios sin riesgo alto de regresión o quiebre del sistema. |
| **Persistencia** | SQLite con consultas SQL puras y concatenadas | 🟡 Medio | Sin sistema de migraciones, propenso a inconsistencias y bloqueos en escrituras. |
| **Infraestructura** | Ejecución directa en entorno local / servidor *host* | 🔴 Alto | No hay contenerización (Docker), lo que genera el problema "en mi máquina sí funciona". |
| **DevOps / CI-CD** | Despliegue manual e informal | 🔴 Alto | Sin trazabilidad de cambios, sin pruebas automáticas antes de mezclar código. |
| **Observabilidad** | Impresiones por consola (`print`) no estructuradas | 🟡 Medio | Imposible rastrear errores en producción, monitorear latencia o analizar métricas. |

---

## 2. Requisitos del Sistema

Para llevar a cabo la transformación a una arquitectura moderna y nativa de la nube (v2.0), se han formalizado los requisitos funcionales y no funcionales.

### 2.1 Requisitos Funcionales (RF)

* **RF-01: Autenticación y Autorización de Usuarios**
  * **RF-01.1:** El sistema debe permitir el inicio de sesión mediante credenciales de usuario (usuario/contraseña).
  * **RF-01.2:** Las contraseñas deben almacenarse encriptadas mediante algoritmos de hashing seguros (Bcrypt o Argon2).
  * **RF-01.3:** La sesión debe gestionarse mediante tokens seguros no falsificables (JWT - JSON Web Tokens) con tiempo de expiración.
  * **RF-01.4:** El sistema debe restringir operaciones administrativas (ej. creación de productos) únicamente a usuarios con rol `admin`.

* **RF-02: Gestión del Catálogo de Productos e Inventario**
  * **RF-02.1:** El sistema debe permitir consultar la lista de productos disponibles con sus respectivos precios y stock actual.
  * **RF-02.2:** El sistema debe permitir la actualización del stock de un producto cuando se procesa una orden de compra.
  * **RF-02.3:** El sistema debe rechazar compras de productos cuyo stock solicitado supere la disponibilidad real.

* **RF-03: Procesamiento de Órdenes de Compra**
  * **RF-03.1:** El sistema debe permitir registrar nuevas órdenes asociando un usuario, un producto y la cantidad deseada.
  * **RF-03.2:** El sistema debe calcular el costo total de la orden de forma automática y atómica.
  * **RF-03.3:** El sistema debe garantizar la consistencia transaccional: el stock solo se descuenta si la orden fue creada exitosamente en la base de datos.
  * **RF-03.4:** El sistema debe permitir listar todas las órdenes registradas en el sistema.

* **RF-04: Notificación y Comunicación Sincrónic/Asincrónica**
  * **RF-04.1:** El sistema debe emitir un evento o registro de notificación al completar una orden sin bloquear la respuesta HTTP al cliente.

---

### 2.2 Requisitos No Funcionales (RNF)

* **RNF-01: Mantenibilidad y Arquitectura Clean**
  * **RNF-01.1:** La base de código debe desacoplarse aplicando una Arquitectura Limpia o Arquitectura Hexagonal (*Repository Pattern*, *Dependency Injection*).
  * **RNF-01.2:** El sistema debe contar con un nivel de cobertura de pruebas unitarias y de integración de mínimo el **80%**.
  * **RNF-01.3:** El código debe cumplir con las directrices de estilo PEP 8 y pasar inspecciones de linters (`flake8`, `black`) sin advertencias críticas.

* **RNF-02: Seguridad (DevSecOps)**
  * **RNF-02.1:** Cero credenciales, claves API o tokens en código fuente (*Zero Hardcoded Secrets*). Todas las configuraciones deben leerse desde variables de entorno (`.env`).
  * **RNF-02.2:** Prevenir vulnerabilidades del OWASP Top 10, especialmente SQL Injections, sanitizando todas las consultas mediante ORM o consultas preparadas.
  * **RNF-02.3:** Integrar herramientas de escaneo estático SAST (ej. SonarQube, Bandit) en el flujo de desarrollo.

* **RNF-03: Contenerización, Orquestación y SRE**
  * **RNF-03.1:** La aplicación y sus servicios dependientes (Base de datos PostgreSQL, Redis) deben empaquetarse en contenedores Docker utilizando un `Dockerfile` optimizado (multi-stage build).
  * **RNF-03.2:** El entorno de desarrollo debe ser orquestado mediante `docker-compose`.
  * **RNF-03.3:** La versión de producción debe ser desplegable en un clúster de Kubernetes (Minikube / k3s) mediante manifiestos declarativos (`Deployment`, `Service`, `ConfigMap`, `Secret`).
  * **RNF-03.4:** Configurar autoescalado horizontal de pods (HPA) con base en el uso de CPU o memoria.

* **RNF-04: Automatización CI/CD**
  * **RNF-04.1:** Todo *Pull Request* hacia la rama principal debe desencadenar automáticamente un pipeline en GitHub Actions o GitLab CI.
  * **RNF-04.2:** El pipeline de CI debe ejecutar pruebas unitarias, análisis estático de código y construcción de la imagen de contenedor.

* **RNF-05: Observabilidad y Monitoreo**
  * **RNF-05.1:** La aplicación debe generar registros (*logs*) estructurados en formato JSON que incluyan marca de tiempo, nivel de severidad y contexto.
  * **RNF-05.2:** Exponer un endpoint `/metrics` para scraping de métricas por parte de Prometheus.
  * **RNF-05.3:** Implementar monitoreo en un Dashboard de Grafana para visualizar la tasa de peticiones, latencia y errores (Métricas RED).

---

## 3. Historias de Usuario (Backlog de Transformación)

A continuación se detalla el backlog de Historias de Usuario (HU) organizado por Unidades de Aprendizaje. Este backlog servirá como la guía práctica para los estudiantes a lo largo del curso.

---

### 🔹 UNIDAD I: Bases, Evolución y Modernización Inteligente

#### HU-01: Auditoría de Código, Seguridad e Ingeniería Inversa
* **Como:** Arquitecto de Software  
* **Quiero:** Ejecutar análisis estático (SAST) e ingeniería inversa asistida por IA sobre la base de código legada  
* **Para:** Identificar vulnerabilidades críticas, mapear la deuda técnica y documentar la arquitectura actual en la bitácora del proyecto  

* **Criterios de Aceptación:**
  1. Identificar y documentar en `docs/TECHNICAL_DEBT_LOG.md` la vulnerabilidad de inyección SQL en `/login` y el manejo de credenciales expuestas en `config.py`.
  2. Generar un informe de auditoría utilizando herramientas como SonarQube, Bandit o asistida por asistentes de IA.
  3. Dibujar el diagrama de arquitectura C4 (Nivel 1 y Nivel 2) del sistema legado en `docs/ARCHITECTURE.md`.

---

#### HU-02: Refactorización del Módulo de Autenticación y Seguridad
* **Como:** Desarrollador Backend  
* **Quiero:** Eliminar las consultas SQL string concatenadas y reemplazar el almacenamiento de texto plano por hashing de contraseñas  
* **Para:** Proteger el sistema contra ataques de Inyección SQL y prevenir la fuga de credenciales  

* **Criterios de Aceptación:**
  1. El endpoint `/login` debe utilizar consultas parametrizadas o un ORM (SQLAlchemy).
  2. Las contraseñas de los usuarios deben encriptarse utilizando `bcrypt` o `argon2` al ser creadas o actualizadas.
  3. Migrar las variables de configuración del archivo `config.py` a un archivo `.env` que no se suba al control de versiones.
  4. La consulta maliciosa `' OR '1'='1` en el campo `username` debe ser rechazada con código HTTP `401 Unauthorized`.

---

#### HU-03: Desacoplamiento de la Lógica de Negocio (Repository Pattern)
* **Como:** Desenvolvedor Backend  
* **Quiero:** Extraer la lógica de cálculo y persistencia del endpoint `/create_order` hacia capas de Servicio y Repositorio  
* **Para:** Garantizar la mantenibilidad del código, el principio de responsabilidad única (SRP) y facilitar la creación de pruebas unitarias  

* **Criterios de Aceptación:**
  1. Mover el acceso a la base de datos a un módulo `repositories/order_repository.py`.
  2. Mover las validaciones de stock y cálculo de precios a un módulo `services/order_service.py`.
  3. El handler en `app.py` únicamente debe recibir las peticiones HTTP, validar la entrada y responder el código HTTP correspondiente.

---

### 🔹 UNIDAD II: Gestión de Proyectos y Cultura DevOps 2.0

#### HU-04: Implementación de Pruebas Unitarias y Cobertura
* **Como:** Ingeniero de Calidad (QA)  
* **Quiero:** Escribir un conjunto de pruebas unitarias y de integración con `pytest` para la lógica de órdenes y usuarios  
* **Para:** Validar que las refactorizaciones no generen regresiones y asegurar una cobertura mínima del 80%  

* **Criterios de Aceptación:**
  1. Implementar pruebas unitarias aisladas con mocks para `OrderService` y `UserService`.
  2. Implementar pruebas de integración HTTP para los endpoints de la API.
  3. Generar un reporte de cobertura con `pytest-cov` confirmando un resultado mayor o igual al 80%.

---

#### HU-05: Automatización de Integración Continua (CI Pipeline)
* **Como:** Ingeniero DevOps  
* **Quiero:** Configurar un pipeline de CI automatizado mediante GitHub Actions / GitLab CI  
* **Para:** Garantizar que cada commit o Pull Request sea auditado antes de integrarse a la rama principal  

* **Criterios de Aceptación:**
  1. El archivo de flujo de trabajo (`.github/workflows/ci.yml`) debe activarse en eventos de `push` y `pull_request` a la rama `main`.
  2. El pipeline debe instalar dependencias, ejecutar linters (`flake8`), correr el escaneo SAST (`bandit`) y ejecutar el suite de pruebas (`pytest`).
  3. Si alguna prueba falla o el linter reporta errores críticos, el paso debe marcarse como fallido imposibilitando la mezcla del código.

---

### 🔹 UNIDAD III: Gestión de la Configuración, Contenerización y SRE

#### HU-06: Contenerización con Docker y Docker Compose
* **Como:** Administrador de Sistemas / DevOps  
* **Quiero:** Crear un `Dockerfile` optimizado y un archivo `docker-compose.yml`  
* **Para:** Empaquetar la aplicación y la base de datos PostgreSQL en un entorno consistente e independiente del sistema operativo anfitrión  

* **Criterios de Aceptación:**
  1. El `Dockerfile` debe implementarse con una construcción multietapa (*multi-stage build*) utilizando una imagen base ligera (ej. `python:3.11-slim`).
  2. El contenedor no debe ejecutarse con permisos de usuario `root`.
  3. El archivo `docker-compose.yml` debe levantar la API de Flask y la base de datos PostgreSQL interconectados en una red privada virtual.
  4. Persistir los datos de la base de datos mediante un volumen administrado por Docker.

---

#### HU-07: Orquestación en Kubernetes y Autoescalado (HPA)
* **Como:** Ingeniero SRE  
* **Quiero:** Declarar los manifiestos de Kubernetes para la aplicación OrderHub  
* **Para:** Garantizar alta disponibilidad, auto-recuperación y escalabilidad automática ante variaciones de tráfico  

* **Criterios de Aceptación:**
  1. Crear manifiestos `Deployment`, `Service` (ClusterIP/NodePort), `ConfigMap` y `Secret` en la carpeta `k8s/`.
  2. Implementar un manifiesto `HorizontalPodAutoscaler` (HPA) configurado para escalar de 2 a 5 réplicas si el consumo de CPU supera el 70%.
  3. Configurar las sondas de estado (*Liveness Probe* y *Readiness Probe*) apuntando a un endpoint `/healthcheck`.

---

### 🔹 UNIDAD IV: Despliegue, Observabilidad y Autocuración

#### HU-08: Instrumentación de Observabilidad (Métricas y Logs)
* **Como:** Operador de Sistemas / SRE  
* **Quiero:** Instrumentar la aplicación con logs estructurados en JSON y un exportador de métricas Prometheus  
* **Para:** Monitorear el estado operativo del servicio y detectar anomalías en tiempo real  

* **Criterios de Aceptación:**
  1. Reemplazar las sentencias `print()` por una librería de logging estructurado (`structlog` o `python-json-logger`).
  2. Exponer el endpoint `/metrics` utilizando la librería cliente de Prometheus (`prometheus_flask_exporter`).
  3. Registrar métricas clave: Total de peticiones HTTP por código de respuesta, latencia por endpoint y número de órdenes procesadas.

---

#### HU-09: Despliegue Progresivo Canary y Pruebas de Carga
* **Como:** Ingeniero DevOps / SRE  
* **Quiero:** Ejecutar una estrategia de despliegue Canary complementada con pruebas de carga automáticas  
* **Para:** Desplegar nuevas versiones reduciendo el impacto en los usuarios finales en caso de fallos  

* **Criterios de Aceptación:**
  1. Configurar una ruta o controlador de tráfico (Ingress Controller / Service Mesh) que dirija el 10% del tráfico a la nueva versión (Canary) y el 90% a la versión estable.
  2. Ejecutar un script de pruebas de carga con Locust o K6 simulando peticiones concurrentes a la API.
  3. Validar que si la tasa de error en la versión Canary supera el 1%, el sistema ejecute un *rollback* automático a la versión estable.

---

## 4. Matriz de Trazabilidad: Temario vs. Historias de Usuario

Esta tabla relaciona la estructura curricular del curso con los entregables prácticos que los alumnos desarrollarán:

| Unidad Temática del Curso | Subtemas Asociados | Historia de Usuario Aplicada |
| :--- | :--- | :--- |
| **Unidad I: Modernización Inteligente** | 1.1 Naturaleza del cambio, 1.3 Categorías de Mantenimiento, 1.6 Ingeniería Inversa | **HU-01:** Auditoría, Seguridad e Ingeniería Inversa |
| | 1.3 Categorías de Mantenimiento, 1.4 Refactorización Asistida, 1.5 Modernización | **HU-02:** Refactorización de Autenticación y Seguridad |
| | 1.2 Evolución del Software, 1.4 Refactorización Asistida | **HU-03:** Desacoplamiento (Repository Pattern) |
| **Unidad II: DevOps 2.0 y Proyectos** | 2.2 Costos de Mantenimiento, 2.3 Deuda Técnica, 3.3 Casos de prueba | **HU-04:** Pruebas Unitarias y Cobertura (80%) |
| | 2.1 Copilotos/Agentes, 2.5 DevOps/DevSecOps, 2.6 Herramientas CI/CD | **HU-05:** Pipeline Automatizado de CI |
| **Unidad III: Configuración y SRE** | 3.4 Infraestructura como Código, 3.4.1 Contenedores en Apps Legadas | **HU-06:** Contenerización (Docker & Compose) |
| | 3.2 Control de Versiones Avanzado, 3.4.2 Orquestación y Autoscaling | **HU-07:** Orquestación en K8s y Autoescalado |
| **Unidad IV: Despliegue y Observabilidad** | 4.2 Calidad y Pruebas, 4.3 Observabilidad y Monitoreo, 4.4 Ética y Seguridad | **HU-08:** Observabilidad (Prometheus & Logs JSON) |
| | 4.1 Estrategias de Despliegue, 4.3 Monitoreo | **HU-09:** Despliegue Canary y Pruebas de Carga |

---
*Este documento establece los criterios oficiales de aceptación para la evaluación práctica del curso.*