# COPIE E COLE ESTE CÓDIGO INTEIRO NO SEU dashboard.py
import pandas as pd
import streamlit as st
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Dashboard Financeiro", page_icon=":bar_chart:", layout="wide")

def check_password():
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

if not check_password():
    st.stop()

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

# --- O RESTANTE DO DASHBOARD ---
st.sidebar.header("Filtros:")
df['Ano'] = df['Data'].dt.year
df['MesNum'] = df['Data'].dt.month
meses_pt = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
df['Mes'] = df['MesNum'].map(meses_pt)
anos_disponiveis = sorted(df['Ano'].unique())
anos_selecionados = st.sidebar.multiselect("Selecione o Ano:", options=anos_disponiveis, default=anos_disponiveis)
meses_disponiveis = sorted(df['Mes'].dropna().unique(), key=lambda mes: list(meses_pt.values()).index(mes))
meses_selecionados_nomes = st.sidebar.multiselect("Selecione o Mês:", options=meses_disponiveis, default=meses_disponiveis)
mapa_nome_para_num = {nome: num for num, nome in meses_pt.items()}
meses_selecionados_numeros = [mapa_nome_para_num[nome] for nome in meses_selecionados_nomes]
if 'Centro de Custo' in df.columns:
    centros_custo_validos = sorted(df['Centro de Custo'].dropna().unique())
    centro_custo_selecionado = st.sidebar.multiselect("Selecione o Centro de Custo:", options=centros_custo_validos, default=centros_custo_validos)
else:
    centro_custo_selecionado = []
query_string = "Ano == @anos_selecionados and MesNum == @meses_selecionados_numeros"
if centro_custo_selecionado and 'Centro de Custo' in df.columns:
    query_string += " and `Centro de Custo` == @centro_custo_selecionado"
df_selection = df.query(query_string)

st.title(":bar_chart: Dashboard Financeiro Advocacia")
st.markdown("##")

if df_selection.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

faturamento_total = df_selection[df_selection['Tipo'] == 'Receita']['Valor Realizado'].sum()
pagamentos_total = df_selection[df_selection['Tipo'] == 'Despesa']['Valor Realizado'].sum()
lucro_total = df_selection['Valor Realizado'].sum()
lucratividade = (lucro_total / faturamento_total) * 100 if faturamento_total > 0 else 0
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric(label="Faturamento Total", value=f"R$ {faturamento_total:,.2f}")
with col2: st.metric(label="Pagamentos Totais", value=f"R$ {abs(pagamentos_total):,.2f}")
with col3: st.metric(label="Lucro Total", value=f"R$ {lucro_total:,.2f}")
with col4: st.metric(label="Lucratividade", value=f"{lucratividade:.2f}%")

st.markdown("---")

# --- ANÁLISE COMPARATIVA ANUAL ---
st.subheader("Análise Comparativa Anual de Lucratividade")
df_com_cc = df.dropna(subset=['Centro de Custo'])
anos_para_analise = sorted(df_com_cc['Ano'].unique())
dados_anuais = []
for ano in anos_para_analise:
    df_ano = df_com_cc[df_com_cc['Ano'] == ano]
    faturamento = df_ano[df_ano['Tipo'] == 'Receita']['Valor Realizado'].sum()
    lucro = df_ano['Valor Realizado'].sum()
    lucratividade_anual = (lucro / faturamento) * 100 if faturamento > 0 else 0
    dados_anuais.append({'Ano': ano, 'Lucratividade': lucratividade_anual})
if len(dados_anuais) > 0:
    df_anual = pd.DataFrame(dados_anuais)
    cols = st.columns(len(df_anual))
    for i, row in df_anual.iterrows():
        ano_atual = row['Ano']
        lucratividade_atual = row['Lucratividade']
        delta_text = ""
        if i > 0:
            lucratividade_anterior = df_anual.iloc[i-1]['Lucratividade']
            delta = lucratividade_atual - lucratividade_anterior
            delta_text = f"{delta:.2f} p.p. vs {int(ano_atual)-1}"
        with cols[i]:
            st.metric(label=f"Lucratividade {int(ano_atual)}", value=f"{lucratividade_atual:.2f}%", delta=delta_text or None)
    fig_anual = px.bar(df_anual, x='Ano', y='Lucratividade', text=df_anual['Lucratividade'].apply(lambda x: f'{x:.2f}%'), title="Comparativo de Lucratividade Anual")
    fig_anual.update_layout(yaxis_title="Lucratividade (%)")
    st.plotly_chart(fig_anual, use_container_width=True)
else:
    st.write("Não há dados de múltiplos anos para uma comparação.")

st.markdown("---")
st.subheader(f"Análise Detalhada para o Período Selecionado")

# --- GRÁFICOS PARA O PERÍODO SELECIONADO ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("DRE Simplificado Mensal")
    dre_mensal = df_selection.copy()
    dre_mensal['MesAno'] = dre_mensal['Data'].dt.to_period('M').astype(str)
    dre_agrupado = dre_mensal.groupby(['MesAno', 'Tipo'])['Valor Realizado'].sum().unstack(fill_value=0)
    if 'Receita' not in dre_agrupado.columns: dre_agrupado['Receita'] = 0
    if 'Despesa' not in dre_agrupado.columns: dre_agrupado['Despesa'] = 0
    dre_agrupado['Despesa'] = dre_agrupado['Despesa'].abs()
    dre_agrupado.reset_index(inplace=True)
    fig_dre = px.bar(dre_agrupado, x='MesAno', y=['Receita', 'Despesa'], title="Receitas vs. Despesas", barmode='group', labels={'value': 'Valor', 'variable': 'Tipo', 'MesAno': 'Mês/Ano'})
    st.plotly_chart(fig_dre, use_container_width=True)

    st.subheader("Análise de Despesas por Categoria")
    despesas_categoria = df_selection[df_selection['Tipo'] == 'Despesa'].copy()
    despesas_categoria['Valor Realizado'] = despesas_categoria['Valor Realizado'].abs()
    despesas_agrupadas = despesas_categoria.groupby('Categoria')['Valor Realizado'].sum().reset_index()
    if not despesas_agrupadas.empty:
        fig_despesas_cat = px.pie(despesas_agrupadas, names='Categoria', values='Valor Realizado', title="Distribuição de Despesas")
        st.plotly_chart(fig_despesas_cat, use_container_width=True)
    else:
        st.write("Nenhuma despesa encontrada para o período selecionado.")

with col2:
    st.subheader("Rentabilidade por Centro de Custo")
    if 'Centro de Custo' in df_selection.columns:
        rentabilidade_cc = df_selection.groupby('Centro de Custo')['Valor Realizado'].sum().reset_index(name='Lucro')
        if not rentabilidade_cc.empty:
            fig_rent_cc = px.bar(rentabilidade_cc, x='Centro de Custo', y='Lucro', title="Lucro por Centro de Custo (Receita - Despesa)", labels={'Lucro': 'Lucro (R$)'})
            st.plotly_chart(fig_rent_cc, use_container_width=True)
        else:
            st.write("Não foi possível calcular a rentabilidade.")
    else:
        st.write("Coluna 'Centro de Custo' não encontrada para análise.")

    st.markdown("---")

    st.subheader("Faturamento por Centro de Custo")
    if 'Centro de Custo' in df_selection.columns:
        faturamento_cc = df_selection[df_selection['Tipo'] == 'Receita'].groupby('Centro de Custo')['Valor Realizado'].sum().reset_index()
        if not faturamento_cc.empty:
            fig_faturamento_cc = px.bar(faturamento_cc, x='Centro de Custo', y='Valor Realizado', title="Faturamento Bruto por Centro de Custo (Apenas Receitas)", labels={'Valor Realizado': 'Faturamento (R$)'})
            st.plotly_chart(fig_faturamento_cc, use_container_width=True)
        else:
            st.write("Nenhuma receita encontrada para os filtros selecionados.")

st.markdown("---")

# --- TOP 10 CLIENTES ---
st.subheader("Top 10 Clientes por Faturamento")
top_10_clientes = df_selection[df_selection['Tipo'] == 'Receita'].groupby('Nome')['Valor Realizado'].sum().nlargest(10).sort_values(ascending=True).reset_index()
if not top_10_clientes.empty:
    fig_top_clientes = px.bar(top_10_clientes, x='Valor Realizado', y='Nome', orientation='h', title="Maiores Faturamentos por Cliente", text='Valor Realizado', labels={'Valor Realizado': 'Faturamento (R$)', 'Nome': 'Cliente'})
    fig_top_clientes.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
    fig_top_clientes.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig_top_clientes, use_container_width=True)
else:
    st.write("Nenhuma receita encontrada para gerar o Top 10 Clientes.")


# --- FLUXO DE CAIXA ---
st.subheader("Fluxo de Caixa Diário")
fluxo_caixa_diario = df_selection.sort_values(by='Data').copy()
fluxo_caixa_diario_agrupado = fluxo_caixa_diario.groupby('Data')['Valor Realizado'].sum().reset_index()
fluxo_caixa_diario_agrupado['Saldo Acumulado'] = fluxo_caixa_diario_agrupado['Valor Realizado'].cumsum()
fig_fluxo_caixa = px.line(fluxo_caixa_diario_agrupado, x='Data', y='Saldo Acumulado', title="Saldo de Caixa Acumulado ao Longo do Tempo")
st.plotly_chart(fig_fluxo_caixa, use_container_width=True)
