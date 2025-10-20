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

# Upload opcional
st.sidebar.header("📂 Importar Arquivos CSV")
with st.sidebar.expander("Carregar novos arquivos"):
    compras_up = st.file_uploader("compras.csv", type=["csv"])
    produtos_up = st.file_uploader("produtos.csv", type=["csv"])
    if st.button("Atualizar dados"):
        if compras_up:
            pd.read_csv(compras_up).to_csv("data/compras.csv", index=False)
        if produtos_up:
            pd.read_csv(produtos_up).to_csv("data/produtos.csv", index=False)
        st.success("✅ Arquivos atualizados! Recarregue a página.")
        st.stop()

ctrl.reload_data()
df = ctrl.comprasDf

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado. Coloque os arquivos CSV na pasta `data/`.")
    st.stop()

# ==============================
# ======== SIDEBAR =============
# ==============================

st.sidebar.header("🔍 Filtros")
fornecedores = sorted(df["fornecedor"].dropna().unique())
produtos = sorted(df["produto_nome"].dropna().unique())

selected_fornecedores = st.sidebar.multiselect("Fornecedor", fornecedores, default=fornecedores)
selected_produtos = st.sidebar.multiselect("Produto", produtos, default=produtos)

min_date = df["data_compra"].min()
max_date = df["data_compra"].max()

start_date = st.sidebar.date_input("Data inicial", min_date)
end_date = st.sidebar.date_input("Data final", max_date)

filtered = ctrl.filter_data(selected_fornecedores, selected_produtos, pd.to_datetime(start_date), pd.to_datetime(end_date))

# ==============================
# ======== MÉTRICAS ============
# ==============================

col1, col2 = st.columns(2)
col1.metric("💰 Gasto Total", f"R$ {ctrl.get_total_spent(filtered):,.2f}")
col2.metric("📦 Quantidade Comprada", f"{filtered['quantidade_comprada'].sum():,}")

st.divider()

# ==============================
# ===== COMPARATIVO ============
# ==============================

st.subheader("🏭 Comparativo entre Fornecedores")
comp = ctrl.get_supplier_comparative(filtered)
if not comp.empty:
    fig = px.scatter(
        comp, x="preco_medio", y="prazo_medio", size="gasto_total",
        hover_name="fornecedor",
        labels={"preco_medio": "Preço Médio (R$)", "prazo_medio": "Prazo Médio (dias)", "gasto_total": "Gasto Total (R$)"},
        title="Comparativo de Fornecedores"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(comp)
else:
    st.info("Sem dados disponíveis para o comparativo.")

st.divider()

# ==============================
# ====== VOLUME MENSAL =========
# ==============================

st.subheader("📅 Volume de Compras por Mês")
ts = ctrl.get_monthly_volume(filtered)
if not ts.empty:
    fig_ts = px.bar(ts, x="data_compra", y="valor_total", title="Evolução Mensal das Compras")
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.info("Sem dados mensais disponíveis.")

st.divider()

# ==============================
# ======= TOP PRODUTOS =========
# ==============================

st.subheader("🏷️ Top Produtos por Gasto")
top = ctrl.get_top_products_by_spend(filtered)
if not top.empty:
    fig_top = px.bar(top, x="produto_nome", y="gasto_total", title="Top Produtos por Gasto")
    st.plotly_chart(fig_top, use_container_width=True)
else:
    st.info("Nenhum produto encontrado.")

st.divider()

st.subheader("📊 Tabela de Compras Filtrada")
st.dataframe(filtered)
