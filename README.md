# graphql-python

Just tinkering with GraphQL in Python, really liking Strawberry so far. Graphene is popular but I find it verbose compared to Strawberry, also its dataloader is unmaintained and the Pydantic integration (which seems cool) is not well-documented.

## Installation

First install Python 3.9.4, then create a `venv` and run `pip install -r requirements-berry.txt` for the `berry` example or just `pip install -r requirements.txt` for the Graphene example.

For the `berry` example also run `cp dev.env .env`.

## Usage

For the `berry` example run `uvicorn berry.app:app --reload --app-dir berry`.

For the Graphene example run the development server with `uvicorn app.main:app --reload`

In either case go to the GraphiQL interface at http://127.0.0.1:8000/graphql

## Development

Install `requirements-dev.txt` too. Run linting with `tox -e lint`
