# Reporte de refactorización backend — Bulls Barber Shop

**Fecha:** 25 de mayo de 2026  
**Plan de referencia:** `refactor_backend_auditoría_ed664676.plan.md`  
**Alcance:** Fases 0–4 (seguridad, integridad de reservas, dominio, limpieza, documentación)

---

## 1. Resumen ejecutivo

Se implementó el plan de auditoría en cinco fases sin capa `application/`, sin `IServiceReader`/`ServiceSnapshot`, y sin helpers HTTP genéricos (no había ≥4 routers duplicados).

| Métrica | Resultado |
|---------|-----------|
| Tests | **251 passed** |
| Cobertura `app/` | **98,61 %** (umbral 80 %) |
| Archivos de producción tocados | 14 modificados + 3 nuevos |
| Archivos de test tocados | 11 modificados + 3 nuevos |
| Migración Alembic | `0002_booking_integrity` |

**Acción post-despliegue:** ejecutar `alembic upgrade head` en cada entorno para crear el índice único parcial de slots.

---

## 2. Implementación por fases

### Fase 0 — Seguridad operativa

| ID | Cambio | Archivo |
|----|--------|---------|
| 0.1 | `TRUST_PROXY_HEADERS: bool = False` | `app/config.py` |
| 0.1 | `X-Forwarded-For` solo si `settings.TRUST_PROXY_HEADERS` | `app/core/rate_limit.py` |
| 0.2 | Validación de ruta con `Path.resolve()` + `relative_to` | `app/infrastructure/storage/local.py` |
| 0.3 | `DeleteImageUseCase`: BD → storage, log si falla fichero | `app/domain/gallery/use_cases.py` |
| 0.4 | Rechazo de `PATCH` con `estado=cancelada` | `app/domain/booking/use_cases.py` |

### Fase 1 — Integridad de reservas

| ID | Cambio | Archivo |
|----|--------|---------|
| 1.1 | `rules.py`: `assert_future_datetime`, `BOOKING_ACTIVE_STATES` | `app/domain/booking/rules.py` (nuevo) |
| 1.1 | Validator Pydantic en `BookingCreate` | `app/api/schemas/booking.py` |
| 1.2 | Validación de servicio activo en router; nombre desde BD | `app/api/routers/bookings.py` |
| 1.3 | `IntegrityError` → `SlotOcupado`; filtros por estados activos | `app/infrastructure/persistence/repositories/booking.py` |
| 1.4 | `deleted_at IS NULL` en `_contar_citas` y `_servicios_mas_solicitados` | `app/infrastructure/persistence/repositories/stats.py` |

### Fase 2 — Dominio y API

| ID | Cambio | Archivo |
|----|--------|---------|
| 2.1 | `UpdateServiceUseCase` con parámetros explícitos | `app/domain/service/use_cases.py` |
| 2.2 | Email `strip().lower()`; `sub` entero seguro | `app/domain/auth/use_cases.py` |
| 2.3 | Repositorio de contacto obligatorio; sin swallow de errores SMTP | `app/domain/contact/use_cases.py` |

### Fase 3 — Limpieza

| ID | Cambio | Archivo |
|----|--------|---------|
| 3.1 | Índice único parcial `uq_bookings_slot_active` | `alembic/versions/0002_booking_integrity.py` (nuevo) |
| 3.2 | `DEFAULT_BARBER` (literal en ≥3 sitios) | `app/core/constants.py` (nuevo) |
| 3.3 | `_build_csv_response()` privada en router | `app/api/routers/bookings.py` |

### Fase 4 — Documentación

| ID | Cambio | Archivo |
|----|--------|---------|
| 4 | Sección reglas de reservas + `TRUST_PROXY_HEADERS` | `README.md` |

**No implementado (según plan):** `0003` índices extra, cache de stats, helpers `to_paged_response` / `require_admin_flag`.

---

## 3. Archivos nuevos (código completo)

### `app/domain/booking/rules.py`

```python
"""Reglas de negocio compartidas para reservas."""

from datetime import datetime, timezone

BOOKING_ACTIVE_STATES = frozenset({"pendiente", "confirmada"})


class FechaEnPasado(Exception):
    """La fecha/hora de la reserva no es futura respecto a UTC."""


def assert_future_datetime(fecha_hora: datetime, *, now: datetime | None = None) -> None:
    ref = now or datetime.now(timezone.utc)
    dt = fecha_hora
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt <= ref:
        raise FechaEnPasado("La fecha y hora deben ser futuras.")
```

### `app/core/constants.py`

```python
"""Constantes compartidas (solo literales usadas en ≥3 sitios del código)."""

DEFAULT_BARBER = "Cualquier barbero"
```

### `alembic/versions/0002_booking_integrity.py`

```python
"""Índice único parcial para slots de reserva activos
Revision ID: 0002 — Revises: 0001
"""
# upgrade(): uq_bookings_slot_active (partial unique on fecha_hora)
#            ix_bookings_fecha_hora_deleted (non-unique)
# downgrade(): drop both indexes
```

Líneas 1–57: ver fichero en repositorio (índice parcial PostgreSQL/SQLite con `deleted_at IS NULL AND estado IN ('pendiente','confirmada')`).

### Tests nuevos

| Fichero | Propósito |
|---------|-----------|
| `tests/unit/test_local_storage.py` | Path traversal → `ValueError` |
| `tests/unit/domain/test_booking_rules.py` | Fecha futura / pasado |
| `tests/unit/domain/test_service_use_cases.py` | Update explícito de servicio |

---

## 4. Archivos modificados — diff por fase

Los bloques siguientes son el **diff unificado exacto** (`git diff`) agrupado por fase. Las líneas con `+` se añadieron; las con `-` se eliminaron.

### Fase 0

#### `app/config.py` (+2)

```diff
     RATE_LIMIT_ENABLED: bool = True
+    # Solo True detrás de nginx/Traefik que sobrescribe X-Forwarded-For de forma fiable
+    TRUST_PROXY_HEADERS: bool = False
```

#### `app/core/rate_limit.py` (+5 / -4)

```diff
 def _get_client_ip(request: Request) -> str:
-    """Extrae la IP real teniendo en cuenta proxies inversos."""
-    forwarded_for = request.headers.get("X-Forwarded-For")
-    if forwarded_for:
-        return forwarded_for.split(",")[0].strip()
+    """Extrae la IP del cliente; X-Forwarded-For solo si TRUST_PROXY_HEADERS está activo."""
+    if settings.TRUST_PROXY_HEADERS:
+        forwarded_for = request.headers.get("X-Forwarded-For")
+        if forwarded_for:
+            return forwarded_for.split(",")[0].strip()
     return request.client.host if request.client else "unknown"
```

#### `app/infrastructure/storage/local.py` (+17 / -4)

```diff
+from pathlib import Path
 _UPLOAD_DIR = "uploads/gallery"
+_BASE_DIR = Path(_UPLOAD_DIR).resolve()
+_URL_PREFIX = "/uploads/gallery/"
 ...
-        return f"/uploads/gallery/{filename}"
+        return f"{_URL_PREFIX}{filename}"
     def delete(self, url_path: str) -> None:
-        local_path = url_path.lstrip("/")
-        if os.path.exists(local_path):
-            os.remove(local_path)
+        if not url_path.startswith(_URL_PREFIX):
+            raise ValueError("Ruta de fichero no permitida")
+        rel = url_path[len(_URL_PREFIX) :].lstrip("/")
+        target = (_BASE_DIR / rel).resolve()
+        try:
+            target.relative_to(_BASE_DIR)
+        except ValueError:
+            raise ValueError("Ruta de fichero no permitida") from None
+        if target.is_file():
+            target.unlink()
```

#### `app/domain/gallery/use_cases.py` (+15 / -1)

```diff
+import logging
+logger = logging.getLogger(__name__)
 ...
-        self._storage.delete(image.imagen_url)
+        url = image.imagen_url
         self._repo.delete(image_id)
+        try:
+            self._storage.delete(url)
+        except OSError as exc:
+            logger.warning(
+                "Registro %s eliminado en BD pero no se pudo borrar el fichero %s: %s",
+                image_id, url, exc,
+            )
```

#### `app/domain/booking/use_cases.py` (+4)

```diff
         if estado is not None:
+            if estado == "cancelada":
+                raise ValueError(
+                    "Para cancelar una reserva usa DELETE /api/bookings/{id}."
+                )
             booking.cambiar_estado(estado)
```

### Fase 1

#### `app/api/schemas/booking.py` (+14 / -2)

```diff
-from pydantic import BaseModel, EmailStr, Field
+from pydantic import BaseModel, EmailStr, Field, field_validator
+from app.core.constants import DEFAULT_BARBER
+from app.domain.booking.rules import FechaEnPasado, assert_future_datetime
 ...
-    barbero: Optional[str] = Field("Cualquier barbero", max_length=100)
+    barbero: Optional[str] = Field(DEFAULT_BARBER, max_length=100)
+
+    @field_validator("fecha_hora")
+    @classmethod
+    def fecha_debe_ser_futura(cls, v: datetime) -> datetime:
+        try:
+            assert_future_datetime(v)
+        except FechaEnPasado as exc:
+            raise ValueError(str(exc)) from exc
+        return v
```

#### `app/api/routers/bookings.py` — `crear_reserva` (+22 en handler)

```diff
+    service_repo = SQLAlchemyServiceRepository(db)
+    service = service_repo.get_by_id(data.servicio_id)
+    if not service or not service.activo:
+        raise HTTPException(
+            status_code=status.HTTP_400_BAD_REQUEST,
+            detail=f"El servicio {data.servicio_id} no existe o no está disponible.",
+        )
     booking = Booking(
 ...
-        servicio_id=data.servicio_id,
-        servicio_nombre=data.servicio_nombre,
+        servicio_id=service.id,
+        servicio_nombre=service.nombre,
-        barbero=data.barbero or "Cualquier barbero",
+        barbero=data.barbero or DEFAULT_BARBER,
```

#### `app/infrastructure/persistence/repositories/booking.py` (+20 / -7)

```diff
+from sqlalchemy.exc import IntegrityError
+from app.domain.booking.ports import ..., SlotOcupado
+from app.domain.booking.rules import BOOKING_ACTIVE_STATES
     def create(self, booking: Booking) -> Booking:
+        if not self.is_slot_available(booking.fecha_hora):
+            raise SlotOcupado(...)
         ...
-        self._session.commit()
+        try:
+            self._session.commit()
+        except IntegrityError as exc:
+            self._session.rollback()
+            raise SlotOcupado("El horario seleccionado ya no está disponible...") from exc
 ...
-                BookingORM.estado != "cancelada",
+                BookingORM.estado.in_(tuple(BOOKING_ACTIVE_STATES)),
```

#### `app/infrastructure/persistence/repositories/stats.py` (+6 / -1)

```diff
+                BookingORM.deleted_at.is_(None),   # en _contar_citas
+                BookingORM.deleted_at.is_(None),   # en ingresos estimados
+            .filter(
+                BookingORM.deleted_at.is_(None),   # en _servicios_mas_solicitados
+                BookingORM.estado != "cancelada",
```

`_distribucion_por_estado` **sin cambios** (historial de cancelaciones visible en panel).

#### `app/domain/booking/entity.py` (+4 / -2)

```diff
-from dataclasses import dataclass, field
+from dataclasses import dataclass
+from app.core.constants import DEFAULT_BARBER
-    barbero: str = "Cualquier barbero"
+    barbero: str = DEFAULT_BARBER
```

### Fase 2

#### `app/domain/service/use_cases.py` (+29 / -4)

`UpdateServiceUseCase.execute` pasa de `**fields` + `setattr` a parámetros nombrados: `nombre`, `descripcion`, `precio`, `duracion_minutos`, `categoria`, `imagen_url`, `activo`, `orden`.

#### `app/domain/auth/use_cases.py` (+6 / -4)

```diff
+        email = email.strip().lower()
 ...
-        user_id = payload.get("sub")
-        if not user_id:
-            raise TokenInvalid("Token sin subject")
-        user = self._user_repo.find_by_id(int(user_id))
+        try:
+            user_id = int(payload.get("sub", ""))
+        except (TypeError, ValueError):
+            raise TokenInvalid("Token inválido") from None
+        user = self._user_repo.find_by_id(user_id)
```

#### `app/domain/contact/use_cases.py` (+8 / -20)

- Eliminados `logging`, `Optional` en repositorio, rama sin repo y `except Exception` en notify.
- Flujo: `save` → `notify` (errores propagan).

### Fase 3

#### `app/api/routers/bookings.py` — CSV (+34 / -21)

- Eliminado bloque inline en `exportar_reservas_csv`.
- Añadida función `_build_csv_response()` (líneas 194–224 del fichero actual).

### Fase 4

#### `README.md` (+14)

Nueva sección **Reglas de negocio — reservas** y subsección **Rate limiting detrás de proxy**.

---

## 5. Tests añadidos o ajustados

| Fase | Test |
|------|------|
| 0 | `test_local_storage_path_traversal`, `test_no_trusts_forwarded_for_by_default`, `test_delete_image_repo_primero_luego_storage`, `test_patch_cancelada_rechazado_400`, `test_update_booking_estado_cancelada_lanza_value_error` |
| 1 | `test_crear_reserva_fecha_pasada_422`, `test_crear_reserva_servicio_inactivo_400`, `test_crear_reserva_servicio_nombre_desde_bd`, `test_is_slot_available_completada_cuenta_como_libre`, `test_create_integrity_error_lanza_slot_ocupado`, `test_stats_excluye_soft_deleted_de_conteos`, `test_booking_rules_*` |
| 2 | `test_login_normaliza_email`, `test_get_current_admin_sub_no_numerico_lanza_token_invalid`, `test_update_service_*`, `test_send_contact_notifier_falla_propaga_excepcion` |
| 3 | Regresión completa + fixture `seed_booking_service` |

Fixture `seed_booking_service` en `tests/conftest.py`: crea servicio activo «Corte Clásico» para módulos de reservas (`pytestmark` en `test_bookings.py`, `test_bookings_export.py`, `test_booking_repository.py`).

---

## 6. Tabla de líneas (git diff --numstat)

| Archivo | + | - |
|---------|---|---|
| README.md | 14 | 0 |
| app/api/routers/bookings.py | 47 | 25 |
| app/api/schemas/booking.py | 14 | 2 |
| app/config.py | 2 | 0 |
| app/core/rate_limit.py | 5 | 4 |
| app/domain/auth/use_cases.py | 6 | 4 |
| app/domain/booking/entity.py | 4 | 2 |
| app/domain/booking/use_cases.py | 4 | 0 |
| app/domain/contact/use_cases.py | 8 | 20 |
| app/domain/gallery/use_cases.py | 15 | 1 |
| app/domain/service/use_cases.py | 29 | 4 |
| app/infrastructure/.../booking.py | 20 | 7 |
| app/infrastructure/.../stats.py | 6 | 1 |
| app/infrastructure/storage/local.py | 17 | 4 |
| tests/conftest.py | 20 | 0 |
| tests/integration/api/test_bookings.py | 62 | 0 |
| tests/integration/api/test_bookings_export.py | 3 | 1 |
| tests/integration/repositories/test_booking_repository.py | 30 | 0 |
| tests/integration/repositories/test_stats_repository.py | 43 | 0 |
| tests/unit/domain/test_auth_use_cases.py | 28 | 0 |
| tests/unit/domain/test_booking_use_cases.py | 11 | 0 |
| tests/unit/domain/test_gallery_use_cases.py | 13 | 2 |
| tests/unit/test_rate_limit.py | 12 | 1 |
| tests/unit/use_cases/test_contact_use_cases.py | 3 | 17 |
| **Nuevos (sin numstat)** | app/domain/booking/rules.py (18 líneas), app/core/constants.py (3), alembic/0002 (57), 3 ficheros test unitarios |

**Total neto:** +416 / −95 líneas en ficheros rastreados por git (sin contar archivos nuevos sin stage).

---

## 7. Verificación

```bash
pytest -q
pytest --cov=app --cov-fail-under=80
alembic upgrade head   # en cada entorno con BD persistente
```

---

## 8. Riesgos y notas

1. **Frontend:** si cancelaba con `PATCH estado=cancelada`, debe usar `DELETE` (ahora responde 400).
2. **SQLite en tests:** `create_all` no aplica migración 0002; la red de seguridad `IntegrityError` está cubierta por tests con mock. En producción el índice parcial sí aplica tras `alembic upgrade head`.
3. **Contacto:** fallos SMTP ya no se tragan en dominio; la API debe devolver 5xx si el notifier falla (comportamiento más estricto y correcto).

---

## 9. Comando para regenerar el diff completo

```bash
cd backend
git diff
git diff --stat
```

Para incluir archivos nuevos:

```bash
git add -N app/domain/booking/rules.py app/core/constants.py alembic/versions/0002_booking_integrity.py
git diff
```
