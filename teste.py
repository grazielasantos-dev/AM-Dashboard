import streamlit as st

st.title("Teste de Segredo")
st.write("O valor do segredo APP_PASSWORD é:", st.secrets["APP_PASSWORD"])
