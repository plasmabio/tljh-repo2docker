import uuid

from jupyterhub.orm import JSONDict
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import DeclarativeMeta, declarative_base

from .schemas import BuildStatusType

BaseSQL: DeclarativeMeta = declarative_base()


class DockerImageSQL(BaseSQL):
    """
    SQLAlchemy image table definition.
    """

    __tablename__ = "images"

    uid = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name = Column(String(length=4096), unique=False, nullable=False)

    status = Column(
        ENUM(
            BuildStatusType,
            name="build_status_enum",
            create_type=False,
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
    )

    log = Column(Text)

    image_meta = Column(JSONDict, default={})

    __mapper_args__ = {"eager_defaults": True}
