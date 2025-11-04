import pandas as pd
import os

class SuperDashboardController:
    def __init__(self):
        self.data_path = "data/"
        self.vendasDf = pd.DataFrame()
        self.comprasDf = pd.DataFrame()
        self.produtosDf = pd.DataFrame()
        self.estoqueDf = pd.DataFrame()
        self.load_data()

    def load_data(self):
        """Carrega todos os CSVs da pasta data se existirem."""
        try:
            self.vendasDf = pd.read_csv(os.path.join(self.data_path, "vendas.csv"), sep=";")
            self.comprasDf = pd.read_csv(os.path.join(self.data_path, "compras.csv"), sep=";")
            self.produtosDf = pd.read_csv(os.path.join(self.data_path, "produtos.csv"), sep=";")
            self.estoqueDf = pd.read_csv(os.path.join(self.data_path, "estoque.csv"), sep=";")

            # Tratamentos básicos
            for df, col in [(self.vendasDf, "data_venda"), (self.comprasDf, "data_compra"), (self.estoqueDf, "data_referencia")]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        except FileNotFoundError:
            print("❌ Um ou mais arquivos não foram encontrados na pasta data.")

    def reload_data(self):
        self.load_data()

    # ===============================
    # ====== Funções de Métricas =====
    # ===============================
    def get_total_revenue(self, vendas):
        return vendas["valor_total"].sum() if not vendas.empty else 0

    def get_total_purchases(self, compras):
        return compras["valor_total"].sum() if not compras.empty else 0

    def get_total_stock_value(self, produtos, estoque):
        if estoque.empty or produtos.empty:
            return 0
        merged = estoque.merge(produtos, on="produto_id", how="left")
        merged["valor_estoque"] = merged["quantidade_estoque"] * merged["custo_unitario"]
        return merged["valor_estoque"].sum()

    def get_stock_status(self, estoque):
        return estoque[estoque["quantidade_estoque"] < estoque["estoque_minimo"]]

    # ===============================
    # ====== Funções de Gráficos =====
    # ===============================
    def get_sales_trend(self, vendas):
        if vendas.empty:
            return pd.DataFrame()
        return vendas.groupby(vendas["data_venda"].dt.to_period("M"))["valor_total"].sum().reset_index().rename(columns={"data_venda":"Mês"})

    def get_purchase_trend(self, compras):
        if compras.empty:
            return pd.DataFrame()
        return compras.groupby(compras["data_compra"].dt.to_period("M"))["valor_total"].sum().reset_index().rename(columns={"data_compra":"Mês"})

    def get_top_products(self, vendas, produtos, n=10):
        if vendas.empty:
            return pd.DataFrame()
        agg = vendas.groupby("produto_id")["quantidade_vendida"].sum().reset_index()
        merged = agg.merge(produtos, on="produto_id", how="left")
        return merged.nlargest(n, "quantidade_vendida")[["produto_nome", "quantidade_vendida"]]

    def get_critical_products(self, produtos, estoque):
        if estoque.empty:
            return pd.DataFrame()
        merged = estoque.merge(produtos, on="produto_id", how="left")
        return merged[merged["quantidade_estoque"] < merged["estoque_minimo"]][["produto_nome", "quantidade_estoque", "estoque_minimo"]]
