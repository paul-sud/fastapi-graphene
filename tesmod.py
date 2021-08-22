import random

from pydantic import BaseModel
from typing import Any, Iterator, Optional, List
import strawberry


class PageInfoModel(BaseModel):
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None


@strawberry.interface
class Node:
    id: str


# Defining and enforcing the interface in Pydantic makes IDs required when validating
# @strawberry.experimental.pydantic.type(
#     model=NodeModel,
#     fields=["id"],
#     is_interface=True,
# )
# class Node:
#     pass


# @strawberry.experimental.pydantic.input(model=NodeModel, fields=['id'])
# class NodeInput:
#     pass


class ChildModel(BaseModel):
    name: str


@strawberry.experimental.pydantic.type(
    model=ChildModel, fields=[
        "name",
        # "id"
    ]  # must specify ID here to get in schema
)
class Child(Node):
    pass


class ChildEdgeModel(BaseModel):
    node: ChildModel


class ChildConnectionModel(BaseModel):
    edges: List[ChildEdgeModel]
    page_info: PageInfoModel


class ParentModel(BaseModel):
    name: str
    # Must be optional so we can validate data when child_ids not passed in mutation
    # child_ids: List[str] = Field(default_factory=list)
    child_ids: List[str]


@strawberry.experimental.pydantic.type(
    model=PageInfoModel,
    fields=["has_next_page", "has_previous_page", "start_cursor", "end_cursor"]
)
class PageInfo:
    pass


@strawberry.experimental.pydantic.type(
    model=ChildEdgeModel, fields=["node"]
)
class ChildEdge:
    cursor: str


@strawberry.experimental.pydantic.type(
    model=ChildConnectionModel, fields=["edges", "page_info"]
)
class ChildConnection:
    pass


@strawberry.experimental.pydantic.type(
    model=ParentModel, fields=[
        "name",
        # "child_ids"
    ]
)
class Parent(Node):
    """
    Need to specify children here since resolver must take arguments per Relay spec.
    """
    @strawberry.field
    def children(self, first: strawberry.ID, after: int) -> List[ChildConnection]:
        return ChildConnection(
            edges=[], page_info=PageInfo(has_next_page=False, has_previous_page=False)
        )


@strawberry.experimental.pydantic.input(model=ChildModel, fields=[
    'name',
])
class ChildInput:
    pass


@strawberry.experimental.pydantic.input(model=ParentModel, fields=[
    'name',
])
class ParentInput:
    children: Optional[List[ChildInput]]


database = {}
nodes = {"parent": Parent, "child": Child}
input_nodes = {ParentInput, ChildInput}


@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: str) -> Node:
        """
        `node` root field required for Relay (refetching etc)
        """
        typename = id.split(":")[0]
        data = database[id]
        # No need for pydantic validation, data in DB is well-formed
        return nodes[typename](**data)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_parent(self, input: ParentInput) -> Parent:
        """
        Cannot validate the whole input graph against the Pydantic graph because
        we first need to create needed children, so that we can then pass the required
        ids to the Pydantic model for schema validation. This is where a transaction
        is desired, otherwise we might create some objects in the database
        corresponding to a valid subgraph, then encounter a Pydantic validation error,
        and need to clean up the subgraph ourselves.

        i.e. we expect that this line should not work, because we don't yet have all the
        child_ids needed for a valid parent.
        result = input.to_pydantic()

        TODO: wrap entire mutation in transaction
        https://www.encode.io/databases/connections_and_transactions/
        async with database.transaction():

        The design of this API is based on deep mutations in Dgraph:
        https://dgraph.io/docs/graphql/mutations/deep/

        Essentially, you should be able to pass in a mix of child objects containing
        info needed to create them, or a child object with an existing ID

        You can see examples here:
        https://github.com/dgraph-io/dgraph/blob/master/graphql/resolve/add_mutation_test.yaml

        Interestingly, in one of the examples that adds a new author with two existing
        posts, the existing posts are detached from their current author, if I
        understand correctly.

        I.e. a post can only have one author. I don't know how I feel about this. It
        seems it should raise an error, especially given our use case. You can imagine
        adding a new experiment with existing replicates, where the replicates already
        have an experiment. In DGraph, this would delete the replicate from the old
        experiment's replicates array, which seems bad.
        https://github.com/dgraph-io/dgraph/blob/master/graphql/resolve/add_mutation_test.yaml#L2029
        """
        for node in depth_first_search(input):
            # Should only create node if id is not specified
            if getattr(node, "id", None) is None:
                database_table = type(node).__name__.lower().strip("Model") + "s"
                # In practice the id would be an autoincrement primary key that we would get
                # from the database when row is added
                database_id = random.randint(1, 100)
                validated = node.to_pydantic()
                database[f"{database_table}:{database_id}"] = validated.dict(exclude_none=True)
        result = input.to_pydantic()
        database["parents:foo"] = result.dict(exclude_none=True)
        parent = ParentModel.parse_obj(database["parents:foo"])
        return Parent.from_pydantic(parent)


def depth_first_search(node: Any) -> Iterator[Any]:
    """
    Perform DFS on a graph of input objects. Return nodes in reverse order of traversal
    so the root is last. You could use BFS too, the main point is that child nodes come
    before parent nodes in the returned iterator.

    Maybe should use weakrefs here so storing pointers to nodes doesn't prevent them
    from being garbage collected?
    """
    stack = []
    explored = {}
    explored[id(node)] = node
    stack.append(node)
    while stack:
        current_node = stack.pop()
        for child_node in get_child_nodes(current_node):
            child_node_id = id(child_node)
            if child_node_id not in explored:
                explored[id(child_node)] = node
                if len(explored) > 100:
                    raise ValueError("Graph has too many nodes")
                stack.append(child_node)
    for value in reversed(explored.values()):
        yield value


def get_child_nodes(node: Any) -> Iterator[Any]:
    """
    Must recurse through lists, which per GraphQL spec can be arbitrarily nested.
    """
    if isinstance(node, list):
        for item in node:
            yield from get_child_nodes(item)
    if type(node) in input_nodes:
        yield node
    for field in vars(node).values():
        # if isinstance(field, BaseModel):
        # if type(field) in nodes:
        if type(field) in input_nodes:
            yield field
        if isinstance(field, list):
            for item in field:
                yield from get_child_nodes(item)


input = ParentInput(name="bob", children=[ChildInput(name="maery")])
for node in depth_first_search(input):
    print(node)


schema = strawberry.Schema(query=Query, mutation=Mutation)

# This mutation should first create a child, then create a parent linked to the child
# by the child's generated ID. Children should be stored in the DB as an array of IDs,
# without the ChildConnection indirection
query = """
    mutation {
        createParent(
            input: {
                name: "Suzy"
                children: [{
                    name: "Bupkiss"
                }]
            }
        ) {
            name
        }
    }
"""
# schema.execute_sync(query)


# This mutation should first create a child, then create a parent linked to the child
# by the child's generated ID. Children should be stored in the DB as an array of IDs,
# without the ChildConnection indirection
# query = """
#     mutation {
#         createParent(
#             input: {
#                 name: "Suzy"
#                 children: [
#                     {
#                         name: "Bupkiss"
#                 }]
#             }
#         ) {
#             name
#         }
#     }
# """
# schema.execute_sync(query)


# query = '{ node( id: "parents:foo" ) { name } }'
# schema.execute_sync(query)
