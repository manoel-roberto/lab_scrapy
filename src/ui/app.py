import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, timedelta

# Configurações da Página
st.set_page_config(
    page_title="DOE-BA Operations Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Personalizado (Aesthetics)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stCard {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #007bff;
    }
    .similarity-badge {
        background-color: #e7f3ff;
        color: #007bff;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .status-badge {
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .status-online { background-color: #d4edda; color: #155724; }
    .status-offline { background-color: #f8d7da; color: #721c24; }
    </style>
    """, unsafe_allow_html=True)

import os
# URL da API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# --- Funções de API ---

def fetch_api(endpoint, method="GET", params=None, json_data=None):
    try:
        with httpx.Client(timeout=10.0) as client:
            if method == "GET":
                response = client.get(f"{API_BASE_URL}{endpoint}", params=params)
            elif method == "PUT":
                response = client.put(f"{API_BASE_URL}{endpoint}", json=json_data)
            elif method == "POST":
                response = client.post(f"{API_BASE_URL}{endpoint}", params=params, json=json_data)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return None

# --- Sidebar (Controles e Status) ---

with st.sidebar:
    st.title("🛡️ Console DOE-BA")
    
    @st.fragment(run_every="10s")
    def render_sidebar_status():
        # Status de Saúde
        st.subheader("Saúde do Sistema")
        status_data = fetch_api("/status")
        settings_data = fetch_api("/settings")
        
        col_pg, col_ol = st.columns(2)
        with col_pg:
            pg_status = "Online" if status_data else "Offline"
            class_pg = "status-online" if pg_status == "Online" else "status-offline"
            st.markdown(f"Postgres: <span class='status-badge {class_pg}'>{pg_status}</span>", unsafe_allow_html=True)
        
        with col_ol:
            ol_status = "Online" if status_data else "Offline"
            class_ol = "status-online" if ol_status == "Online" else "status-offline"
            st.markdown(f"Ollama: <span class='status-badge {class_ol}'>{ol_status}</span>", unsafe_allow_html=True)

        st.divider()

        # Configurações Dinâmicas (Mover para fora se o toggle causar re-run do fragmento, 
        # mas como é fragmento, o estado deve ser mantido localmente)
        if settings_data:
            st.subheader("⚙️ Configurações")
            mon_ativo = st.toggle("Monitoramento Ativo", value=settings_data.get("monitoramento_ativo", True))
            polling = st.slider("Intervalo de Polling (min)", 1, 120, value=settings_data.get("polling_interval_minutes", 60))
            
            if st.button("Salvar Configurações"):
                res = fetch_api("/settings", method="PUT", json_data={
                    "polling_interval_minutes": polling,
                    "monitoramento_ativo": mon_ativo
                })
                if res:
                    st.success("Configurações atualizadas!")
                    st.rerun()

        st.divider()
        
        if status_data:
            stats = status_data.get("estatisticas", {})
            st.subheader("📊 Estatísticas Gerais")
            st.metric("Total de Atos", stats.get("total_atos_oficiais", 0))
            st.metric("Chunks Vetorizados", stats.get("total_chunks_com_embedding", 0))
            
            progress = 0
            if stats.get("total_chunks_gerados", 0) > 0:
                progress = stats.get("total_chunks_com_embedding", 0) / stats.get("total_chunks_gerados", 0)
            st.progress(progress, text=f"Vetorização: {int(progress*100)}%")

    render_sidebar_status()

# --- Main Content ---

tab_search, tab_inventory, tab_alerts = st.tabs(["🔍 Busca Semântica", "📦 Gerenciamento de Dados", "🚨 Alertas Recentes"])

# 1. ABA BUSCA
with tab_search:
    st.header("Busca Semântica Inteligente")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("O que você está procurando?", placeholder="Ex: Nomeação de diretores na SESAB")
    with col2:
        limit = st.selectbox("Limite", [5, 10, 20, 50], index=1)
        
    if query:
        search_res = fetch_api("/search", params={"query": query, "limit": limit})
        if search_res and search_res.get("results"):
            results = search_res["results"]
            st.write(f"Encontrados {len(results)} resultados relevantes:")
            
            for res in results:
                identificador = res.get("ato_identificador")
                link_html = f"https://diariooficial.egba.ba.gov.br/ver-html/{identificador}/"
                similarity = res.get('similaridade') or 0
                
                with st.container():
                    st.markdown(f"""
                        <div class="stCard">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: bold; color: #2c3e50;">{res.get('ato_secretaria', 'Desconhecida')} | {res.get('ato_orgao', 'Desconhecido')}</span>
                                <span class="similarity-badge">{int(similarity * 100)}% Relevância</span>
                            </div>
                            <h4 style="margin: 10px 0;">{res.get('ato_titulo')}</h4>
                            <p style="font-size: 0.95em; color: #34495e;">{res.get('texto_chunk', '')[:500]}...</p>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                                <span style="color: #6c757d; font-size: 0.85em;">📅 Publicado em: {res.get('data_publicacao')} | ID: {identificador}</span>
                                <a href="{link_html}" target="_blank" style="text-decoration: none;">
                                    <button style="background-color: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
                                        Ver Ato Original 🔗
                                    </button>
                                </a>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nenhum resultado encontrado.")

# 2. ABA GERENCIAMENTO DE DADOS (INVENTÁRIO)
with tab_inventory:
    st.header("Gerenciamento de Dados e Backfill")
    
    col_inv, col_back = st.columns([2, 1])
    
    with col_inv:
        @st.fragment(run_every="10s")
        def render_inventory():
            st.subheader("📦 Inventário de Edições")
            st.caption("Atualização automática a cada 10 segundos.")
            
            status_data = fetch_api("/status")
            if status_data and status_data.get("inventario"):
                df_inv = pd.DataFrame(status_data["inventario"])
                df_inv['data_publicacao'] = pd.to_datetime(df_inv['data_publicacao']).dt.date
                st.dataframe(
                    df_inv,
                    column_config={
                        "data_publicacao": "Data da Edição",
                        "total_atos": "Qtd de Atos",
                        "total_chunks": "Qtd de Chunks",
                        "ultima_ingestao": st.column_config.DatetimeColumn("Ingestão", format="DD/MM/YYYY HH:mm")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum dado de inventário disponível.")
        
        render_inventory()

    with col_back:
        st.subheader("🕒 Ingestão Histórica")
        st.write("Selecione um período para capturar edições passadas.")
        
        start_date = st.date_input("Data Inicial", value=datetime.now() - timedelta(days=7))
        end_date = st.date_input("Data Final", value=datetime.now())
        
        if st.button("🚀 Iniciar Ingestão Histórica"):
            if start_date > end_date:
                st.error("Data inicial não pode ser maior que a final.")
            else:
                params = {
                    "start_date": start_date.strftime("%d/%m/%Y"),
                    "end_date": end_date.strftime("%d/%m/%Y")
                }
                res = fetch_api("/ingest/backfill", method="POST", params=params)
                if res:
                    st.success("Backfill iniciado em segundo plano! Acompanhe os logs do Worker.")
                else:
                    st.error("Erro ao disparar Backfill.")

# 3. ABA ALERTAS
with tab_alerts:
    st.header("🚨 Alertas Recentes")
    alerts_data = fetch_api("/watchlist/alerts")
    
    if not alerts_data or not alerts_data.get("alerts"):
        st.info("Nenhum alerta detectado recentemente.")
    else:
        flat_alerts = []
        for alert_group in alerts_data["alerts"]:
            termo = alert_group.get("termo")
            for match in alert_group.get("matches", []):
                match["termo_match"] = termo
                flat_alerts.append(match)
        
        if flat_alerts:
            df = pd.DataFrame(flat_alerts)
            st.dataframe(
                df[['termo_match', 'data_publicacao', 'secretaria', 'titulo', 'identificador']],
                use_container_width=True,
                hide_index=True
            )
            
            st.subheader("Detalhes")
            for alert in flat_alerts:
                identificador = alert.get("identificador")
                link_html = f"https://diariooficial.egba.ba.gov.br/ver-html/{identificador}/"
                with st.expander(f"🚨 [{alert.get('termo_match')}] {alert.get('titulo')}"):
                    st.write(f"**Secretaria:** {alert.get('secretaria')}")
                    st.write(f"**Data:** {alert.get('data_publicacao')}")
                    st.markdown(f"[🔗 Abrir Ato no Diário Oficial]({link_html})")
