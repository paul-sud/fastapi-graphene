import uuid

import graphene
from graphene_pydantic import PydanticObjectType

from .models import ExperimentModel, FileModel, PersonModel


class Person(PydanticObjectType):
    class Meta:
        model = PersonModel
        # exclude specified fields
        exclude_fields = ("uuid",)


class File(PydanticObjectType):
    class Meta:
        model = FileModel


class Experiment(PydanticObjectType):
    class Meta:
        model = ExperimentModel

    def resolve_files(parent, info):
        return [
            FileModel(uuid=uuid.uuid4(), s3_uri="s3://foo/bar") for _ in parent.files
        ]


class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))
    goodbye = graphene.String()
    people = graphene.List(Person)
    experiments = graphene.List(Experiment)

    def resolve_hello(parent, info, name):
        return "Hello " + name

    def resolve_goodbye(parent, info):
        return "See ya!"

    def resolve_people(parent, info):
        # fetch actual PersonModels here
        return [PersonModel(uuid=uuid.uuid4(), first_name="Beth", last_name="Smith")]

    def resolve_experiments(parent, info):
        return [ExperimentModel(uuid=uuid.uuid4(), assay="foo", files=["1"])]
