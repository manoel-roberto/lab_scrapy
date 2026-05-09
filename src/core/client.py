import asyncio
import logging
from typing import Optional, Tuple, List
import httpx
from playwright.async_api import async_playwright

from src.utils.helpers import apply_jitter, format_date_to_api

logger = logging.getLogger("DOE_BA_Engine")

class DOEBahiaClient:
    """
    Cliente otimizado para o Diário Oficial da Bahia.
    """
    def __init__(self, base_url: str = "https://dool.egba.ba.gov.br"):
        self.base_url = base_url
        self.semaphore = asyncio.Semaphore(8)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*"
        }
        self.api_base_url = "https://www.dool.egba.ba.gov.br"
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=60.0,
            verify=False,
            follow_redirects=True
        )

    async def close(self):
        await self.http_client.aclose()

    async def get_summary_html(self, edicao_id: str) -> Optional[str]:
        """Recupera o fragmento HTML do sumário diretamente."""
        url = f"/html/{edicao_id}.html"
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"[@debugger] Falha ao obter sumário para ID {edicao_id}: {e}")
            return None

    async def get_editions_by_date(self, date_str: str) -> List[str]:
        """
        Busca edições de uma data específica. Retorna lista de IDs internos.
        """
        api_date = format_date_to_api(date_str)
        url = f"/apifront/portal/edicoes/edicoes_from_data/{api_date}.json"
        
        logger.info(f"[@debugger] Buscando edições para a data: {date_str}")
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            ids = [str(item['id']) for item in data.get('itens', [])]
            return ids
        except Exception as e:
            logger.error(f"[@debugger] Erro ao buscar edições por data: {e}")
            return []

    async def get_editions_by_range(self, start_date: str, end_date: str) -> List[str]:
        """
        Busca edições em um intervalo de datas usando a API de calendário.
        """
        di = format_date_to_api(start_date)
        df = format_date_to_api(end_date)
        # Endpoint de busca agregada (calendário)
        url = f"/busca/busca/buscar/query/0/di:{di}/df:{df}/?1=1&q=*&calendario=1"
        
        logger.info(f"[@debugger] Buscando edições no período: {start_date} até {end_date}")
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            data = response.json()
            
            ids = []
            buckets = data.get('aggregations', {}).get('group_by_data', {}).get('buckets', [])
            for day_bucket in buckets:
                edicoes = day_bucket.get('group_by_edicao', {}).get('buckets', [])
                for ed_bucket in edicoes:
                    ids.append(str(ed_bucket['key']))
            
            return sorted(list(set(ids))) # Remove duplicatas e ordena
        except Exception as e:
            logger.error(f"[@debugger] Erro ao buscar edições por período: {e}")
            return []

    async def get_edition_metadata_html(self, edicao_id: str) -> Optional[str]:
        """Acessa a página principal da edição para extrair metadados via Playwright."""
        url = f"{self.base_url}/ver-html/{edicao_id}/"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                # Tenta clicar no modal se houver
                try:
                    await page.click("button:has-text('CONTINUAR SEM CADASTRO')", timeout=5000)
                except Exception:
                    pass
                await page.wait_for_selector(".edi-p-id-data", timeout=10000)
                return await page.content()
            except Exception:
                return None
            finally:
                await browser.close()

    async def fetch_content(self, identificador: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Baixa o conteúdo de uma publicação."""
        url = f"/apifront/portal/edicoes/publicacoes_ver_conteudo/{identificador}"
        async with self.semaphore:
            for attempt in range(3):
                await apply_jitter()
                try:
                    response = await self.http_client.get(url)
                    response.raise_for_status()
                    return response.content, response.headers.get("Content-Type", "")
                except Exception:
                    await asyncio.sleep(2 ** attempt)
            return None, None
