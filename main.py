from contextlib import asynccontextmanager

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from database.seed_roles import inicializar_roles_y_permisos
from schema.schema import schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_roles_y_permisos()
    yield


app = FastAPI(
    title="Sistema Financiero - GraphQL",
    version="1.0.0",
    lifespan=lifespan,
)



# GRAPHQL


app.include_router(GraphQLRouter(schema), prefix="/graphql")
