from enum import Enum

from pydantic import UUID4, BaseModel


class BuildStatusType(str, Enum):
    SUCCESS = "success"
    BUILDING = "building"
    FAILED = "failed"


class ImageMetadataType(BaseModel):
    label: str
    repo: str
    ref: str
    cpu: str
    memory: str


class DockerImageCreateSchema(BaseModel):
    uid: UUID4
    name: str
    status: BuildStatusType
    log: str
    metadata: ImageMetadataType

    class Config:
        use_enum_values = True


class DockerImageUpdateSchema(DockerImageCreateSchema):
    pass


class DockerImageOutSchema(DockerImageCreateSchema):

    class Config:
        use_enum_values = True
        from_attributes = True
        orm_mode = True
