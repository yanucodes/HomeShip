"""Ship endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_ship_or_404, get_ship_service
from models import Ship
from schemas import (ShipRead, ShipMemberAdd, ShipMemberRead, TaskCreate,
                     TaskRead)
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