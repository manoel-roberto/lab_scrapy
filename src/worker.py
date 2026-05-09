import asyncio
import logging
from datetime import datetime

from src.core.client import DOEBahiaClient
from src.core.config import WatchlistConfig, POSTGRES_DSN
from src.parsers.html_parser import HTMLParser
from src.parsers.pdf_parser import PDFParser
from src.core.models import AtoOficial
from src.persistence.pg_repository import PostgresRepository
from src.intelligence.engine import IntelligenceEngine
from src.intelligence.chunker import chunk_text
from src.intelligence.embeddings import OllamaEmbeddings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DOE_Worker")

async def notify_match(ato: AtoOficial):
    """
    Dispara notificações para atos detectados pela watchlist.
    Atualmente envia logs estruturados, preparado para Telegram/Slack.
    """
    emoji = "🚨" if ato.motor_extracao == "REGEX" else "🧠"
    message = (
        f"\n{emoji} MATCH DETECTADO: {ato.titulo}\n"
        f"ID: {ato.identificador}\n"
        f"Motor: {ato.motor_extracao}\n"
        f"Link: https://dool.egba.ba.gov.br/apifront/portal/edicoes/publicacoes_ver_conteudo/{ato.identificador}\n"
        f"Snippet: {ato.texto_limpo[:200]}..."
    )
    logger.critical(message)
    # TODO: Integrar com httpx para enviar para Webhook (Telegram/Slack)


async def worker_loop():
    logger.info("Iniciando Worker do DOE-BA...")
    
    config = WatchlistConfig(keywords=[], pessoas_monitoradas=[])
    db_repo = PostgresRepository(dsn=POSTGRES_DSN)
    client = DOEBahiaClient()
    engine = IntelligenceEngine(config=config)
    embeddings_client = OllamaEmbeddings()
    
    await db_repo.connect()
    await db_repo.setup_schema()
    
    try:
        while True:
            logger.info("Iniciando ciclo de processamento...")
            
            # 1. Processar chunks pendentes de vetorização (em loop até esvaziar a fila)
            while True:
                pendentes = await db_repo.get_chunks_without_vectors(limit=100)
                if not pendentes:
                    break
                    
                logger.info(f"Processando lote de {len(pendentes)} chunks para vetorização...")
                for chunk in pendentes:
                    texto = chunk["texto_chunk"]
                    vetor = await embeddings_client.get_embedding(texto)
                    if vetor:
                        await db_repo.save_chunk_vector(chunk["id"], vetor)
                logger.info(f"Lote de {len(pendentes)} chunks vetorizado.")
            
            # 2. Buscar configurações dinâmicas
            settings = await db_repo.get_settings()
            monitoramento_ativo = settings.get("monitoramento_ativo", True)
            polling_minutes = settings.get("polling_interval_minutes", 60)

            if monitoramento_ativo:
                # 3. Buscar novas edições (Simulação simplificada do Scraper)
                hoje = datetime.now().strftime("%d/%m/%Y")
                edicoes = await client.get_editions_by_date(hoje)
                
                if edicoes:
                    logger.info(f"Edições encontradas para hoje ({hoje}): {edicoes}")
                    for ed_id in edicoes:
                        html_sumario = await client.get_summary_html(ed_id)
                        if html_sumario:
                            metadados = HTMLParser.parse_metadata(html_sumario)
                            atos_links = HTMLParser.parse_summary_tree(html_sumario)
                            
                            for ato_ref in atos_links:
                                identificador = ato_ref["identificador"]
                                exists = await db_repo.get_ato_id_by_identificador(identificador)
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
                                        
                                        inseriu = await db_repo.insert_ato_if_not_exists(ato_processado)
                                        if inseriu:
                                            # Disparar notificação se houve match na inteligência
                                            if ato_processado.motor_extracao != "NENHUM":
                                                await notify_match(ato_processado)
                                                
                                            ato_id = await db_repo.get_ato_id_by_identificador(identificador)
                                            if ato_id and ato_processado.texto_limpo:
                                                chunks = chunk_text(ato_processado.texto_limpo)
                                                for c_text in chunks:
                                                    await db_repo.insert_chunk(ato_id, c_text)
                                                logger.info(f"Gerados {len(chunks)} chunks para o ato {identificador}")
            else:
                logger.info("Monitoramento pausado via configurações do sistema.")

            logger.info(f"Ciclo concluído. Aguardando {polling_minutes} minutos...")
            await asyncio.sleep(polling_minutes * 60)
            
    except asyncio.CancelledError:
        logger.info("Worker cancelado.")
    finally:
        await db_repo.close()
        await client.close()
        await embeddings_client.close()

if __name__ == "__main__":
    asyncio.run(worker_loop())
