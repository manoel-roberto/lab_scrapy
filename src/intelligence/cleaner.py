import re

def clean_text(text: str) -> str:
    """
    Remove ruídos comuns de extração de PDF, como numeração de páginas,
    cabeçalhos repetitivos e quebras de linha quebradas.
    """
    if not text:
        return ""
        
    # Remove cabeçalhos de página típicos do DOE (ex: "Diário Oficial do Estado da Bahia - xx/xx/xxxx")
    # Ajuste a regex conforme o padrão real do DOE
    text = re.sub(r'Diário Oficial.*?Estado da Bahia.*?\n', '', text, flags=re.IGNORECASE)
    
    # Remove números de página isolados (ex: "123 \n" ou "- 12 -")
    text = re.sub(r'^\s*-?\s*\d+\s*-?\s*$\n?', '', text, flags=re.MULTILINE)
    
    # Consolida quebras de linha onde a frase não terminou (ex: final não tem ponto)
    # text = re.sub(r'([^\.\;\:\?!])\n([A-Z0-9a-z])', r'\1 \2', text)
    
    # Remove espaços em branco excessivos
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()
