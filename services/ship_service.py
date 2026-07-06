"""Service layer for Ship: orchestrates operations on ship, its tasks and
supplies."""
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from config import settings
from models import Ship, ShipMember, Supply, Task
from models.supply import StockState
from repositories import (ShipMemberRepository, ShipRepository,
                          TaskRepository, SupplyRepository, UserRepository)
from schemas import (ShipMemberAdd, ShipMemberUpdate, TaskCreate, TaskUpdate,
                     SupplyCreate, SupplyUpdate)


class ShipService:
    """Application-service for a ship and the tasks, supplies and crew it
    owns."""

    def __init__(self,
                 ship_repository: ShipRepository,
                 ship_member_repository: ShipMemberRepository,
                 task_repository: TaskRepository,
                 supply_repository: SupplyRepository,
                 user_repository: UserRepository):
        self.ship_repository = ship_repository
        self.ship_member_repository = ship_member_repository
        self.task_repository = task_repository
        self.supply_repository = supply_repository
        self.user_repository = user_repository

    @staticmethod
    def _supply_deadline_windows() -> tuple[timedelta, timedelta]:
        """Build the supply deadline urgency windows from settings.

        Returns:
            The `(red_within, yellow_within)` timedeltas that
            `Supply.derive_alert` uses to grade a deadline supply's urgency.
        """
        return (timedelta(days=settings.supply_deadline_red_days),
                timedelta(days=settings.supply_deadline_yellow_days))

    def get_ship_by_id(self, ship_id: uuid.UUID) -> Ship | None:
        """
        Find ship by its ID.

        Args:
            ship_id: UUID of that ship.

        Returns:
            Ship object or None if ship is not found.
        """
        return self.ship_repository.get(ship_id)

    def get_dashboard(self, ship: Ship) -> Ship:
        """Gather everything a client needs to render the ship's console.

        The ship object already carries all dashboard data — its tasks,
        supplies and crew relationships plus the derived `current_condition`,
        `current_speed` and `current_alerts` properties — so today this is a
        deliberate pass-through. It exists as the dashboard's orchestration
        point: eager loading or additional dashboard data would land here,
        not in the router.

        Args:
            ship: Ship whose console data to gather.

        Returns:
            The ship, ready to be serialized as a dashboard.
        """
        return ship

    def run_daily(self, ship: Ship, now: datetime | None = None) -> bool:
        """Advance the ship one day if its local rollover hour has arrived.

        Called once an hour by the cron for every ship. The reference instant
        `now` is converted to the ship's own timezone; the ship is advanced
        only when its local clock has reached `settings.daily_rollover_hour`
        and it has not already been advanced today. Using "at or past the hour"
        plus the `last_advanced_on` stamp makes the run idempotent and
        self-healing: a ship whose rollover-hour run was missed is still caught
        up by a later hourly run that day, and no ship is advanced twice.

        When it does advance, the ship's distance change is applied first,
        while alert states still reflect the previous day — so an item that
        turns critical only costs progress the *next* day, giving the crew a
        one-day grace window. Tasks and supplies are then re-evaluated:
        overdue tasks escalate and supply deadlines tick closer. Items whose
        `get_daily_changes` returns an empty dict (not overdue, no deadline,
        inactive, or unchanged) are left untouched.

        Args:
            ship: Ship to advance, with its tasks and supplies loaded.
            now: Reference instant; defaults to `datetime.now(timezone.utc)`.
                Converted to the ship's timezone to derive its local date and
                hour. Injectable to keep the logic deterministic in tests.

        Returns:
            True if the ship was advanced on this run; False if it was skipped
            because its local rollover hour has not yet arrived or it was
            already advanced today.
        """
        now = now or datetime.now(timezone.utc)
        local = now.astimezone(ZoneInfo(ship.timezone))
        today = local.date()
        if local.hour < settings.daily_rollover_hour or (
                ship.last_advanced_on is not None
                and ship.last_advanced_on >= today):
            return False
        postpone_time = timedelta(days=settings.default_postpone_days)
        red_within, yellow_within = self._supply_deadline_windows()
        ship_changes = ship.get_daily_changes(today)
        ship_changes["last_advanced_on"] = today
        self.ship_repository.update(ship, ship_changes)
        for task in ship.tasks:
            if changes := task.get_daily_changes(postpone_time, today):
                self.task_repository.update(task, changes)
        for supply in ship.supplies:
            if changes := supply.get_daily_changes(
                    red_within, yellow_within, today):
                self.supply_repository.update(supply, changes)
        return True

    def create_task(self, ship: Ship, task_data: TaskCreate) -> Task:
        """Create a task belonging to the given ship.

        Args:
            ship: Ship for which the task is created
            task_data: Validated task fields from the request.

        Returns:
            The newly created Task.
        """
        task = Task.scheduled(
            ship_id=ship.ship_id,
            content=task_data.content,
            frequency=task_data.frequency,
            date_last=task_data.date_last,
            date_due=task_data.date_due,
        )
        return self.task_repository.add(task)

    def get_tasks(self, ship: Ship) -> list[Task]:
        """
        Get all tasks for the ship.

        Args:
            ship: Ship whose tasks to get.

        Returns:
            List of Task objects.
        """
        return ship.tasks

    def get_task(self, ship: Ship, task_id: uuid.UUID) -> Task | None:
        """
        Get a single task belonging to the ship.

        Fetches the task by primary key and confirms it belongs to the
        given ship, so a task_id from another ship resolves to None rather
        than leaking across ships.

        Args:
            ship: Ship the task must belong to.
            task_id: UUID of the task to get.

        Returns:
            The Task, or None if no task with that id belongs to the ship.
        """
        task = self.task_repository.get(task_id)
        if task is not None and task.ship_id == ship.ship_id:
            return task
        return None

    def update_task(self, task: Task, task_data: TaskUpdate) -> Task:
        """
        Update task content.

        Args:
            task: Task to update.
            task_data: Validated fields from the request.

        Returns:
            Updated Task object.
        """
        changes = task_data.model_dump(exclude_unset=True)
        return self.task_repository.update(task, changes)

    def complete_task(self, task: Task) -> Task:
        """
        Complete the task. Updates date_last, date_due, and alert_state.

        Args:
            task: Task which was completed.

        Returns:
            Updated Task object.
        """
        return self.task_repository.update(task,
                                           task.get_changes_on_completing())

    def postpone_task(self, task: Task, date_due: date) -> Task | None:
        """
        Postpone a task to a later due date, escalating its alert state.

        Args:
            task: Task to postpone.
            date_due: New due date for the task.

        Returns:
            The updated Task, or None if the task cannot be postponed: it
            has no active due date, or the new date is not later than the
            current one. The caller turns None into a 400.
        """
        if task.date_due is None or date_due <= task.date_due:
            return None
        return self.task_repository.update(
            task, task.get_changes_on_postponing(date_due)
        )

    def change_task_frequency(
        self, task: Task, new_frequency: timedelta | None
    ) -> Task:
        """
        Change the frequency of a task.

        Re-derives the task's schedule (date_last, date_due) and alert
        state from the new frequency via
        `Task.get_changes_on_frequency_changing`.

        Args:
            task: Task whose frequency is being changed.
            new_frequency: Validated new frequency from the request body.

        Returns:
            The updated task.
        """
        return self.task_repository.update(
            task, task.get_changes_on_frequency_changing(new_frequency))

    def deactivate_task(self, task: Task) -> Task:
        """
        Deactivate task.

        Deactivating a task sets `frequency`, `date_due` and `date_last` to
        None and drops its `alert_state` to INACTIVE.

        Args:
            task: Task to deactivate.

        Returns:
            The updated task.
        """
        return self.task_repository.update(task,
                                           task.get_changes_on_deactivation())

    def delete_task(self, task: Task) -> None:
        """
        Delete task from the ship.

        Args:
            task: Task to delete.
        """
        self.task_repository.delete(task)

    def create_supply(self, ship: Ship, supply_data: SupplyCreate) -> Supply:
        """Create a supply belonging to the given ship.

        Args:
            ship: Ship for which the supply is created
            supply_data: Validated supply fields from the request.

        Returns:
            The newly created Supply.
        """
        red_within, yellow_within = self._supply_deadline_windows()
        supply = Supply.set_alert_on_creation(
            ship_id=ship.ship_id,
            name=supply_data.name,
            red_within=red_within,
            yellow_within=yellow_within,
            stock_state=supply_data.stock_state,
            quantity=supply_data.quantity,
            date_due=supply_data.date_due,
        )
        return self.supply_repository.add(supply)

    def get_supplies(self, ship: Ship) -> list[Supply]:
        """
        Get all supplies for the ship.

        Args:
            ship: Ship whose supplies to get.

        Returns:
            List of Supply objects.
        """
        return ship.supplies

    def get_supply(self, ship: Ship, supply_id: uuid.UUID) -> Supply | None:
        """
        Get a single supply belonging to the ship.

        Fetches the supply by primary key and confirms it belongs to the
        given ship, so a supply_id from another ship resolves to None rather
        than leaking across ships.

        Args:
            ship: Ship the supply must belong to.
            supply_id: UUID of the supply to get.

        Returns:
            The Supply, or None if no supply with that id belongs to the ship.
        """
        supply = self.supply_repository.get(supply_id)
        if supply is not None and supply.ship_id == ship.ship_id:
            return supply
        return None

    def update_supply(self, supply: Supply, supply_data: SupplyUpdate
                      ) -> Supply:
        """
        Update a supply's editable attributes (name, quantity).

        Args:
            supply: Supply to update.
            supply_data: Validated fields from the request.

        Returns:
            Updated Supply object.
        """
        changes = supply_data.model_dump(exclude_unset=True)
        return self.supply_repository.update(supply, changes)

    def change_supply_stock_state(
        self, supply: Supply, stock_state: StockState
    ) -> Supply:
        """
        Change a supply's stock state, re-deriving its alert state.

        Args:
            supply: Supply whose stock state is being changed.
            stock_state: Validated new stock state from the request body.

        Returns:
            The updated supply.
        """
        red_within, yellow_within = self._supply_deadline_windows()
        return self.supply_repository.update(
            supply, supply.get_changes_on_stock_state_change(
                stock_state, red_within, yellow_within))

    def reschedule_supply(self, supply: Supply, date_due: date) -> Supply:
        """
        Reschedule a supply's buy-by deadline, re-deriving its alert state.

        Args:
            supply: Supply whose deadline is being rescheduled.
            date_due: Validated new buy-by deadline from the request body.

        Returns:
            The updated supply.
        """
        red_within, yellow_within = self._supply_deadline_windows()
        return self.supply_repository.update(
            supply, supply.get_changes_on_reschedule(
                date_due, red_within, yellow_within))

    def deactivate_supply(self, supply: Supply) -> Supply:
        """
        Deactivate a supply (stop tracking it).

        Clears the supply's buy-by deadline and quantity and drops its
        alert_state to INACTIVE.

        Args:
            supply: Supply to deactivate.

        Returns:
            The updated supply.
        """
        return self.supply_repository.update(
            supply, supply.get_changes_on_deactivation())

    def delete_supply(self, supply: Supply) -> None:
        """
        Delete supply from the ship.

        Args:
            supply: Supply to delete.
        """
        self.supply_repository.delete(supply)

    def get_members(self, ship: Ship) -> list[ShipMember]:
        """
        Get all crew members of the ship.

        Args:
            ship: Ship whose members to get.

        Returns:
            List of ShipMember objects.
        """
        return ship.ship_memberships

    def add_member_to_ship(self, ship: Ship,
                           member_data: ShipMemberAdd) -> ShipMember | None:
        """
        Add an existing user to the ship's crew, found by email.

        Args:
            ship: Ship to which a member is being added.
            member_data: Validated member fields from the request.

        Returns:
            The newly created ShipMember, or None if no user has that email.
        """
        user = self.user_repository.get_by_email(member_data.email)
        if user is None:
            return None
        new_member = ShipMember(
            user_id=user.user_id,
            ship_id=ship.ship_id,
            role=member_data.role,
        )
        self.ship_member_repository.add(new_member)
        return new_member

    def update_ship_member(self, membership: ShipMember,
                           member_data: ShipMemberUpdate) -> ShipMember:
        """
        Update a crew member's editable attributes (role).

        Args:
            membership: Ship membership to update.
            member_data: Validated member fields from the request.

        Returns:
            Updated ShipMember object.
        """
        changes = member_data.model_dump(exclude_unset=True)
        return self.ship_member_repository.update(membership, changes)
