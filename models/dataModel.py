import pandas as pd
from pathlib import Path

dataDir = Path("data")

def _try_read_csv(path: Path) -> pd.DataFrame:
    # tenta com separador padrão, se falhar tenta tab
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, sep="\t", engine="python")

def loadClientes() -> pd.DataFrame:
    p = dataDir / "clientes.csv"
    return _try_read_csv(p) if p.exists() else pd.DataFrame()

def loadEstoque() -> pd.DataFrame:
    p = dataDir / "estoque.csv"
    if not p.exists():
        return pd.DataFrame()
    df = _try_read_csv(p)
    if "data_referencia" in df.columns:
        df["data_referencia"] = pd.to_datetime(df["data_referencia"], errors="coerce")
    return df

def loadCompras() -> pd.DataFrame:
    p = dataDir / "compras.csv"
    return _try_read_csv(p) if p.exists() else pd.DataFrame()

def loadLogistica() -> pd.DataFrame:
    p = dataDir / "logistica.csv"
    return _try_read_csv(p) if p.exists() else pd.DataFrame()

def loadProdutos() -> pd.DataFrame:
    p = dataDir / "produtos.csv"
    if not p.exists():
        return pd.DataFrame()
    df = _try_read_csv(p)
    # limpa cabeçalhos
    df.columns = [c.strip() for c in df.columns]
    return df

def loadVendas() -> pd.DataFrame:
    p = dataDir / "vendas.csv"
    return _try_read_csv(p) if p.exists() else pd.DataFrame()