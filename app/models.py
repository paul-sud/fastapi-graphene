import uuid

from pydantic import BaseModel


class PersonModel(BaseModel):
    uuid: uuid.UUID
    first_name: str
    last_name: str


class FileModel(BaseModel):
    uuid: uuid.UUID
    s3_uri: str


class ExperimentModel(BaseModel):
    uuid: uuid.UUID
    assay: str
    files: list[FileModel]
