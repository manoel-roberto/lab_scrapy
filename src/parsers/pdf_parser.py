import os
import tempfile
import logging
import pdfplumber

from src.utils.helpers import clean_text

logger = logging.getLogger("DOE_BA_Engine")

class PDFParser:
    """
    Parser focado em conteúdo PDF (application/pdf).
    Salva em disco temporariamente, extrai o texto e apaga o arquivo.
    """
    
    @staticmethod
    def extract_text(pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            return ""
            
        logger.info("[@debugger] [Parsing Phase] Extraindo texto de arquivo PDF (pdfplumber)")
        
        # Cria arquivo temporário seguro
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(pdf_bytes)
                
            text_blocks = []
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_blocks.append(page_text)
                        
            full_text = "\n".join(text_blocks)
            return clean_text(full_text)
            
        except Exception as e:
            logger.error(f"[@debugger] [Parsing Phase] Erro ao extrair texto do PDF: {e}")
            return ""
        finally:
            # Cleanup garantido
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug("[@debugger] [Parsing Phase] Arquivo PDF temporário deletado com sucesso.")
