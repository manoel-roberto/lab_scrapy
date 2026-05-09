from datetime import datetime
import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from src.core.models import MetadadosEdicao
from src.utils.helpers import clean_text

logger = logging.getLogger("DOE_BA_Engine")

class HTMLParser:
    """
    Parser focado em conteúdo HTML (text/html).
    Extrai metadados e conteúdo da árvore de sumário usando BeautifulSoup4.
    """
    
    @staticmethod
    def parse_metadata(html_content: str) -> MetadadosEdicao:
        """
        Extrai o número da edição e a data de publicação a partir da tag div.edi-p-id-data.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        div = soup.select_one('div.edi-p-id-data')
        
        texto_metadados = clean_text(div.text) if div else ""
        logger.debug(f"[@debugger] [Parsing Phase] Texto base de metadados: {texto_metadados}")
        
        # Expressões regulares simples para extração - podem precisar de ajuste fino
        numero_match = re.search(r'Edição\s*n?[º°]?\s*(\d+)', texto_metadados, re.IGNORECASE)
        data_match = re.search(r'(\d{2}/\d{2}/\d{4})', texto_metadados)
        
        numero = int(numero_match.group(1)) if numero_match else 0
        
        data_publicacao = datetime.today().date()
        if data_match:
            try:
                data_publicacao = datetime.strptime(data_match.group(1), "%d/%m/%Y").date()
            except ValueError:
                pass
                
        return MetadadosEdicao(numero=numero, data_publicacao=data_publicacao)

    @staticmethod
    def parse_summary_tree(html_content: str) -> List[Dict[str, Any]]:
        """
        Varre a árvore de sumário (#tree) em busca de links com a classe .linkMateria.
        Retorna uma lista de dicionários contendo identificador, titulo e hierarquia básica.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        tree = soup.select_one('#tree')
        
        if not tree:
            logger.warning("[@debugger] [Parsing Phase] Elemento #tree não encontrado no HTML.")
            return []
            
        atos = []
        links_materia = tree.select('a.linkMateria')
        
        for link in links_materia:
            identificador = link.get('identificador')
            titulo = clean_text(link.text)
            
            # Tenta encontrar a hierarquia (Secretaria / Órgão) subindo na árvore
            # Geralmente o nome da pasta está em um <span> ou link anterior no <li>/<ul>
            hierarquia = []
            parent = link.parent
            while parent and parent.name != 'div' and parent.get('id') != 'tree':
                # Procura por elementos que indiquem o nome da pasta
                folder_text = ""
                # Dependendo da versão do site, o nome está em um <a> ou <span> irmão
                prev = parent.find_previous_sibling()
                if prev:
                    folder_text = clean_text(prev.text)
                
                if folder_text and folder_text not in hierarquia:
                    hierarquia.append(folder_text)
                
                parent = parent.parent
            
            if identificador:
                atos.append({
                    "identificador": identificador,
                    "titulo": titulo,
                    "hierarquia": hierarquia[::-1] # Inverte para ficar do topo para a base
                })
                
        logger.info(f"[@debugger] [Parsing Phase] Total de {len(atos)} atos identificados no sumário.")
        return atos

    @staticmethod
    def extract_text(html_content: bytes) -> str:
        """
        Extrai texto de um trecho HTML baixado via HTTPX.
        """
        soup = BeautifulSoup(html_content, 'lxml')
        return clean_text(soup.get_text(separator=' '))
