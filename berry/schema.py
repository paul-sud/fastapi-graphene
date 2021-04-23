import strawberry


def get_books():
    return [Book(title="The Great Gatsby", author="F. Scott Fitzgerald")]


def get_files() -> list["File"]:
    return [File(s3_uri="foo", uuid="bar")]


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class File:
    s3_uri: str
    uuid: str


@strawberry.type
class Experiment:
    uuid: str
    file_ids: strawberry.Private[list[str]]

    @strawberry.field
    def files(self) -> list[File]:
        return [File(s3_uri="foo", uuid="bar") for _ in self.file_ids]


@strawberry.type
class Query:
    books: list[Book] = strawberry.field(resolver=get_books)
    files: list[File] = strawberry.field(resolver=get_files)

    @strawberry.field
    def one_experiment(self) -> Experiment:
        return Experiment(uuid="my_uuid", file_ids=["foo", "bar"])


schema = strawberry.Schema(query=Query)
