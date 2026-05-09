from src.persistence.pg_repository import PostgresRepository
from src.intelligence.embeddings import OllamaEmbeddings
from src.core.config import POSTGRES_DSN

# Instâncias globais para a API
db_repo = PostgresRepository(dsn=POSTGRES_DSN)
embeddings_client = OllamaEmbeddings()

async def get_db():
    if not db_repo.pool:
        await db_repo.connect()
    return db_repo

async def get_embeddings_client():
    return embeddings_client
