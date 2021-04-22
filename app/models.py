import uuid

import pydantic

class PersonModel(pydantic.BaseModel):
    uuid: uuid.UUID
    first_name: str
    last_name: str
