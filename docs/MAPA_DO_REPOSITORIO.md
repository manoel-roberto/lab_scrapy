# 🗺️ Mapa do Repositório: DOE-BA Intelligence Engine
> "Para navegar com precisão, é preciso conhecer cada compartimento da nossa nave."

Olá, aluno! Este documento serve como o seu **GPS técnico**. Abaixo, explico a função de cada pasta e arquivo principal que você encontrará neste projeto.

---

## 📁 Estrutura de Pastas (Visão Geral)

### 1. `src/` (O Coração)
Aqui reside todo o código-fonte da aplicação. É onde a lógica de negócio acontece.
- **`api/`**: Contém o servidor **FastAPI**. Define os endpoints que a UI e outros sistemas usam para ler dados.
- **`core/`**: Onde definimos os **Modelos Pydantic** (`models.py`), as configurações globais (`config.py`) e o cliente de rede assíncrono (`client.py`).
- **`intelligence/`**: O cérebro da plataforma. Contém a lógica de limpeza de texto, particionamento (**Chunking**), geração de **Embeddings** e o motor de decisão do funil de IA.
- **`parsers/`**: Os especialistas em extração. Transformam HTML bruto e arquivos PDF em texto processável.
- **`persistence/`**: A camada de banco de dados. Gerencia a escrita em JSONL (auditoria) e a interação com o **PostgreSQL/pgvector**.
- **`ui/`**: A interface visual construída em **Streamlit**.
- **`utils/`**: Ferramentas de apoio, como helpers para datas e jitter de rede.

### 2. `docs/` (O Conhecimento)
Nossa biblioteca técnica. Aqui estão os manuais didáticos e as especificações de arquitetura profunda.

### 3. `data/` (A Memória)
Pasta persistente (mapeada via volumes Docker).
- **`backups/`**: Cópias de segurança do banco.
- **`logs/`**: Rastreabilidade de erros e eventos.
- **`temp/`**: Buffer temporário para processamento de arquivos.

### 4. `tests/` (A Segurança)
Contém os testes automatizados para garantir que nenhuma alteração quebre o sistema existente.

---

## 📄 Arquivos Principais na Raiz

- **`ARCHITECTURE.md`**: O manifesto técnico com os diagramas de fluxo de alto nível.
- **`docker-compose.yml`**: O script que orquestra os 5 serviços (db, ollama, api, worker, ui).
- **`Dockerfile`**: As instruções para construir a imagem do nosso sistema.
- **`pyproject.toml` / `requirements.txt`**: A lista de "ingredientes" (bibliotecas Python) necessários.
- **`watchlist.yaml`**: Onde você define as palavras e pessoas que o sistema deve vigiar.
- **`worker.py` (em src/)**: O motor que roda em loop infinito processando os novos diários.
- **`cli.py` (em src/)**: Sua ferramenta de linha de comando para testes rápidos.

---

## 🛠️ Como usar este Mapa?

Sempre que precisar fazer uma manutenção, pergunte-se:
1. **É uma mudança visual?** Vá para `src/ui/`.
2. **É uma nova regra de inteligência?** Vá para `src/intelligence/`.
3. **É um novo campo no banco de dados?** Vá para `src/core/models.py` e `src/persistence/`.
4. **O scraper parou de funcionar?** Verifique `src/core/client.py` e `src/parsers/`.

---
*Professor Sênior & Especialista em IA*
