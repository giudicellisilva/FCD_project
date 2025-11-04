import pandas as pd
import os

class SupplyChainController:
    def __init__(self):
        self.data_path = "data"
        self.vendas = self._load_csv("vendas")
        self.compras = self._load_csv("compras")
        self.produtos = self._load_csv("produtos")
        self.estoque = self._load_csv("estoque")
        self.logistica = self._load_csv("logistica")
        self.clientes = self._load_csv("clientes")
        self._process_dates()

    # ===========================================================
    # ====== LEITURA ROBUSTA DE ARQUIVOS CSV ====================
    # ===========================================================
    def _load_csv(self, name):
        path = os.path.join(self.data_path, f"{name}.csv")
        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            with open(path, "r", encoding="utf-8") as f:
                first = f.readline()
                sep = ";" if first.count(";") > first.count(",") else ","
            df = pd.read_csv(path, sep=sep, encoding="utf-8")
            df.columns = df.columns.str.strip().str.lower()
            return df
        except Exception as e:
            print(f"Erro ao carregar {name}.csv: {e}")
            return pd.DataFrame()

    # ===========================================================
    # ====== RECEITA MENSAL =====================================
    # ===========================================================
    def get_receita_mensal(self, ano=None, mes=None):
        """
        Retorna o total de vendas (receita) do mês e ano informados.
        """
        if self.vendas.empty or "data_venda" not in self.vendas.columns or "valor_total" not in self.vendas.columns:
            return 0.0

        df = self.vendas.copy()

        # Garante que a coluna de data é datetime
        df["data_venda"] = pd.to_datetime(df["data_venda"], errors="coerce")

        # Cria colunas auxiliares de ano e mês
        df["ano"] = df["data_venda"].dt.year
        df["mes"] = df["data_venda"].dt.month

        # Filtro opcional
        if ano is not None:
            df = df[df["ano"] == ano]
        if mes is not None:
            df = df[df["mes"] == mes]

        # Calcula a soma total
        return df["valor_total"].sum()


    # ===========================================================
    # ====== CONVERSÃO DE DATAS =================================
    # ===========================================================
    def _process_dates(self):
        mapping = {
            "vendas": ["data_venda"],
            "compras": ["data_compra"],
            "logistica": ["data_pedido", "data_entrega"],
            "estoque": ["data_referencia"]
        }
        for name, cols in mapping.items():
            df = getattr(self, name)
            if not df.empty:
                for col in cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce")

    # ===========================================================
    # ====== KPI PRINCIPAIS =====================================
    # ===========================================================
    def get_estoque_critico(self):
        if self.estoque.empty:
            return pd.DataFrame()
        if all(c in self.estoque.columns for c in ["quantidade_estoque", "estoque_minimo"]):
            return self.estoque[self.estoque["quantidade_estoque"] < self.estoque["estoque_minimo"]]
        return pd.DataFrame()

    def get_receita_total(self):
        if not self.vendas.empty and "valor_total" in self.vendas.columns:
            return self.vendas["valor_total"].sum()
        return 0.0

    def get_fornecedor_mais_usado(self):
        if not self.compras.empty and "fornecedor" in self.compras.columns:
            return self.compras["fornecedor"].value_counts().idxmax()
        return "N/A"

    def get_taxa_entregas_no_prazo(self):
        if self.logistica.empty:
            return 0.0
        if all(c in self.logistica.columns for c in ["prazo_estimado_dias", "prazo_real_dias"]):
            total = len(self.logistica)
            no_prazo = len(self.logistica[self.logistica["prazo_real_dias"] <= self.logistica["prazo_estimado_dias"]])
            return (no_prazo / total * 100) if total > 0 else 0
        return 0.0

    # ===========================================================
    # ====== COMPARAÇÕES E INDICADORES ==========================
    # ===========================================================
    def get_vendas_vs_estoque(self):
        if self.vendas.empty or self.estoque.empty:
            return pd.DataFrame()
        if "produto_id" not in self.vendas.columns or "produto_id" not in self.estoque.columns:
            return pd.DataFrame()

        vendas_prod = self.vendas.groupby("produto_id")["valor_total"].sum().reset_index()
        estoq_prod = self.estoque.groupby("produto_id")["quantidade_estoque"].sum().reset_index()
        df = pd.merge(vendas_prod, estoq_prod, on="produto_id", how="inner")

        if "produto_nome" in self.produtos.columns:
            df = pd.merge(df, self.produtos[["produto_id", "produto_nome"]], on="produto_id", how="left")

        return df

    def get_custo_total_compras(self):
        if not self.compras.empty and "valor_total" in self.compras.columns:
            return self.compras["valor_total"].sum()
        return 0.0

    def get_margem_bruta_estimada(self):
        if self.vendas.empty or self.produtos.empty:
            return 0.0
        if "custo_unitario" not in self.produtos.columns or "quantidade_vendida" not in self.vendas.columns:
            return 0.0

        receita = self.vendas["valor_total"].sum()
        custo_estimado = self.produtos["custo_unitario"].mean() * self.vendas["quantidade_vendida"].sum()
        return receita - custo_estimado

    # ===========================================================
    # ====== RELOAD =============================================
    # ===========================================================
    def reload_data(self):
        self.__init__()