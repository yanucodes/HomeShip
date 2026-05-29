"""Generic CRUD base for entity repositories."""
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """CRUD operations on a single SQLAlchemy model.

    Subclasses bind the model with `model = SomeModel` and add their own
    query methods.
    """

    model: type[ModelType]

    def __init__(self, session: Session):
        self.session = session

    def get(self, entity_id) -> ModelType | None:
        """Fetch one entity by primary key.

        Returns:
            The entity, or None if no row matches the given PK.
        """
        return self.session.get(self.model, entity_id)

    def add(self, entity: ModelType) -> ModelType:
        """Insert a new entity and flush so server-generated fields
        populate. After flush, the entity's PK is readable and can be used
        as an FK for subsequent writes in the same request.

        Returns:
            The same entity, now with server-generated fields populated.

        Raises:
            IntegrityError: if a NOT NULL, UNIQUE, CHECK, or FK constraint
                fails (e.g. duplicate shipname, missing required field).
        """
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: ModelType, changes: dict[str, Any]) -> ModelType:
        """Apply a partial update to an existing entity. Pass only fields
        the client sent. Fields not present in `changes` are left untouched.

        Returns:
            The same entity, with the given fields modified.

        Raises:
            IntegrityError: if the new values violate a UNIQUE, CHECK, or
                FK constraint.
        """
        for field, value in changes.items():
            setattr(entity, field, value)
        self.session.flush()
        return entity

    def delete(self, entity: ModelType) -> None:
        """Delete an entity and flush so FK violations surface immediately.

        Raises:
            IntegrityError: if another row still references this entity
                via a foreign key.
        """
        self.session.delete(entity)
        self.session.flush()
