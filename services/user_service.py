"""Service layer for User: orchestrates operations on user and their ships."""
import uuid
from models import Ship, ShipMember, User
from repositories import ShipMemberRepository, ShipRepository, UserRepository
from schemas import ShipCreate, ShipMemberCreate, UserCreate, UserUpdate
from security import hash_password


class UserService:
    def __init__(self,
                 ship_repository: ShipRepository,
                 ship_member_repository: ShipMemberRepository,
                 user_repository: UserRepository):
        self.ship_repository = ship_repository
        self.ship_member_repository = ship_member_repository
        self.user_repository = user_repository

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: Validated user fields from the request.

        Returns:
            The newly created User, with their server-generated user_id and
            password hash.
        """
        data = user_data.model_dump(exclude={"password"})
        if data.get("display_name") is None:
            data["display_name"] = data["username"]
        new_user = User(**data, password_hash=hash_password(
            user_data.password))
        return self.user_repository.add(new_user)

    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """
        Find user by their ID.

        Args:
            user_id: UUID of that user.

        Returns:
            User object or None if user not found.
        """
        return self.user_repository.get(user_id)

    def update_user(self, user: User, user_data: UserUpdate) -> User:
        """
        Update user data.

        Args:
            user: User whose profile is being updated.
            user_data: Validated user fields from the request.

        Returns:
            Updated User object.
        """
        changes = user_data.model_dump(exclude_unset=True)
        if "password" in changes:
            changes["password_hash"] = hash_password(changes.pop("password"))
        return self.user_repository.update(user, changes)

    def delete_user(self, user: User) -> None:
        """
        Delete user from the database.

        The user's ship memberships are deleted along with them (cascade).
        Any ship on which this user was the only crew member is also deleted
        (taking its tasks and supplies with it); ships with other members
        remain.

        Args:
            user: User to delete.
        """
        for membership in list(user.ship_memberships):
            ship = membership.ship
            if len(ship.ship_memberships) == 1:
                self.ship_repository.delete(ship)
        self.user_repository.delete(user)

    def create_ship_for_user(self, user: User, ship_data: ShipCreate,
                             ship_member_data: ShipMemberCreate) -> Ship:
        """Create a ship and make user its crew member with the chosen role.

        Args:
            user: The user creating the ship; becomes its first member.
            ship_data: Validated ship fields from the request.
            ship_member_data: Validated ship member fields from the request

        Returns:
            The newly created Ship, with its server-generated ship_id.
        """
        ship = self.ship_repository.add(Ship(**ship_data.model_dump()))
        self.ship_member_repository.add(
            ShipMember(
                user_id=user.user_id,
                ship_id=ship.ship_id,
                **ship_member_data.model_dump()
            )
        )
        return ship

    def get_ships(self, user: User) -> list[Ship]:
        """
        Get all ships the user is a member of.

        Args:
            user: The user whose ships to get.

        Returns:
            List of Ship objects.
        """
        return [membership.ship for membership in user.ship_memberships]

    def delete_ship_membership(self,
                               user: User,
                               ship_membership: ShipMember) -> None:
        """
        Delete ship membership for the user.

        Associated ship is deleted if the user is the only member.

        Args:
            user: User whose membership is to delete.
            ship_membership: Ship membership to delete.
        """
        ship = ship_membership.ship
        if len(ship.ship_memberships) == 1:
            self.ship_repository.delete(ship) # cascade removes the membership
        else:
            self.ship_member_repository.delete(ship_membership)
