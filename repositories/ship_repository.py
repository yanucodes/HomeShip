"""Repository for Ship."""
from models import Ship

from .base_repository import BaseRepository


class ShipRepository(BaseRepository[Ship]):
    """CRUD operations on Ship model."""
    model = Ship
