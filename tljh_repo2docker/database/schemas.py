from enum import Enum
from typing import Optional

from pydantic import UUID4, BaseModel


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


class DockerImageCreateSchema(BaseModel):
    uid: UUID4
    name: str
    status: BuildStatusType
    log: str
    image_meta: ImageMetadataType

    class Config:
        use_enum_values = True


class DockerImageUpdateSchema(DockerImageCreateSchema):
    uid: UUID4
    name: Optional[str] = None
    status: Optional[BuildStatusType] = None
    log: Optional[str] = None
    image_meta: Optional[ImageMetadataType] = None

    class Config:
        use_enum_values = True


class DockerImageOutSchema(DockerImageCreateSchema):

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True
