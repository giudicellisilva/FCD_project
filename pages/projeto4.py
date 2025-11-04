import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.superController import SuperDashboardController

st.set_page_config(page_title="Projeto 4 - Super Dashboard Integrado", layout="wide")
st.title("📈 Super Dashboard Integrado (Estoque • Vendas • Compras)")

ctrl = SuperDashboardController()

# =================================================
# ======== UPLOAD OPCIONAL DE NOVOS DADOS =========
# =================================================
st.sidebar.header("📂 Importar Arquivos CSV")

with st.sidebar.expander("Carregar novos arquivos"):
    vendas_up = st.file_uploader("vendas.csv", type=["csv"])
    compras_up = st.file_uploader("compras.csv", type=["csv"])
    produtos_up = st.file_uploader("produtos.csv", type=["csv"])
    estoque_up = st.file_uploader("estoque.csv", type=["csv"])

    if st.button("🔄 Atualizar dados"):
        try:
            if vendas_up:
                pd.read_csv(vendas_up, sep=";").to_csv("data/vendas.csv", index=False, sep=";")
            if compras_up:
                pd.read_csv(compras_up, sep=";").to_csv("data/compras.csv", index=False, sep=";")
            if produtos_up:
                pd.read_csv(produtos_up, sep=";").to_csv("data/produtos.csv", index=False, sep=";")
            if estoque_up:
                pd.read_csv(estoque_up, sep=";").to_csv("data/estoque.csv", index=False, sep=";")
            st.success("✅ Arquivos atualizados! Recarregue a página.")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")
            st.stop()

ctrl.reload_data()

if ctrl.vendasDf.empty or ctrl.comprasDf.empty or ctrl.produtosDf.empty or ctrl.estoqueDf.empty:
    st.warning("⚠️ Um ou mais arquivos CSV estão faltando na pasta `data/`.")
    st.stop()

# =================================================
# =============== SIDEBAR DE FILTROS ==============
# =================================================
st.sidebar.header("🎛️ Filtros")

produtos = sorted(ctrl.produtosDf["produto_nome"].dropna().unique())
categorias = sorted(ctrl.produtosDf["categoria"].dropna().unique())

selected_produtos = st.sidebar.multiselect("Produto", produtos, default=produtos[:3])
selected_categorias = st.sidebar.multiselect("Categoria", categorias, default=categorias[:3])

min_date = ctrl.vendasDf["data_venda"].min()
max_date = ctrl.vendasDf["data_venda"].max()

start_date = st.sidebar.date_input("Data inicial", min_date)
end_date = st.sidebar.date_input("Data final", max_date)

# =================================================
# =================== FILTROS =====================
# =================================================
vendas = ctrl.vendasDf.copy()
compras = ctrl.comprasDf.copy()
produtosDf = ctrl.produtosDf.copy()
estoque = ctrl.estoqueDf.copy()

if selected_produtos:
    ids_prod = produtosDf[produtosDf["produto_nome"].isin(selected_produtos)]["produto_id"]
    vendas = vendas[vendas["produto_id"].isin(ids_prod)]
    compras = compras[compras["produto_id"].isin(ids_prod)]
    estoque = estoque[estoque["produto_id"].isin(ids_prod)]

if selected_categorias:
    ids_cat = produtosDf[produtosDf["categoria"].isin(selected_categorias)]["produto_id"]
    vendas = vendas[vendas["produto_id"].isin(ids_cat)]
    compras = compras[compras["produto_id"].isin(ids_cat)]
    estoque = estoque[estoque["produto_id"].isin(ids_cat)]

vendas = vendas[(vendas["data_venda"] >= pd.to_datetime(start_date)) & (vendas["data_venda"] <= pd.to_datetime(end_date))]
compras = compras[(compras["data_compra"] >= pd.to_datetime(start_date)) & (compras["data_compra"] <= pd.to_datetime(end_date))]

# =================================================
# ==================== MÉTRICAS ===================
# =================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Receita Total", f"R$ {ctrl.get_total_revenue(vendas):,.2f}")
col2.metric("🛒 Gasto Total", f"R$ {ctrl.get_total_purchases(compras):,.2f}")
col3.metric("🏭 Valor em Estoque", f"R$ {ctrl.get_total_stock_value(produtosDf, estoque):,.2f}")
col4.metric("⚠️ Produtos Críticos", len(ctrl.get_stock_status(estoque)))

st.divider()

# =================================================
# ==================== GRÁFICOS ===================
# =================================================
st.subheader("📅 Evolução Mensal de Vendas e Compras")
vendas_ts = ctrl.get_sales_trend(vendas)
compras_ts = ctrl.get_purchase_trend(compras)

if not vendas_ts.empty and not compras_ts.empty:
    df_merged = pd.merge(
        vendas_ts, compras_ts,
        on="Mês", how="outer", suffixes=("_vendas", "_compras")
    ).fillna(0)

    # Converte colunas do tipo Period para string antes de plotar
    for col in df_merged.columns:
        if pd.api.types.is_period_dtype(df_merged[col]):
            df_merged[col] = df_merged[col].astype(str)

    fig = px.line(
        df_merged,
        x="Mês",
        y=["valor_total_vendas", "valor_total_compras"],
        markers=True,
        title="Série Temporal - Vendas x Compras"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sem dados suficientes para gerar o gráfico temporal.")


st.divider()

st.subheader("🔥 Top 10 Produtos Mais Vendidos")
top = ctrl.get_top_products(vendas, produtosDf)
if not top.empty:
    fig_top = px.bar(top, x="produto_nome", y="quantidade_vendida", title="Top Produtos")
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("Sem dados de vendas disponíveis.")

st.divider()

st.subheader("🚨 Produtos com Estoque Crítico")
criticos = ctrl.get_critical_products(produtosDf, estoque)
st.dataframe(criticos, use_container_width=True)

st.divider()

st.subheader("📊 Dados Consolidados (Visão 360°)")
merged = produtosDf.merge(estoque, on="produto_id", how="left").merge(vendas, on="produto_id", how="left").merge(compras, on="produto_id", how="left")
st.dataframe(merged, use_container_width=True)
