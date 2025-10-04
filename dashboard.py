import pandas as pd
import streamlit as st
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Financeiro",
                   page_icon=":bar_chart:",
                   layout="wide")

# --- FUNÇÃO DE VERIFICAÇÃO DE SENHA ---
def check_password():
    """Retorna True se o usuário digitou a senha correta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False):
        return True
    st.text_input(
        "Digite a senha para acessar o dashboard", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Senha incorreta. Tente novamente.")
    return False

# --- EXECUÇÃO PRINCIPAL ---
if not check_password():
    st.stop()

# --- FUNÇÃO PARA CARREGAR DADOS DO GOOGLE SHEETS ---
@st.cache_data
def carregar_dados_gsheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    NOME_DA_PLANILHA = "Dados Dashboard Financeiro"
    spreadsheet = client.open(NOME_DA_PLANILHA)
    df_receitas = pd.DataFrame(spreadsheet.worksheet('contas_recebidas').get_all_records())
    df_pagamentos = pd.DataFrame(spreadsheet.worksheet('contas_pagas').get_all_records())
    mapa_colunas = {
        'Vencimento': 'Data', 'Descrição': 'Descrição', 'Categoria': 'Categoria',
        'Centro de Custo': 'Centro de Custo', 'Valor categoria/centro de custo': 'Valor Realizado', 'Nome': 'Nome'
    }
    df_receitas = df_receitas.rename(columns=mapa_colunas)
    df_pagamentos = df_pagamentos.rename(columns=mapa_colunas)
    if 'Valor Realizado' in df_receitas.columns:
        df_receitas['Valor Realizado'] = pd.to_numeric(df_receitas['Valor Realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    if 'Valor Realizado' in df_pagamentos.columns:
        df_pagamentos['Valor Realizado'] = pd.to_numeric(df_pagamentos['Valor Realizado'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
    df_receitas['Tipo'] = 'Receita'
    df_pagamentos['Tipo'] = 'Despesa'
    colunas_essenciais = ['Data', 'Descrição', 'Categoria', 'Centro de Custo', 'Valor Realizado', 'Tipo', 'Nome']
    if 'Nome' not in df_receitas.columns: df_receitas['Nome'] = 'N/A'
    if 'Nome' not in df_pagamentos.columns: df_pagamentos['Nome'] = 'N/A'
    df_completo = pd.concat([df_receitas[colunas_essenciais], df_pagamentos[colunas_essenciais]], ignore_index=True)
    df_completo['Data'] = pd.to_datetime(df_completo['Data'], errors='coerce', dayfirst=True)
    df_completo.dropna(subset=['Data'], inplace=True)
    return df_completo

df = carregar_dados_gsheets()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros:")
df['Ano'] = df['Data'].dt.year
df['MesNum'] = df['Data'].dt.month
meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
