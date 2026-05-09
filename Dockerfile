# Imagem base
FROM python:3.10-slim

# Evitar criação de arquivos .pyc e garantir output em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Diretório de trabalho
WORKDIR /app

# Instalação de dependências de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalação de dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalação do modelo Spacy
RUN python -m spacy download pt_core_news_sm

# Copiar o projeto
COPY . .

# Criar diretório de dados e garantir permissões
RUN mkdir -p /app/data && chmod 777 /app/data

# Instalar o pacote em modo editável para garantir que 'src' seja encontrado
RUN pip install -e .

# O comando padrão será sobrescrito pelo docker-compose para cada serviço
CMD ["python", "src/worker.py"]
