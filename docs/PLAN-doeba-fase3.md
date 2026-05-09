# DOE-BA Fase 003: Embeddings, pgvector e API de Consulta

Visão geral: Iniciar a Fase 003 do scraper DOE-BA, focada em gerar embeddings de texto para os chunks de Diário Oficial extraídos e armazená-los usando o pgvector no PostgreSQL. O projeto também incluirá uma API FastAPI para consultas semânticas e integração com Watchlist.

## 🛑 Socratic Gate / Questões Abertas (Para revisão do usuário)

> [!IMPORTANT]
> **Questão 1: Relação Ato -> Chunks no Banco de Dados**
> Como cada Ato Oficial pode gerar dezenas de *chunks*, a inserção de vetores na "tabela de atos" implicaria em um de dois cenários:
> A) Adicionar uma nova tabela `atos_chunks` (Recomendado: ID do Ato, Texto do Chunk, Vetor).
> B) Modificar a tabela `atos_oficiais` para aceitar um array de vetores (Não recomendado para buscas vetorizadas HNSW/IVFFlat).
> **Podemos prosseguir com a criação de uma tabela `atos_chunks` relacional?**

> [!IMPORTANT]
> **Questão 2: Mecânica de Watchlist**
> O endpoint `/watchlist/alerts` fará o match através de uma busca léxica estrita (match exato dos termos do `watchlist.yaml`) ou utilizaremos a busca vetorial para encontrar menções semanticamente similares aos nomes/termos da watchlist?

> [!IMPORTANT]
> **Questão 3: worker.py**
> O `worker.py` (simulando um Cron) será uma task assíncrona do próprio FastAPI (ex: via `apscheduler` / `FastAPI background tasks`) ou um script Python daemonizado e independente no diretório `/src`? (Recomendado: Script independente para não bloquear a API).

## 1. Project Type
**BACKEND** (API FastAPI + PostgreSQL + Scraper Core Engine)

## 2. Success Criteria
- [ ] O banco de dados PostgreSQL deve possuir a extensão `pgvector` habilitada e a tabela adequada para embeddings (`atos_chunks`).
- [ ] O serviço de extração deve gerar embeddings incrementalmente chamando o `nomic-embed-text` no Ollama.
- [ ] A FastAPI deve expor os endpoints `/search`, `/watchlist/alerts` e `/status` com métricas.
- [ ] O `worker.py` deve processar novas edições em loop cíclico sem intervenção manual.
- [ ] Tempos de geração de embeddings locais devem ser monitorados e "logados".

## 3. Tech Stack
- **FastAPI:** Para a criação da API assíncrona de consulta.
- **pgvector:** Extensão oficial do PostgreSQL para buscas por Similaridade de Cosseno (`<=>`).
- **Ollama (`nomic-embed-text`):** Geração de vetores local (768 dimensões).
- **aiohttp / httpx:** Cliente HTTP assíncrono para conversar com o Ollama e expor endpoints de forma performática.
- **PyYAML:** Para carregar a `watchlist.yaml`.

## 4. File Structure

```text
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py            # Servidor FastAPI e rotas
│   │   ├── routes.py          # Implementação de /search, /status, /watchlist
│   │   └── dependencies.py    # Injeção de repo e clientes
│   ├── persistence/
│   │   └── pg_repository.py   # [MODIFICADO] SQL do pgvector e funções de busca
│   ├── intelligence/
│   │   ├── chunker.py         # [EXISTENTE] Lógica de chunk
│   │   └── embeddings.py      # [NOVO] Integração Ollama (nomic-embed-text)
│   ├── worker.py              # [NOVO] Daemon de monitoramento/Cron cíclico
```

## 5. Task Breakdown

| Task ID | Componente | Descrição | Agent | Skill |
|---------|------------|-----------|-------|-------|
| TASK-01 | **Database** | Habilitar `CREATE EXTENSION IF NOT EXISTS vector;` no PostgreSQL e criar a tabela `atos_chunks` para armazenar o embedding (vetor `vector(768)`) referenciando `atos_oficiais.id`. | `database-architect` | `database-design` |
| TASK-02 | **Intelligence** | Criar o módulo `embeddings.py` que fará chamadas HTTP assíncronas ao servidor Ollama local (`/api/embeddings` usando modelo `nomic-embed-text`) para retornar a representação vetorial do texto. Incluir logging de latência (métrica de tempo de resposta). | `backend-specialist` | `api-patterns` |
| TASK-03 | **Persistence** | Atualizar `pg_repository.py`. Adicionar funções `get_chunks_without_vectors()`, `save_chunk_vector()` para lógica incremental. Adicionar função `search_similar_chunks(query_vector)` usando o operador `<=>` (Similaridade de Cosseno). | `database-architect` | `database-design` |
| TASK-04 | **API** | Implementar `src/api/main.py`. Criar GET `/search` (gera embedding da query no Ollama e busca no DB). Criar GET `/status` (contagens do banco). Criar GET `/watchlist/alerts` (carrega `watchlist.yaml` e encontra matches vetoriais ou textuais). | `backend-specialist` | `api-patterns` |
| TASK-05 | **Orchestration**| Criar script `worker.py` na raiz de `/src` que instancia o `Core Engine` em um loop infinito com `asyncio.sleep`, buscando a última edição e rodando o pipeline (Scraper -> Limpeza -> Chunker -> Ollama -> pgvector). | `backend-specialist` | `python-patterns` |

### Detalhamento das Entradas e Saídas (INPUT -> OUTPUT -> VERIFY)

**TASK-01 (Database):**
- **INPUT:** `pg_repository.py` setup_schema.
- **OUTPUT:** Tabelas `atos_oficiais` + `atos_chunks` e extensão pgvector configuradas.
- **VERIFY:** `psql -c "\d atos_chunks"` exibe a coluna do tipo `vector`.

**TASK-02 (Embeddings):**
- **INPUT:** Chunks de texto provindos do `chunker.py`.
- **OUTPUT:** Uma lista de floats representando o vetor do texto gerado pelo Ollama.
- **VERIFY:** Rodar `python -c "import asyncio; from src.intelligence.embeddings import get_embedding; print(asyncio.run(get_embedding('teste')))"` retorna lista de floats de tamanho correspondente.

**TASK-03 (Persistence):**
- **INPUT:** Vetores e query embeddings.
- **OUTPUT:** Retorno do pgvector com Similaridade de Cosseno ordenada de forma ascendente e limit.
- **VERIFY:** Um mock insert + mock query deve retornar os vetores mais próximos primeiro.

**TASK-04 (API):**
- **INPUT:** Requisições HTTP para `/search`, `/watchlist/alerts` e `/status`.
- **OUTPUT:** JSON estruturado contendo matches ou estatísticas.
- **VERIFY:** `curl http://localhost:8000/status` retorna JSON com números.

**TASK-05 (Worker):**
- **INPUT:** Ciclo de relógio / intervalo.
- **OUTPUT:** Atos e embeddings salvos no banco.
- **VERIFY:** Executar `python src/worker.py` e ver no log a varredura das edições, chunking e salvamento no BD.

## 6. Phase X: Verification Plan

### Testes Manuais & Automated:
- [ ] **Lint Check**: Rodar `flake8` ou `pylint` nos novos arquivos.
- [ ] **Security**: Rodar checklist de segurança (`python .agent/scripts/verify_all.py` se suportado ou scripts manuais).
- [ ] **Testes Ollama**: Garantir que o container local do Ollama está up e possui o modelo nomic-embed-text.
- [ ] **Teste do pgvector**: Validar consulta de similaridade.
