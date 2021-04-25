from typing import Optional

import strawberry

from .database import database, experiments, files


def get_books():
    return [Book(title="The Great Gatsby", author="F. Scott Fitzgerald")]


def get_files() -> list["File"]:
    return [File(s3_uri="foo", uuid=12)]


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class File:
    s3_uri: str
    uuid: int


@strawberry.input
class FileInput:
    s3_uri: str
    file_format: Optional[str] = None


@strawberry.type
class Experiment:
    uuid: int
    file_ids: strawberry.Private[list[str]]

    @strawberry.field
    def files(self) -> list[File]:
        return [File(s3_uri="foo", uuid=2) for _ in self.file_ids]


@strawberry.input
class ExperimentInput:
    file_ids: list[str]


@strawberry.type
class Query:
    books: list[Book] = strawberry.field(resolver=get_books)
    files: list[File] = strawberry.field(resolver=get_files)

    @strawberry.field
    async def get_experiment(self, uuid: int) -> Experiment:
        query = experiments.select().where(uuid=uuid)
        row = await database.fetch_one(query=query)
        return Experiment(uuid=uuid, **row.data)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_file(self, file_input: FileInput) -> int:
        result = await database.execute(
            query=files.insert(),
            values={
                "data": {k: v for k, v in vars(file_input).items() if v is not None}
            },
        )
        return result.inserted_primary_key

    @strawberry.mutation
    async def create_experiment(self, experiment_input: ExperimentInput) -> int:
        result = await database.execute(
            query=experiments.insert(),
            values={
                "data": {
                    k: v for k, v in vars(experiment_input).items() if v is not None
                }
            },
        )
        return result.inserted_primary_key


schema = strawberry.Schema(query=Query, mutation=Mutation)
