"""Ship endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import (get_ship_or_404, get_ship_service,
                          get_supply_or_404, get_task_or_404)
from models import Ship, Supply, Task
from schemas import (FrequencyChange, ShipRead, ShipMemberAdd, ShipMemberRead,
                     SupplyCreate, SupplyRead, SupplyUpdate, TaskCreate,
                     TaskPostpone, TaskRead, TaskUpdate)
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
def get_tasks(ship: Ship = Depends(get_ship_or_404),
              service: ShipService = Depends(get_ship_service)):
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


@router.get("/{ship_id}/tasks/{task_id}", response_model=TaskRead)
def get_task(task: Task = Depends(get_task_or_404)):
    """
    Get a single task belonging to the ship.

    Task is only returned if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        task: Task resolved from the path (404 if not found).

    Returns:
        The Task serialized as `TaskRead`.
    """
    return task


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


@router.patch("/{ship_id}/tasks/{task_id}", response_model=TaskRead)
def update_task(task_data: TaskUpdate,
                task: Task = Depends(get_task_or_404),
                service: ShipService = Depends(get_ship_service)):
    """
    Update a task's editable attributes.

    Task is only updated if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        task_data: Validated task fields from the request body.
        task: Task to update, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Task serialized as `TaskRead`.
    """
    return service.update_task(task, task_data)


@router.post("/{ship_id}/tasks/{task_id}/complete", response_model=TaskRead)
def complete_task(task: Task = Depends(get_task_or_404),
                  service: ShipService = Depends(get_ship_service)):
    """
    Mark a task as completed.

    Records completion as of today, recomputing the task's due date and
    alert state. Task is only completed if it belongs to the ship with the
    given ID. Otherwise, Error 404 is raised.

    Args:
        task: Task to complete, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Task serialized as `TaskRead`.
    """
    return service.complete_task(task)


@router.post("/{ship_id}/tasks/{task_id}/postpone", response_model=TaskRead)
def postpone_task(postpone_data: TaskPostpone,
                  task: Task = Depends(get_task_or_404),
                  service: ShipService = Depends(get_ship_service)):
    """
    Postpone a task to a later due date.

    Pushes the due date out and escalates the task's alert state. Task is
    only postponed if it belongs to the ship with the given ID. Otherwise,
    Error 404 is raised.

    Args:
        postpone_data: Validated new due date from the request body.
        task: Task to postpone, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Task serialized as `TaskRead`.

    Raises:
        HTTPException: 400 if the task cannot be postponed (no active due
            date, or the new date is not later than the current one).
    """
    updated_task = service.postpone_task(task, postpone_data.date_due)
    if updated_task is None:
        raise HTTPException(status_code=400, detail="Task cannot be postponed")
    return updated_task


@router.post("/{ship_id}/tasks/{task_id}/change_frequency",
             response_model=TaskRead)
def change_task_frequency(frequency_data: FrequencyChange,
                          task: Task = Depends(get_task_or_404),
                          service: ShipService = Depends(get_ship_service)):
    """
    Change a task's frequency.

    Re-derives the task's schedule and alert state from the new frequency.
    Task is only changed if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        frequency_data: Validated new frequency from the request body.
        task: Task to update, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Task serialized as `TaskRead`.
    """
    return service.change_task_frequency(task, frequency_data.frequency)


@router.post("/{ship_id}/tasks/{task_id}/deactivate",
             response_model=TaskRead)
def deactivate_task(task: Task = Depends(get_task_or_404),
                    service: ShipService = Depends(get_ship_service)):
    """
    Deactivate a task.

    Task is only deactivated if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        task: Task to update, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Task serialized as `TaskRead`.
    """
    return service.deactivate_task(task)


@router.delete("/{ship_id}/tasks/{task_id}",
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
def get_supplies(ship: Ship = Depends(get_ship_or_404),
                 service: ShipService = Depends(get_ship_service)):
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


@router.get("/{ship_id}/supplies/{supply_id}", response_model=SupplyRead)
def get_supply(supply: Supply = Depends(get_supply_or_404)):
    """
    Get a single supply belonging to the ship.

    Supply is only returned if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        supply: Supply resolved from the path (404 if not found).

    Returns:
        The Supply serialized as `SupplyRead`.
    """
    return supply


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


@router.patch("/{ship_id}/supplies/{supply_id}", response_model=SupplyRead)
def update_supply(supply_data: SupplyUpdate,
                  supply: Supply = Depends(get_supply_or_404),
                  service: ShipService = Depends(get_ship_service)):
    """
    Update a supply's editable attributes.

    Supply is only updated if it belongs to the ship with the given ID.
    Otherwise, Error 404 is raised.

    Args:
        supply_data: Validated supply fields from the request body.
        supply: Supply to update, resolved from the path (404 if not found).
        service: Ship service, injected by FastAPI via `get_ship_service`.

    Returns:
        The updated Supply serialized as `SupplyRead`.
    """
    return service.update_supply(supply, supply_data)


@router.delete("/{ship_id}/supplies/{supply_id}",
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
