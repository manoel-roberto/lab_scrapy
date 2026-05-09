from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

class MetadadosEdicao(BaseModel):
    """
    Representa os metadados extraídos de uma edição do Diário Oficial.
    """
    numero: int
    data_publicacao: date
    caderno: Optional[str] = None
    url_origem: Optional[str] = None


class AtoOficial(BaseModel):
    """
    Representa um ato oficial extraído, mantendo sua hierarquia.
    """
    identificador: str
    secretaria: str
    orgao: str
    titulo: str
    texto_integral: str
    texto_limpo: Optional[str] = Field(default=None, description="Texto após remoção de ruídos (cabeçalhos, rodapés)")
    pagina: Optional[int] = Field(default=None, description="Número da página onde o ato se encontra")
    hash_conteudo: Optional[str] = Field(default=None, description="Hash SHA-256 do texto limpo para deduplicação")
    motor_extracao: Optional[str] = Field(default=None, description="Qual motor extraiu os dados: REGEX, SPACY, OLLAMA")
    metadados: MetadadosEdicao
