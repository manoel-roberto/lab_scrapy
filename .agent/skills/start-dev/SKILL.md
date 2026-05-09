---
name: start-dev
description: Verifica a saúde do ambiente (DB, Ollama) e inicia os serviços do projeto.
---

# Skill: /start-dev

Esta skill automatiza a verificação de pré-requisitos e inicia o ecossistema de desenvolvimento do DOE-BA.

## 📋 Protocolo de Execução

Ao receber o comando `/start-dev`, você deve seguir estes passos:

### 1. Verificação de Infraestrutura
- **PostgreSQL:** Tentar uma conexão simples via `pg_isready` ou script python.
- **Ollama:** Verificar se o serviço está respondendo em `localhost:11434` e se os modelos `qwen2.5:1.5b` e `nomic-embed-text` estão presentes.

### 2. Inicialização de Serviços
Se a infraestrutura estiver OK:
- Iniciar a **API FastAPI** em background (`uvicorn src.api.main:app`).
- Iniciar o **Worker** em background (`python3 -m src.worker`).
- Iniciar o **Dashboard Streamlit** (`streamlit run src/ui/app.py`).

## 🛠️ Scripts de Apoio

Use este comando para verificar tudo:
```bash
python3 -c "
import socket
import requests

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

db_ok = check_port(5432)
ollama_ok = check_port(11434)

if ollama_ok:
    try:
        models = requests.get('http://localhost:11434/api/tags').json()
        names = [m['name'] for m in models.get('models', [])]
        qwen_ok = 'qwen2.5:1.5b' in names
        embed_ok = 'nomic-embed-text:latest' in names
    except:
        qwen_ok = embed_ok = False
else:
    qwen_ok = embed_ok = False

print(f'DB_OK={db_ok}')
print(f'OLLAMA_OK={ollama_ok}')
print(f'QWEN_OK={qwen_ok}')
print(f'EMBED_OK={embed_ok}')
"
```

## 🚨 Tratamento de Erros
- Se o **DB** falhar: Instruir o usuário a rodar `docker-compose up -d`.
- Se o **Ollama** falhar: Instruir a iniciar o serviço.
- Se os **Modelos** faltarem: Sugerir `ollama pull`.
