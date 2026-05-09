import json
import logging
from pathlib import Path
from src.core.models import AtoOficial

logger = logging.getLogger(__name__)

class JSONLWriter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_ato(self, ato: AtoOficial, filename: str = "atos.jsonl"):
        """Grava um ato oficial de forma incremental em um arquivo JSONL."""
        file_path = self.output_dir / filename
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(ato.model_dump(), default=str, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Erro ao gravar JSONL: {e}")
