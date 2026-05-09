import yaml
import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from src.api.dependencies import get_db, get_embeddings_client
from src.persistence.pg_repository import PostgresRepository
from src.intelligence.embeddings import OllamaEmbeddings

router = APIRouter()

@router.get("/search")
async def search(
    query: str, 
    limit: int = 5,
    db: PostgresRepository = Depends(get_db),
    embeddings_client: OllamaEmbeddings = Depends(get_embeddings_client)
):
    """Realiza uma busca semântica por atos oficiais usando texto natural."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query não pode estar vazia.")
        
    query_vector = await embeddings_client.get_embedding(query)
    if not query_vector:
        raise HTTPException(status_code=500, detail="Erro ao gerar embedding da query.")
        
    results = await db.search_similar_chunks(query_vector, limit=limit)
    return {"query": query, "results": results}

@router.get("/status")
async def status(db: PostgresRepository = Depends(get_db)):
    """Retorna estatísticas do banco de dados."""
    if not db.pool:
        raise HTTPException(status_code=500, detail="Banco de dados desconectado.")
        
    async with db.pool.acquire() as conn:
        total_atos = await conn.fetchval("SELECT COUNT(*) FROM atos_oficiais")
        total_chunks = await conn.fetchval("SELECT COUNT(*) FROM atos_chunks")
        total_vectored = await conn.fetchval("SELECT COUNT(*) FROM atos_chunks WHERE embedding IS NOT NULL")
        
    inventory = await db.get_inventory_stats()
    
    return {
        "estatisticas": {
            "total_atos_oficiais": total_atos,
            "total_chunks_gerados": total_chunks,
            "total_chunks_com_embedding": total_vectored,
            "pendentes_vetorizacao": total_chunks - total_vectored
        },
        "inventario": inventory
    }

class SettingsUpdate(BaseModel):
    polling_interval_minutes: int
    monitoramento_ativo: bool

@router.get("/settings")
async def get_settings(db: PostgresRepository = Depends(get_db)):
    return await db.get_settings()

@router.put("/settings")
async def update_settings(update: SettingsUpdate, db: PostgresRepository = Depends(get_db)):
    success = await db.update_settings(update.polling_interval_minutes, update.monitoramento_ativo)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao atualizar configurações.")
    return {"message": "Configurações atualizadas com sucesso."}

@router.post("/ingest/backfill")
async def backfill(
    start_date: str, 
    end_date: str, 
    background_tasks: BackgroundTasks,
    db: PostgresRepository = Depends(get_db),
    embeddings_client: OllamaEmbeddings = Depends(get_embeddings_client)
):
    """Dispara a ingestão histórica para um período específico."""
    background_tasks.add_task(run_backfill_ingestion, start_date, end_date, db, embeddings_client)
    return {"message": f"Backfill iniciado para o período {start_date} a {end_date}. Verifique os logs."}

async def run_backfill_ingestion(start_date: str, end_date: str, db: PostgresRepository, embeddings: OllamaEmbeddings):
    from src.core.client import DOEBahiaClient
    from src.parsers.html_parser import HTMLParser
    from src.parsers.pdf_parser import PDFParser
    from src.core.models import AtoOficial, WatchlistConfig
    from src.intelligence.engine import IntelligenceEngine
    from src.intelligence.chunker import chunk_text
    import logging

    logger = logging.getLogger("Backfill_Ingestion")
    logger.info(f"Iniciando backfill: {start_date} -> {end_date}")

    client = DOEBahiaClient()
    engine = IntelligenceEngine(config=WatchlistConfig(keywords=[], pessoas_monitoradas=[]))

    try:
        edicoes_ids = await client.get_editions_by_range(start_date, end_date)
        logger.info(f"Total de {len(edicoes_ids)} edições encontradas para processar.")

        for ed_id in edicoes_ids:
            html_sumario = await client.get_summary_html(ed_id)
            if not html_sumario:
                continue

            metadados = HTMLParser.parse_metadata(html_sumario)
            atos_links = HTMLParser.parse_summary_tree(html_sumario)

            for ato_ref in atos_links:
                identificador = ato_ref["identificador"]
                exists = await db.get_ato_id_by_identificador(identificador)
                if not exists:
                    conteudo_bytes, content_type = await client.fetch_content(identificador)
                    if conteudo_bytes:
                        if "application/pdf" in content_type:
                            texto_integral = PDFParser.extract_text(conteudo_bytes)
                        else:
                            texto_integral = HTMLParser.extract_text(conteudo_bytes)

                        novo_ato = AtoOficial(
                            identificador=identificador,
                            secretaria=ato_ref["hierarquia"][0] if ato_ref["hierarquia"] else "Desconhecida",
                            orgao=ato_ref["hierarquia"][-1] if ato_ref["hierarquia"] else "Desconhecido",
                            titulo=ato_ref["titulo"],
                            texto_integral=texto_integral,
                            metadados=metadados
                        )
                        
                        ato_processado = await engine.processar_ato(novo_ato)
                        inseriu = await db.insert_ato_if_not_exists(ato_processado)
                        
                        if inseriu:
                            ato_id = await db.get_ato_id_by_identificador(identificador)
                            if ato_id and ato_processado.texto_limpo:
                                chunks = chunk_text(ato_processado.texto_limpo)
                                for c_text in chunks:
                                    await db.insert_chunk(ato_id, c_text)
        
        logger.info(f"Backfill concluído com sucesso: {start_date} -> {end_date}")
    except Exception as e:
        logger.error(f"Falha durante o backfill: {e}")
    finally:
        await client.close()

@router.get("/watchlist/alerts")
async def watchlist_alerts(db: PostgresRepository = Depends(get_db)):
    """
    Retorna os atos que possuem match com os termos da watchlist.yaml.
    Fazendo uma busca lexical simples por ILIKE no banco.
    """
    if not db.pool:
        raise HTTPException(status_code=500, detail="Banco de dados desconectado.")
        
    watchlist_path = "watchlist.yaml"
    if not os.path.exists(watchlist_path):
        raise HTTPException(status_code=404, detail="Arquivo watchlist.yaml não encontrado.")
        
    with open(watchlist_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    termos = config.get("keywords", []) + config.get("pessoas_monitoradas", [])
    if not termos:
        return {"alerts": []}
        
    alerts = []
    async with db.pool.acquire() as conn:
        for termo in termos:
            query = """
                SELECT id, identificador, titulo, secretaria, data_publicacao 
                FROM atos_oficiais 
                WHERE texto_limpo ILIKE $1 
                LIMIT 10;
            """
            records = await conn.fetch(query, f"%{termo}%")
            if records:
                alerts.append({
                    "termo": termo,
                    "matches": [
                        {
                            "id": r["id"],
                            "identificador": r["identificador"],
                            "titulo": r["titulo"],
                            "secretaria": r["secretaria"],
                            "data_publicacao": str(r["data_publicacao"])
                        }
                        for r in records
                    ]
                })
                
    return {"alerts": alerts}
