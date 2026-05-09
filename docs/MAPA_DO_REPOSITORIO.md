# 🗺️ Mapa do Repositório: DOE-BA Intelligence Engine
> "A maestria técnica nasce do conhecimento profundo de cada engrenagem."

Olá, aluno! Este é o seu guia definitivo. Abaixo, detalho a função de **cada arquivo** do projeto, dividido por diretórios.

---

## 📂 Pasta: `src/` (Código Fonte)

### 🧩 `src/core/` (Cérebro Estrutural)
- **`client.py`**: O motor de rede. Contém o `DOEBahiaClient` que lida com requisições assíncronas, bypass de modais com Playwright e controle de fluxo via Semaphore.
- **`models.py`**: Define os contratos de dados usando **Pydantic**. Aqui estão as classes `AtoOficial` e `MetadadosEdicao`.
- **`config.py`**: Gerencia o carregamento de variáveis de ambiente (`.env`) e configurações da Watchlist.

### 🧠 `src/intelligence/` (Camada de IA)
- **`engine.py`**: Orquestra o Funil de Inteligência (Regex -> Spacy -> Ollama). Decide qual motor usar para cada ato.
- **`chunker.py`**: Implementa a lógica de divisão de texto em pedaços de 600 palavras com 10% de overlap.
- **`embeddings.py`**: Interface com a API do Ollama para transformar texto em vetores de 768 dimensões.
- **`cleaner.py`**: Limpeza de ruídos (cabeçalhos, rodapés e caracteres especiais) do texto extraído.

### 🕷️ `src/parsers/` (Extratores)
- **`html_parser.py`**: Especialista em navegar pela estrutura DOM dos diários em formato HTML.
- **`pdf_parser.py`**: Utiliza bibliotecas como `pdfplumber` para extrair texto de atos anexos em formato PDF.

### 💾 `src/persistence/` (Armazenamento)
- **`pg_repository.py`**: Gerencia a conexão com o PostgreSQL, criação de tabelas e as buscas vetoriais via `pgvector`.
- **`jsonl_writer.py`**: Utilitário para salvar atos em arquivos JSONL, servindo como uma trilha de auditoria bruta.

### 🌐 `src/api/` (Porta de Saída)
- **`main.py`**: Ponto de entrada do servidor **FastAPI**.
- **`routes.py`**: Define as rotas de busca semântica, listagem de atos e estatísticas do sistema.
- **`dependencies.py`**: Gerencia a injeção de dependências (como conexões de banco) para as rotas.

### 📊 `src/ui/` (Interface)
- **`app.py`**: O dashboard construído em **Streamlit**. É onde o usuário final realiza as buscas e visualiza os alertas.

### ⚙️ Raiz do `src/`
- **`worker.py`**: O processo de segundo plano que monitora novas edições e processa a inteligência continuamente.
- **`cli.py`**: Interface de linha de comando para tarefas administrativas e testes manuais.
- **`__init__.py`**: Transforma a pasta em um pacote Python.

---

## 📁 Pasta: `docs/` (Documentação)
- **`README.md`**: Índice geral do Livro Mestre.
- **`TECHNICAL_MASTER.md`**: Consolidação técnica profunda da arquitetura.
- **`MAPA_DO_REPOSITORIO.md`**: Este guia que você está lendo.
- **Capítulos 01 a 04**: Lições didáticas sobre Scraping, IA, RAG e Infra.

---

## 📁 Pasta: `data/` (Dados Persistentes)
- **`logs/`**: Arquivos `.log` que registram cada passo (e erro) do sistema.
- **`backups/`**: Snapshots do banco para recuperação de desastres.
- **`temp/`**: Arquivos temporários usados durante o download e parsing de PDFs.

---

## 📄 Arquivos de Raiz (Infraestrutura)
- **`docker-compose.yml`**: Configuração dos serviços Docker (Postgres, Ollama, API, Worker, UI).
- **`Dockerfile`**: Receita para construir o ambiente de execução Python.
- **`requirements.txt`**: Lista de dependências Python.
- **`watchlist.yaml`**: Sua lista personalizada de termos e nomes a serem vigiados.
- **`.env.example`**: Modelo de configuração de credenciais.

---
*Professor Sênior & Especialista em IA*
