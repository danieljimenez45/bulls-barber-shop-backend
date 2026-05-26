# Bulls Barber Shop — Backend

API REST construida con **FastAPI** siguiendo **arquitectura hexagonal** (puertos y adaptadores).
Base de datos: **SQLite** en desarrollo, **PostgreSQL** en producción.

---

## Requisitos

- Python 3.11+
- pip

---

## Instalación

```bash
# Entrar en la carpeta del backend
cd backend

# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate       # Mac / Linux
venv\Scripts\activate          # Windows

# Instalar dependencias de producción
pip install -r requirements.txt

# Instalar dependencias de desarrollo y test
pip install -r requirements-dev.txt

# Crear .env en la raíz del backend (no se sube al repo; ver sección Configuración)
```

---

## Configuración

La app **no arranca** sin `SECRET_KEY`. Genera un valor seguro y ponlo en `.env`:

```bash
openssl rand -hex 32
# o:
python -c "import secrets; print(secrets.token_hex(32))"
```

El resto de variables tienen valores por defecto en `app/config.py`. Opcional en `.env`: `DATABASE_URL`, `CORS_ORIGINS`, SMTP, Cloudinary (ver comentarios en `app/config.py`).

---

## Arrancar el servidor

```bash
uvicorn app.main:app --reload
```

- API:           `http://localhost:8000`
- Documentación: `http://localhost:8000/docs`
- Health check:  `http://localhost:8000/api/health/`

---

## Tests

```bash
# Todos los tests
pytest

# Solo unitarios (sin BD ni HTTP)
pytest -m unit

# Solo de integración
pytest -m integration

# Con informe de cobertura
pytest --cov=app --cov-report=term-missing
```

Las variables de entorno de test se inyectan automáticamente desde `pytest.ini` — no es necesario un `.env` de test separado.

---

## Reglas de negocio — reservas

- **Fecha futura:** `fecha_hora` debe ser estrictamente posterior a la hora actual en **UTC**. Las fechas sin zona horaria se interpretan como UTC.
- **Slot ocupado:** solo las reservas en estado `pendiente` o `confirmada` (y no eliminadas con soft-delete) bloquean un horario. `cancelada` y `completada` no impiden una nueva reserva en el mismo instante.
- **Cancelar:** usar siempre `DELETE /api/bookings/{id}`. No se admite `PATCH` con `estado=cancelada` (el soft-delete y `deleted_at` solo aplican vía DELETE).
- **Servicio:** al crear una reserva, el nombre del servicio se toma de la base de datos según `servicio_id`; el cliente no puede imponer otro nombre en el payload.
- **Concurrencia:** comprobación previa del slot + índice único parcial en BD; colisión → HTTP 409.

### Rate limiting detrás de proxy

Por defecto `TRUST_PROXY_HEADERS=false`: la IP del rate limit es la conexión directa (`request.client.host`). Activa `TRUST_PROXY_HEADERS=true` en `.env` **solo** si la API está detrás de un reverse proxy (nginx, Traefik, etc.) que sobrescribe `X-Forwarded-For` de forma fiable.

---

## Endpoints principales

### Públicos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/services/` | Listar servicios activos |
| GET | `/api/services/{id}` | Obtener servicio por ID |
| POST | `/api/bookings/` | Crear reserva |
| GET | `/api/bookings/disponibilidad` | Slots ocupados por fecha |
| GET | `/api/reviews/` | Listar reseñas visibles |
| POST | `/api/reviews/` | Enviar reseña |
| GET | `/api/gallery/` | Listar imágenes de galería |
| POST | `/api/contact/` | Enviar mensaje de contacto |
| GET | `/api/health/` | Estado de la API y la BD |

### Protegidos (requieren JWT)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Obtener token JWT |
| GET | `/api/bookings/` | Listar reservas (paginado) |
| PATCH | `/api/bookings/{id}` | Actualizar estado de reserva |
| DELETE | `/api/bookings/{id}` | Cancelar reserva (soft delete) |
| GET | `/api/bookings/export` | Exportar reservas a CSV |
| POST | `/api/services/` | Crear servicio |
| PUT | `/api/services/{id}` | Actualizar servicio |
| DELETE | `/api/services/{id}` | Eliminar servicio |
| PATCH | `/api/reviews/{id}/visibilidad` | Cambiar visibilidad de reseña |
| DELETE | `/api/reviews/{id}` | Eliminar reseña |
| POST | `/api/gallery/upload` | Subir imagen |
| DELETE | `/api/gallery/{id}` | Eliminar imagen |
| GET | `/api/contact/` | Listar mensajes de contacto |
| PATCH | `/api/contact/{id}/leido` | Marcar mensaje como leído |
| GET | `/api/admin/stats` | Estadísticas del panel admin |

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py                   # Bootstrap y registro de routers
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── database.py               # SQLAlchemy session factory
│   ├── core/
│   │   ├── logging.py            # Configuración de logging
│   │   └── rate_limit.py         # Middleware de rate limiting
│   ├── domain/                   # Núcleo de negocio (sin dependencias externas)
│   │   ├── auth/
│   │   │   ├── entity.py         # AdminUser
│   │   │   ├── ports.py          # Interfaces IUserRepository, ITokenService…
│   │   │   └── use_cases.py      # LoginUseCase, GetCurrentAdminUseCase
│   │   ├── booking/
│   │   │   ├── entity.py
│   │   │   ├── ports.py
│   │   │   └── use_cases.py
│   │   ├── contact/
│   │   ├── gallery/
│   │   ├── review/
│   │   ├── service/
│   │   └── stats/
│   ├── infrastructure/           # Adaptadores de salida
│   │   ├── notifications/        # SMTP (email)
│   │   ├── persistence/
│   │   │   ├── orm/              # Modelos SQLAlchemy
│   │   │   └── repositories/     # Implementaciones de los puertos de repositorio
│   │   ├── security/
│   │   │   ├── jwt_service.py    # PyJWT
│   │   │   └── password_hasher.py # bcrypt
│   │   └── storage/              # Local / Cloudinary
│   └── api/                      # Adaptadores de entrada
│       ├── dependencies/         # Inyección de dependencias FastAPI
│       ├── routers/              # Endpoints HTTP
│       └── schemas/              # Esquemas Pydantic de entrada/salida
├── migrations/                   # Migraciones Alembic
├── tests/
│   ├── conftest.py               # Fixtures compartidos (client, db_session, auth_headers…)
│   ├── unit/
│   │   ├── domain/               # Tests de entidades y casos de uso
│   │   └── test_jwt_service.py   # Tests del servicio JWT
│   └── integration/
│       └── api/                  # Tests HTTP endpoint a endpoint
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

`.env` y `.env.example` son locales (en `.gitignore`) y no forman parte del repositorio.

---

## Migraciones (Alembic)

```bash
# Crear una nueva migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Ver el estado actual
alembic current
```

---

## Almacenamiento de imágenes

- **Desarrollo:** las imágenes se guardan en `uploads/` (almacenamiento local).
- **Producción:** se usa Cloudinary cuando `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` y `CLOUDINARY_API_SECRET` están configuradas en `.env`.

---

## Gestión de dependencias

Las versiones exactas se bloquean con **pip-compile** (pip-tools).

```bash
# Instalar pip-tools (solo una vez)
pip install pip-tools

# Regenerar lockfiles tras cambiar requirements.in o requirements-dev.in
pip-compile requirements.in           # → requirements.txt
pip-compile requirements-dev.in       # → requirements-dev.txt

# Instalar exactamente las versiones bloqueadas
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Edita siempre los ficheros `.in` — nunca los `.txt` directamente.

---

## Despliegue con Docker

```bash
# Desarrollo
docker compose -f docker/docker-compose.dev.yml up

# Producción
docker compose -f docker/docker-compose.prod.yml up -d
```
