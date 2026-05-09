import re
import json
import hashlib
import httpx
import logging
from typing import Dict, Any, Optional

from src.core.models import AtoOficial
from src.core.config import WatchlistConfig
from src.intelligence.cleaner import clean_text

logger = logging.getLogger(__name__)

class IntelligenceEngine:
    def __init__(self, config: WatchlistConfig, ollama_url: str = "http://localhost:11434"):
        self.config = config
        self.ollama_url = ollama_url
        self._spacy_nlp = None
        self._load_spacy()

    def _load_spacy(self):
        try:
            import spacy
            # Tenta carregar o modelo em português
            self._spacy_nlp = spacy.load("pt_core_news_sm")
            logger.info("Modelo Spacy 'pt_core_news_sm' carregado com sucesso.")
        except Exception as e:
            logger.warning(f"Não foi possível carregar Spacy 'pt_core_news_sm': {e}. Motor NER ficará desabilitado.")

    def camada_1_regex(self, text: str) -> bool:
        """Verifica se o texto contém keywords ou pessoas monitoradas da watchlist."""
        # Verifica keywords
        if self.config.keywords:
            kw_pattern = re.compile(
                r'\b(?:' + '|'.join(map(re.escape, self.config.keywords)) + r')\b',
                re.IGNORECASE
            )
            if kw_pattern.search(text):
                return True

        # Verifica pessoas monitoradas (busca literal, sem boundary para nomes compostos)
        if self.config.pessoas_monitoradas:
            pessoas_pattern = re.compile(
                '|'.join(map(re.escape, self.config.pessoas_monitoradas)),
                re.IGNORECASE
            )
            if pessoas_pattern.search(text):
                return True

        return False

    def camada_2_spacy_ner(self, text: str) -> Dict[str, list]:
        """Extrai entidades nomeadas usando Spacy (Pessoas, Organizações, Valores)."""
        if not self._spacy_nlp:
            return {}
            
        doc = self._spacy_nlp(text)
        entidades = {
            "PESSOAS": [],
            "ORGANIZACOES": [],
            "VALORES": []
        }
        
        for ent in doc.ents:
            if ent.label_ == "PER":
                entidades["PESSOAS"].append(ent.text)
            elif ent.label_ == "ORG":
                entidades["ORGANIZACOES"].append(ent.text)
            elif ent.label_ in ["MONEY", "NUM"]:
                # Spacy em português as vezes erra money, mas podemos refinar depois
                entidades["VALORES"].append(ent.text)
                
        # Deduplicar
        return {k: list(set(v)) for k, v in entidades.items() if v}

    async def camada_3_ollama_fallback(self, text: str, max_tokens: int = 800) -> Optional[Dict[str, Any]]:
        """Fallback para o Ollama local quando estrutura complexa é requerida."""
        prompt = f"""
        Extraia as informações principais deste ato oficial.
        Responda APENAS com um JSON válido contendo as chaves: "pessoas_envolvidas", "valor_contrato", "resumo".
        Texto do Ato:
        {text[:max_tokens]}
        """
        
        payload = {
            "model": "qwen2.5:1.5b",  # Conforme planejamento, modelo rápido e pequeno
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                result_text = data.get("response", "{}")
                return json.loads(result_text)
        except Exception as e:
            logger.error(f"Erro na camada 3 (Ollama Fallback): {e}")
            return None

    async def processar_ato(self, ato: AtoOficial) -> AtoOficial:
        """
        Orquestra o pipeline de inteligência: Limpeza -> Regex -> Spacy -> Ollama (se necessário).
        """
        # 1. Limpeza e Hash
        texto_limpo = clean_text(ato.texto_integral)
        hash_conteudo = hashlib.sha256(texto_limpo.encode('utf-8')).hexdigest()
        
        ato.texto_limpo = texto_limpo
        ato.hash_conteudo = hash_conteudo
        
        # 2. Camada 1: Regex Watchlist
        if not self.camada_1_regex(texto_limpo):
            ato.motor_extracao = "NENHUM"
            return ato
            
        # 3. Camada 2: Spacy NER
        entidades = self.camada_2_spacy_ner(texto_limpo)
        
        # Simulação de lógica de negócio: Se Spacy falhar em achar pessoas num ato que regex achou algo,
        # ou se o regex encontrou termos complexos como 'licitação', chamamos o fallback
        if not entidades.get("PESSOAS") and "licita" in texto_limpo.lower():
            ato.motor_extracao = "OLLAMA"
            ollama_result = await self.camada_3_ollama_fallback(texto_limpo)
            if ollama_result:
                # Aqui poderíamos injetar os metadados estruturados extraídos, 
                # por enquanto salvamos no log/motor
                logger.info(f"Ollama extraiu: {ollama_result}")
        else:
            ato.motor_extracao = "SPACY"
            logger.info(f"Spacy extraiu entidades: {entidades}")
            
        return ato
