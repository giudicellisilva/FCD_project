import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.salesController import SalesController

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
st.title("📈 Dashboard de Movimentações de Vendas")

salesCtrl = SalesController()
df = salesCtrl.vendasDf

# Upload opcional
st.sidebar.header("Dados")
with st.sidebar.expander("Carregar novos CSVs (opcional)"):
    uploadedVendas = st.file_uploader("vendas.csv", type=["csv"], key="upVendas")
    uploadedProdutos = st.file_uploader("produtos.csv", type=["csv"], key="upProdutos")
    if st.button("Atualizar dados"):
        if uploadedVendas is not None:
            uploadedVendas.seek(0)
            pd.read_csv(uploadedVendas).to_csv("data/vendas.csv", index=False)
        if uploadedProdutos is not None:
            uploadedProdutos.seek(0)
            pd.read_csv(uploadedProdutos).to_csv("data/produtos.csv", index=False)
        st.success("Arquivos salvos em data/. Reinicialize para recarregar.")

# Verifica se há dados
if df.empty:
    st.warning("Nenhum dado de vendas disponível. Por favor, carregue os arquivos CSV.")
else:
    st.sidebar.header("Filtros")
    lojas = sorted(df["loja"].dropna().unique())
    produtos = sorted(df["produtoNome"].dropna().unique())

    selectedLojas = st.sidebar.multiselect("Filtrar por loja", options=lojas, default=lojas)
    selectedProdutos = st.sidebar.multiselect("Filtrar por produto", options=produtos, default=produtos)
    startDate = st.sidebar.date_input("Data inicial", value=df["data"].min())
    endDate = st.sidebar.date_input("Data final", value=df["data"].max())

    filtered = salesCtrl.filterData(selectedLojas, selectedProdutos, pd.to_datetime(startDate), pd.to_datetime(endDate))

    # Métricas principais
    totalRevenue = salesCtrl.getRevenue(filtered)
    totalQty = filtered["quantidadeVendida"].sum()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Receita Total", f"R$ {totalRevenue:,.2f}")
    with col2:
        st.metric("Quantidade Total Vendida", f"{totalQty}")

    st.markdown("---")
    # Série temporal
    st.subheader("Quantidade Vendida por Mês")
    tsDf = salesCtrl.getTimeSeries(filtered)
    if tsDf.empty:
        st.info("Não há dados para o período selecionado.")
    else:
        fig = px.line(tsDf, x="data", y="quantidadeVendida", markers=True, labels={"data":"Mês", "quantidadeVendida":"Quantidade Vendida"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    # Top 10 produtos
    st.subheader("Top 10 Produtos Mais Vendidos")
    topDf = salesCtrl.getTopProducts(filtered)
    if topDf.empty:
        st.info("Não há produtos vendidos no período filtrado.")
    else:
        figTop = px.bar(topDf, x="produtoNome", y="quantidadeVendida", labels={"produtoNome":"Produto", "quantidadeVendida":"Quantidade Vendida"})
        st.plotly_chart(figTop, use_container_width=True)

    st.markdown("---")
    # Tabela detalhada
    st.subheader("Tabela de Vendas Filtradas")
    displayCols = ["data", "loja", "produtoId", "produtoNome", "quantidadeVendida", "precoUnitario", "valorTotal"]
    for c in displayCols:
        if c not in filtered.columns:
            filtered[c] = ""
    st.dataframe(filtered[displayCols].sort_values(["data", "loja", "produtoNome"]).reset_index(drop=True), use_container_width=True)
