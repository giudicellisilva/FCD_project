import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
from controllers.purchasesController import PurchasesController

st.set_page_config(page_title="Dashboard de Compras e Fornecedores", layout="wide")
st.title("📦 Dashboard de Compras e Fornecedores")

ctrl = PurchasesController()
df = ctrl.comprasDf

# Upload de CSVs
st.sidebar.header("📂 Dados")
with st.sidebar.expander("Carregar novos arquivos (opcional)"):
    compras_up = st.file_uploader("compras.csv", type=["csv"], key="compras")
    produtos_up = st.file_uploader("produtos.csv", type=["csv"], key="produtos")
    fornecedores_up = st.file_uploader("fornecedores.csv", type=["csv"], key="fornecedores")

    if st.button("Atualizar dados"):
        if compras_up is not None:
            pd.read_csv(compras_up).to_csv("data/compras.csv", index=False)
        if produtos_up is not None:
            pd.read_csv(produtos_up).to_csv("data/produtos.csv", index=False)
        if fornecedores_up is not None:
            pd.read_csv(fornecedores_up).to_csv("data/fornecedores.csv", index=False)
        st.success("✅ Arquivos salvos! Recarregue a página para atualizar.")

ctrl.reload_data()
df = ctrl.comprasDf

if df.empty:
    st.warning("Nenhum dado encontrado. Carregue os arquivos CSV em data/.")
    st.stop()

# -----------------------------
# Filtros laterais
# -----------------------------
st.sidebar.header("🔎 Filtros")

fornecedores = sorted(df["fornecedor"].dropna().unique()) if "fornecedor" in df.columns else []
produtos = sorted(df["produto_nome"].dropna().unique()) if "produto_nome" in df.columns else []

selected_fornecedores = st.sidebar.multiselect("Fornecedores", fornecedores, default=fornecedores)
selected_produtos = st.sidebar.multiselect("Produtos", produtos, default=produtos)

min_date = df["data_compra"].min() if "data_compra" in df.columns else pd.to_datetime("2025-01-01")
max_date = df["data_compra"].max() if "data_compra" in df.columns else pd.to_datetime("2025-12-31")
start_date = st.sidebar.date_input("Data inicial", min_date)
end_date = st.sidebar.date_input("Data final", max_date)

filtered = ctrl.filter_data(selected_fornecedores, selected_produtos, pd.to_datetime(start_date), pd.to_datetime(end_date))

# -----------------------------
# Métricas
# -----------------------------
total_spent = ctrl.get_total_spent(filtered)
total_qty = filtered["quantidade_comprada"].sum() if "quantidade_comprada" in filtered.columns else 0

col1, col2 = st.columns(2)
col1.metric("💰 Gasto Total", f"R$ {total_spent:,.2f}")
col2.metric("📦 Quantidade Comprada", f"{total_qty:,}")

st.divider()

# -----------------------------
# Comparativo entre fornecedores
# -----------------------------
st.subheader("🏭 Comparativo entre Fornecedores (Preço Médio e Prazo Médio)")
comp = ctrl.get_supplier_comparative(filtered)
if comp.empty:
    st.info("Sem dados disponíveis para o comparativo.")
else:
    fig = px.scatter(
        comp, x="preco_medio", y="prazo_medio", size="gasto_total",
        hover_name="fornecedor", title="Comparativo de Fornecedores",
        labels={"preco_medio": "Preço Médio (R$)", "prazo_medio": "Prazo Médio (dias)", "gasto_total": "Gasto Total (R$)"}
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(comp)

st.divider()

# -----------------------------
# Volume de compras por mês
# -----------------------------
st.subheader("📅 Volume de Compras por Mês")
ts = ctrl.get_monthly_volume(filtered)
if ts.empty:
    st.info("Sem dados mensais.")
else:
    fig_ts = px.bar(ts, x="data_compra", y="valor_total",
                    labels={"data_compra": "Mês", "valor_total": "Gasto Total (R$)"},
                    title="Evolução Mensal das Compras")
    st.plotly_chart(fig_ts, use_container_width=True)

st.divider()

# -----------------------------
# Produtos com maior gasto
# -----------------------------
st.subheader("🏷️ Produtos com Maior Gasto em Compras")
top = ctrl.get_top_products_by_spend(filtered)
if top.empty:
    st.info("Nenhum produto encontrado.")
else:
    fig_top = px.bar(top, x="produto_nome", y="gasto_total", title="Top Produtos por Gasto")
    st.plotly_chart(fig_top, use_container_width=True)
    st.dataframe(top)

st.divider()
st.subheader("📊 Tabela de Compras (Filtrada)")
st.dataframe(filtered)
