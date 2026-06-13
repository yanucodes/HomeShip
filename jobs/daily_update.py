"""Daily ship update job.

Advances every ship one day: accrues distance from the day's alert mix, then
re-evaluates each task and supply (overdue tasks escalate, supply deadlines
tick closer). Runnable as `python -m jobs.daily_update`; the scheduler that
fires it (Render Cron, system cron, manual run).
"""
import logging
from datetime import date

from database import SessionLocal
from repositories import (
    ShipMemberRepository,
    ShipRepository,
    SupplyRepository,
    TaskRepository,
    UserRepository,
)
from services import ShipService

logger = logging.getLogger(__name__)


def run(today: date | None = None) -> None:
    """Run the daily update over all ships in one transaction.

    Wires a ShipService onto a fresh session (the same composition as the
    request-time `dependencies.get_ship_service`), advances each ship via
    `ShipService.run_daily`, and commits once so the run is atomic — any
    failure rolls every ship back rather than leaving some advanced and others
    not.

    Args:
        today: Reference date passed through to `run_daily`; defaults to
            `date.today()`. Injectable to keep the job deterministic in tests.
    """
    today = today or date.today()
    session = SessionLocal()
    try:
        ship_repository = ShipRepository(session)
        service = ShipService(
            ship_repository=ship_repository,
            ship_member_repository=ShipMemberRepository(session),
            task_repository=TaskRepository(session),
            supply_repository=SupplyRepository(session),
            user_repository=UserRepository(session),
        )
        ships = ship_repository.get_all()
        for ship in ships:
            service.run_daily(ship, today)
        session.commit()
        logger.info("Daily update committed for %d ship(s) (today=%s).",
                    len(ships), today)
    except Exception:
        session.rollback()
        logger.exception("Daily update failed (today=%s); rolled back.", today)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
