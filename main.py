import uuid

import graphene
import pydantic
from fastapi import FastAPI
from graphene_pydantic import PydanticObjectType
from starlette.graphql import GraphQLApp


class PersonModel(pydantic.BaseModel):
    uuid: uuid.UUID
    first_name: str
    last_name: str


class Person(PydanticObjectType):
    class Meta:
        model = PersonModel
        # exclude specified fields
        exclude_fields = ("uuid",)


class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))
    goodbye = graphene.String()
    people = graphene.List(Person)

    def resolve_hello(parent, info, name):
        return "Hello " + name

    def resolve_goodbye(parent, info):
        return 'See ya!'

    def resolve_people(parent, info):
        # fetch actual PersonModels here
        return [PersonModel(uuid=uuid.uuid4(), first_name="Beth", last_name="Smith")]


app = FastAPI()
app.add_route("/", GraphQLApp(schema=graphene.Schema(query=Query)))
