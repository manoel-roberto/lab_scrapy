from typing import List
import re

def chunk_text(text: str, chunk_size: int = 600, overlap_size: int = 60) -> List[str]:
    """
    Divide o texto limpo em blocos (chunks) usando uma aproximação baseada em palavras/tokens
    para preparação de RAG, garantindo um overlap entre os blocos.
    
    chunk_size: Tamanho alvo do chunk em palavras (aproximando tokens).
    overlap_size: Tamanho da sobreposição em palavras.
    """
    if not text:
        return []
        
    # Uma separação simples por palavras atende bem como baseline (1 token ~= 0.75 palavras)
    words = re.findall(r'\S+', text)
    chunks = []
    
    i = 0
    while i < len(words):
        end_idx = min(i + chunk_size, len(words))
        chunk = " ".join(words[i:end_idx])
        chunks.append(chunk)
        
        # Se chegamos ao fim, sai do loop
        if end_idx == len(words):
            break
            
        # Avança reduzindo o overlap
        i += (chunk_size - overlap_size)
        
    return chunks
