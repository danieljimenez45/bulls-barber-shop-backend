from fastapi import APIRouter

from app.api.schemas.contact import ContactMessageIn
from app.domain.contact.entity import ContactMessage
from app.domain.contact.use_cases import LogContactNotifier, SendContactMessageUseCase

router = APIRouter()


@router.post("/")
def enviar_mensaje(data: ContactMessageIn):
    """Recibe un mensaje de contacto y lo registra en el log."""
    message = ContactMessage(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        asunto=data.asunto,
        mensaje=data.mensaje,
    )
    notifier = LogContactNotifier()
    uc = SendContactMessageUseCase(notifier)
    uc.execute(message)
    return {
        "ok": True,
        "mensaje": "Mensaje recibido. Nos pondremos en contacto contigo pronto.",
    }
