# Legacy OrderHub - Proyecto Base de Modernización y Mantenimiento

> **Asignatura:** Actualización y Mantenimiento de Software  
> **Estado del Sistema:** Producción Legada (v1.0.0-legacy) — *Alta Deuda Técnica*  
> **Nivel de Cobertura de Pruebas:** 0%  

---

## Descripción del Proyecto

**Legacy OrderHub** es una aplicación monolítica encargada de la gestión básica de usuarios, catálogo de productos y procesamiento de órdenes de compra. El sistema fue desarrollado de manera acelerada años atrás para responder a una necesidad puntual de negocio, pero con el tiempo ha acumulado un nivel crítico de **deuda técnica, vulnerabilidades de seguridad y rigidez en la arquitectura**.

Actualmente, el sistema presenta fallas de rendimiento ante picos de tráfico, no cuenta con un entorno de ejecución estandarizado (sin contenerizar), carece de telemetría u observabilidad y las actualizaciones de código se realizan mediante despliegues manuales propensos a errores humanos.

Tu rol como ingeniero/a en este curso será asumir el mantenimiento de este sistema, auditarlo, estabilizarlo y aplicar técnicas modernas (Refactorización manual y asistida por IA, DevOps, Contenerización, SRE y CI/CD) para transformarlo progresivamente en una **aplicación nativa de la nube (Cloud-Native) v2.0**.

---

## Objetivos del Proyecto

### 🎯 Objetivo General
Evolucionar y modernizar la aplicación **Legacy OrderHub** desde su estado monolítico vulnerable hasta una arquitectura escalable, segura, observadamente monitoreada y desplegada mediante flujos automatizados de CI/CD.

### 🎯 Objetivos Específicos por Unidad

1. **Unidad I: Modernización Inteligente e Ingeniería Inversa**
   * Realizar auditorías de código estático y dinámico para mapear la deuda técnica y las vulnerabilidades críticas.
   * Refactorizar la arquitectura monolítica aplicando patrones de diseño (*Repository Pattern*, *Dependency Injection*) y asistencia de IA (Copilotos/Agentes).
   * Eliminar vulnerabilidades de seguridad de alto impacto (SQL Injection, exposición de secretos, contraseñas en texto plano).

2. **Unidad II: DevOps 2.0 y Calidad Automatizada**
   * Automatizar el flujo de integración continua (CI) mediante GitHub Actions / GitLab CI.
   * Implementar puertas de calidad (*Quality Gates*) para prevenir la entrada de nuevo código defectuoso.
   * Asignar métricas cuantitativas al costo de la deuda técnica y estimación de refactorización.

3. **Unidad III: Contenerización, IaC y SRE**
   * Empaquetar la aplicación y sus dependencias utilizando contenedores Docker.
   * Definir y desplegar la infraestructura en Kubernetes configurando autoescalado horizontal (HPA).
   * Gestionar secretos y variables de entorno de forma segura e independiente del código.

4. **Unidad IV: Despliegue Progresivo y Observabilidad**
   * Instrumentar la aplicación para generación de logs estructurados, métricas de rendimiento y trazas distribuidas.
   * Implementar estrategias de despliegue sin caída de servicio (*Blue/Green* o *Canary*).
   * Automatizar pruebas de regresión y de carga asistidas por IA para validar paridad funcional y resiliencia.

---

## Stack Tecnológico Actual vs. Estado Objetivo

| Componente | Estado Actual (v1.0 - Legado) | Estado Objetivo (v2.0 - Modernizado) |
| :--- | :--- | :--- |
| **Lenguaje / Framework** | Python 3.8 / Flask Monolítico | Python 3.11+ / Flask o FastAPI modular |
| **Base de Datos** | SQLite (Sin migraciones / SQL Directo) | PostgreSQL + ORM (SQLAlchemy / Alembic) |
| **Seguridad** | Secretos *hardcoded*, contraseñas plano | `.env` / Vault, Hash Bcrypt/Argon2, JWT |
| **Pruebas** | Ninguna (0% coverage) | Pytest + Cobertura > 80% + Mocks de IA |
| **Infraestructura** | Ejecución local/servidor directo | Docker Compose + Kubernetes (Minikube/k3s) |
| **CI / CD** | Despliegue manual | GitHub Actions / GitLab CI + SonarQube |
| **Observabilidad** | `print()` en consola | Prometheus + Grafana + Structured Logs (JSON) |

---

## Módulos y Puntos Críticos Detectados (Deuda Técnica)

A continuación se resumen las áreas más críticas identificadas en el sistema actual que deberán ser abordadas durante el curso:

* **Vulnerabilidades de Seguridad:** Inyección de SQL en el endpoint `/login`, almacenamiento de credenciales en texto plano y credenciales de base de datos expuestas en el repositorio (`config.py`).
* **Código Acoplado (Spaghetti):** El endpoint `/create_order` mezcla control de HTTP, lógica de cálculo de negocio, transacciones a la base de datos y llamadas sincrónicas a servicios externos.
* **Falta de Manejo de Errores y Transacciones:** Fallos en la red o llamadas externas dejan la base de datos en estados inconsistentes (p. ej., stock descontado sin notificación confirmada).
* **Configuración Rígida:** Modo `debug=True` activado por defecto y puertos quemados en el código.

---

## Guía de Inicio Rápido (Entorno Legado Local)

## La API estará disponible en http://localhost:5000.

### Reglas del Proyecto Durante el Curso

1. Prohibido hacer Push directo a la rama main: Todas las modificaciones deben realizarse mediante ramas (Feature Branches) y ser integradas a través de Pull Requests.

2. Cero Tolerancia a Secretos: No se aceptará ningún commit que contenga claves, tokens o contraseñas en texto plano.

3. Documentación Continua: Cada refactorización o cambio arquitectónico importante debe quedar documentado en la carpeta /docs.

¡Bienvenido/a al proceso de modernización! El éxito de la operación depende de tu capacidad para diagnosticar, refactorizar y automatizar.

### Requisitos Previos
* Python 3.8 o superior instalado.
* Git.

### Pasos para Ejecutar
1. Clonar este repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/legacy-orderhub.git](https://github.com/tu-usuario/legacy-orderhub.git)
   cd legacy-orderhub
2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   # En Linux/macOS:
   source venv/bin/activate
   # En Windows:
   venv\Scripts\activate

3.Instalar las dependencias legadas:
  ```bash
  pip install -r requirements.txt
   

   
