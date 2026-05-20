from abc import ABC, abstractmethod

from app.domain.stats.entity import StatsSnapshot


class IStatsRepository(ABC):

    @abstractmethod
    def get_snapshot(self) -> StatsSnapshot:
        """Devuelve una instantánea completa de estadísticas del negocio."""
