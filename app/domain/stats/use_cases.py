from app.domain.stats.entity import StatsSnapshot
from app.domain.stats.ports import IStatsRepository


class GetStatsUseCase:
    """Obtiene la instantánea de estadísticas del negocio para el dashboard."""

    def __init__(self, repo: IStatsRepository) -> None:
        self._repo = repo

    def execute(self) -> StatsSnapshot:
        return self._repo.get_snapshot()
