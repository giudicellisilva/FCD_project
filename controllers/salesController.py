import pandas as pd

class SalesController:
    def __init__(self):
        self.vendasDf = pd.DataFrame()
        self.produtosDf = pd.DataFrame()
        self.reloadData()

    def reloadData(self):
        # Ler vendas.csv
        try:
            self.vendasDf = pd.read_csv("data/vendas.csv")
            if not self.vendasDf.empty:
                # Renomear colunas para padrão interno
                rename_map = {
                    "data_venda": "data",
                    "produto_id": "produtoId",
                    "loja_id": "loja",
                    "quantidade_vendida": "quantidadeVendida",
                    "valor_unitario": "precoUnitario",
                    "valor_total": "valorTotal"
                }
                self.vendasDf.rename(columns=rename_map, inplace=True)

                # Converte data para datetime
                if "data" in self.vendasDf.columns:
                    self.vendasDf["data"] = pd.to_datetime(self.vendasDf["data"], errors="coerce")
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self.vendasDf = pd.DataFrame(columns=[
                "data", "loja", "produtoId", "quantidadeVendida", "precoUnitario", "valorTotal"
            ])

        # Ler produtos.csv
        try:
            self.produtosDf = pd.read_csv("data/produtos.csv")
            if not self.produtosDf.empty:
                rename_map_prod = {
                    "produto_id": "produtoId",
                    "produto_nome": "produtoNome",
                    "preco_unitario": "precoUnitario"
                }
                self.produtosDf.rename(columns=rename_map_prod, inplace=True)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            self.produtosDf = pd.DataFrame(columns=["produtoId", "produtoNome", "precoUnitario"])

        # Merge e cálculo do valor total somente se ambas as colunas existirem
        if not self.vendasDf.empty and not self.produtosDf.empty and "produtoId" in self.vendasDf.columns and "produtoId" in self.produtosDf.columns:
            self.vendasDf = self.vendasDf.merge(self.produtosDf, on="produtoId", how="left")
            if "valorTotal" not in self.vendasDf.columns:
                self.vendasDf["valorTotal"] = self.vendasDf["quantidadeVendida"] * self.vendasDf["precoUnitario"]
        else:
            self.vendasDf = pd.DataFrame(columns=[
                "data", "loja", "produtoId", "produtoNome",
                "quantidadeVendida", "precoUnitario", "valorTotal"
            ])


    def filterData(self, lojas=None, produtos=None, startDate=None, endDate=None):
        if self.vendasDf.empty:
            return pd.DataFrame(columns=self.vendasDf.columns)
        df = self.vendasDf.copy()
        if lojas:
            df = df[df["loja"].isin(lojas)]
        if produtos:
            df = df[df["produtoNome"].isin(produtos)]
        if startDate:
            df = df[df["data"] >= startDate]
        if endDate:
            df = df[df["data"] <= endDate]
        return df

    def getTopProducts(self, df, top=10):
        if df.empty:
            return pd.DataFrame(columns=["produtoNome", "quantidadeVendida"])
        return df.groupby("produtoNome")["quantidadeVendida"].sum().sort_values(ascending=False).head(top).reset_index()

    def getRevenue(self, df):
        return df["valorTotal"].sum() if not df.empty else 0

    def getTimeSeries(self, df):
        if df.empty:
            return pd.DataFrame(columns=["data", "quantidadeVendida"])
        return df.groupby(pd.Grouper(key="data", freq="M"))["quantidadeVendida"].sum().reset_index()
