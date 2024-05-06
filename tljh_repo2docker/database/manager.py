import logging
from typing import List, Optional, Type, Union

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from tornado.web import HTTPError

from .model import DockerImageSQL
from .schemas import (
    DockerImageCreateSchema,
    DockerImageOutSchema,
    DockerImageUpdateSchema,
)


class ImagesDatabaseManager:

    @property
    def _table(self) -> Type[DockerImageSQL]:
        return DockerImageSQL

    @property
    def _schema_out(self) -> Type[DockerImageOutSchema]:
        return DockerImageOutSchema

    async def create(
        self, db: AsyncSession, obj_in: DockerImageCreateSchema
    ) -> DockerImageOutSchema:
        """
        Create one resource.

        Args:
            db: An asyncio version of SQLAlchemy session.
            obj_in: An object containing the resource instance to create

        Returns:
            The created resource instance on success.

        Raises:
            DatabaseError: If `db.commit()` failed.
        """
        entry = self._table(**obj_in.model_dump())

        db.add(entry)

        try:
            await db.commit()
            # db.refresh(entry)
        except IntegrityError as e:
            logging.error(f"create: {e}")
            raise HTTPError(409, "That resource already exists.")
        except SQLAlchemyError as e:
            logging.error(f"create: {e}")
            raise e

        return self._schema_out.model_validate(entry)

    async def read(
        self, db: AsyncSession, uid: UUID4
    ) -> Union[DockerImageOutSchema, None]:
        """
        Get one resource by uid.

        Args:
            db: An asyncio version of SQLAlchemy session.
            uid: The primary key of the resource to retrieve.

        Returns:
            The first resource instance found, `None` if no instance retrieved.
        """
        if entry := await db.get(self._table, uid):
            return self._schema_out.model_validate(entry)
        return None

    async def read_many(
        self, db: AsyncSession, uids: List[UUID4]
    ) -> List[DockerImageOutSchema]:
        """
        Get multiple resources.

        Args:
            db: An asyncio version of SQLAlchemy session.
            uids: The primary keys of the resources to retrieve.

        Returns:
            The list of resources retrieved.
        """
        resources = (
            await db.execute(sa.select(self._table).where(self._table.uid.in_(uids)))
        ).scalars()
        return [self._schema_out.model_validate(r) for r in resources]

    async def read_all(self, db: AsyncSession) -> List[DockerImageOutSchema]:
        """
        Get all rows.

        Args:
            db: An asyncio version of SQLAlchemy session.

        Returns:
            The list of resources retrieved.
        """
        resources = (await db.execute(sa.select(self._table))).scalars().all()
        return [self._schema_out.model_validate(r) for r in resources]

    async def read_by_image_name(
        self, db: AsyncSession, image: str
    ) -> Optional[DockerImageOutSchema]:
        """
        Get image by its name.

        Args:
            db: An asyncio version of SQLAlchemy session.

        Returns:
            The list of resources retrieved.
        """
        statement = sa.select(self._table).where(self._table.name == image)
        try:
            result = await db.execute(statement)
            return self._schema_out.model_validate(result.scalars().first())
        except Exception:
            return None

    async def update(
        self, db: AsyncSession, obj_in: DockerImageUpdateSchema, optimistic: bool = True
    ) -> Union[DockerImageOutSchema, None]:
        """
        Update one object.

        Args:
            db: An asyncio version of SQLAlchemy session.
            obj_in: A model containing values to update
            optimistic: If `True`, assert the new model instance to be
            `**{**obj_db.dict(), **obj_in.dict()}`

        Returns:
            The updated model instance on success, `None` if it does not exist
            yet in database.

        Raises:
            DatabaseError: If `db.commit()` failed.
        """
        if not (obj_db := await self.read(db=db, uid=obj_in.uid)):
            await self.create(db, obj_in)

        update_data = obj_in.model_dump(exclude_none=True)

        await db.execute(
            sa.update(self._table)
            .where(self._table.uid == obj_in.uid)
            .values(**update_data)
        )

        try:
            await db.commit()
        except SQLAlchemyError as e:
            logging.error(f"update: {e}")
            raise e

        if optimistic:
            for field in update_data:
                setattr(obj_db, field, update_data[field])
            return self._schema_out.model_validate(obj_db)

        return await self.read(db=db, uid=obj_in.uid)

    async def delete(self, db: AsyncSession, uid: UUID4) -> bool:
        """
        Delete one object.

        Args:
            db: An asyncio version of SQLAlchemy session.
            uid: The primary key of the resource to delete.

        Returns:
            bool: `True` if the object has been deleted, `False` otherwise.

        Raises:
            DatabaseError: If `db.commit()` failed.
        """
        results = await db.execute(sa.delete(self._table).where(self._table.uid == uid))

        try:
            await db.commit()
        except SQLAlchemyError as e:
            logging.error(f"delete: {e}")
            raise e

        return results.rowcount == 1
