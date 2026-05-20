import logging

from app.domain.booking.entity import Booking
from app.domain.booking.ports import IBookingNotifier
from app.infrastructure.notifications.smtp_email import send_email

logger = logging.getLogger(__name__)


class SMTPBookingNotifier(IBookingNotifier):
    """Envía emails de confirmación al cliente y de aviso a Jonathan."""

    def notify_new_booking(self, booking: Booking) -> None:
        from app.config import settings

        fecha_fmt = booking.fecha_hora.strftime("%d/%m/%Y a las %H:%M")
        servicio = booking.servicio_nombre or f"Servicio #{booking.servicio_id}"

        # ── Email al cliente (solo si dejó email) ──────────────────────────────
        if booking.email:
            send_email(
                to=booking.email,
                subject="Confirmación de reserva — Bulls Barber Shop",
                body=(
                    f"Hola {booking.nombre_cliente},\n\n"
                    "Tu reserva ha sido recibida correctamente.\n\n"
                    f"  Fecha y hora : {fecha_fmt}\n"
                    f"  Servicio     : {servicio}\n"
                    f"  Barbero      : {booking.barbero}\n"
                    "  Dirección    : C. de Pepe Isbert 5, Ciudad Lineal, Madrid\n\n"
                    "Si necesitas cancelar o cambiar tu cita, llámanos al 632 548 698.\n\n"
                    "¡Hasta pronto!\n"
                    "Bulls Barber Shop · @bulls.barber.shop98\n"
                ),
            )

        # ── Notificación a Jonathan ────────────────────────────────────────────
        if settings.ADMIN_EMAIL:
            send_email(
                to=settings.ADMIN_EMAIL,
                subject=f"Nueva reserva — {booking.nombre_cliente} · {fecha_fmt}",
                body=(
                    "Nueva cita recibida en la web:\n\n"
                    f"  Cliente   : {booking.nombre_cliente}\n"
                    f"  Teléfono  : {booking.telefono}\n"
                    f"  Email     : {booking.email or '—'}\n"
                    f"  Servicio  : {servicio}\n"
                    f"  Fecha/hora: {fecha_fmt}\n"
                    f"  Notas     : {booking.notas or '—'}\n"
                ),
            )
        else:
            logger.info(
                "[BOOKING] ADMIN_EMAIL no configurado — aviso a Jonathan no enviado."
            )
