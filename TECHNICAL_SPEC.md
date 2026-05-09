# Technical Specification 2.0: DOE-BA Intelligence Engine

## 1. Visão de Arquitetura (Macro)

O **DOE-BA Intelligence Engine** é projetado seguindo o padrão **Local-First**, priorizando a soberania de dados, baixa latência e custo operacional zero (pós-setup). A arquitetura é baseada em um pipeline **ETL (Extract, Transform, Load) + RAG (Retrieval-Augmented Generation)** distribuído via Docker Compose.

### Fluxo Geral de Dados
1.  **Descoberta:** Orquestração via Playwright para bypass de modais informativos e identificação de IDs de edições.
2.  **Extração Híbrida:** Download e extração de texto de fontes HTML (direto da API de fragmentos) e PDF (via `pdfplumber`).
3.  **Limpeza/Chunking:** Normalização de texto e quebra em blocos semânticos com sobreposição.
4.  **Inteligência em 3 Camadas:** Filtragem e estruturação progressiva de dados.
5.  **Persistência Vetorial:** Indexação de embeddings no PostgreSQL via `pgvector`.
6.  **API de Busca:** Endpoint FastAPI para consultas semânticas e alertas de watchlist.

---

## 2. Core Scraper Engine: Resiliência e Performance

O servidor alvo do Diário Oficial utiliza **Apache/2.2.22**, uma versão legada que apresenta limitações de conexões simultâneas e sensibilidade a picos de tráfego (comportamento "bot-like").

### Estratégias de Robustez
-   **`asyncio.Semaphore(8)`:** Limitamos estritamente a concorrência a 8 workers simultâneos. Isso evita a exaustão do pool de conexões do servidor alvo e reduz a probabilidade de bloqueios por IP (WAF/Rate Limit).
-   **Jitter e Backoff:**
    -   **Delay Aleatório (Jitter):** Introduzimos uma pausa de 200-500ms entre requisições para descaracterizar o padrão robótico.
    -   **Exponential Backoff:** Em caso de erro 50x ou Timeouts, o sistema aguarda tempos progressivamente maiores (2s, 4s, 8s...) antes de retestar.
-   **Bypass de Modal:** O uso do Playwright é restrito à fase de descoberta inicial (Summary), onde é necessário simular o clique no botão "CONTINUAR SEM CADASTRO". Uma vez obtidos os identificadores, o sistema consome diretamente os fragmentos HTML/PDF, ganhando performance ao ignorar o carregamento de assets de UI (JS/CSS/Imagens).

---

## 3. O Funil de Inteligência (3 Camadas)

Para otimizar o consumo de hardware local e garantir precisão, o processamento segue um modelo de "cascata de inteligência":

| Camada | Tecnologia | Objetivo | Custo de Recurso |
| :--- | :--- | :--- | :--- |
| **Layer 1 (Regex)** | Python Native | Filtro instantâneo baseado em `watchlist.yaml`. Descarta atos irrelevantes. | Mínimo |
| **Layer 2 (NLP Local)** | Spacy (`pt_core_news_sm`) | Extração de Entidades Nomeadas (NER): Órgãos, Pessoas e Valores Monetários. | Médio |
| **Layer 3 (LLM Fallback)** | Ollama (`qwen2.5:1.5b`) | Estruturação de dados complexos em JSON e análise de sentimento/intenção. | Alto |

---

## 4. Engenharia de Dados e Busca Semântica

### Estratégia de Chunking
O sistema utiliza um particionamento de texto fixo com overlap para manter a coesão semântica:
-   **Tamanho do Bloco:** 600 palavras (alinhado com o contexto do modelo `nomic-embed-text`).
-   **Overlap:** 10% (60 palavras). Isso evita que entidades ou conceitos sejam "cortados" ao meio na fronteira entre dois vetores.

### Persistência Vetorial (pgvector)
Os vetores são gerados pelo modelo `nomic-embed-text` (768 dimensões).
-   **Similaridade de Cosseno:** Implementada via operador `<=>` no SQL. 
    -   `SELECT content FROM chunks ORDER BY embedding <=> query_vector LIMIT 5;`
-   **Por que Cosseno?** É a métrica mais robusta para comparar documentos de comprimentos variados, focando na orientação (direção) do vetor de termos em vez de sua magnitude.

---

## 5. Infraestrutura e Operação

A orquestração via Docker Compose isola as responsabilidades em 5 serviços principais:
1.  **db:** PostgreSQL 16 + pgvector.
2.  **ollama:** Runtime de modelos de IA (aceleração via CPU/GPU).
3.  **api:** Backend FastAPI para consumo de dados.
4.  **worker:** Motor assíncrono de scraping e processamento.
5.  **dashboard:** Interface Streamlit para visualização e alertas.

### IA Onboarding
O setup inicial requer o download manual dos modelos (Sovereignty Check):
```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

---

## 6. Roadmap e Manutenibilidade

-   **Índices HNSW:** Implementação planejada para quando a base superar 100k chunks, garantindo busca de vizinhos mais próximos (ANN) com custo O(log n).
-   **Webhooks:** Ativação de notificações proativas (Slack/Discord) quando um termo da watchlist for detectado com alta confiança semântica.
-   **Observabilidade:** Integração de logs estruturados em JSON para análise via ELK Stack ou Grafana Loki.
