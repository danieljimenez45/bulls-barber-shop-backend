from fastapi import APIRouter
from app.schemas.contact import ContactMessage

router = APIRouter()


@router.post("/")
def enviar_mensaje(data: ContactMessage):
    """
    Recibe un mensaje de contacto.
    TODO: integrar envío de email con SMTP cuando esté configurado.
    """
    # Por ahora devolvemos confirmación — más adelante añadimos email
    print(f"[CONTACTO] De: {data.nombre} ({data.email}) — {data.mensaje}")
    return {
        "ok": True,
        "mensaje": "Mensaje recibido. Nos pondremos en contacto contigo pronto.",
    }
