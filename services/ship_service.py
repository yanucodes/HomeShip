"""Service layer for Ship: orchestrates operations on ship, its tasks and
supplies."""
import uuid
from models import Ship, ShipMember, Supply, Task, User
from repositories import (ShipMemberRepository, ShipRepository,
                          TaskRepository, SupplyRepository)
from schemas import ShipMemberCreate, TaskCreate, SupplyCreate


class ShipService:
    def __init__(self,
                 ship_repository: ShipRepository,
                 ship_member_repository: ShipMemberRepository,
                 task_repository: TaskRepository,
                 supply_repository: SupplyRepository):
        self.ship_repository = ship_repository
        self.ship_member_repository = ship_member_repository
        self.task_repository = task_repository
        self.supply_repository = supply_repository

    def create_task(self, ship: Ship, task_data: TaskCreate) -> Task:
        """Create a task belonging to the given ship.

        Args:
            ship: Ship for which the task is created
            task_data: Validated task fields from the request.

        Returns:
            The newly created Task.
        """
        task = self.task_repository.add(
            Task(**task_data.model_dump(), ship_id=ship.ship_id)
        )
        return task

    def get_tasks(self, ship: Ship) -> list[Task]:
        """
        Get all tasks for the ship.

        Args:
            ship: Ship whose tasks to get.

        Returns:
            List of Task objects.
        """
        return ship.tasks

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
        supply = self.supply_repository.add(
            Supply(**supply_data.model_dump(), ship_id=ship.ship_id)
        )
        return supply

    def get_supplies(self, ship: Ship) -> list[Supply]:
        """
        Get all supplies for the ship.

        Args:
            ship: Ship whose supplies to get.

        Returns:
            List of Supply objects.
        """
        return ship.supplies

    def delete_supply(self, supply: Supply) -> None:
        """
        Delete supply from the ship.

        Args:
            supply: Supply to delete.
        """
        self.supply_repository.delete(supply)

    def add_member_to_ship(self, user: User, ship: Ship,
                   ship_member_data: ShipMemberCreate) -> ShipMember:
        """
        Add user as a new member of the crew on the ship.

        Args:
            user: User to add.
            ship: Ship to which a member is being added.
            ship_member_data: Validated ship member fields from the request.

        Returns:
            Newly created ShipMember object.
        """
        new_member = ShipMember(
            user_id=user.user_id,
            ship_id=ship.ship_id,
            **ship_member_data.model_dump()
        )
        self.ship_member_repository.add(new_member)
        return new_member