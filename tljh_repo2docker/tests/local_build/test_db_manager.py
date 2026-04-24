from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tljh_repo2docker.database.manager import ImagesDatabaseManager
from tljh_repo2docker.database.model import BaseSQL
from tljh_repo2docker.database.schemas import (
    BuildStatusType,
    DockerImageCreateSchema,
    DockerImageUpdateSchema,
    ImageMetadataType,
)


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseSQL.metadata.create_all)
    maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with maker() as session:
        yield session
    await engine.dispose()


def _make_schema(uid=None, name="test-image:HEAD", status=BuildStatusType.BUILDING):
    return DockerImageCreateSchema(
        uid=uid or uuid4(),
        name=name,
        status=status,
        log="",
        image_meta=ImageMetadataType(
            display_name="test-image",
            repo="https://github.com/test/test",
            ref="HEAD",
            creation_date="01/01/2025",
            owner="admin",
            cpu_limit="",
            mem_limit="",
            node_selector={},
        ),
    )


async def test_create_and_read(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema()
    created = await manager.create(db_session, schema)

    assert created.uid == schema.uid
    assert created.status == BuildStatusType.BUILDING.value
    assert created.name == "test-image:HEAD"

    fetched = await manager.read(db_session, schema.uid)
    assert fetched is not None
    assert fetched.uid == schema.uid


async def test_read_by_image_name(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema(name="unique-image:abc")
    await manager.create(db_session, schema)

    result = await manager.read_by_image_name(db_session, "unique-image:abc")
    assert result is not None
    assert result.uid == schema.uid


async def test_read_by_image_name_not_found(db_session):
    manager = ImagesDatabaseManager()
    result = await manager.read_by_image_name(db_session, "no-such-image:xyz")
    assert result is None


async def test_read_all(db_session):
    manager = ImagesDatabaseManager()
    for i in range(3):
        await manager.create(db_session, _make_schema(name=f"img-{i}:HEAD"))

    all_images = await manager.read_all(db_session)
    assert len(all_images) == 3


async def test_update_status(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema()
    await manager.create(db_session, schema)

    await manager.update(
        db_session,
        DockerImageUpdateSchema(uid=schema.uid, status=BuildStatusType.BUILT),
    )
    updated = await manager.read(db_session, schema.uid)
    assert updated is not None
    assert updated.status == BuildStatusType.BUILT.value


async def test_update_log(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema()
    await manager.create(db_session, schema)

    await manager.update(
        db_session,
        DockerImageUpdateSchema(uid=schema.uid, log="some log content"),
    )
    updated = await manager.read(db_session, schema.uid)
    assert updated is not None
    assert updated.log == "some log content"


async def test_update_log_accumulation(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema()
    await manager.create(db_session, schema)

    await manager.update(
        db_session,
        DockerImageUpdateSchema(uid=schema.uid, log="line1\nline2\n"),
    )
    await manager.update(
        db_session,
        DockerImageUpdateSchema(uid=schema.uid, log="line1\nline2\nline3\n"),
    )
    updated = await manager.read(db_session, schema.uid)
    assert updated is not None
    assert "line3" in updated.log


async def test_delete(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema()
    await manager.create(db_session, schema)

    deleted = await manager.delete(db_session, schema.uid)
    assert deleted is True

    result = await manager.read(db_session, schema.uid)
    assert result is None


async def test_delete_nonexistent(db_session):
    manager = ImagesDatabaseManager()
    deleted = await manager.delete(db_session, uuid4())
    assert deleted is False


async def test_failed_image_has_log(db_session):
    manager = ImagesDatabaseManager()
    schema = _make_schema(status=BuildStatusType.FAILED)
    schema_with_log = DockerImageCreateSchema(
        **{**schema.model_dump(), "log": "Error: build failed"}
    )
    await manager.create(db_session, schema_with_log)

    fetched = await manager.read(db_session, schema.uid)
    assert fetched is not None
    assert fetched.status == BuildStatusType.FAILED.value
    assert "Error" in fetched.log
