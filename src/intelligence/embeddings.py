import asyncio
import httpx
import logging
import time
from typing import List

logger = logging.getLogger(__name__)

# nomic-embed-text suporta ~8192 tokens; ~4 chars/token → limite seguro de 8000 chars
_MAX_CHARS = 8000


class OllamaEmbeddings:
    """Cliente assíncrono para gerar embeddings usando Ollama Local."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def get_embedding(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """
        Gera embedding de um texto via Ollama.
        Trunca automaticamente textos acima do limite do modelo e
        tenta até 3 vezes com backoff exponencial em caso de erro 500.
        """
        # Trunca para o limite seguro do modelo
        if len(text) > _MAX_CHARS:
            logger.warning(f"Texto truncado: {len(text)} → {_MAX_CHARS} chars para geração de embedding.")
            text = text[:_MAX_CHARS]

        for attempt in range(3):
            start_time = time.perf_counter()
            try:
                response = await self.client.post(
                    "/api/embeddings",
                    json={"model": model, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                embedding = data.get("embedding", [])
                latency = (time.perf_counter() - start_time) * 1000
                logger.info(
                    f"Embedding ({len(embedding)} dims) gerado em {latency:.2f}ms "
                    f"para {len(text)} chars (tentativa {attempt + 1})."
                )
                return embedding
            except httpx.HTTPStatusError as e:
                wait = 2 ** attempt
                logger.warning(f"Ollama HTTP {e.response.status_code} na tentativa {attempt + 1}. Aguardando {wait}s...")
                await asyncio.sleep(wait)
            except Exception as e:
                logger.error(f"Erro inesperado ao gerar embedding: {e}")
                return []

        logger.error("Falha ao gerar embedding após 3 tentativas.")
        return []

    async def close(self):
        await self.client.aclose()
