import os
import shutil
import sys
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory
from typing import AsyncGenerator, List
from urllib.parse import urlparse

import alembic
import alembic.config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

HERE = Path(__file__).parent.resolve()
ALEMBIC_DIR = HERE / "alembic"
ALEMBIC_INI_TEMPLATE_PATH = ALEMBIC_DIR / "alembic.ini"


def write_alembic_ini(alembic_ini: Path, db_url="sqlite:///tljh_repo2docker.sqlite"):
    """Write a complete alembic.ini from our template.

    Parameters
    ----------
    alembic_ini : str
        path to the alembic.ini file that should be written.
    db_url : str
        The SQLAlchemy database url, e.g. `sqlite:///tljh_repo2docker.sqlite`.
    """
    with open(ALEMBIC_INI_TEMPLATE_PATH) as f:
        alembic_ini_tpl = f.read()

    with open(alembic_ini, "w") as f:
        f.write(
            alembic_ini_tpl.format(
                alembic_dir=ALEMBIC_DIR,
                db_url=str(db_url).replace("%", "%%"),
            )
        )


@contextmanager
def _temp_alembic_ini(db_url):
    """Context manager for temporary JupyterHub alembic directory

    Temporarily write an alembic.ini file for use with alembic migration scripts.

    Context manager yields alembic.ini path.

    Parameters
    ----------
    db_url : str
        The SQLAlchemy database url.

    Returns
    -------
    alembic_ini: str
        The path to the temporary alembic.ini that we have created.
        This file will be cleaned up on exit from the context manager.
    """
    with TemporaryDirectory() as td:
        alembic_ini = Path(td) / "alembic.ini"
        write_alembic_ini(alembic_ini, db_url)
        yield alembic_ini


def upgrade(db_url, revision="head"):
    """Upgrade the given database to revision.

    db_url: str
        The SQLAlchemy database url.

    revision: str [default: head]
        The alembic revision to upgrade to.
    """
    with _temp_alembic_ini(db_url) as alembic_ini:
        check_call(["alembic", "-c", alembic_ini, "upgrade", revision])


def backup_db_file(db_file, log=None):
    """Backup a database file if it exists"""
    timestamp = datetime.now().strftime(".%Y-%m-%d-%H%M%S")
    backup_db_file = db_file + timestamp
    for i in range(1, 10):
        if not os.path.exists(backup_db_file):
            break
        backup_db_file = f"{db_file}.{timestamp}.{i}"
    #
    if os.path.exists(backup_db_file):
        raise OSError("backup db file already exists: %s" % backup_db_file)
    if log:
        log.info("Backing up %s => %s", db_file, backup_db_file)
    shutil.copy(db_file, backup_db_file)


def _alembic(db_url: str, alembic_arg: List[str]):
    """Run an alembic command with a temporary alembic.ini"""

    with _temp_alembic_ini(db_url) as alembic_ini:
        check_call(["alembic", "-c", alembic_ini] + alembic_arg)


def check_db_revision(engine):
    """Check the database revision"""
    # Check database schema version
    current_table_names = set(inspect(engine).get_table_names())

    # alembic needs the password if it's in the URL
    engine_url = engine.url.render_as_string(hide_password=False)

    if "alembic_version" not in current_table_names:
        return True

    with _temp_alembic_ini(engine_url) as ini:
        cfg = alembic.config.Config(ini)
        scripts = ScriptDirectory.from_config(cfg)
        head = scripts.get_heads()[0]

    # check database schema version
    # it should always be defined at this point
    with engine.begin() as connection:
        alembic_revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).first()[0]
    if alembic_revision == head:
        return False
    else:
        raise Exception(
            f"Found database schema version {alembic_revision} != {head}. "
            "Backup your database and run `tljh_repo2docker_upgrade_db`"
            " to upgrade to the latest schema."
        )


def upgrade_if_needed(db_url, log=None):
    """Upgrade a database if needed

    If the database is sqlite, a backup file will be created with a timestamp.
    Other database systems should perform their own backups prior to calling this.
    """
    # run check-db-revision first
    engine = create_engine(async_to_sync_url(db_url))
    need_upgrade = check_db_revision(engine=engine)
    if not need_upgrade:
        if log:
            log.info("Database schema is up-to-date")
        return

    urlinfo = urlparse(db_url)
    if urlinfo.password:
        # avoid logging the database password
        urlinfo = urlinfo._replace(
            netloc=f"{urlinfo.username}:[redacted]@{urlinfo.hostname}:{urlinfo.port}"
        )
        db_log_url = urlinfo.geturl()
    else:
        db_log_url = db_url
    if log:
        log.info("Upgrading %s", db_log_url)

    upgrade(db_url)


def sync_to_async_url(db_url: str) -> str:
    """Convert a sync database URL to async one"""
    if db_url.startswith("sqlite:"):
        return db_url.replace("sqlite:", "sqlite+aiosqlite:")
    if db_url.startswith("postgresql:"):
        return db_url.replace("postgresql:", "postgresql+asyncpg:")
    if db_url.startswith("mysql:"):
        return db_url.replace("mysql:", "mysql+aiomysql:")
    return db_url


def async_to_sync_url(db_url: str) -> str:
    """Convert a async database URL to sync one"""
    if db_url.startswith("sqlite+aiosqlite:"):
        return db_url.replace("sqlite+aiosqlite:", "sqlite:")
    if db_url.startswith("postgresql+asyncpg:"):
        return db_url.replace("postgresql+asyncpg:", "postgresql:")
    if db_url.startswith("mysql+aiomysql:"):
        return db_url.replace("mysql+aiomysql:", "mysql:")
    return db_url


def async_session_context_factory(async_db_url: str):
    """
    Factory function to create an asynchronous session context manager.

    Parameters:
    - async_db_url (str): The URL for the asynchronous database connection.

    Returns:
    - AsyncContextManager[AsyncSession]: An asynchronous context manager that yields
      an async session for database interactions within the context.
    """
    async_engine = create_async_engine(async_db_url)
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    async_session_context = asynccontextmanager(get_async_session)
    return async_session_context


def main():
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
        upgrade(db_url)
    else:
        print("Missing database URL")
