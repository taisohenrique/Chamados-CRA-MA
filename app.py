import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
import time

# Configuração da página
st.set_page_config(page_title="TI CRA-MA | Chamados", layout="wide", page_icon="🛠️")

# Conexão
conn = st.connection("supabase", type=SupabaseConnection)

# --- FUNÇÃO DO ALERTA SONORO (3 BIPS DE 1s) ---
def alerta_sonoro_3_bips():
    # Som de bip curto
    sound_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    
    html_string = f"""
        <audio id="beepAudio">
          <source src="{sound_url}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById("beepAudio");
            var count = 0;
            function playBeep() {{
                if (count < 3) {{
                    audio.play().catch(function(error) {{
                        console.log("Aguardando interação do usuário para tocar som.");
                    }});
                    count++;
                    // Espera 1.5 segundos para o próximo bip (1s de som + 0.5s de silêncio)
                    setTimeout(playBeep, 1500);
                }}
            }}
            playBeep();
        </script>
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
        
        # Filtra apenas os que estão abertos
        chamados_abertos = df[df['status'] == "Aberto"]
        
        if not chamados_abertos.empty:
            st.error(f"🚨 ATENÇÃO: {len(chamados_abertos)} CHAMADO(S) AGUARDANDO!")
            # DISPARA OS 3 BIPS
            alerta_sonoro_3_bips()
        else:
            st.success("✅ Nenhum chamado pendente no momento.")

        # Exibir Tabela (Removemos a coluna interna 'id' da visualização se quiser, mas deixamos para consulta)
        st.dataframe(df, use_container_width=True)
        
        # Ações de Gerenciamento
        st.divider()
        st.subheader("Atualizar Chamado")
        col_id, col_status = st.columns(2)
        with col_id:
            id_update = st.number_input("Digite o ID do Chamado", step=1, min_value=0)
        with col_status:
            novo_status = st.selectbox("Mudar para:", ["Em Atendimento", "Concluído", "Cancelado"])
        
        if st.button("Salvar Alteração"):
            conn.table("chamados").update({"status": novo_status}).eq("id", id_update).execute()
            st.toast(f"Chamado {id_update} atualizado!")
            time.sleep(1)
            st.rerun()
    else:
        st.info("Nenhum chamado no momento.")

# --- AUTO REFRESH (30 segundos) ---
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=30 * 1000, key="datarefresh")
