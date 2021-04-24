from starlette.config import Config
from starlette.datastructures import URL

config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
DATABASE_URL = config("DATABASE_URL", cast=URL)
GRAPHQL_ROUTE = "/graphql"
