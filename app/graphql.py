import uuid

import graphene
from graphene_pydantic import PydanticObjectType

from .models import PersonModel


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
        return "See ya!"

    def resolve_people(parent, info):
        # fetch actual PersonModels here
        return [PersonModel(uuid=uuid.uuid4(), first_name="Beth", last_name="Smith")]
