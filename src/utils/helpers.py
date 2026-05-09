import asyncio
import random
import re
import logging
from datetime import datetime

logger = logging.getLogger("DOE_BA_Engine")

async def apply_jitter(min_ms: int = 200, max_ms: int = 500) -> None:
    """
    Aplica um delay assíncrono aleatório (Jitter) para evitar sobrecarregar
    o servidor legado do Diário Oficial.
    """
    delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    logger.debug(f"Aplicando jitter de {delay:.3f}s")
    await asyncio.sleep(delay)

def clean_text(text: str) -> str:
    """
    Limpa e normaliza textos extraídos de HTML e PDF.
    """
    if not text:
        return ""
    
    # Substitui múltiplos espaços e quebras por um único espaço
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_date_to_api(date_str: str) -> str:
    """
    Converte uma data de DD/MM/AAAA para YYYY-MM-DD (formato da API).
    """
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Formato de data inválido: {date_str}. Use DD/MM/AAAA.")

def parse_input_type(input_str: str) -> dict:
    """
    Detecta se a entrada é um ID numérico, uma data única ou um período.
    """
    input_str = input_str.strip()
    
    # Caso: Período (DD/MM/AAAA até DD/MM/AAAA)
    range_match = re.match(r'(\d{2}/\d{2}/\d{4})\s+até\s+(\d{2}/\d{2}/\d{4})', input_str, re.IGNORECASE)
    if range_match:
        return {
            "type": "range",
            "start": range_match.group(1),
            "end": range_match.group(2)
        }
    
    # Caso: Data Única (DD/MM/AAAA)
    date_match = re.match(r'^\d{2}/\d{2}/\d{4}$', input_str)
    if date_match:
        return {
            "type": "date",
            "value": input_str
        }
    
    # Caso: ID Numérico
    if input_str.isdigit():
        return {
            "type": "id",
            "value": input_str
        }
    
    raise ValueError("Entrada não reconhecida. Use ID, DD/MM/AAAA ou DD/MM/AAAA até DD/MM/AAAA.")
