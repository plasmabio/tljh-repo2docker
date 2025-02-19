from enum import Enum
from typing import Optional

from pydantic import UUID4, BaseModel, ConfigDict


class BuildStatusType(str, Enum):
    BUILT = "built"
    BUILDING = "building"
    FAILED = "failed"


class ImageMetadataType(BaseModel):
    display_name: str
    repo: str
    ref: str
    cpu_limit: str
    mem_limit: str
    node_selector: dict


class DockerImageCreateSchema(BaseModel):
    uid: UUID4
    name: str
    status: BuildStatusType
    log: str
    image_meta: ImageMetadataType

    model_config = ConfigDict(use_enum_values=True)


class DockerImageUpdateSchema(DockerImageCreateSchema):
    uid: UUID4
    name: Optional[str] = None
    status: Optional[BuildStatusType] = None
    log: Optional[str] = None
    image_meta: Optional[ImageMetadataType] = None

    model_config = ConfigDict(use_enum_values=True)


class DockerImageOutSchema(DockerImageCreateSchema):

    model_config = ConfigDict(use_enum_values=True, from_attributes=True)
