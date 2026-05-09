import os
import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import List

POSTGRES_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql:///doe_ba"  # peer auth via socket Unix (usuário do SO)
)

class WatchlistConfig(BaseModel):
    keywords: List[str]
    pessoas_monitoradas: List[str]

def load_watchlist(path: str = "watchlist.yaml") -> WatchlistConfig:
    """Carrega as configurações de filtros da watchlist."""
    file_path = Path(path)
    if not file_path.exists():
        return WatchlistConfig(keywords=[], pessoas_monitoradas=[])
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return WatchlistConfig(**(data or {"keywords": [], "pessoas_monitoradas": []}))
