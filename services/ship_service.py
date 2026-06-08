"""Service layer for Ship: orchestrates operations on ship, its tasks and
supplies."""
import uuid
from datetime import date, timedelta
from models import Ship, ShipMember, Supply, Task
from models.supply import StockState
from repositories import (ShipMemberRepository, ShipRepository,
                          TaskRepository, SupplyRepository, UserRepository)
from schemas import (ShipMemberAdd, ShipMemberUpdate, TaskCreate, TaskUpdate,
                     SupplyCreate, SupplyUpdate)


class ShipService:
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

    def get_ship_by_id(self, ship_id: uuid.UUID) -> Ship | None:
        """
        Find ship by its ID.

        Args:
            ship_id: UUID of that ship.

        Returns:
            Ship object or None if ship is not found.
        """
        return self.ship_repository.get(ship_id)

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
        return self.task_repository.update(task, task.get_changes_on_completing())

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
        supply = Supply.set_alert_on_creation(
            ship_id=ship.ship_id,
            name=supply_data.name,
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
        return self.supply_repository.update(
            supply, supply.get_changes_on_stock_state_change(stock_state))

    def reschedule_supply(self, supply: Supply, date_due: date) -> Supply:
        """
        Reschedule a supply's buy-by deadline, re-deriving its alert state.

        Args:
            supply: Supply whose deadline is being rescheduled.
            date_due: Validated new buy-by deadline from the request body.

        Returns:
            The updated supply.
        """
        return self.supply_repository.update(
            supply, supply.get_changes_on_reschedule(date_due))

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
