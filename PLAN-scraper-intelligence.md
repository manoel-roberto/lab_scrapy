# PLAN: Scraper Intelligence & Persistence

## Overview
Evoluir o scraper do DOE-BA substituindo o pipeline estático atual por um motor de extração inteligente híbrido (Local-First: Regex -> NLP/Spacy -> LLM/Ollama). Adicionar persistência dual (JSONL + PostgreSQL/pgvector) visando integração com RAG.

## Project Type
BACKEND

## Tech Stack
*   **Pydantic**: Modelagem rigorosa de dados.
*   **Spacy (`pt_core_news_sm`)**: Extração de entidades nomeadas (NER) ultraleve.
*   **Ollama**: Extração estruturada via LLM local (fallback).
*   **PostgreSQL + pgvector**: Banco de dados para deduplicação e busca semântica.
*   **Asyncio/httpx**: Manutenção do desempenho (589 atos/65s).

## File Structure
```
├── watchlist.yaml               # Arquivo de configuração de filtros
├── src/
│   ├── core/
│   │   ├── models.py            # Atualização para Pydantic
│   ├── intelligence/
│   │   ├── engine.py            # IntelligenceEngine (Camadas 1, 2 e 3)
│   │   ├── chunker.py           # Divisão de texto para RAG
│   │   └── cleaner.py           # Limpeza de ruídos
│   └── persistence/
│       ├── jsonl_writer.py      # Geração de arquivos de auditoria
│       └── pg_repository.py     # Deduplicação e Inserção no PostgreSQL
```

## Task Breakdown

### Task 1: Modelagem Pydantic e Watchlist
*   **Agent**: `backend-specialist`
*   **Skill**: `python-patterns`
*   **Action**: Converter `AtoOficial` em modelo Pydantic. Adicionar: `secretaria`, `orgao`, `titulo`, `texto_limpo`, `pagina`, `hash_conteudo`, `motor_extracao`. Criar parser para `watchlist.yaml`.
*   **Verify**: Validar tipos Pydantic com mock e verificar se watchlist carrega corretamente.

### Task 2: Preparação RAG (Cleaner & Chunker)
*   **Agent**: `backend-specialist`
*   **Skill**: `python-patterns`
*   **Action**: Criar rotinas em `cleaner.py` (remoção de cabeçalho) e `chunker.py` (divisão em blocos de 500-800 tokens com 10% overlap).
*   **Verify**: Testar limpeza e divisão com bloco grande de texto.

### Task 3: Intelligence Engine (Camadas 1 e 2 - Regex/Spacy)
*   **Agent**: `backend-specialist`
*   **Skill**: `python-patterns`
*   **Action**: Criar classe `IntelligenceEngine`. C1: Regex match das keywords. C2: Spacy NER (`pt_core_news_sm`) para extrair pessoas/valores.
*   **Verify**: Testar se NER extrai corretamente a entidade de um texto exemplo.

### Task 4: Camada 3 - Fallback LLM Ollama
*   **Agent**: `backend-specialist`
*   **Skill**: `python-patterns`
*   **Action**: Integrar httpx com `localhost:11434` no engine para processamento complexo retornando JSON Pydantic.
*   **Verify**: Mockar endpoint e confirmar tipagem Pydantic de saída.

### Task 5: Persistência Dual e Deduplicação
*   **Agent**: `database-architect`
*   **Skill**: `database-design`
*   **Action**: Implementar `jsonl_writer.py`. Implementar `pg_repository.py` com check `id_ato` / `hash_conteudo` antes do insert.
*   **Verify**: Rodar mock duplo de inserção e confirmar log de deduplicação sem quebrar rotina.

## ✅ Phase X: Verification
- [ ] P0: Type Check (`mypy`)
- [ ] P0: Testes Unitários (`pytest`)
- [ ] P1: Integração HTTPX Ollama assíncrona
- [ ] P2: Teste inserção Banco
