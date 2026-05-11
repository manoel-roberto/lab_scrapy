# Guia de Instalação: DOE-BA Intelligence Engine

Este guia detalha como configurar o ambiente de desenvolvimento usando Docker (Recomendado) ou de forma manual (Híbrida).

## 🚀 1. Fluxo Rápido com Docker (Recomendado)

Este método é ideal para contribuidores e para garantir que todos rodem exatamente a mesma versão do sistema.

### Pré-requisitos
- Docker e Docker Compose instalados.

### Passo a Passo
1. **Clone do Repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd lab_scrapy
   ```
2. **Configuração de Ambiente:**
   ```bash
   cp .env.example .env
   ```
3. **Subir o Ecossistema:**
   ```bash
   docker compose up -d --build
   ```
4. **Baixar Modelos de IA:**
   Os modelos são persistidos em volumes, então você só precisa rodar isso uma vez:
   ```bash
   docker exec -it doe_ollama ollama pull qwen2.5:1.5b
   docker exec -it doe_ollama ollama pull nomic-embed-text
   ```

---

## 🛠️ 2. Fluxo Manual (Híbrido - Para Debug Profundo)

Use este fluxo se precisar debugar o código Python diretamente na sua IDE fora do container.

### Pré-requisitos
- Python 3.10+
- [Ollama](https://ollama.ai/) instalado localmente.

### Instalação
1. **Ambiente Virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Infra Mínima (DB):**
   ```bash
   docker compose up -d db
   ```
3. **Execução:**
   - API: `uvicorn src.api.main:app --reload`
   - UI: `streamlit run src/ui/app.py`
   - Worker: `python3 -m src.worker`

---

## 🏗️ 3. Deploy em Produção

Para colocar o sistema em um servidor de produção:

1. **Segurança:** Edite o `.env` e altere a `POSTGRES_PASSWORD`.
2. **Persistence:** Certifique-se de que os volumes `./data` e `pgdata` estão em discos com backup.
3. **Recursos de GPU:** Se o servidor tiver GPU NVIDIA, instale o `nvidia-container-toolkit` e descomente a seção `deploy` no `docker-compose.yml` para acelerar a IA em 10x.
4. **Execução:**
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

---

## 🤖 4. Assistente Antigravity

Se estiver usando o Antigravity para contribuir:
1. `npx @vudovn/ag-kit init`
2. `echo ".agent/" >> .git/info/exclude`

---
*Dúvidas? Consulte o canal de engenharia ou abra uma Issue.*
