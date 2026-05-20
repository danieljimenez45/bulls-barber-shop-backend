from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain.service.entity import Service
from app.domain.service.ports import IServiceRepository, ServiceNotFound
from app.infrastructure.persistence.orm.service import ServiceORM


class SQLAlchemyServiceRepository(IServiceRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_entity(orm: ServiceORM) -> Service:
        return Service(
            id=orm.id,
            nombre=orm.nombre,
            descripcion=orm.descripcion,
            precio=orm.precio,
            duracion_minutos=orm.duracion_minutos,
            categoria=orm.categoria,
            imagen_url=orm.imagen_url,
            activo=orm.activo,
            orden=orm.orden,
        )

    def create(self, service: Service) -> Service:
        orm = ServiceORM(
            nombre=service.nombre,
            descripcion=service.descripcion,
            precio=service.precio,
            duracion_minutos=service.duracion_minutos,
            categoria=service.categoria,
            imagen_url=service.imagen_url,
            activo=service.activo,
            orden=service.orden,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def get_by_id(self, service_id: int) -> Optional[Service]:
        orm = (
            self._session.query(ServiceORM)
            .filter(ServiceORM.id == service_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def list(
        self,
        solo_activos: bool = True,
        categoria: Optional[str] = None,
    ) -> List[Service]:
        query = self._session.query(ServiceORM)
        if solo_activos:
            query = query.filter(ServiceORM.activo == True)  # noqa: E712
        if categoria:
            query = query.filter(ServiceORM.categoria == categoria)
        return [
            self._to_entity(o)
            for o in query.order_by(ServiceORM.orden).all()
        ]

    def update(self, service: Service) -> Service:
        orm = (
            self._session.query(ServiceORM)
            .filter(ServiceORM.id == service.id)
            .first()
        )
        if not orm:
            raise ServiceNotFound(f"Servicio {service.id} no encontrado")
        orm.nombre = service.nombre
        orm.descripcion = service.descripcion
        orm.precio = service.precio
        orm.duracion_minutos = service.duracion_minutos
        orm.categoria = service.categoria
        orm.imagen_url = service.imagen_url
        orm.activo = service.activo
        orm.orden = service.orden
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def delete(self, service_id: int) -> None:
        orm = (
            self._session.query(ServiceORM)
            .filter(ServiceORM.id == service_id)
            .first()
        )
        if not orm:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        self._session.delete(orm)
        self._session.commit()
