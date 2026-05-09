from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.api.dependencies import db_repo, embeddings_client
from src.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db_repo.connect()
    await db_repo.setup_schema()
    yield
    # Shutdown
    await db_repo.close()
    await embeddings_client.close()

app = FastAPI(
    title="DOE-BA Intelligence API",
    description="API de busca semântica para os atos oficiais do Diário Oficial do Estado da Bahia.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)
