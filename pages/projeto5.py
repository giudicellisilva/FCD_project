# pages/projeto5.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from controllers.logisticsController import LogisticsController

st.set_page_config(page_title="Projeto 5 - Dashboard Logístico", layout="wide")
st.title("🚚 Projeto 5 — Dashboard de Performance Logística")

# Controller
ctrl = LogisticsController()
ctrl.reload_data()  # carrega data/logistica.csv por padrão

# ----------------------
# Upload opcional (como nos outros projetos)
# ----------------------
st.sidebar.header("📂 Importar Arquivos CSV")
with st.sidebar.expander("Carregar novo arquivo de logística (opcional)"):
    log_up = st.file_uploader("logistica.csv", type=["csv"], key="log_up")
    if st.button("Atualizar dados"):
        if log_up:
            # detecta separador automaticamente e salva em data/logistica.csv
            pd.read_csv(log_up, sep=None, engine="python").to_csv("data/logistica.csv", index=False)
            st.success("Arquivo salvo em data/logistica.csv. Recarregue a página.")
            st.stop()
        else:
            st.info("Nenhum arquivo selecionado. Nada foi alterado.")

# verifica se existem dados carregados
if ctrl.logistica.empty:
    st.warning("Nenhum dado logístico encontrado (data/logistica.csv). Faça upload do arquivo.")
    st.stop()

# Normaliza periodos convertidos (evita Period/Datetime problemas)
# (já tratado no controller, mas reforçamos)
for col in ctrl.logistica.columns:
    if pd.api.types.is_period_dtype(ctrl.logistica[col]):
        ctrl.logistica[col] = ctrl.logistica[col].astype(str)

# ----------------------
# Sidebar filtros
# ----------------------
st.sidebar.header("🔎 Filtros")
transportadoras = sorted(ctrl.logistica["transportadora"].dropna().unique()) if "transportadora" in ctrl.logistica.columns else []
cidades_origem = sorted(ctrl.logistica["cidade_origem"].dropna().unique()) if "cidade_origem" in ctrl.logistica.columns else []
cidades_destino = sorted(ctrl.logistica["cidade_destino"].dropna().unique()) if "cidade_destino" in ctrl.logistica.columns else []

selected_transportadoras = st.sidebar.multiselect("Transportadora", transportadoras, default=transportadoras)
selected_origens = st.sidebar.multiselect("Cidade origem", cidades_origem, default=cidades_origem)
selected_destinos = st.sidebar.multiselect("Cidade destino", cidades_destino, default=cidades_destino)

# período
min_date = ctrl.logistica["data_pedido"].min() if "data_pedido" in ctrl.logistica.columns else pd.to_datetime("2025-01-01")
max_date = ctrl.logistica["data_pedido"].max() if "data_pedido" in ctrl.logistica.columns else pd.to_datetime("2025-12-31")
start_date = st.sidebar.date_input("Data inicial", min_date)
end_date = st.sidebar.date_input("Data final", max_date)

filtered = ctrl.filter_data(transportadoras=selected_transportadoras,
                            cidades_origem=selected_origens,
                            cidades_destino=selected_destinos,
                            start_date=pd.to_datetime(start_date),
                            end_date=pd.to_datetime(end_date))

# ----------------------
# KPIs
# ----------------------
st.subheader("📊 Indicadores Principais")
col1, col2, col3 = st.columns(3)

on_time_pct = ctrl.on_time_percentage(filtered)
col1.metric("✅ Entregas no Prazo (%)", f"{on_time_pct:.2f}%")

avg_by_carrier = ctrl.avg_delivery_time_by_carrier(filtered)
avg_overall = avg_by_carrier["prazo_medio"].mean() if not avg_by_carrier.empty else 0.0
col2.metric("⏱️ Prazo Médio (dias)", f"{avg_overall:.2f}")

total_cost = filtered["custo_transporte"].sum() if "custo_transporte" in filtered.columns else 0.0
col3.metric("💸 Custo Total (período)", f"R$ {total_cost:,.2f}")

st.markdown("---")

# ----------------------
# Tempo médio por transportadora (gráfico de barras)
# ----------------------
st.subheader("🏷️ Tempo Médio de Entrega por Transportadora")
if avg_by_carrier.empty:
    st.info("Sem dados de prazo por transportadora.")
else:
    fig_bar = px.bar(avg_by_carrier, x="transportadora", y="prazo_medio",
                     labels={"transportadora":"Transportadora","prazo_medio":"Prazo médio (dias)"},
                     title="Tempo Médio de Entrega por Transportadora (menor -> melhor)")
    st.plotly_chart(fig_bar, use_container_width=True)

# ----------------------
# Mapa ou Sankey de fluxo origem -> destino
# ----------------------
st.subheader("🗺️ Fluxos Origem → Destino")
flows = ctrl.flows_origin_dest(filtered, top_n=100)
if flows.empty:
    st.info("Não há dados de fluxos origem→destino para o filtro selecionado.")
else:
    st.markdown("Top fluxos (contagem de pedidos e custo médio):")
    st.dataframe(flows)

    # preparar Sankey
    labels, source, target, values = ctrl.prepare_sankey(filtered, top_n=100)
    if labels:
        sankey_fig = go.Figure(data=[go.Sankey(
            node = dict(label=labels, pad=15, thickness=15),
            link = dict(source=source, target=target, value=values)
        )])
        sankey_fig.update_layout(title_text="Fluxos Origem → Destino (Sankey)", font_size=10, height=600)
        st.plotly_chart(sankey_fig, use_container_width=True)

# ----------------------
# Custos logísticos por região
# ----------------------
st.subheader("📍 Custos Logísticos por Região")
# priori: estado_destino, se existir; senão cidade_destino
if "estado_destino" in filtered.columns:
    by = "estado_destino"
elif "cidade_destino" in filtered.columns:
    by = "cidade_destino"
else:
    by = None

if by:
    costs = ctrl.costs_by_region(filtered, by=by)
    if costs.empty:
        st.info("Sem dados de custo por região.")
    else:
        st.dataframe(costs.head(50))
        fig_cost = px.bar(costs.head(30), x=by, y="total_custo",
                          labels={by:by, "total_custo":"Custo Total (R$)"},
                          title=f"Custo de Transporte por {by}")
        st.plotly_chart(fig_cost, use_container_width=True)
else:
    st.info("Nenhuma coluna de cidade/estado destino disponível para agregação por região.")

# ----------------------
# Tabelas brutas
# ----------------------
st.markdown("---")
st.subheader("📋 Tabela de Entregas (filtrada)")
st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

st.caption("Projeto 5 — Dashboard Logístico. Ajuste o CSV em /data/logistica.csv ou use o upload na barra lateral.")
