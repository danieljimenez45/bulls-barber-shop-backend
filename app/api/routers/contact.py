"""
contact.py
─────────────────────────────────────────────────────────────────────────────
Router de mensajes de contacto.

Endpoints públicos:
  POST /api/contact/          — envía y persiste un mensaje de contacto

Endpoints de administración (JWT requerido):
  GET  /api/contact/          — lista mensajes paginados
  PATCH /api/contact/{id}/leido — marca un mensaje como leído
─────────────────────────────────────────────────────────────────────────────
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.dependencies.pagination import PaginationParams
from app.api.schemas.contact import ContactMessageIn, ContactMessageOut
from app.api.schemas.pagination import PagedResponse
from app.core.rate_limit import limiter
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import ContactMessageNotFound
from app.domain.contact.use_cases import (
    ListContactMessagesUseCase,
    MarkMessageReadUseCase,
    SendContactMessageUseCase,
)
from app.infrastructure.notifications.contact_notifier import SMTPContactNotifier
from app.infrastructure.persistence.repositories.contact import (
    SQLAlchemyContactRepository,
)

router = APIRouter()


# ── Público ───────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensaje de contacto",
)
def enviar_mensaje(
    data: ContactMessageIn,
    db:   Session = Depends(get_db),
    _rl:  None    = Depends(limiter(max_requests=5, window_seconds=60)),
):
    """
    Recibe un mensaje del formulario de contacto público.
    - Persiste el mensaje en la base de datos (B-24).
    - Envía notificación por email al barbero.
    """
    message = ContactMessage(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        asunto=data.asunto,
        mensaje=data.mensaje,
    )
    repo     = SQLAlchemyContactRepository(db)
    notifier = SMTPContactNotifier()
    uc       = SendContactMessageUseCase(notifier=notifier, repository=repo)
    saved    = uc.execute(message)

    return {
        "ok":     True,
        "id":     saved.id,
        "mensaje": "Mensaje recibido. Nos pondremos en contacto contigo pronto.",
    }


# ── Admin ─────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PagedResponse[ContactMessageOut],
    summary="Listar mensajes de contacto (admin)",
)
def listar_mensajes(
    solo_no_leidos: bool          = False,
    pagination:     PaginationParams = Depends(),
    db:             Session          = Depends(get_db),
    _admin:         AdminUser        = Depends(get_current_admin),
):
    """Lista todos los mensajes de contacto. Solo accesible para el admin."""
    repo  = SQLAlchemyContactRepository(db)
    uc    = ListContactMessagesUseCase(repo)
    items, total = uc.execute(
        solo_no_leidos=solo_no_leidos,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return PagedResponse(
        items=[ContactMessageOut.model_validate(m) for m in items],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pagination.total_pages(total),
    )


@router.patch(
    "/{message_id}/leido",
    response_model=ContactMessageOut,
    summary="Marcar mensaje como leído (admin)",
)
def marcar_leido(
    message_id: int,
    db:         Session   = Depends(get_db),
    _admin:     AdminUser = Depends(get_current_admin),
):
    """Marca el mensaje como leído. Solo accesible para el admin."""
    repo = SQLAlchemyContactRepository(db)
    uc   = MarkMessageReadUseCase(repo)
    try:
        updated = uc.execute(message_id)
        return ContactMessageOut.model_validate(updated)
    except ContactMessageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
