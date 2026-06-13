"""Repository for Ship."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import Ship

from .base_repository import BaseRepository


class ShipRepository(BaseRepository[Ship]):
    """CRUD operations on Ship model."""
    model = Ship

    def get_all(self) -> list[Ship]:
        """Fetch every ship with its tasks and supplies eagerly loaded.

        Used by the daily distance cron, which touches each ship's items. The
        `selectinload` options pull all tasks and supplies in two extra
        queries (one per relationship) rather than one-per-ship, keeping the
        whole scan at three queries regardless of how many ships exist. Those
        same loaded objects serve both the alert count and the per-item
        update, so no separate aggregate query is needed.

        Returns:
            A list of all ships, each with `tasks` and `supplies` populated.
        """
        statement = (
            select(Ship)
            .options(selectinload(Ship.tasks), selectinload(Ship.supplies))
        )
        return list(self.session.scalars(statement))
