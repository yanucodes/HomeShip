"""Repository for Supply."""
from models import Supply

from .base import BaseRepository


class SupplyRepository(BaseRepository[Supply]):
    """CRUD operations on Supply model."""
    model = Supply
