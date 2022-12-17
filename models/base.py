from sqlalchemy import select, delete, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.exceptions import GetFromDatabaseException


class BaseOrmMixin:
    """Class for create base orm query"""

    @classmethod
    async def by_id(cls, db: AsyncSession, instance_id: int, selectinload_attr: str = None):
        query = select(cls).where(cls.id == instance_id)
        #
        if selectinload_attr:
            query = query.options(selectinload(getattr(cls, selectinload_attr)))
        #
        try:
            instance = await db.execute(query)
            instance = instance.first()
        except SQLAlchemyError:
            await db.rollback()
            raise GetFromDatabaseException(f'Error get {cls.__name__} from finance database')
        #
        if not instance:
            return
        (instance,) = instance
        return instance

    @classmethod
    async def by_name(cls, db: AsyncSession, name: str):
        query = select(cls).where(cls.name == name)
        try:
            instance = await db.execute(query)
            instance = instance.first()
        except SQLAlchemyError:
            await db.rollback()
            raise GetFromDatabaseException(f'Error get {cls.__name__} from finance database')
        #
        if not instance:
            return
        (instance,) = instance
        return instance

    @classmethod
    async def get_all(cls, db: AsyncSession, selectinload_attr: str = None):
        query = select(cls).order_by(cls.id)
        #
        if selectinload_attr:
            query = query.options(selectinload(getattr(cls, selectinload_attr)))
        #
        try:
            instances = await db.execute(query)
            instances = instances.scalars().all()
        except SQLAlchemyError:
            await db.rollback()
            raise GetFromDatabaseException(f'Error get {cls.__name__} from finance database')
        return instances

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        instance = cls(**kwargs)
        db.add(instance)
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise
        return instance

    @classmethod
    async def delete_by_id(cls, db: AsyncSession, instance_id: int):
        query = delete(cls).where(cls.id == instance_id)
        await db.execute(query)
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise
        return True

    @classmethod
    async def update(cls, db: AsyncSession, instance_id: int, **kwargs):
        query = (
            update(cls).where(cls.id == instance_id).values(**kwargs).execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise
