import logging

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import IContactNotifier
from app.infrastructure.notifications.smtp_email import send_email

logger = logging.getLogger(__name__)


class SMTPContactNotifier(IContactNotifier):
    """Reenvía el mensaje de contacto al email del barbero (ADMIN_EMAIL)."""

    def notify(self, message: ContactMessage) -> None:
        from app.config import settings

        # Siempre loguear (útil en desarrollo)
        logger.info(
            "[CONTACTO] De: %s (%s) — Asunto: %s — %s",
            message.nombre,
            message.email,
            message.asunto or "(sin asunto)",
            message.mensaje,
        )

        if not settings.ADMIN_EMAIL:
            logger.info(
                "[CONTACTO] ADMIN_EMAIL no configurado — mensaje no reenviado por email."
            )
            return

        send_email(
            to=settings.ADMIN_EMAIL,
            subject=f"Mensaje web — {message.asunto or 'Sin asunto'} · {message.nombre}",
            body=(
                "Nuevo mensaje de contacto recibido en la web:\n\n"
                f"  Nombre   : {message.nombre}\n"
                f"  Email    : {message.email}\n"
                f"  Teléfono : {message.telefono or '—'}\n"
                f"  Asunto   : {message.asunto or '—'}\n\n"
                "Mensaje:\n"
                f"{message.mensaje}\n"
            ),
        )
