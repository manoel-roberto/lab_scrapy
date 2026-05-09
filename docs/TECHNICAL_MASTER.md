# TECHNICAL MASTER: Arquitetura DOE-BA Intelligence Engine
> Documento consolidado para engenheiros e especialistas em IA.

## 1. Pipeline de Ingestão e Resiliência (Web Scraping)

O motor de coleta reside em `src/core/client.py`. Ele foi projetado para lidar com as idiossincrasias do servidor **Apache/2.2.22** da EGBA.

### Estratégias de Robustez:
- **Semaphore(8):** Localizado no `__init__` do `DOEBahiaClient`, limita a concorrência global para evitar 503 Service Unavailable.
- **Bypass de Modal:** Implementado via **Playwright** no método `get_edition_metadata_html`. Simula a interação humana para transpor o bloqueio informativo da EGBA.
- **Validação de Contrato:** Todo dado raspado (PDF/HTML) é convertido no modelo `AtoOficial` em `src/core/models.py`, utilizando **Pydantic** para garantir integridade tipográfica e estrutural.

---

## 2. O Funil de Inteligência (Intelligence Layer)

A lógica de processamento semântico está centralizada em `src/intelligence/engine.py`.

### Arquitetura de Camadas:
1.  **Camada 1 (Regex):** Filtragem léxica rápida. Descarta textos irrelevantes antes do processamento pesado.
2.  **Camada 2 (NER):** Utiliza o **Spacy** (`pt_core_news_sm`) para extração de Entidades Nomeadas (Pessoas, Organizações, Valores).
3.  **Camada 3 (LLM Fallback):** Chamada assíncrona ao **Ollama** (`qwen2.5:1.5b`) para estruturação de JSON quando o Spacy é insuficiente.
    - **Pós-Processamento:** O resultado do Ollama é validado pelo Pydantic para evitar erros de parser em etapas subsequentes.

---

## 3. Vetorização e Busca Semântica (RAG)

### Particionamento (Chunking):
Implementado em `src/intelligence/chunker.py`.
- **Configuração:** 600 palavras por bloco com 10% (60 palavras) de **overlap**.
- **Propósito:** Manter a coesão semântica e evitar a perda de contexto em fronteiras de corte.

### Persistência Vetorial:
O arquivo `src/persistence/pg_repository.py` gerencia o **pgvector**.
- **Métrica:** Similaridade de Cosseno via operador `<=>`.
- **Performance:** Busca vetorial nativa em SQL, permitindo consultas híbridas (metadados + semântica).

---

## 4. Orquestração e Infraestrutura

### O Loop de Execução:
O `src/worker.py` orquestra o pipeline completo:
- Polling do banco de dados.
- Disparo de extração e inteligência.
- Vetorização de chunks pendentes via `src/intelligence/embeddings.py`.

### Persistência de Dados:
Volumes mapeados em `docker-compose.yml` para a pasta `data/`:
- `data/logs/`: Diagnóstico técnico.
- `data/backups/`: Segurança do estado do banco.
- `data/temp/`: Área de manobra para buffer de PDFs.

---

## 5. Guia de Estudo Técnico

- **Concorrência:** [Estude Asyncio Semaphores em Python](https://docs.python.org/3/library/asyncio-sync.html#semaphore)
- **Busca Vetorial:** [Pesquise por HNSW no PostgreSQL (pgvector)](https://github.com/pgvector/pgvector)
- **NLP:** [Documentação Spacy NER](https://spacy.io/usage/linguistic-features#named-entities)

---
*Este documento é a verdade técnica definitiva da Plataforma DOE-BA.*
