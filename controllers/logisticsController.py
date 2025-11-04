# controllers/logistics_controller.py
import os
import pandas as pd
from typing import Optional, Tuple, Dict

def _to_snake(s: str) -> str:
    return s.strip().lower().replace(" ", "_")

class LogisticsController:
    """
    Controlador para o Projeto 5 - Dashboard Logístico.
    Lê data/logistica.csv (ou outro nome passado) e expõe funções para KPIs e agregações.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.logistica = pd.DataFrame()
        self.load_data()

    def _safe_read(self, path: str) -> pd.DataFrame:
        if os.path.exists(path):
            try:
                # tenta inferir separador (',' ou ';')
                return pd.read_csv(path, sep=None, engine="python")
            except Exception:
                return pd.read_csv(path, sep=";")
        return pd.DataFrame()

    def load_data(self, filename: str = "logistica.csv"):
        """Lê o CSV de logística (padrão: data/logistica.csv)"""
        path = os.path.join(self.data_dir, filename)
        df = self._safe_read(path)
        df = self._normalize(df)
        self.logistica = df

    def reload_data(self, filename: str = "logistica.csv"):
        self.load_data(filename)

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nomes de colunas para snake_case e tenta mapear nomes comuns."""
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.copy()
        df.columns = [_to_snake(c) for c in df.columns]

        # mapeamentos comuns (aceita variações)
        rename_map = {
            "pedido_id": "pedido_id",
            "id_pedido": "pedido_id",
            "data_pedido": "data_pedido",
            "data_entrega": "data_entrega",
            "transportadora": "transportadora",
            "transportadora_nome": "transportadora",
            "cidade_origem": "cidade_origem",
            "cidade_destino": "cidade_destino",
            "estado_origem": "estado_origem",
            "estado_destino": "estado_destino",
            "prazo_estimado_dias": "prazo_estimado_dias",
            "prazo_real_dias": "prazo_real_dias",
            "custo_transporte": "custo_transporte",
            "status_entrega": "status_entrega",
            # eventuais lat/lon
            "origem_lat": "origem_lat",
            "origem_lon": "origem_lon",
            "destino_lat": "destino_lat",
            "destino_lon": "destino_lon"
        }
        # aplica apenas para chaves existentes (protege contra KeyError)
        apply_map = {k: v for k, v in rename_map.items() if k in df.columns}
        if apply_map:
            df = df.rename(columns=apply_map)

        # converte datas quando presentes
        for date_col in ["data_pedido", "data_entrega"]:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # converte numéricos
        for num_col in ["prazo_estimado_dias", "prazo_real_dias", "custo_transporte"]:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)

        # garante colunas de cidade/estado como string
        for txt in ["cidade_origem", "cidade_destino", "estado_origem", "estado_destino", "transportadora", "status_entrega"]:
            if txt in df.columns:
                df[txt] = df[txt].astype(str)

        return df

    # -------------------------
    # Funções analíticas
    # -------------------------
    def filter_data(self,
                    transportadoras: Optional[list] = None,
                    cidades_origem: Optional[list] = None,
                    cidades_destino: Optional[list] = None,
                    start_date: Optional[pd.Timestamp] = None,
                    end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """Filtra logistica por transportadora/origem/destino/período."""
        df = self.logistica.copy()
        if df.empty:
            return df
        if transportadoras:
            df = df[df["transportadora"].isin(transportadoras)]
        if cidades_origem:
            df = df[df["cidade_origem"].isin(cidades_origem)]
        if cidades_destino:
            df = df[df["cidade_destino"].isin(cidades_destino)]
        if start_date is not None and "data_pedido" in df.columns:
            df = df[df["data_pedido"] >= pd.to_datetime(start_date)]
        if end_date is not None and "data_pedido" in df.columns:
            df = df[df["data_pedido"] <= pd.to_datetime(end_date)]
        return df

    def on_time_percentage(self, df: Optional[pd.DataFrame] = None) -> float:
        """
        Percentual de entregas no prazo:
        condição de on-time: prazo_real_dias <= prazo_estimado_dias
        """
        d = self.logistica if df is None else df.copy()
        if d.empty or "prazo_real_dias" not in d.columns or "prazo_estimado_dias" not in d.columns:
            return 0.0
        mask_valid = d["prazo_estimado_dias"].notna() & d["prazo_real_dias"].notna()
        if mask_valid.sum() == 0:
            return 0.0
        on_time = (d.loc[mask_valid, "prazo_real_dias"] <= d.loc[mask_valid, "prazo_estimado_dias"]).sum()
        pct = (on_time / mask_valid.sum()) * 100.0
        return round(pct, 2)

    def avg_delivery_time_by_carrier(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Tempo médio de entrega por transportadora (dias)"""
        d = self.logistica if df is None else df.copy()
        if d.empty or "transportadora" not in d.columns or "prazo_real_dias" not in d.columns:
            return pd.DataFrame(columns=["transportadora", "prazo_medio", "qtd_pedidos"])
        g = d.groupby("transportadora").agg(prazo_medio=("prazo_real_dias", "mean"),
                                           qtd_pedidos=("pedido_id", "count") if "pedido_id" in d.columns else ("prazo_real_dias","count"))
        g = g.reset_index().sort_values("prazo_medio")
        g["prazo_medio"] = g["prazo_medio"].round(2)
        return g

    def flows_origin_dest(self, df: Optional[pd.DataFrame] = None, top_n: int = 50) -> pd.DataFrame:
        """Retorna agregação de fluxo origem->destino com contagem e custo médio."""
        d = self.logistica if df is None else df.copy()
        if d.empty or "cidade_origem" not in d.columns or "cidade_destino" not in d.columns:
            return pd.DataFrame(columns=["cidade_origem","cidade_destino","count","avg_custo"])
        agg = d.groupby(["cidade_origem","cidade_destino"], dropna=False).agg(
            count=("pedido_id","count") if "pedido_id" in d.columns else ("cidade_origem","count"),
            avg_custo=("custo_transporte","mean")
        ).reset_index().sort_values("count", ascending=False).head(top_n)
        agg["avg_custo"] = agg["avg_custo"].round(2)
        return agg

    def costs_by_region(self, df: Optional[pd.DataFrame] = None, by: str = "cidade_destino") -> pd.DataFrame:
        """Agrega custo_transporte por cidade_destino ou estado_destino"""
        d = self.logistica if df is None else df.copy()
        if d.empty:
            return pd.DataFrame()
        if by not in d.columns:
            return pd.DataFrame()
        agg = d.groupby(by).agg(total_custo=("custo_transporte","sum"), qtd=("pedido_id","count") if "pedido_id" in d.columns else ("custo_transporte","count")).reset_index()
        agg["total_custo"] = agg["total_custo"].round(2)
        return agg.sort_values("total_custo", ascending=False)

    def supplier_efficiency(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Alias para avg_delivery_time_by_carrier (mantido para consistência conceitual)."""
        return self.avg_delivery_time_by_carrier(df)

    # Preparar dados para Sankey (origem->destino)
    def prepare_sankey(self, df: Optional[pd.DataFrame] = None, top_n: int = 50) -> Tuple[list, list, list]:
        """
        Retorna (labels, source_indices, target_indices, values) para plotar Sankey.
        Aqui devolvemos (labels, source_idx, target_idx, values).
        """
        agg = self.flows_origin_dest(df=df, top_n=top_n)
        if agg.empty:
            return [], [], [], []
        labels = list(pd.unique(agg["cidade_origem"].tolist() + agg["cidade_destino"].tolist()))
        source = [labels.index(r["cidade_origem"]) for _, r in agg.iterrows()]
        target = [labels.index(r["cidade_destino"]) for _, r in agg.iterrows()]
        values = agg["count"].tolist()
        return labels, source, target, values
