# Bitácora de Deuda Técnica (Technical Debt Log)

> **Historia de usuario:** HU-01 – Auditoría de Código, Seguridad e Ingeniería Inversa
> **Sistema auditado:** Legacy OrderHub v1.0.0-legacy (rama `main`, commit `2d6a20b`)
> **Fecha de auditoría:** 2026-10-19
> **Documento relacionado:** [`REVERSE_ENGINEERING.md`](REVERSE_ENGINEERING.md) (resumen, diagramas C4 nivel 1 y 2, documentación por función y patrones)

---

## 1. Cómo se hizo la auditoría

| Técnica | Herramienta | Qué cubre |
| :--- | :--- | :--- |
| SAST (análisis estático de seguridad) | **Bandit 1.9.4** | Patrones inseguros en el código Python |
| SCA (análisis de dependencias) | **pip-audit** | Vulnerabilidades conocidas (CVE/PYSEC) en `requirements.txt` |
| Revisión asistida por IA | **Claude Code** (agente con acceso de lectura al repositorio) | Lógica de negocio, control de acceso, transacciones, diseño |
| Verificación dinámica | Cliente de pruebas de Flask sobre una copia aislada | Confirmar que cada hallazgo se puede explotar o reproducir |

**Escala de severidad:** 🔴 Crítica (explotable, compromete datos o el sistema) · 🟠 Alta · 🟡 Media · 🟢 Baja.
**Esfuerzo estimado:** S (menos de medio día) · M (1–2 días) · L (más de 2 días).

---

## 2. Resumen

| Severidad | Cantidad | IDs |
| :--- | :---: | :--- |
| 🔴 Crítica | 4 | TD-01, TD-02, TD-03, TD-04 |
| 🟠 Alta | 7 | TD-05, TD-06, TD-07, TD-08, TD-09, TD-10, TD-11 |
| 🟡 Media | 6 | TD-12, TD-13, TD-14, TD-15, TD-16, TD-17 |
| 🟢 Baja | 3 | TD-18, TD-19, TD-20 |
| **Total** | **20** | |

**Estado al cierre de esta auditoría:** el PR #1 (arquitectura hexagonal) resuelve o mitiga 9 ítems, marcados como "En PR #1". Los demás siguen abiertos.

**Actualización (segunda entrega, rama `feature/auth-security`):** se resuelven **TD-03** (Argon2) y **TD-06** (JWT + roles), y avanza **TD-10** (67 pruebas). Detalle en [`ARCHITECTURE.md`](ARCHITECTURE.md), secciones 5 y 6.

---

## 3. Registro de deuda técnica

### 🔴 TD-01 · Inyección SQL en `/login`
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A03 Injection, CWE-89 |
| **Ubicación** | `app.py:25` y `app.py:29` |
| **Descripción** | La consulta se arma interpolando `username` y `password` en un f-string: `f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"`. |
| **Evidencia** | Bandit **B608**. Verificación dinámica: `{"username":"admin' --","password":"x"}` → **200**, sesión como `admin` sin conocer la contraseña. `' OR '1'='1` en ambos campos también devuelve 200. |
| **Impacto** | Cualquiera puede suplantar a cualquier usuario, incluido el administrador. |
| **Remediación** | Consultas parametrizadas (`WHERE username = ?`) o un ORM, y comparar la contraseña en código, no en SQL. |
| **Requisito** | RNF-02.2, HU-02 (CA-1 y CA-4) |
| **Esfuerzo / Estado** | S · **En PR #1**: `SqliteUserRepository.get_by_username` usa consultas parametrizadas; prueba `test_login_sql_injection_is_rejected` → 401 |

### 🔴 TD-02 · Credenciales y secretos en el código (`config.py`)
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A02/A05, CWE-259, CWE-798 |
| **Ubicación** | `config.py:3-7` |
| **Descripción** | `DB_PASS = "admin1234_super_secret"` y `SECRET_KEY = "clave_secreta_super_insegura_123"` están en texto plano y versionados en Git, en un repositorio **público**. |
| **Evidencia** | Bandit **B105** (×2) en `config.py:5` y `config.py:7`. |
| **Impacto** | Quien vea el repositorio obtiene las claves. Una `SECRET_KEY` conocida permite falsificar cookies y sesiones firmadas cuando se usen (RF-01.3). Además, los secretos quedan para siempre en el historial de Git. |
| **Remediación** | Leer la configuración desde variables de entorno (`.env` en `.gitignore`, más un `.env.example` sin valores reales) y rotar las claves expuestas. |
| **Requisito** | RNF-02.1, HU-02 (CA-3), regla del proyecto "Cero Tolerancia a Secretos" |
| **Esfuerzo / Estado** | S · **Abierto** |

### 🔴 TD-03 · Contraseñas en texto plano
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A02 Cryptographic Failures, CWE-256 |
| **Ubicación** | Esquema `users.password` (`database.py:15`), datos semilla (`database.py:43-44`) |
| **Descripción** | Las contraseñas se guardan y comparan sin hash. Los usuarios semilla (`admin/admin123`, `juan/123456`) están escritos en el código. |
| **Evidencia** | Revisión con IA y lectura directa del código. Bandit **no** lo detecta porque las contraseñas están dentro de un literal SQL. |
| **Impacto** | Una fuga de `orderhub.db` expone todas las contraseñas, reutilizables en otros servicios. |
| **Remediación** | Guardar las contraseñas con hash bcrypt o argon2, migrar las existentes y sacar la semilla del código. |
| **Requisito** | RF-01.2, HU-02 (CA-2) |
| **Esfuerzo / Estado** | M · ✅ **Resuelto (segunda entrega)**: puerto `PasswordHasher` + `Argon2PasswordHasher` (Argon2id). La semilla se guarda con hash y las contraseñas legadas en texto plano se migran al arrancar (`schema._migrate_plaintext_passwords`). Las contraseñas semilla siguen escritas en el código hasta RNF-02.1. |

### 🔴 TD-04 · Depurador de Werkzeug expuesto a la red
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A05 Security Misconfiguration, CWE-94, CWE-605 |
| **Ubicación** | `app.py:87`: `app.run(host='0.0.0.0', port=5000, debug=True)` |
| **Descripción** | El modo debug está activo y la app escucha en todas las interfaces. |
| **Evidencia** | Bandit **B201** (severidad High) y **B104**. |
| **Impacto** | Ante un error, el depurador interactivo permite ejecutar código Python en el servidor (protegido solo por un PIN). |
| **Remediación** | Sacar `debug` y `host` a la configuración por entorno (desactivados por defecto) y usar un servidor WSGI de producción (gunicorn). |
| **Requisito** | RNF-02.1, RNF-03.1 |
| **Esfuerzo / Estado** | S · **Abierto** |

### 🟠 TD-05 · Exposición de datos sensibles en respuestas y logs
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: CWE-200, CWE-532 |
| **Ubicación** | `app.py:26` (`print` de la consulta con la contraseña), `app.py:32` (`dict(user)` incluye `password`), `app.py:35` (`str(e)` al cliente) |
| **Evidencia** | El login exitoso devolvió `"password":"admin123"`. El usuario `o'brien` produjo un 500 con `near "brien": syntax error`. |
| **Impacto** | Credenciales en la consola y en las respuestas HTTP; mensajes internos que facilitan los ataques. |
| **Remediación** | Serializar sin `password`, registrar errores en el log del servidor y devolver mensajes genéricos al cliente. |
| **Requisito** | RNF-02.2, RNF-05.1 |
| **Esfuerzo / Estado** | S · **En PR #1** (`user_to_dict` quita la contraseña; los errores devuelven un 500 genérico) |

### 🟠 TD-06 · Endpoints sin autenticación ni autorización
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A01 Broken Access Control, CWE-862 |
| **Ubicación** | `app.py:37` (`/create_order`) y `app.py:77` (`/get_all_orders_legacy`) |
| **Descripción** | Cualquier cliente lista **todas** las órdenes y crea órdenes con cualquier `user_id`. El login no emite token ni sesión, así que no hay forma de saber quién hace cada petición. |
| **Evidencia** | Revisión con IA. Se crearon órdenes sin autenticarse durante la verificación dinámica. |
| **Impacto** | Exposición de datos de clientes y órdenes fraudulentas a nombre de otros. |
| **Remediación** | JWT con expiración, el `user_id` tomado del token y no del cuerpo, y roles para las operaciones administrativas. |
| **Requisito** | RF-01.3, RF-01.4 |
| **Esfuerzo / Estado** | M · ✅ **Resuelto (segunda entrega)**: `JWTTokenService` (HS256, expiración de 30 min). `@token_required` en `/create_order`, que toma el `user_id` del token. `@admin_required` en `/get_all_orders_legacy` y en `POST /products` (403 para otros roles). |

### 🟠 TD-07 · Cantidad no validada: stock manipulable
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Lógica de negocio: CWE-20 |
| **Ubicación** | `app.py:42`, `app.py:52` |
| **Descripción** | `quantity` no se valida como entero positivo. Con un valor negativo la orden pasa la validación de stock. |
| **Evidencia** | `quantity: -10` → **201**, orden con `total: -155.0` y el stock de "Mouse USB" sube de **50 a 60**. `quantity: "abc"` → **500** (`ValueError`). |
| **Impacto** | Inventario y montos falsificables; errores 500 provocables a voluntad. |
| **Remediación** | Validar la entrada en el adaptador HTTP y la regla `quantity > 0` en el dominio. |
| **Requisito** | RF-02.3, RF-03.2 |
| **Esfuerzo / Estado** | S · **En PR #1** (`Order.place` exige cantidad > 0; la ruta responde 400 si no es un entero) |

### 🟠 TD-08 · Condición de carrera al descontar stock (lost update)
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Concurrencia / consistencia de datos |
| **Ubicación** | `app.py:47` (lectura) → `app.py:64-65` (escritura) |
| **Descripción** | El nuevo stock se calcula en Python con un valor leído antes (`new_stock = product['stock'] - quantity`). Dos compras simultáneas pueden leer el mismo stock y sobrevender. |
| **Evidencia** | Revisión con IA (no se reprodujo con carga concurrente). |
| **Impacto** | Stock inconsistente o negativo en producción ante picos de tráfico. |
| **Remediación** | Actualización atómica y condicional: `UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?`, y verificar las filas afectadas. Con PostgreSQL, `SELECT ... FOR UPDATE`. |
| **Requisito** | RF-02.2, RF-03.3 |
| **Esfuerzo / Estado** | S · **Abierto** (el PR #1 agrega Unit of Work, pero la lectura y la escritura siguen separadas) |

### 🟠 TD-09 · Monolito acoplado (Big Ball of Mud / Transaction Script)
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Arquitectura / mantenibilidad |
| **Ubicación** | `app.py` completo; sobre todo `create_order` (`app.py:37-75`) |
| **Descripción** | Cada handler mezcla HTTP, reglas de negocio, SQL y notificación. No hay capas ni interfaces. |
| **Impacto** | Un cambio en cualquier capa obliga a tocar los handlers; las reglas no se pueden probar de forma aislada. |
| **Remediación** | Arquitectura hexagonal con Repository Pattern e inyección de dependencias. |
| **Requisito** | RNF-01.1, HU-03 |
| **Esfuerzo / Estado** | L · **En PR #1** |

### 🟠 TD-10 · Sin pruebas automatizadas (0 % de cobertura)
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Calidad |
| **Descripción** | No existe ninguna prueba. Además, `init_db()` se ejecuta al importar `app.py`, lo que impide probar sin tocar la base real. |
| **Impacto** | Cada cambio corre un riesgo alto de regresión. |
| **Remediación** | pytest con pruebas unitarias (con mocks o fakes) y de integración; cobertura ≥ 80 %. |
| **Requisito** | RNF-01.2, HU-04 |
| **Esfuerzo / Estado** | M · **Parcial**: 22 pruebas en el PR #1 y 67 en la segunda entrega; falta medir cobertura con `pytest-cov` |

### 🟠 TD-11 · Dependencias con vulnerabilidades conocidas
| Campo | Detalle |
| :--- | :--- |
| **Categoría** | Seguridad: OWASP A06 Vulnerable and Outdated Components |
| **Ubicación** | `requirements.txt` |
| **Evidencia (pip-audit)** | `requests 2.25.1`: 4 avisos (PYSEC-2023-74, PYSEC-2026-1872, -1873, -2275; corregido en ≥ 2.33.0). Sus dependencias transitivas: `urllib3 1.26.20` con 7 avisos (corregido en ≥ 2.8.0) e `idna 2.10` con 2 (corregido en ≥ 3.15). `werkzeug 3.1.8`: 1 aviso (PYSEC-2026-4312 / CVE-2026-102598, `safe_join` en Windows; corregido en 3.1.9). |
| **Agravante** | `requests` **no se usa** en ningún módulo: agrega superficie de ataque sin ningún beneficio. |
| **Remediación** | Quitar `requests`, actualizar Werkzeug a ≥ 3.1.9 y agregar `pip-audit` al pipeline de CI. |
| **Requisito** | RNF-02.3, HU-05 |
| **Esfuerzo / Estado** | S · **Abierto** |

### 🟡 TD-12 · Sin transacción explícita ni manejo de errores en `create_order`
| Campo | Detalle |
| :--- | :--- |
| **Ubicación** | `app.py:44-67` |
| **Descripción** | No hay `try/except` ni `rollback`. Si algo falla después de abrir la conexión, esta queda abierta y el error llega al cliente como un 500 de Flask. |
| **Requisito** | RF-03.3 |
| **Esfuerzo / Estado** | S · **En PR #1** (Unit of Work con rollback y cierre garantizados) |

### 🟡 TD-13 · Notificación sincrónica simulada con `print`
| Campo | Detalle |
| :--- | :--- |
| **Ubicación** | `app.py:69` |
| **Descripción** | La "notificación por correo" no existe. Si se implementara en ese mismo lugar, bloquearía la respuesta y, si fallara, la orden ya estaría confirmada sin aviso. |
| **Requisito** | RF-04.1 |
| **Esfuerzo / Estado** | M · **Parcial en PR #1** (puerto `OrderNotifier`; falta un adaptador asíncrono) |

### 🟡 TD-14 · Esquema sin integridad referencial ni restricciones
| Campo | Detalle |
| :--- | :--- |
| **Ubicación** | `database.py:12-39` |
| **Descripción** | No hay `FOREIGN KEY`, `UNIQUE(username)`, `NOT NULL` ni `CHECK(stock >= 0)`. El dinero se guarda como `REAL` (errores de redondeo). No hay migraciones. |
| **Requisito** | Estado objetivo del README: PostgreSQL + SQLAlchemy/Alembic |
| **Esfuerzo / Estado** | M · **Abierto** |

### 🟡 TD-15 · Logging no estructurado (`print`)
| Campo | Detalle |
| :--- | :--- |
| **Ubicación** | `app.py:26`, `app.py:69` |
| **Descripción** | Sin niveles, marcas de tiempo ni contexto; imposible de agregar o consultar. |
| **Requisito** | RNF-05.1, HU-08 |
| **Esfuerzo / Estado** | S · **Parcial en PR #1** (`logging` estándar; falta el formato JSON) |

### 🟡 TD-16 · Efectos laterales al importar y configuración rígida
| Campo | Detalle |
| :--- | :--- |
| **Ubicación** | `app.py:6-9` (app global + `init_db()`), `database.py:4` (`'orderhub.db'` fija y relativa al directorio de trabajo), `app.py:87` (puerto fijo) |
| **Descripción** | Importar el módulo crea o modifica la base de datos. No se pueden crear instancias con otra configuración (por ejemplo, para pruebas). `config.DB_NAME` no coincide con el archivo que se usa realmente. |
| **Requisito** | RNF-02.1, RNF-03 |
| **Esfuerzo / Estado** | S · **Parcial en PR #1** (`create_app()` con contenedor inyectable; la ruta de la BD y el puerto siguen fijos) |

### 🟡 TD-17 · Formato de errores inconsistente
| Campo | Detalle |
| :--- | :--- |
| **Descripción** | Conviven `{"status","message"}`, `{"error"}`, `{"status","exception"}` y páginas HTML de error (415 y 500), así que el cliente no puede tratar los errores de forma uniforme. |
| **Esfuerzo / Estado** | S · **Abierto** (el PR #1 centraliza el manejo en `error_handlers.py`, pero conserva los formatos por compatibilidad) |

### 🟢 TD-18 · Código y configuración muertos
`import sqlite3` sin uso (`app.py:2`); `DB_HOST/DB_USER/DB_PASS/DB_NAME` sin uso (`config.py`); comentario con HTML antiguo (`app.py:14`); `SECRET_KEY` configurada sin sesiones. · S · **Abierto**

### 🟢 TD-19 · Magic strings y nombres incoherentes
`'PENDING'` y `'orderhub.db'` escritos en el código; la función `get_orders` responde en la ruta `/get_all_orders_legacy`; rutas con verbos (`/create_order`) en lugar de recursos REST (`POST /orders`). · S · **Abierto**

### 🟢 TD-20 · Listado sin paginación y frontend sin manejo de errores HTTP
`SELECT * FROM orders` devuelve toda la tabla (`app.py:80`); `fetchOrders()` no comprueba `response.ok` (`templates/index.html:37-39`). · S · **Abierto**

---

## 4. Informe de auditoría con herramientas

### 4.1 Bandit (SAST)
Comando: `bandit app.py database.py config.py` (114 líneas analizadas).

| ID Bandit | Severidad / Confianza | Ubicación | Ítem |
| :--- | :--- | :--- | :--- |
| B201 `flask_debug_true` | High / Medium | `app.py:87` | TD-04 |
| B608 `hardcoded_sql_expressions` | Medium / Low | `app.py:25` | TD-01 |
| B104 `hardcoded_bind_all_interfaces` | Medium / Medium | `app.py:87` | TD-04 |
| B105 `hardcoded_password_string` | Low / Medium | `config.py:5` | TD-02 |
| B105 `hardcoded_password_string` | Low / Medium | `config.py:7` | TD-02 |

**Total:** 1 High, 2 Medium, 2 Low.

### 4.2 pip-audit (SCA)
Comando: `pip-audit -r requirements.txt`.

| Paquete | Versión | Avisos | Versión corregida |
| :--- | :--- | :---: | :--- |
| requests | 2.25.1 | 4 | ≥ 2.33.0 (o eliminarlo: no se usa) |
| urllib3 (transitiva) | 1.26.20 | 7 | ≥ 2.8.0 |
| idna (transitiva) | 2.10 | 2 | ≥ 3.15 |
| werkzeug | 3.1.8 | 1 | 3.1.9 |
| flask, jinja2, click, itsdangerous, markupsafe, blinker, certifi, chardet | — | 0 | — |

### 4.3 Qué encontró la revisión asistida por IA que las herramientas no detectan
Las herramientas automáticas detectaron 4 de los 20 ítems: TD-01, TD-02, TD-04 y TD-11. Bandit marcó TD-01 con confianza baja. La revisión con IA, confirmada luego con ejecución real, agregó los problemas de **lógica y diseño** que un SAST no ve:
- Contraseñas en texto plano dentro de literales SQL (TD-03).
- Falta de control de acceso (TD-06).
- Stock manipulable con cantidades negativas (TD-07) y la condición de carrera (TD-08).
- Fuga de la contraseña en la respuesta y en el log (TD-05).
- Acoplamiento arquitectónico (TD-09) y la falta de transacciones (TD-12).

Conclusión: el SAST y el SCA deben correr en CI (HU-05), pero no reemplazan la revisión de diseño.

---

## 5. Priorización recomendada

| Orden | Ítems | Motivo |
| :---: | :--- | :--- |
| 1 | TD-01, TD-05, TD-07, TD-09, TD-12 | Ya resueltos en el PR #1: revisarlo y mergearlo. |
| 2 | TD-02, TD-04, TD-11 | Críticos y de bajo esfuerzo (S): `.env`, desactivar debug, limpiar dependencias. |
| 3 | TD-03, TD-06, TD-08 | Hash de contraseñas, JWT con roles y descuento de stock atómico. |
| 4 | TD-10, TD-15, TD-16 | Cobertura ≥ 80 %, logs JSON y configuración por entorno (habilitan CI y contenedores). |
| 5 | TD-13, TD-14, TD-17 a TD-20 | Migración a PostgreSQL, notificación asíncrona y limpieza. |

---

## 6. Historial de la bitácora

| Fecha | Cambio |
| :--- | :--- |
| 2026-10-19 | Auditoría inicial (HU-01): Bandit, pip-audit, revisión con IA y verificación dinámica. 20 ítems registrados. |
| 2026-10-19 | Segunda entrega: TD-03 y TD-06 resueltos; TD-10 actualizado. |
