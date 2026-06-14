"""Hourly ship update job.

Runs every hour and advances each ship once per local day, when its own
`settings.daily_rollover_hour` has arrived in its timezone (see
`ShipService.run_daily`). Advancing accrues distance from the day's alert mix,
then re-evaluates each task and supply (overdue tasks escalate, supply
deadlines tick closer). Runnable as `python -m jobs.hourly_update`; the
scheduler that fires it (Render Cron, system cron, manual run).
"""
import logging
from datetime import datetime, timezone

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


def run(now: datetime | None = None) -> None:
    """Run the hourly update over all ships in one transaction.

    Wires a ShipService onto a fresh session (the same composition as the
    request-time `dependencies.get_ship_service`), offers each ship to
    `ShipService.run_daily` (which advances it only if its local rollover hour
    has arrived), and commits once so the run is atomic — any failure rolls
    every ship back rather than leaving some advanced and others not.

    A single reference instant is captured up front and passed to every ship,
    so the run is consistent; each ship converts it to its own timezone to get
    its local date and hour.

    Args:
        now: Reference instant passed through to `run_daily`; defaults to
            `datetime.now(timezone.utc)`. Injectable to keep the job
            deterministic in tests.
    """
    now = now or datetime.now(timezone.utc)
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
        advanced = sum(service.run_daily(ship, now) for ship in ships)
        session.commit()
        logger.info("Hourly update committed: advanced %d of %d ship(s) "
                    "(now=%s).", advanced, len(ships), now)
    except Exception:
        session.rollback()
        logger.exception("Hourly update failed (now=%s); rolled back.", now)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
