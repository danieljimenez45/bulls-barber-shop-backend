"""Tests de notificadores SMTP (sin envío real)."""

from datetime import datetime

import pytest

from app.domain.booking.entity import Booking
from app.domain.contact.entity import ContactMessage
from app.infrastructure.notifications.booking_notifier import SMTPBookingNotifier
from app.infrastructure.notifications.contact_notifier import SMTPContactNotifier


def _booking(**kwargs) -> Booking:
    defaults = dict(
        nombre_cliente="Juan",
        telefono="600111222",
        servicio_id=1,
        servicio_nombre="Corte",
        fecha_hora=datetime(2030, 6, 1, 10, 0),
        email="cliente@test.com",
    )
    defaults.update(kwargs)
    return Booking(**defaults)


@pytest.mark.unit
def test_booking_notifier_envia_email_cliente_y_admin(mocker):
    from app.config import settings

    send = mocker.patch("app.infrastructure.notifications.booking_notifier.send_email")
    mocker.patch.object(settings, "ADMIN_EMAIL", "admin@barber.com")

    SMTPBookingNotifier().notify_new_booking(_booking())

    assert send.call_count == 2


@pytest.mark.unit
def test_booking_notifier_sin_admin_email_solo_cliente(mocker):
    from app.config import settings

    mocker.patch.object(settings, "ADMIN_EMAIL", "")
    send = mocker.patch("app.infrastructure.notifications.booking_notifier.send_email")

    SMTPBookingNotifier().notify_new_booking(_booking())

    assert send.call_count == 1


@pytest.mark.unit
def test_booking_notifier_sin_email_cliente_solo_admin(mocker):
    from app.config import settings

    mocker.patch.object(settings, "ADMIN_EMAIL", "admin@barber.com")
    send = mocker.patch("app.infrastructure.notifications.booking_notifier.send_email")

    SMTPBookingNotifier().notify_new_booking(_booking(email=None))

    assert send.call_count == 1


@pytest.mark.unit
def test_contact_notifier_envia_email_si_hay_admin(mocker):
    from app.config import settings

    mocker.patch.object(settings, "ADMIN_EMAIL", "admin@barber.com")
    send = mocker.patch("app.infrastructure.notifications.contact_notifier.send_email")
    msg = ContactMessage(
        nombre="Ana",
        email="ana@test.com",
        telefono="600000000",
        asunto="Hola",
        mensaje="Mensaje de prueba",
    )
    SMTPContactNotifier().notify(msg)
    send.assert_called_once()


@pytest.mark.unit
def test_contact_notifier_sin_admin_no_envia_email(mocker):
    from app.config import settings

    mocker.patch.object(settings, "ADMIN_EMAIL", "")
    send = mocker.patch("app.infrastructure.notifications.contact_notifier.send_email")
    msg = ContactMessage(
        nombre="Ana",
        email="ana@test.com",
        mensaje="Hola",
    )
    SMTPContactNotifier().notify(msg)
    send.assert_not_called()
