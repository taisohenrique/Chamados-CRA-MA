import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
import time

# Configuração da página
st.set_page_config(page_title="TI CRA-MA | Chamados", layout="wide", page_icon="🛠️")

# Conexão
conn = st.connection("supabase", type=SupabaseConnection)

# --- FUNÇÃO DO ALERTA SONORO ---
def alerta_sonoro():
    # Link de um som de notificação (você pode trocar por qualquer link .mp3)
    sound_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    html_string = f"""
        <audio autoplay>
          <source src="{sound_url}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(html_string, height=0)

# --- INTERFACE ---
st.title("🛠️ Central de Chamados - TI")

tab1, tab2 = st.tabs(["🆕 Abrir Chamado", "🖥️ Painel de Controle (TI)"])

# TAB 1: PARA OS USUÁRIOS
with tab1:
    st.header("Solicitar Suporte Técnico")
    with st.form("form_chamado", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            setor = st.selectbox("Seu Setor", ["Financeiro", "Fiscalização", "Cofic", "Diretoria", "Recepção"])
            nome = st.text_input("Seu Nome")
        with col2:
            assunto = st.selectbox("Tipo de Problema", ["Impressora", "Internet/Rede", "Computador não liga", "Sistema", "Outros"])
        
        descricao = st.text_area("Descreva o problema com detalhes")
        enviar = st.form_submit_button("🚨 ENVIAR CHAMADO")

        if enviar and nome and descricao:
            conn.table("chamados").insert([
                {"setor": setor, "solicitante": nome, "descricao": f"[{assunto}] {descricao}", "status": "Aberto"}
            ]).execute()
            st.success("Chamado enviado com sucesso! Aguarde o técnico.")

# TAB 2: PARA VOCÊ E O RUY
with tab2:
    st.header("Fila de Atendimento")
    
    # Buscar chamados
    res = conn.table("chamados").select("*").order("criado_em", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data)
        
        # Lógica do Alerta: Se houver um chamado "Aberto" criado nos últimos 10 segundos
        chamados_novos = df[df['status'] == "Aberto"]
        
        if not chamados_novos.empty:
            st.warning(f"Existem {len(chamados_novos)} chamados aguardando atendimento!")
            # Toca o som se houver algo aberto (você pode refinar essa lógica)
            alerta_sonoro()

        # Exibir Tabela
        st.dataframe(df, use_container_width=True)
        
        # Ações de Gerenciamento
        st.divider()
        col_id, col_status = st.columns(2)
        with col_id:
            id_update = st.number_input("ID do Chamado para atualizar", step=1, min_value=0)
        with col_status:
            novo_status = st.selectbox("Mudar para:", ["Em Atendimento", "Concluído", "Cancelado"])
        
        if st.button("Atualizar Status"):
            conn.table("chamados").update({"status": novo_status}).eq("id", id_update).execute()
            st.success(f"Chamado {id_update} atualizado!")
            st.rerun()
    else:
        st.info("Nenhum chamado no momento.")

# --- AUTO REFRESH (Para o alerta funcionar sozinho) ---
# Isso faz a página atualizar a cada 30 segundos para checar novos chamados
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=30 * 1000, key="datarefresh")