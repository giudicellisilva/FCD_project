# app.py
import streamlit as st
import plotly.express as px
from controllers.inventoryController import InventoryController
import pandas as pd

st.set_page_config(page_title="Dashboard de Estoque", layout="wide")

st.title("📦 Dashboard de Controle de Estoque")

invCtrl = InventoryController()

# upload opcional
st.sidebar.header("Dados")
with st.sidebar.expander("Carregar novos CSVs (opcional)"):
    uploadedProdutos = st.file_uploader("produtos.csv", type=["csv"], key="upProdutos")
    uploadedEstoque = st.file_uploader("estoque.csv", type=["csv"], key="upEstoque")
    if st.button("Atualizar dados"):
        if uploadedProdutos is not None:
            uploadedProdutos.seek(0)
            pd.read_csv(uploadedProdutos).to_csv("data/produtos.csv", index=False)
        if uploadedEstoque is not None:
            uploadedEstoque.seek(0)
            pd.read_csv(uploadedEstoque).to_csv("data/estoque.csv", index=False)
        st.success("Arquivos salvos em data/. Reinicialize para recarregar.")

invCtrl.reloadData()
inventoryDf = invCtrl.buildInventoryView()

st.sidebar.header("Filtros")
categorias = sorted(inventoryDf["categoria"].dropna().unique().tolist()) if "categoria" in inventoryDf.columns else []
selectedCategories = st.sidebar.multiselect("Filtrar por categoria", options=categorias, default=categorias)

filtered = invCtrl.filterByCategory(inventoryDf, selectedCategories)

belowMask = filtered["quantidadeEstoque"] < filtered["estoqueMinimo"]
numBelow = int(belowMask.sum())
totalProducts = len(filtered)

col1, col2, col3 = st.columns([1,1,2])
with col1:
    st.metric("Produtos em alerta", value=f"{numBelow}", delta=f"{numBelow}/{totalProducts}")
with col2:
    totalValue = filtered["valorTotal"].sum()
    st.metric("Valor total do estoque (filtrado)", value=f"R$ {totalValue:,.2f}")
with col3:
    pct = (numBelow / totalProducts * 100) if totalProducts else 0
    st.write(f"Percentual em alerta: **{pct:.1f}%**")

st.markdown("---")
st.subheader("Tabela de Produtos")
displayCols = ["produtoId", "produtoNome", "categoria", "quantidadeEstoque", "estoqueMinimo", "precoUnitario", "valorTotal"]
for c in displayCols:
    if c not in filtered.columns:
        filtered[c] = ""

st.dataframe(filtered[displayCols].sort_values(["categoria", "produtoNome"]).reset_index(drop=True), use_container_width=True)

st.markdown("---")
st.subheader("Estoque Atual vs Estoque Mínimo")
maxBars = 40
plotDf = filtered.copy().sort_values("quantidadeEstoque", ascending=False).head(maxBars)

fig = px.bar(
    plotDf.melt(id_vars=["produtoNome"], value_vars=["quantidadeEstoque", "estoqueMinimo"]),
    x="produtoNome", y="value", color="variable",
    barmode="group",
    labels={"value": "Quantidade", "produtoNome": "Produto", "variable": "Métrica"},
    title=f"Comparação (top {min(maxBars, len(plotDf))} produtos)"
)

alertProducts = plotDf[plotDf["quantidadeEstoque"] < plotDf["estoqueMinimo"]]["produtoNome"].tolist()
if alertProducts:
    fig.update_layout(legend_title_text=None)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Produtos com Estoque Abaixo do Mínimo (filtrado)")
if numBelow > 0:
    alertDf = filtered[belowMask].sort_values("categoria")
    st.table(alertDf[["produtoId", "produtoNome", "categoria", "quantidadeEstoque", "estoqueMinimo", "precoUnitario", "valorTotal"]])
else:
    st.info("Nenhum produto em alerta no conjunto filtrado.")
