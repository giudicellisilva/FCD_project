# controllers/inventoryController.py
import pandas as pd
from models.dataModel import loadProdutos, loadEstoque

class InventoryController:
    def __init__(self):
        self.reloadData()

    def reloadData(self):
        """Recarrega os dados brutos de produtos e estoque."""
        self.produtos = loadProdutos()
        self.estoque = loadEstoque()

    def getLatestStockPerProduct(self) -> pd.DataFrame:
        """Retorna o último registro de estoque por produto."""
        dfEst = self.estoque.copy()

        # Caso o CSV esteja vazio
        if dfEst.empty:
            return pd.DataFrame(columns=["produto_id", "quantidade_estoque", "estoque_minimo"])

        # Normaliza nomes de colunas
        dfEst.columns = dfEst.columns.str.strip().str.lower()

        # Se tiver data, pega o registro mais recente
        if "data_referencia" in dfEst.columns and dfEst["data_referencia"].notna().any():
            dfEst = (
                dfEst.sort_values("data_referencia")
                .groupby("produto_id", as_index=False)
                .last()
            )
        else:
            # fallback: agrupa somando as quantidades
            grouped = (
                dfEst.groupby("produto_id", as_index=False)
                .agg({
                    "quantidade_estoque": "sum",
                    "estoque_minimo": "max"
                })
                .reset_index(drop=True)
            )
            dfEst = grouped

        # Garante colunas essenciais
        for c in ["quantidade_estoque", "estoque_minimo"]:
            if c not in dfEst.columns:
                dfEst[c] = 0

        return dfEst[["produto_id", "quantidade_estoque", "estoque_minimo"]]

    def buildInventoryView(self) -> pd.DataFrame:
        """Constrói a tabela consolidada de inventário."""
        produtos = self.produtos.copy()
        estoqueLatest = self.getLatestStockPerProduct()

        # Caso algum CSV esteja vazio
        if produtos.empty or estoqueLatest.empty:
            return pd.DataFrame(columns=[
                "produtoId", "produtoNome", "categoria",
                "quantidadeEstoque", "estoqueMinimo",
                "precoUnitario", "valorTotal"
            ])

        # Normaliza nomes de colunas
        produtos.columns = produtos.columns.str.strip().str.lower()

        # Mapeia colunas
        colmap = {}
        colsLower = list(produtos.columns)

        # === Identificação do produto ===
        if "produto_id" in colsLower:
            colmap["produto_id"] = "produto_id"
        elif "produtoid" in colsLower:
            colmap["produto_id"] = "produtoid"
        elif "id" in colsLower:
            colmap["produto_id"] = "id"

        # === Nome do produto ===
        if "produto_nome" in colsLower:
            colmap["produto_nome"] = "produto_nome"
        elif "produto nome" in colsLower:
            colmap["produto_nome"] = "produto nome"
        elif "produto" in colsLower:
            colmap["produto_nome"] = "produto"

        # === Categoria ===
        if "categoria" in colsLower:
            colmap["categoria"] = "categoria"

        # === Preço ===
        if "preco_unitario" in colsLower:
            colmap["preco_unitario"] = "preco_unitario"
        elif "preço_unitario" in colsLower:
            colmap["preco_unitario"] = "preço_unitario"
        elif "preco" in colsLower:
            colmap["preco_unitario"] = "preco"

        # === SKU ===
        if "sku" in colsLower:
            colmap["sku"] = "sku"

        produtos = produtos.rename(columns={v: k for k, v in colmap.items()})

        # Verificação mínima
        if "produto_id" not in produtos.columns:
            print("⚠️ Nenhuma coluna identificada como 'produto_id' no CSV de produtos.")
            produtos["produto_id"] = range(1, len(produtos) + 1)

        # === Merge produtos + estoque ===
        inv = produtos.merge(estoqueLatest, how="left", on="produto_id")

        # Preencher valores ausentes
        inv["quantidade_estoque"] = inv.get("quantidade_estoque", pd.Series([0]*len(inv))).fillna(0).astype(float)
        inv["estoque_minimo"] = inv.get("estoque_minimo", pd.Series([0]*len(inv))).fillna(0).astype(float)

        if "preco_unitario" not in inv.columns:
            inv["preco_unitario"] = 0.0
        inv["preco_unitario"] = pd.to_numeric(inv["preco_unitario"], errors="coerce").fillna(0.0)

        # Calcula valor total
        inv["valor_total"] = inv["quantidade_estoque"] * inv["preco_unitario"]

        # Renomeia colunas para padrão camelCase
        inv = inv.rename(columns={
            "produto_id": "produtoId",
            "produto_nome": "produtoNome",
            "categoria": "categoria",
            "quantidade_estoque": "quantidadeEstoque",
            "estoque_minimo": "estoqueMinimo",
            "preco_unitario": "precoUnitario",
            "valor_total": "valorTotal"
        })

        # Se não tiver nome de produto, usa o SKU ou o ID
        if "produtoNome" not in inv.columns:
            if "sku" in inv.columns:
                inv["produtoNome"] = inv["sku"]
            else:
                inv["produtoNome"] = inv["produtoId"].astype(str)

        return inv

    def filterByCategory(self, inventoryDf: pd.DataFrame, categories: list) -> pd.DataFrame:
        """Filtra o inventário por categoria."""
        if inventoryDf.empty:
            return inventoryDf
        if not categories:
            return inventoryDf
        return inventoryDf[inventoryDf["categoria"].isin(categories)]
