# 🗺️ Mapa do Repositório: DOE-BA Intelligence Engine
> "O conhecimento total da estrutura é o que separa um codificador de um Arquiteto de Sistemas."

Olá, aluno! Este é o seu **Atlas Técnico**. Abaixo, detalho não apenas onde os arquivos estão, mas **o que eles fazem internamente** e como se conectam.

---

## 📂 Pasta: `src/` (O Ecossistema de Código)

### 🧩 `src/core/` (Fundações e Contratos)
- **`client.py`**: 
    - **Classe:** `DOEBahiaClient`.
    - **Funções Chave:** `get_editions_by_date` (descoberta), `fetch_content` (download com retry e jitter).
    - **Detalhe:** Gerencia o pool de conexões HTTP e a automação do navegador Playwright.
- **`models.py`**: 
    - **Esquemas:** `AtoOficial` (o objeto principal), `MetadadosEdicao`.
    - **Papel:** Garante que o dado extraído siga um contrato rígido antes de ser vetorizado.
- **`config.py`**: 
    - **Papel:** Centraliza o acesso ao `.env`. Define constantes como `POSTGRES_DSN` e `OLLAMA_URL`.

### 🧠 `src/intelligence/` (O Cérebro RAG)
- **`engine.py`**: 
    - **Classe:** `IntelligenceEngine`.
    - **Lógica:** Implementa as 3 camadas de triagem. Note como a `camada_1_regex` economiza processamento ao descartar atos sem interesse.
- **`chunker.py`**: 
    - **Função:** `chunk_text`.
    - **Matemática:** Usa o `chunk_size=600` e `overlap_size=60` para manter a coesão semântica.
- **`embeddings.py`**: 
    - **Classe:** `OllamaEmbeddings`.
    - **Papel:** Converte texto em vetores. É o ponto de integração com o modelo `nomic-embed-text`.
- **`cleaner.py`**: 
    - **Papel:** Regex especializados para limpar "ruído governamental" (brasões, rodapés legais repetitivos).

### 💾 `src/persistence/` (Memória de Longo Prazo)
- **`pg_repository.py`**: 
    - **Classe:** `PostgresRepository`.
    - **Destaque:** Método `search_similar_chunks` que executa a busca semântica via SQL.
    - **SQL:** Gerencia as tabelas `atos_oficiais` e `atos_chunks`.
- **`jsonl_writer.py`**: 
    - **Papel:** Persistência secundária para auditoria fria (cold storage).

### 🌐 `src/api/` (Acesso Externo)
- **`main.py`**: Inicializa o FastAPI e configura o CORS e Middlewares.
- **`routes.py`**: 
    - **Endpoints:** `/search` (busca semântica), `/stats` (dashboard), `/settings` (configurações do worker).
- **`dependencies.py`**: Injeta a conexão do banco de dados em cada requisição de forma segura.

### 📊 `src/ui/` (A Janela do Usuário)
- **`app.py`**: Dashboard **Streamlit**. Consome a API do backend para exibir os resultados de forma visual e amigável.

### ⚙️ Orquestradores (Na Raiz do `src/`)
- **`worker.py`**: O "batimento cardíaco" do sistema. Orquestra o loop: **Busca -> Download -> Limpeza -> Inteligência -> Vetorização**.
- **`cli.py`**: Ferramenta de linha de comando. Útil para reprocessar datas específicas ou testar a conexão com o banco.

---

## 📁 Pasta: `docs/` (Centro de Inteligência)
- **`TECHNICAL_MASTER.md`**: Onde as decisões arquiteturais pesadas são explicadas.
- **`01-fundamentos.md` a `04-infra.md`**: Curso didático completo para novos desenvolvedores.
- **`MAPA_DO_REPOSITORIO.md`**: Este guia que serve como o GPS do projeto.

---

## 📄 Arquivos de Configuração (O Enquadramento)
- **`docker-compose.yml`**: Define o ambiente de rede. O serviço `db` usa a imagem `pgvector/pgvector`.
- **`watchlist.yaml`**: O arquivo mais importante para o usuário final. Define **quem** e **o que** estamos vigiando.
- **`.env`**: (Não versionado por segurança) Contém as chaves do reino. Use o `.env.example` como guia.

---

## 🔗 Como os Arquivos Conversam? (O Fluxo)

1. `worker.py` usa `client.py` para descobrir novos atos.
2. `client.py` entrega HTML/PDF para `parsers/`.
3. `parsers/` entrega texto bruto para `engine.py`.
4. `engine.py` limpa o texto via `cleaner.py` e valida via `models.py`.
5. Se for relevante, `chunker.py` quebra o texto.
6. `embeddings.py` vetoriza os pedaços.
7. `pg_repository.py` salva tudo no banco.
8. `ui/app.py` pede dados para `api/main.py`, que consulta o `pg_repository.py`.

---
*Professor Sênior & Especialista em IA*
