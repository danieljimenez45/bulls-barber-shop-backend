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

    def execute(self, service_id: int, **fields) -> Service:
        service = self._repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        for key, value in fields.items():
            if value is not None and hasattr(service, key):
                setattr(service, key, value)
        return self._repo.update(service)


class DeleteServiceUseCase:
    def __init__(self, repo: IServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: int) -> None:
        service = self._repo.get_by_id(service_id)
        if not service:
            raise ServiceNotFound(f"Servicio {service_id} no encontrado")
        self._repo.delete(service_id)
