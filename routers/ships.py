"""Ship endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_ship_service
from schemas import (ShipRead, ShipMemberAdd, ShipMemberRead, TaskCreate,
                     TaskRead)
from services import ShipService

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("/{ship_id}", response_model=ShipRead)
def get_ship(ship_id: uuid.UUID,
             service: ShipService = Depends(get_ship_service)):
    """
    Fetch ship data.

    Args:
        ship_id: ID of the ship.
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The ship serialized as `ShipRead`.
    """
    ship = service.get_ship_by_id(ship_id)
    if ship is None:
        raise HTTPException(status_code=404)
    return ship


@router.post("/{ship_id}/members", response_model=ShipMemberRead,
             status_code=status.HTTP_201_CREATED)
def add_member(ship_id: uuid.UUID, member_data: ShipMemberAdd,
               service: ShipService = Depends(get_ship_service)):
    """
    Add an existing user to the ship's crew, identified by email.

    Args:
        ship_id: ID of the ship.
        member_data: Validated member fields from the request body (the
            email of the user to add plus their role).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The newly created ShipMember serialized as `ShipMemberRead`.
    """
    ship = service.get_ship_by_id(ship_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Ship not found")
    member = service.add_member_to_ship(ship, member_data)
    if member is None:
        raise HTTPException(status_code=404, detail="User not found")
    return member


@router.post("/{ship_id}/tasks", response_model=TaskRead,
             status_code=status.HTTP_201_CREATED)
def add_task(ship_id: uuid.UUID, task_data: TaskCreate,
             service: ShipService=Depends(get_ship_service)):
    """
    Add a new task to the ship.

    Args:
        ship_id: ID of the ship.
        task_data: Validated Task fields from the request body.
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The newly created Task serialized as `TaskRead`.
    """
    ship = service.get_ship_by_id(ship_id)
    if ship is None:
        raise HTTPException(status_code=404, detail="Ship not found")
    return service.create_task(ship, task_data)