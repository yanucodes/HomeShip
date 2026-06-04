"""Service layer for Ship: orchestrates operations on ship, its tasks and
supplies."""
import uuid
from models import Ship, ShipMember, Supply, Task
from repositories import (ShipMemberRepository, ShipRepository,
                          TaskRepository, SupplyRepository, UserRepository)
from schemas import ShipMemberAdd, TaskCreate, SupplyCreate


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

    def delete_supply(self, supply: Supply) -> None:
        """
        Delete supply from the ship.

        Args:
            supply: Supply to delete.
        """
        self.supply_repository.delete(supply)

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
