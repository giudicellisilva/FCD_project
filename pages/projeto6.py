import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import plotly.express as px
from controllers.supplyChainController import SupplyChainController
import pandas as pd
import calendar

st.set_page_config(page_title="Dashboard Supply Chain", layout="wide")
st.title("📦 Dashboard Estratégico de Supply Chain")

ctrl = SupplyChainController()

# ==============================
# ===== IMPORTAÇÃO MANUAL ======
# ==============================
st.sidebar.header("📂 Atualizar Arquivos CSV")
with st.sidebar.expander("Carregar novos arquivos"):
    arquivos = {
        "vendas": st.file_uploader("vendas.csv", type=["csv"]),
        "compras": st.file_uploader("compras.csv", type=["csv"]),
        "produtos": st.file_uploader("produtos.csv", type=["csv"]),
        "estoque": st.file_uploader("estoque.csv", type=["csv"]),
        "logistica": st.file_uploader("logistica.csv", type=["csv"]),
        "clientes": st.file_uploader("clientes.csv", type=["csv"])
    }

    if st.button("Atualizar dados"):
        for nome, arquivo in arquivos.items():
            if arquivo is not None:
                df = pd.read_csv(arquivo, sep=None, engine="python")
                df.to_csv(f"data/{nome}.csv", index=False)
        st.success("✅ Arquivos atualizados com sucesso! Recarregue a página.")
        st.stop()

ctrl.reload_data()

# ==============================
# ===== FILTRO DE PERÍODO ======
# ==============================
st.sidebar.subheader("📅 Filtro de Período para Receita Mensal")

anos = sorted(ctrl.vendas["data_venda"].dt.year.dropna().unique()) if not ctrl.vendas.empty else []
meses = list(range(1, 13))

ano_sel = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1 if anos else 0)
mes_sel = st.sidebar.selectbox("Mês", meses, index=pd.Timestamp.now().month - 1)
nome_mes = calendar.month_name[mes_sel]

# ==============================
# ===== KPIs ==================
# ==============================
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📉 Produtos com Estoque Crítico", len(ctrl.get_estoque_critico()))
col2.metric("💰 Receita Total de Vendas", f"R$ {ctrl.get_receita_total():,.2f}")
col3.metric("📅 Receita de " + nome_mes, f"R$ {ctrl.get_receita_mensal(ano_sel, mes_sel):,.2f}")
col4.metric("🏭 Fornecedor Mais Usado", ctrl.get_fornecedor_mais_usado())
col5.metric("🚚 Entregas no Prazo", f"{ctrl.get_taxa_entregas_no_prazo():.1f}%")

st.divider()

# ==============================
# ===== VENDAS x ESTOQUE ======
# ==============================
st.subheader("📊 Vendas vs Nível de Estoque")
df_comb = ctrl.get_vendas_vs_estoque()
if not df_comb.empty:
    fig = px.bar(df_comb, x="produto_nome", y=["valor_total", "quantidade_estoque"],
                 barmode="group", title="Vendas x Estoque por Produto")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Dados insuficientes para gerar o gráfico.")

st.divider()

# ==============================
# ===== INDICADORES FINANCEIROS ======
# ==============================
st.subheader("💵 Indicadores Financeiros")
col1, col2 = st.columns(2)
col1.metric("💸 Custo Total de Compras", f"R$ {ctrl.get_custo_total_compras():,.2f}")
col2.metric("📈 Margem Bruta Estimada", f"R$ {ctrl.get_margem_bruta_estimada():,.2f}")

st.success("✅ Dashboard Estratégico carregado com sucesso!")
