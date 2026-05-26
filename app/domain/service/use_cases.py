from typing import List, Optional

from app.domain.service.entity import Service
from app.domain.service.ports import IServiceRepository, ServiceNotFound


class ListServicesUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(
        self,
        solo_activos: bool = True,
        categoria: Optional[str] = None,
    ) -> List[Service]:
        return self._repo.list(solo_activos=solo_activos, categoria=categoria)


class GetServiceUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: int) -> Service:
        service = self._repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        return service


class CreateServiceUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(self, service: Service) -> Service:
        return self._repo.create(service)


class UpdateServiceUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(
        self,
        service_id: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        precio: float | None = None,
        duracion_minutos: int | None = None,
        categoria: str | None = None,
        imagen_url: str | None = None,
        activo: bool | None = None,
        orden: int | None = None,
    ) -> Service:
        service = self._repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        if nombre is not None:
            service.nombre = nombre
        if descripcion is not None:
            service.descripcion = descripcion
        if precio is not None:
            service.precio = precio
        if duracion_minutos is not None:
            service.duracion_minutos = duracion_minutos
        if categoria is not None:
            service.categoria = categoria
        if imagen_url is not None:
            service.imagen_url = imagen_url
        if activo is not None:
            service.activo = activo
        if orden is not None:
            service.orden = orden
        return self._repo.update(service)


class DeleteServiceUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: int) -> None:
        service = self._repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        self._repo.delete(service_id)
