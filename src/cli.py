import asyncio
import argparse
import logging
import sys
from typing import List

from src.core.client import DOEBahiaClient
from src.parsers.html_parser import HTMLParser
from src.parsers.pdf_parser import PDFParser
from src.core.models import AtoOficial
from src.utils.helpers import parse_input_type

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DOE_BA_CLI")

async def process_edition(client: DOEBahiaClient, edicao_id: str):
    """
    Processa uma única edição completa.
    """
    logger.info(f"[@cli] >>> Iniciando extração da edição ID {edicao_id} <<<")
    
    # Discovery
    summary_html = await client.get_summary_html(edicao_id)
    if not summary_html:
        logger.error(f"Não foi possível recuperar o sumário para ID {edicao_id}.")
        return
        
    lista_atos_info = HTMLParser.parse_summary_tree(summary_html)
    if not lista_atos_info:
        logger.warning(f"Nenhum ato encontrado para a edição {edicao_id}.")
        return

    # Metadados
    metadata_html = await client.get_edition_metadata_html(edicao_id)
    metadados = HTMLParser.parse_metadata(metadata_html if metadata_html else summary_html)

    logger.info(f"[@cli] Processando {len(lista_atos_info)} atos para a Edição {metadados.numero}")

    # Batch Processing de Atos
    tasks = [process_single_ato(client, ato_info, metadados) for ato_info in lista_atos_info]
    resultados = await asyncio.gather(*tasks)
    
    sucessos = [r for r in resultados if r is not None]
    logger.info(f"[@cli] Edição {edicao_id} finalizada. Sucesso: {len(sucessos)}/{len(lista_atos_info)}")

async def process_single_ato(client: DOEBahiaClient, ato_info: dict, metadados):
    identificador = ato_info['identificador']
    titulo = ato_info['titulo']
    
    content_bytes, content_type = await client.fetch_content(identificador)
    if not content_bytes:
        return None
        
    try:
        if "application/pdf" in content_type:
            texto = PDFParser.extract_text(content_bytes)
        else:
            texto = HTMLParser.extract_text(content_bytes)
            
        return AtoOficial(
            identificador=identificador,
            secretaria=ato_info['hierarquia'][0] if ato_info['hierarquia'] else "N/A",
            orgao=ato_info['hierarquia'][1] if len(ato_info['hierarquia']) > 1 else "N/A",
            titulo=titulo,
            texto_integral=texto,
            metadados=metadados
        )
    except Exception as e:
        logger.error(f"Erro no parsing do ato {identificador}: {e}")
        return None

async def run_pipeline(input_query: str):
    client = DOEBahiaClient()
    try:
        parsed = parse_input_type(input_query)
        ids_to_process: List[str] = []

        if parsed["type"] == "id":
            ids_to_process = [parsed["value"]]
        elif parsed["type"] == "date":
            ids_to_process = await client.get_editions_by_date(parsed["value"])
        elif parsed["type"] == "range":
            ids_to_process = await client.get_editions_by_range(parsed["start"], parsed["end"])

        if not ids_to_process:
            logger.warning(f"Nenhuma edição encontrada para a consulta: '{input_query}'")
            return

        logger.info(f"[@cli] Total de edições a processar: {len(ids_to_process)}")
        
        # Processa edições sequencialmente para não sobrecarregar com Playwright
        for eid in ids_to_process:
            await process_edition(client, eid)

    except ValueError as e:
        logger.error(f"Erro de entrada: {e}")
    finally:
        await client.close()

def main():
    parser = argparse.ArgumentParser(description="DOE-BA CLI Scraper")
    parser.add_argument("query", nargs='+', help="ID, Data ou Período (ex: 01/01/2024 até 05/01/2024)")
    args = parser.parse_args()
    
    query_str = " ".join(args.query)
    asyncio.run(run_pipeline(query_str))

if __name__ == "__main__":
    main()
