import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Unidad III: el dashboard (Vite, http://localhost:5173) es otro origen. Solo se aceptan los orígenes
# listados en CORS_ORIGINS (separados por coma); GraphiQL sigue funcionando porque es el mismo origen.
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)



# GRAPHQL


app.include_router(GraphQLRouter(schema), prefix="/graphql")
