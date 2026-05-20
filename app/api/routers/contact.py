from fastapi import APIRouter

from app.api.schemas.contact import ContactMessageIn
from app.domain.contact.entity import ContactMessage
from app.domain.contact.use_cases import SendContactMessageUseCase
from app.infrastructure.notifications.contact_notifier import SMTPContactNotifier

router = APIRouter()


@router.post("/")
def enviar_mensaje(data: ContactMessageIn):
    """Recibe un mensaje de contacto y lo reenvía al barbero por email."""
    message = ContactMessage(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        asunto=data.asunto,
        mensaje=data.mensaje,
    )
    notifier = SMTPContactNotifier()
    uc = SendContactMessageUseCase(notifier)
    uc.execute(message)
    return {
        "ok": True,
        "mensaje": "Mensaje recibido. Nos pondremos en contacto contigo pronto.",
    }
