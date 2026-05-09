# Guia de Instalação: DOE-BA Intelligence Engine

Seja bem-vindo ao esquadrão! Siga este guia para configurar seu ambiente de desenvolvimento do zero.

## 1. Pré-requisitos
- Python 3.10 ou superior
- Docker e Docker Compose
- [Ollama](https://ollama.ai/) instalado no sistema

## 2. Configuração Inicial

### Clone do Repositório
```bash
git clone <url-do-repositorio>
cd lab_scrapy
```

### Ambiente Virtual e Dependências
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuração do Antigravity Kit (AI-Pair)
Se você estiver usando o assistente Antigravity, inicialize o kit:
```bash
npx @vudovn/ag-kit init
```
**CRÍTICO:** Não adicione a pasta `.agent/` ao seu `.gitignore`. Em vez disso, oculte-a apenas localmente para o seu Git:
```bash
echo ".agent/" >> .git/info/exclude
```
*Isso permite que as Skills do projeto funcionem sem poluir o repositório público.*

## 3. Infraestrutura (Docker & IA)

### Subindo o Banco de Dados
O sistema utiliza PostgreSQL com a extensão `pgvector`.
```bash
docker-compose up -d
```

### Preparando os Modelos de IA
Certifique-se de que o Ollama está rodando e baixe os modelos necessários:
```bash
# Para extração e análise
ollama pull qwen2.5:1.5b

# Para geração de vetores de busca
ollama pull nomic-embed-text
```

## 4. Executando o Projeto

### Iniciar a API
```bash
uvicorn src.api.main:app --reload
```

### Iniciar o Worker (Ingestão e Vetorização)
```bash
# Em um novo terminal com venv ativo
python3 -m src.worker
```

### Iniciar o Dashboard Streamlit
```bash
# Em um novo terminal com venv ativo
streamlit run src/ui/app.py
```

## 5. Comando Mestre (/start-dev)
Se você configurou o assistente Antigravity corretamente, basta digitar `/start-dev` no chat para que ele verifique a saúde de todos os componentes e inicie os serviços para você.

---
*Dúvida? Consulte o manifesto em ARCHITECTURE.md ou abra uma issue.*
