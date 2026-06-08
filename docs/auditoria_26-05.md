# Auditoría técnica — Backend Bulls Barber Shop

| Campo | Valor |
|-------|--------|
| **Rama auditada** | `main` |
| **Commit** | `10e8ba6` — *feat(backend): endurecer reservas, seguridad y dominio* |
| **Fecha de auditoría** | 20/05/2026 |
| **Auditor** | Revisión senior (código, coherencia, negocio barbería, comentarios, tests) |
| **Stack** | FastAPI, SQLAlchemy, Alembic, SQLite (dev) / PostgreSQL (prod), JWT, pytest |

---

## 1. Veredicto ejecutivo

El backend está **en buen estado para producción de una barbería pequeña/mediana**: arquitectura hexagonal reconocible, endpoints públicos vs admin bien separados, reglas de reservas recientemente endurecidas y **251 tests** con **~99 % de cobertura** en `app/`.

| Área | Nota (1–5) | Comentario breve |
|------|------------|------------------|
| Arquitectura y alineación | **4,5** | Capas claras; DI manual repetitiva pero aceptable |
| Seguridad | **4** | JWT, rate limit, validación de uploads; límites conocidos (rate limit en memoria) |
| Lógica de negocio (barbería) | **3,5** | Reservas por **instante**, no por duración; barbero decorativo |
| Coherencia API / contratos | **4** | Pequeñas incoherencias en schemas vs runtime |
| Comentarios en código | **3,5** | Buenos en routers críticos e infra; dominio más escueto |
| Tests y CI | **5** | Suite amplia + guardia anti-legacy |
| Documentación | **4** | README sólido; detalle menor en rutas de migraciones |

**Conclusión:** El código es **coherente y mantenible** para la web de la barbería. Las mejoras prioritarias son de **modelo de citas** (duración del servicio, horario del local), no de reescritura arquitectónica.

---

## 2. Alcance y metodología

Se revisó:

- Estructura `app/` (domain, api, infrastructure, core).
- Routers HTTP, schemas Pydantic, casos de uso y repositorios.
- Migraciones Alembic (`0001`, `0002`).
- Tests (`pytest -q`, cobertura `--cov=app`).
- README y `docs/REPORTE.md`.
- Ausencia de carpetas legacy (`app/routers`, `app/models`, `app/schemas`) vía `tests/test_no_legacy.py`.

No se auditó el frontend React ni infraestructura Docker en profundidad.

---

## 3. Arquitectura y alineación del código

### 3.1 Lo que está bien alineado

```
Cliente (web) → app/api/routers → domain/use_cases → ports
                                      ↓
                    infrastructure/repositories | security | storage | notifications
```

- **`main.py`** solo monta routers bajo `app/api/`, CORS, logging, migraciones al arranque y SPA opcional. Punto de entrada claro.
- **Dominio** sin imports de FastAPI/SQLAlchemy en entidades y casos de uso (salvo tipos estándar).
- **Puertos** (`IBookingRepository`, `IContactNotifier`, etc.) con adaptadores en `infrastructure/`.
- **Patrón público / admin** reutilizado de forma consistente en servicios y reseñas (`get_optional_admin` + 401 si `solo_activos=false` o `solo_visibles=false` sin token).
- **Soft-delete** en reservas (`deleted_at` + `estado=cancelada` en `delete()`), documentado en el repositorio.
- **Guardia CI** impide reintroducir routers legacy sin JWT.

### 3.2 Desalineaciones menores (no bloqueantes)

| Tema | Detalle |
|------|---------|
| **Inyección de dependencias** | Cada endpoint instancia `SQLAlchemy*Repository(db)` y use cases inline. Válido en proyectos pequeños; si crece el equipo, un módulo `dependencies/repositories.py` reduciría ruido. |
| **Doble comprobación de slot** | `CreateBookingUseCase` y `SQLAlchemyBookingRepository.create()` llaman ambos a `is_slot_available`. Redundante pero defensivo. |
| **README vs repo** | El árbol del README menciona `migrations/`; las migraciones reales están en `alembic/versions/`. |
| **`create_tables()`** | Sigue en `database.py` y en `scripts/create_admin.py`; producción usa Alembic (`run_migrations`). Conviene dejar claro en README que el script admin es solo bootstrap local. |
| **FK ausente** | `bookings.servicio_id` no tiene FK a `services` en `0001`. Borrar un servicio puede dejar reservas huérfanas (solo nombre desnormalizado). |

### 3.3 Código muerto / no usado en producción

| Elemento | Ubicación | Notas |
|----------|-----------|--------|
| `Booking.completar()` | `domain/booking/entity.py` | Solo tests; en runtime se usa `cambiar_estado("completada")` vía PATCH. |
| `servicio_nombre` en `BookingCreate` | `api/schemas/booking.py` | El router **ignora** el payload y toma el nombre de BD. Campo engañoso en OpenAPI. |
| Carpetas legacy | — | No existen en disco; el glob del IDE puede mostrar caché antigua. `test_no_legacy` pasa. |

---

## 4. Revisión por dominio (fit barbería)

### 4.1 Reservas (`booking`) — núcleo del negocio

**Flujo actual (correcto y documentado en README):**

1. Cliente elige servicio + fecha/hora (público, rate limit 10/min).
2. Validación Pydantic: fecha futura UTC (`rules.assert_future_datetime`).
3. Router valida servicio **activo** y copia `servicio_nombre` desde BD.
4. Slot libre si no hay otra reserva `pendiente`/`confirmada` no eliminada.
5. Índice único parcial (`0002`) + `IntegrityError` → 409 en carrera.
6. Admin: listar, PATCH estado/notas/barbero, DELETE cancelar (soft-delete), export CSV.

**Coherencia con la operativa real de una barbería:**

| Regla de negocio | ¿Implementada? | Observación |
|------------------|----------------|-------------|
| No reservar en el pasado | Sí | UTC; naive → UTC |
| Un turno por hora (mismo instante) | Sí | Por `fecha_hora` exacta |
| Duración del servicio (30/45/60 min) | **No** | `duracion_minutos` existe en `Service` pero **no** bloquea solapamientos (ej. corte 30 min a las 10:00 no bloquea 10:15) |
| Horario de apertura / festivos | **No** | Cualquier hora futura es válida |
| Barbero concreto / agenda por profesional | **Parcial** | Campo texto `barbero` + default «Cualquier barbero»; sin entidad Barbero ni conflictos por persona |
| Confirmar / completar cita | Sí (manual) | PATCH `confirmada` / `completada` por admin |
| Cancelar | Sí | Solo `DELETE` (PATCH `cancelada` → 400) |
| Email de confirmación | Opcional | Si el cliente deja email y SMTP configurado |

**Lógica `completada` vs fecha futura:** Como ya se discutió, marcar completada después del turno no “libera” horas pasadas (la validación de fecha futura lo impide). El estado sirve para **historial, stats e ingresos estimados**, no para reabrir slots pasados. Coherente si el admin completa tras el servicio.

**Recomendación de producto:** Si la web muestra franjas cada 15/30 min, el backend debería eventualmente tratar slots como **intervalos** `[inicio, inicio + duracion_minutos)` y validar solapes, no solo igualdad de `fecha_hora`.

### 4.2 Servicios (`service`)

- CRUD admin; listado público solo activos.
- `GET /api/services/{id}` devuelve el servicio **aunque esté inactivo** (no filtra `activo`). No rompe el flujo de reserva (POST valida activo), pero el detalle público podría devolver 404 para inactivos.
- Precio y duración alimentan **stats** (ingresos estimados); la duración no afecta disponibilidad.

### 4.3 Reseñas (`review`)

- Creación pública con rate limit; moderación admin (`visible`).
- Adecuado para reputación de barbería. Sin verificación de “cliente real” (normal en negocios locales).

### 4.4 Galería (`gallery`)

- Subida admin con validación **excelente** (tamaño, extensión, doble extensión, Pillow).
- Storage local seguro (`path traversal` mitigado) o Cloudinary.
- Delete: BD primero, fichero después (orden correcto).

### 4.5 Contacto (`contact`)

- Persistencia obligatoria + notificación SMTP.
- Errores del notifier **propagan** (antes se tragaban). Correcto para transparencia; la API puede devolver 5xx si SMTP falla tras guardar — valorar respuesta 201 + cola de email en el futuro.
- `POST` devuelve `dict` suelto, no un schema Pydantic de respuesta (inconsistencia menor con el resto de routers).

### 4.6 Auth y admin

- Login OAuth2 form, email normalizado, bcrypt, JWT 24 h.
- Rate limit en login (5/min).
- Panel stats: citas, ingresos estimados, top servicios, distribución por estado, próxima cita.
- Comentario en `admin.py` menciona «Jonathan»; mejor generalizar a «administrador».

### 4.7 Notificaciones

- Textos de email con datos reales del negocio (dirección Madrid, teléfono).
- Dependen de `SMTP_*` y `ADMIN_EMAIL`; si no hay SMTP, la reserva **sí se crea** (notifier no bloquea create).

---

## 5. Seguridad

| Control | Estado |
|---------|--------|
| `SECRET_KEY` obligatoria al arrancar | OK |
| JWT en rutas admin | OK |
| Rate limiting (bookings, contact, reviews, login) | OK; desactivado en tests vía `pytest.ini` |
| `TRUST_PROXY_HEADERS=false` por defecto | OK |
| Path traversal en `LocalFileStorage` | OK |
| Validación de imágenes (galería) | OK |
| Health no filtra errores BD en prod (`DEBUG=False`) | OK |
| CORS configurable | OK |
| Docs OpenAPI solo si `DEBUG` | OK |

**Limitaciones aceptadas (documentadas en código):**

- Rate limit **en memoria** → no sirve multi-instancia sin Redis.
- Sin refresh token / revocación JWT.
- Sin CAPTCHA en formularios públicos (contacto, reseñas, reservas).
- Reseñas y contacto pueden ser spam si no hay límites adicionales (solo rate limit por IP).

---

## 6. Coherencia API y contratos

### 6.1 Incoherencias detectadas

| # | Problema | Impacto | Sugerencia |
|---|----------|---------|------------|
| 1 | `BookingUpdate.estado` incluye `"cancelada"` pero el caso de uso rechaza con 400 | Confusión en Swagger / frontend | Quitar `cancelada` del `Literal` y documentar solo `DELETE` |
| 2 | `BookingCreate.servicio_nombre` opcional sigue en el schema | Cliente cree que puede falsificar el nombre | Eliminar del schema o marcar `deprecated` / ignorado en descripción |
| 3 | `POST /api/contact/` sin `response_model` tipado | Contrato OpenAPI incompleto | `ContactSubmitResponse` Pydantic |
| 4 | `GET /services/{id}` sin filtro `activo` | Detalle de servicio retirado visible | 404 si `not activo` en ruta pública |
| 5 | Versión API en `health.py` (`1.0.0`) vs `main.py` FastAPI version | Menor | Unificar constante |

### 6.2 Coherencia interna dominio ↔ API ↔ BD

- Estados de reserva alineados entre entidad, schema, ORM y stats.
- `BOOKING_ACTIVE_STATES` centralizado en `rules.py` y usado en repositorio.
- Stats: `deleted_at` en conteos e ingresos; distribución por estado mantiene historial (decisión consciente y acertada).

---

## 7. Comentarios y documentación en código

### 7.1 Buen nivel de comentarios (ejemplos)

| Archivo | Tipo de comentario |
|---------|-------------------|
| `app/infrastructure/persistence/repositories/booking.py` | Módulo: soft-delete, semántica cancelada |
| `app/domain/booking/entity.py` | `deleted_at` B-22 |
| `app/api/routers/gallery.py` | Validaciones de subida paso a paso |
| `app/api/routers/health.py` | Cabecera y comportamiento DEBUG |
| `app/core/rate_limit.py` | Uso, limitación multi-proceso |
| `app/database.py` | Alembic vs `create_tables` |
| `app/config.py` | Variables sensibles y CORS |
| `app/api/dependencies/auth.py` | Cuándo usar `get_current_admin` vs opcional |

### 7.2 Donde faltan comentarios útiles (no obvios)

| Archivo | Qué documentar |
|---------|----------------|
| `app/domain/booking/rules.py` | Por qué solo UTC y por qué `completada` no está en `BOOKING_ACTIVE_STATES` |
| `app/domain/booking/use_cases.py` | Transiciones de estado permitidas; por qué no hay `completar()` en UC |
| `app/api/routers/bookings.py` | Por qué validación de servicio está en router y no en dominio |
| `app/infrastructure/persistence/repositories/stats.py` | Por qué `_distribucion_por_estado` no filtra `deleted_at` |
| `app/domain/service/use_cases.py` | Sin comentarios; código autoexplicativo |

**Criterio senior:** Los comentarios actuales están **donde hay riesgo o decisión no obvia** (seguridad, soft-delete, proxy). No hace falta comentar cada función CRUD. Sí conviene **2–3 comentarios de negocio** en booking sobre slots por instante vs duración, para el próximo desarrollador.

### 7.3 Documentación externa

- **README:** reglas de reservas, proxy, endpoints, tests — **alineado con `main`**.
- **`docs/REPORTE.md`:** registro del último refactor; útil como histórico, no sustituye esta auditoría.
- **`docs/auditoria-backend.html`:** no revisado en esta pasada; mantener sincronizado si existe versión publicada.

---

## 8. Tests y calidad

```
251 passed (~4,6–6 s)
Cobertura app/: 98,61 % (22 líneas sin cubrir)
```

| Capa | Cobertura |
|------|-----------|
| Domain + repositories | ~100 % en la mayoría |
| `main.py` (SPA) | 83 % — ramas solo con `static_frontend/` |
| `stats.py` | 98 % |

**Fortalezas:**

- Integración API por router + repositorios.
- Unitarios de reglas, auth, gallery delete order, rate limit proxy, path traversal.
- Fixture `seed_booking_service` para reservas.
- `test_no_legacy`.

**Huecos de test (negocio, no bugs probados):**

- No hay test E2E de solapamiento por duración (porque no existe la regla).
- No hay test de “completada antes de `fecha_hora`”.
- Migración `0002` no se aplica en tests en memoria (`create_all`); la integridad en prod depende de ejecutar Alembic.

---

## 9. Migraciones y despliegue

| Revisión | Contenido |
|----------|-----------|
| `0001` | Esquema inicial 6 tablas |
| `0002` | Índice único parcial `uq_bookings_slot_active` + índice `(fecha_hora, deleted_at)` |

**Checklist producción:**

1. `alembic upgrade head` en cada entorno.
2. `TRUST_PROXY_HEADERS=true` solo detrás de proxy fiable.
3. `SECRET_KEY`, SMTP y Cloudinary según entorno.
4. Confirmar que el frontend usa `DELETE` para cancelar, no `PATCH cancelada`.

---

## 10. Hallazgos priorizados

### Alta (producto / datos)

| ID | Hallazgo |
|----|----------|
| H1 | Slots por **instante**, no por **duración** del servicio → solapes posibles en horarios cercanos |
| H2 | Sin **horario de apertura** ni bloqueo de domingos/festivos |
| H3 | Sin **FK** `bookings.servicio_id` → `services.id` |

### Media (API / UX desarrollador)

| ID | Hallazgo |
|----|----------|
| M1 | `servicio_nombre` en body de creación es ignorado |
| M2 | `BookingUpdate` permite `cancelada` en schema pero no en runtime |
| M3 | `GET /services/{id}` expone servicios inactivos |
| M4 | `completada` sin validar que la cita ya haya pasado (edge case) |

### Baja (mantenimiento)

| ID | Hallazgo |
|----|----------|
| B1 | DI repetida en routers |
| B2 | Rate limit no distribuido |
| B3 | `create_admin.py` usa `create_tables` en lugar de Alembic |
| B4 | Comentario personalizado en `admin.py` |
| B5 | README `migrations/` vs `alembic/` |

---

## 11. Matriz de módulos vs necesidades web barbería

| Necesidad web típica | Backend `main` |
|----------------------|----------------|
| Ver servicios y precios | Sí |
| Reservar cita online | Sí (con límites de slot) |
| Ver huecos libres por día | Sí (`/disponibilidad` — ocupados, no “libres”) |
| Panel admin citas | Sí |
| Exportar citas | Sí (CSV) |
| Galería de cortes | Sí |
| Reseñas con moderación | Sí |
| Formulario contacto | Sí |
| Dashboard ingresos / stats | Sí (estimados) |
| Varios barberos con agenda | No (solo texto) |
| Recordatorios SMS | No (solo email opcional) |
| Pago online | No |

---

## 12. Recomendaciones (orden sugerido)

1. **Documentar en `rules.py` o README** que el slot es un instante, no un rango (evita malentendidos).
2. **Quitar `cancelada` y `servicio_nombre`** del contrato de creación/actualización en OpenAPI.
3. **Planificar slots por duración** si el frontend ya trabaja con intervalos (cambio de mayor impacto).
4. **Añadir FK** servicio–reserva en migración `0003` (con limpieza de huérfanos).
5. **Validar `completada`** solo si `fecha_hora + duracion <= now` (opcional, mejora operativa).
6. **Unificar** bootstrap admin con Alembic o documentar el flujo híbrido.

---

## 13. Conclusión

La rama **`main`** presenta un backend **alineado con arquitectura hexagonal**, **seguro en lo esencial** para una barbería con panel admin, y **bien probado**. El código es **lógico** para: catálogo, reservas, reseñas, galería, contacto y estadísticas.

Las brechas principales no son de “código desordenado”, sino de **modelo de negocio simplificado** (citas punta a punta, un barbero genérico, sin horario del local), aceptable en un MVP y mejorable de forma incremental.

**Estado global:** apto para seguir en producción con las precauciones de despliegue (`alembic upgrade head`, proxy, SMTP) y consciencia de las limitaciones de slots y duración.

---

*Documento generado tras revisión estática del código y ejecución de `pytest -q` y `pytest --cov=app` en `main` @ `10e8ba6`.*
