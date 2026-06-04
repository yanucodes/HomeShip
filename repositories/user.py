"""Repository for User."""
from sqlalchemy import select

from models import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD operations on User model."""
    model = User

    def get_by_email(self, user_email: str) -> User | None:
        """Fetch user by email.

        Args:
            user_email: email to search for.

        Returns:
            User object or None, if user not found.
        """
        return self.session.execute(
            select(User).filter_by(email=user_email)
        ).scalar_one_or_none()
