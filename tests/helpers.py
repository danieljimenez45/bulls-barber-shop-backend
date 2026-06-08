"""
Utilidades compartidas para payloads y datos de prueba.

Centraliza valores por defecto para evitar divergencias entre módulos de test.
"""

from datetime import datetime

# Slots futuros estables (evitan colisiones con datos reales).
# Todos en :00 o :30 para cumplir la validación del grid.
FUTURE_SLOT   = "2030-12-01T10:00:00"
FUTURE_SLOT_2 = "2030-12-01T11:00:00"
FUTURE_SLOT_3 = "2030-12-01T10:30:00"


def booking_payload(**kwargs) -> dict:
    defaults = {
        "nombre_cliente": "Pedro Martínez",
        "telefono": "611222333",
        "servicio_id": 1,
        "fecha_hora": FUTURE_SLOT,
    }
    defaults.update(kwargs)
    return defaults


def service_payload(**kwargs) -> dict:
    defaults = {
        "nombre": "Corte Clásico",
        "descripcion": "Corte tradicional",
        "precio": 15.0,
        "duracion_minutos": 30,
        "categoria": "corte",
        "activo": True,
        "orden": 0,
    }
    defaults.update(kwargs)
    return defaults


def review_payload(**kwargs) -> dict:
    defaults = {
        "nombre": "Cliente Satisfecho",
        "valoracion": 5,
        "comentario": "Excelente servicio",
    }
    defaults.update(kwargs)
    return defaults


def contact_payload(**kwargs) -> dict:
    defaults = {
        "nombre": "María López",
        "email": "maria@example.com",
        "telefono": "600111222",
        "asunto": "Consulta",
        "mensaje": "Quisiera información sobre horarios.",
    }
    defaults.update(kwargs)
    return defaults


def domain_booking(**kwargs):
    """Entidad de dominio Booking para tests de repositorio."""
    from app.domain.booking.entity import Booking

    defaults = dict(
        nombre_cliente="Cliente Test",
        telefono="600000001",
        servicio_id=1,
        servicio_nombre="Corte",
        fecha_hora=datetime(2025, 8, 15, 10, 0),
        estado="pendiente",
    )
    defaults.update(kwargs)
    return Booking(**defaults)
