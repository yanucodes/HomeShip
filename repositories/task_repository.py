"""Repository for Task."""
from models import Task

from .base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """CRUD operations on Task model."""
    model = Task
