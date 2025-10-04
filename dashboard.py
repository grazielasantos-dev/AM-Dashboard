# CÓDIGO DE TESTE FINAL
import pandas as pd
import streamlit as st
# Demais imports omitidos para brevidade, mas o código completo está no final

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Financeiro",
                   page_icon=":bar_chart:",
                   layout="wide")

# --- FUNÇÃO DE VERIFICAÇÃO DE SENHA ---
def check_password():
    """Retorna True se o usuário digitou a senha correta."""
    def password_entered():
        # Verifica se a chave 'APP_PASSWORD' existe nos segredos
        if "APP_PASSWORD" not in st.secrets:
            st.error("ERRO DE CONFIGURAÇÃO: A variável APP_PASSWORD não foi encontrada nos segredos do Streamlit.")
            st.session_state["password_correct"] = False
            return

        # Compara a senha digitada com a senha nos segredos
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
    
    # Linha de debug para verificar se os segredos estão sendo lidos
    if "APP_PASSWORD" in st.secrets:
        st.info("Segredo 'APP_PASSWORD' encontrado. Aguardando senha...")
    else:
        st.error("ALERTA: O segredo 'APP_PASSWORD' NÃO FOI ENCONTRADO na configuração do Streamlit.")

    return False

# --- EXECUÇÃO PRINCIPAL ---
if not check_password():
    st.stop()

# Se a senha estiver correta, o resto do código (que já sabemos que funciona) será executado.
# Apenas uma mensagem de sucesso será exibida para confirmar.
st.success("🎉 Acesso Liberado! A senha e os segredos estão funcionando!")
st.balloons()
