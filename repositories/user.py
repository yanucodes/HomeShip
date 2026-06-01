"""Repository for User."""
from models import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD operations on User model."""
    model = User
