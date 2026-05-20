from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.service.entity import Service


class ServiceNotFound(Exception):
    """Se lanza cuando no se encuentra un servicio por su ID."""


class IServiceRepository(ABC):

    @abstractmethod
    def create(self, service: Service) -> Service: ...

    @abstractmethod
    def get_by_id(self, service_id: int) -> Optional[Service]: ...

    @abstractmethod
    def list(
        self,
        solo_activos: bool = True,
        categoria: Optional[str] = None,
    ) -> List[Service]: ...

    @abstractmethod
    def update(self, service: Service) -> Service: ...

    @abstractmethod
    def delete(self, service_id: int) -> None: ...
