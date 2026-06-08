"""Repository for Supply."""
from models import Supply

from .base_repository import BaseRepository


class SupplyRepository(BaseRepository[Supply]):
    """CRUD operations on Supply model."""
    model = Supply
