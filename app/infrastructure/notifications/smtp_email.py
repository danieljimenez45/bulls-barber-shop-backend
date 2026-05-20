"""
Función de bajo nivel para enviar emails via SMTP.
Si SMTP_HOST está vacío, loguea y no hace nada (útil en desarrollo).
Los errores nunca propagan — el fallo de email no rompe el flujo principal.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    from app.config import settings

    if not settings.SMTP_HOST:
        logger.info(
            "[EMAIL] SMTP no configurado — email no enviado. Para: %s | Asunto: %s",
            to,
            subject,
        )
        return

    remitente = settings.EMAIL_FROM or settings.SMTP_USER

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = remitente
        msg["To"] = to
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.ehlo()
            # STARTTLS para puerto 587 (TLS) — no para puerto 465 (SSL directo)
            if settings.SMTP_PORT != 465:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(remitente, to, msg.as_string())

        logger.info("[EMAIL] Enviado a %s — %s", to, subject)

    except Exception as exc:  # noqa: BLE001
        # El fallo de email nunca debe romper la reserva o el contacto
        logger.error("[EMAIL] Error enviando a %s (%s): %s", to, subject, exc)
