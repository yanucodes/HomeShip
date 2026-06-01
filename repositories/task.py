"""Repository for Task."""
from models import Task

from .base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """CRUD operations on Task model."""
    model = Task
