import streamlit as st

st.set_page_config(page_title="Projetos de Ciência de Dados", layout="wide")

st.title("📊 Projetos de Ciência de Dados – UFAPE 2025.2")

st.markdown("Selecione um projeto para visualizar:")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Projeto 1 – Dashboard de Controle de Estoque"):
        st.switch_page("pages/projeto1.py")

with col2:
    if st.button("📈 Projeto 2 – Análise de Vendas"):
        st.switch_page("pages/projeto2.py")

st.markdown("---")
st.info("📘 Curso: Sistemas de Informação – Disciplina de Fundamentos em Ciência de Dados (2025.2)")
