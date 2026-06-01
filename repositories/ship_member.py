"""Repository for ShipMember."""
from models import ShipMember

from .base import BaseRepository


class ShipMemberRepository(BaseRepository[ShipMember]):
    """CRUD operations on ShipMember model."""
    model = ShipMember
