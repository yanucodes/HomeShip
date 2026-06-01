"""Repository for Ship."""
from models import Ship

from .base import BaseRepository


class ShipRepository(BaseRepository[Ship]):
    """CRUD operations on Ship model."""
    model = Ship
