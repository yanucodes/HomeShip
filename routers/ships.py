"""Ship endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import (get_ship_or_404, get_ship_service,
                          get_supply_or_404, get_task_or_404)
from models import Ship, Supply, Task
from schemas import (ShipRead, ShipMemberAdd, ShipMemberRead, SupplyCreate,
                     SupplyRead, TaskCreate, TaskRead)
from services import ShipService

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("/{ship_id}", response_model=ShipRead)
def get_ship(ship: Ship = Depends(get_ship_or_404)):
    """
    Fetch ship data.

    Args:
        ship: Ship resolved from the path's `ship_id` (404 if not found).

    Returns:
        The ship serialized as `ShipRead`.
    """
    return ship


@router.post("/{ship_id}/members", response_model=ShipMemberRead,
             status_code=status.HTTP_201_CREATED)
def add_member(member_data: ShipMemberAdd,
               ship: Ship = Depends(get_ship_or_404),
               service: ShipService = Depends(get_ship_service)):
    """
    Add an existing user to the ship's crew, identified by email.

    Args:
        member_data: Validated member fields from the request body (the
            email of the user to add plus their role).
        ship: Ship resolved from the path's `ship_id` (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The newly created ShipMember serialized as `ShipMemberRead`.
    """
    member = service.add_member_to_ship(ship, member_data)
    if member is None:
        raise HTTPException(status_code=404, detail="User not found")
    return member


@router.get("/{ship_id}/tasks", response_model=list[TaskRead])
def get_tasks(ship: Ship = Depends(get_ship_or_404), service:
              ShipService=Depends(get_ship_service)):
    """
    List all tasks belonging to the ship.

    Args:
        ship: Ship resolved from the path's `ship_id` (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The ship's tasks, each serialized as `TaskRead`. An empty list if
        the ship has no tasks.
    """
    return service.get_tasks(ship)


@router.post("/{ship_id}/tasks", response_model=TaskRead,
             status_code=status.HTTP_201_CREATED)
def add_task(task_data: TaskCreate,
             ship: Ship = Depends(get_ship_or_404),
             service: ShipService = Depends(get_ship_service)):
    """
    Add a new task to the ship.

    Args:
        task_data: Validated Task fields from the request body.
        ship: Ship resolved from the path's `ship_id` (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The newly created Task serialized as `TaskRead`.
    """
    return service.create_task(ship, task_data)


@router.delete("{ship_id}/tasks/{task_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task: Task = Depends(get_task_or_404),
                service: ShipService = Depends(get_ship_service)):
    """
    Delete task from the database.

    Task is only deleted if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        task: Task to delete.
        service: Ship service, injected by FastAPI via `get_ship_service`.
    """
    service.delete_task(task)


@router.get("/{ship_id}/supplies", response_model=list[SupplyRead])
def get_supplies(ship: Ship = Depends(get_ship_or_404), service:
              ShipService=Depends(get_ship_service)):
    """
    List all supplies belonging to the ship.

    Args:
        ship: Ship resolved from the path's `ship_id` (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The ship's supplies, each serialized as `SupplyRead`. An empty list if
        the ship has no supplies.
    """
    return service.get_supplies(ship)


@router.post("/{ship_id}/supplies", response_model=SupplyRead,
             status_code=status.HTTP_201_CREATED)
def add_supply(supply_data: SupplyCreate,
             ship: Ship = Depends(get_ship_or_404),
             service: ShipService = Depends(get_ship_service)):
    """
    Add a new supply to the ship.

    Args:
        supply_data: Validated Supply fields from the request body.
        ship: Ship resolved from the path's `ship_id` (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The newly created Supply serialized as `SupplyRead`.
    """
    return service.create_supply(ship, supply_data)


@router.delete("{ship_id}/supplies/{supply_id}",
               status_code=status.HTTP_204_NO_CONTENT)
def delete_supply(supply: Supply = Depends(get_supply_or_404),
                service: ShipService = Depends(get_ship_service)):
    """
    Delete supply from the database.

    Supply is only deleted if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        supply: Supply to delete.
        service: Ship service, injected by FastAPI via `get_ship_service`.
    """
    service.delete_supply(supply)
