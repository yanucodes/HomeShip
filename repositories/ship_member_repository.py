"""Repository for ShipMember."""
from models import ShipMember

from .base_repository import BaseRepository


class ShipMemberRepository(BaseRepository[ShipMember]):
    """CRUD operations on ShipMember model."""
    model = ShipMember
