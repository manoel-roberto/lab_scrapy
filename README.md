# 🛡️ DOE-BA Intelligence Engine

O **DOE-BA Intelligence Engine** é uma plataforma avançada de inteligência e monitoramento do Diário Oficial do Estado da Bahia. O sistema automatiza a extração, limpeza, análise e busca semântica de atos oficiais, permitindo vigilância proativa sobre termos sensíveis e nomes monitorados.

## 🚀 Filosofia Local-First

Diferente de soluções baseadas em nuvem, este projeto adota uma arquitetura **100% Local**:
- **Privacidade:** O processamento ocorre internamente, garantindo conformidade total com a LGPD.
- **Custo Zero:** Utiliza LLMs locais (via Ollama) para extração e embeddings, eliminando custos com APIs externas (OpenAI/Anthropic).
- **Independência:** O sistema opera sem dependências de serviços externos de IA.

## 🏗️ Arquitetura do Sistema

O pipeline segue o fluxo **RAG (Retrieval-Augmented Generation) Local**:
1. **Ingestão:** Captura híbrida (HTML/PDF) com bypass de modais e resiliência contra servidores legados.
2. **Inteligência:** Funil de 3 camadas (Regex -> Spacy NER -> LLM Qwen2.5) para classificação de atos.
3. **Vetorização:** Geração de embeddings usando `nomic-embed-text` e armazenamento em PostgreSQL com `pgvector`.
4. **Interface:** Operations Console em Streamlit para busca semântica e gerenciamento de inventário.

## 🛠️ Stack Tecnológica
- **Backend:** Python 3.10+, FastAPI, Asyncpg.
- **Scraper:** Playwright (Bypass de JS), HTTPX.
- **IA/LLM:** Ollama (Qwen2.5 & Nomic-Embed).
- **NLP:** Spacy (pt_core_news_sm).
- **Database:** PostgreSQL + pgvector.
- **UI:** Streamlit.

## 📖 Documentação Adicional
- [**Guia de Instalação (Onboarding)**](INSTALL.md)
- [**Manifesto Técnico e Arquitetura**](ARCHITECTURE.md)
- [**Configuração de Monitoramento**](watchlist.example.yaml)

---
*Desenvolvido pelo Esquadrão de Elite para o laboratório de inteligência governamental.*
