import pandas as pd
import os

class PurchasesController:
    def __init__(self):
        self.data_dir = "data"
        self.comprasDf = pd.DataFrame()
        self.produtosDf = pd.DataFrame()
        self.fornecedoresDf = pd.DataFrame()
        self.load_data()

    # -----------------------------
    # Carrega todos os arquivos CSV
    # -----------------------------
    def load_data(self):
        try:
            compras_path = os.path.join(self.data_dir, "compras.csv")
            produtos_path = os.path.join(self.data_dir, "produtos.csv")
            fornecedores_path = os.path.join(self.data_dir, "fornecedores.csv")

            if os.path.exists(compras_path):
                self.comprasDf = pd.read_csv(compras_path, sep=",", encoding="utf-8")
            if os.path.exists(produtos_path):
                self.produtosDf = pd.read_csv(produtos_path, sep=",", encoding="utf-8")
            if os.path.exists(fornecedores_path):
                self.fornecedoresDf = pd.read_csv(fornecedores_path, sep=",", encoding="utf-8")

            self._merge_data()
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")

    # -----------------------------
    # Recarrega os dados após upload
    # -----------------------------
    def reload_data(self):
        self.load_data()

    # -----------------------------
    # Faz merge entre tabelas
    # -----------------------------
    def _merge_data(self):
        if self.comprasDf.empty:
            return

        df = self.comprasDf.copy()

        # Merge com produtos
        if not self.produtosDf.empty:
            df = df.merge(
                self.produtosDf[["produto_id", "produto_nome", "categoria", "marca"]],
                on="produto_id",
                how="left"
            )

        # Merge com fornecedores
        if not self.fornecedoresDf.empty:
            # Normaliza o nome da coluna antes de merge
            df["fornecedor"] = df["fornecedor"].astype(str)
            self.fornecedoresDf["nome_fornecedor"] = self.fornecedoresDf["nome_fornecedor"].astype(str)

            df = df.merge(
                self.fornecedoresDf,
                left_on="fornecedor",
                right_on="nome_fornecedor",
                how="left"
            )

        # Converte datas
        if "data_compra" in df.columns:
            df["data_compra"] = pd.to_datetime(df["data_compra"], errors="coerce")

        self.comprasDf = df

    # -----------------------------
    # Filtra dados
    # -----------------------------
    def filter_data(self, fornecedores=None, produtos=None, start=None, end=None):
        df = self.comprasDf.copy()

        if df.empty:
            return df

        if fornecedores:
            df = df[df["fornecedor"].isin(fornecedores)]

        if produtos:
            df = df[df["produto_nome"].isin(produtos)]

        if start is not None:
            df = df[df["data_compra"] >= start]

        if end is not None:
            df = df[df["data_compra"] <= end]

        return df

    # -----------------------------
    # Total gasto
    # -----------------------------
    def get_total_spent(self, df):
        if "valor_total" in df.columns and not df.empty:
            return df["valor_total"].sum()
        return 0.0

    # -----------------------------
    # Comparativo entre fornecedores
    # -----------------------------
    def get_supplier_comparative(self, df):
        if df.empty:
            return pd.DataFrame()

        cols = ["fornecedor", "valor_unitario", "prazo_entrega_dias", "valor_total"]
        for c in cols:
            if c not in df.columns:
                return pd.DataFrame()

        comp = (
            df.groupby("fornecedor")
            .agg({
                "valor_unitario": "mean",
                "prazo_entrega_dias": "mean",
                "valor_total": "sum"
            })
            .reset_index()
        )
        comp.rename(columns={
            "valor_unitario": "preco_medio",
            "prazo_entrega_dias": "prazo_medio",
            "valor_total": "gasto_total"
        }, inplace=True)

        return comp

    # -----------------------------
    # Volume de compras mensal
    # -----------------------------
    def get_monthly_volume(self, df):
        if df.empty or "data_compra" not in df.columns:
            return pd.DataFrame()

        ts = (
            df.groupby(df["data_compra"].dt.to_period("M"))
            .agg({"valor_total": "sum"})
            .reset_index()
        )
        ts["data_compra"] = ts["data_compra"].dt.to_timestamp()
        return ts

    # -----------------------------
    # Top produtos por gasto
    # -----------------------------
    def get_top_products_by_spend(self, df, top=10):
        if df.empty or "valor_total" not in df.columns:
            return pd.DataFrame()

        top_df = (
            df.groupby("produto_nome")
            .agg({"valor_total": "sum"})
            .reset_index()
            .sort_values("valor_total", ascending=False)
            .head(top)
        )
        top_df.rename(columns={"valor_total": "gasto_total"}, inplace=True)
        return top_df
