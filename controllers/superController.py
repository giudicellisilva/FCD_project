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

    # =========================================================
    # ================ Carregamento de Dados ==================
    # =========================================================
    def load_csv(self, filename):
        """Carrega um CSV de forma robusta, detectando separador e limpando nomes de colunas."""
        filepath = os.path.join(self.data_path, filename)
        if not os.path.exists(filepath):
            print(f"⚠️ Arquivo {filename} não encontrado.")
            return pd.DataFrame()

        try:
            # Detecta separador
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = f.readline()
                sep = ";" if first_line.count(";") > first_line.count(",") else ","

            df = pd.read_csv(filepath, sep=sep, encoding="utf-8")

            # Se veio tudo em uma coluna só, tenta corrigir
            if len(df.columns) == 1:
                if ";" in df.columns[0]:
                    df = pd.read_csv(filepath, sep=";", encoding="utf-8")
                elif "," in df.columns[0]:
                    df = pd.read_csv(filepath, sep=",", encoding="utf-8")

            # Normaliza nomes das colunas
            df.columns = df.columns.str.strip().str.lower()

            # Correção de nomes alternativos
            rename_map = {
                "nome_produto": "produto_nome",
                "produto": "produto_nome",
                "produto nome": "produto_nome",
                "qtd_estoque": "quantidade_estoque",
                "estoque": "quantidade_estoque",
                "qtd_vendida": "quantidade_vendida",
                "qtd_comprada": "quantidade_comprada"
            }
            df.rename(columns=rename_map, inplace=True)

            return df

        except Exception as e:
            print(f"❌ Erro ao carregar {filename}: {e}")
            return pd.DataFrame()

    def load_data(self):
        """Carrega todos os CSVs da pasta data se existirem."""
        self.vendasDf = self.load_csv("vendas.csv")
        self.comprasDf = self.load_csv("compras.csv")
        self.produtosDf = self.load_csv("produtos.csv")
        self.estoqueDf = self.load_csv("estoque.csv")

        # Conversão de colunas de data (se existirem)
        date_columns = {
            "vendas.csv": ("data_venda", self.vendasDf),
            "compras.csv": ("data_compra", self.comprasDf),
            "estoque.csv": ("data_referencia", self.estoqueDf)
        }

        for fname, (col, df) in date_columns.items():
            if not df.empty and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                print(f"⚠️ Nenhuma coluna de data encontrada em {fname}")

    def reload_data(self):
        """Recarrega todos os CSVs."""
        self.load_data()

    # =========================================================
    # ===================== MÉTRICAS ==========================
    # =========================================================
    def get_total_revenue(self, vendas):
        return vendas["valor_total"].sum() if not vendas.empty and "valor_total" in vendas.columns else 0

    def get_total_purchases(self, compras):
        return compras["valor_total"].sum() if not compras.empty and "valor_total" in compras.columns else 0

    def get_total_stock_value(self, produtos, estoque):
        if estoque.empty or produtos.empty:
            return 0
        if "produto_id" not in estoque.columns or "produto_id" not in produtos.columns:
            return 0
        merged = estoque.merge(produtos, on="produto_id", how="left")
        if "quantidade_estoque" not in merged.columns or "custo_unitario" not in merged.columns:
            return 0
        merged["valor_estoque"] = merged["quantidade_estoque"] * merged["custo_unitario"]
        return merged["valor_estoque"].sum()

    def get_stock_status(self, estoque):
        if estoque.empty or "quantidade_estoque" not in estoque.columns or "estoque_minimo" not in estoque.columns:
            return pd.DataFrame()
        return estoque[estoque["quantidade_estoque"] < estoque["estoque_minimo"]]

    # =========================================================
    # ===================== GRÁFICOS ==========================
    # =========================================================
    def get_sales_trend(self, vendas):
        if vendas.empty or "data_venda" not in vendas.columns or "valor_total" not in vendas.columns:
            return pd.DataFrame()
        return vendas.groupby(vendas["data_venda"].dt.to_period("M"))["valor_total"].sum().reset_index().rename(columns={"data_venda": "Mês"})

    def get_purchase_trend(self, compras):
        if compras.empty or "data_compra" not in compras.columns or "valor_total" not in compras.columns:
            return pd.DataFrame()
        return compras.groupby(compras["data_compra"].dt.to_period("M"))["valor_total"].sum().reset_index().rename(columns={"data_compra": "Mês"})

    def get_top_products(self, vendas, produtos, n=10):
        if vendas.empty or "produto_id" not in vendas.columns or "quantidade_vendida" not in vendas.columns:
            return pd.DataFrame()
        agg = vendas.groupby("produto_id")["quantidade_vendida"].sum().reset_index()
        merged = agg.merge(produtos, on="produto_id", how="left")
        if "produto_nome" not in merged.columns:
            merged["produto_nome"] = merged["produto_id"].astype(str)
        return merged.nlargest(n, "quantidade_vendida")[["produto_nome", "quantidade_vendida"]]

    def get_critical_products(self, produtos, estoque):
        if estoque.empty or "quantidade_estoque" not in estoque.columns or "estoque_minimo" not in estoque.columns:
            return pd.DataFrame()
        merged = estoque.merge(produtos, on="produto_id", how="left")
        if "produto_nome" not in merged.columns:
            merged["produto_nome"] = merged["produto_id"].astype(str)
        return merged[merged["quantidade_estoque"] < merged["estoque_minimo"]][
            ["produto_nome", "quantidade_estoque", "estoque_minimo"]
        ]