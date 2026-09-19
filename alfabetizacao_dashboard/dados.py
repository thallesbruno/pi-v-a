"""
dados.py — camada de dados do projeto: Alfabetização no Censo 2022 (IBGE)

Duas tabelas, ligadas pela chave id_municipio (código IBGE de 7 dígitos):
  • FATO      br_ibge_censo_2022_alfabetizacao_grupo_idade_sexo_raca.csv
              1 linha = 1 combinação (município × cor/raça × sexo × faixa etária × alfabetização)
              medida  = populacao (pessoas de 15 anos ou mais)
  • DIMENSÃO  br_bd_diretorios_brasil_municipio.csv
              nome do município, UF, região e centroide (latitude/longitude)

Responsabilidades deste módulo (tudo o que NÃO é interface):
  1. ler os CSVs e tratá-los (tipos, nulos, chaves)
  2. ligar fato e dimensão (join)
  3. calcular KPIs e agregações para os gráficos

Separar dados de interface é a ideia central de BI: o mesmo módulo alimenta o
Streamlit hoje e qualquer outra ferramenta amanhã.

LIÇÃO CENTRAL DESTA BASE: a tabela já vem AGREGADA (contagens de pessoas). Logo,
taxa = soma(numerador) ÷ soma(denominador). NUNCA tire a média das linhas.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------
PASTA = Path(__file__).parent / "dados"
CSV_CENSO = PASTA / "br_ibge_censo_2022_alfabetizacao_grupo_idade_sexo_raca.csv"
CSV_MUNICIPIO = PASTA / "br_bd_diretorios_brasil_municipio.csv"
PARQUET_FATO = PASTA / "cache_fato.parquet"
PARQUET_DIM = PASTA / "cache_municipios.parquet"

ALFABETIZADAS = "Alfabetizadas"
NAO_ALFABETIZADAS = "Não alfabetizadas"
IDOSOS = "65 anos ou mais"
ORDEM_IDADE = ["15 a 19 anos", "20 a 24 anos", "25 a 34 anos", "35 a 44 anos",
               "45 a 54 anos", "55 a 64 anos", IDOSOS]
COLUNAS_CENSO = ["id_municipio", "cor_raca", "sexo", "grupo_idade", "alfabetizacao", "populacao"]
COLUNAS_MUNICIPIO = ["id_municipio", "nome", "sigla_uf", "nome_uf", "nome_regiao", "centroide"]


# ----------------------------------------------------------------------------
# LEITURA E TRATAMENTO
# ----------------------------------------------------------------------------
def arquivos_disponiveis() -> list[Path]:
    return [p for p in (CSV_CENSO, CSV_MUNICIPIO) if not p.exists()]


def _validar_arquivos() -> None:
    faltando = arquivos_disponiveis()
    if faltando:
        nomes = "\n  - ".join(str(p.name) for p in faltando)
        raise FileNotFoundError(
            f"Arquivos não encontrados em '{PASTA}':\n  - {nomes}\n"
            "Coloque os dois CSVs na pasta 'dados/' (veja `python preparar_dados.py`)."
        )


def _ler_fato() -> pd.DataFrame:
    df = pd.read_csv(CSV_CENSO, dtype={"id_municipio": str, "cor_raca": "category", "sexo": "category",
                                       "grupo_idade": "category", "alfabetizacao": "category"})
    faltam = [c for c in COLUNAS_CENSO if c not in df.columns]
    if faltam:
        raise ValueError(f"Colunas ausentes no censo: {faltam}. Encontradas: {list(df.columns)}")
    # DECISÃO DE TRATAMENTO: população nula = nenhuma pessoa naquela combinação (zero).
    # Validado: com nulo=0 o Brasil fecha em 162,9 mi de pessoas e 7,0% de analfabetismo,
    # o mesmo divulgado pelo IBGE.
    df["populacao"] = df["populacao"].fillna(0).astype("int32")
    df["grupo_idade"] = pd.Categorical(df["grupo_idade"], categories=ORDEM_IDADE, ordered=True)
    return df[COLUNAS_CENSO]


def _ler_municipios() -> pd.DataFrame:
    d = pd.read_csv(CSV_MUNICIPIO, dtype=str, usecols=COLUNAS_MUNICIPIO)
    coords = d["centroide"].str.extract(r"POINT\(\s*(-?[\d.]+)\s+(-?[\d.]+)\s*\)").astype(float)
    d["lon"], d["lat"] = coords[0], coords[1]
    d = d.rename(columns={"nome": "municipio", "nome_uf": "uf", "nome_regiao": "regiao"})
    return d.drop(columns="centroide")


def carregar_municipios() -> pd.DataFrame:
    """Dimensão município (1 linha por município, com lat/lon do centroide)."""
    _validar_arquivos()
    if PARQUET_DIM.exists() and PARQUET_DIM.stat().st_mtime >= CSV_MUNICIPIO.stat().st_mtime:
        try:
            return pd.read_parquet(PARQUET_DIM)
        except Exception:
            pass
    d = _ler_municipios()
    try:
        d.to_parquet(PARQUET_DIM, index=False)
    except Exception:
        pass
    return d


def carregar() -> pd.DataFrame:
    """Fato já ligada à dimensão: uma tabela larga pronta para filtrar e agregar."""
    _validar_arquivos()
    mais_novo = max(CSV_CENSO.stat().st_mtime, CSV_MUNICIPIO.stat().st_mtime)
    if PARQUET_FATO.exists() and PARQUET_FATO.stat().st_mtime >= mais_novo:
        try:
            return pd.read_parquet(PARQUET_FATO)
        except Exception:
            pass

    fato = _ler_fato()
    dim = carregar_municipios()[["id_municipio", "municipio", "sigla_uf", "uf", "regiao"]]
    df = fato.merge(dim, on="id_municipio", how="left", validate="many_to_one")
    sem_par = int(df["municipio"].isna().sum())
    if sem_par:
        raise ValueError(f"{sem_par} linhas do censo sem município correspondente no diretório.")
    for c in ["municipio", "sigla_uf", "uf", "regiao"]:
        df[c] = df[c].astype("category")
    try:
        df.to_parquet(PARQUET_FATO, index=False)
    except Exception:
        pass
    return df


# ----------------------------------------------------------------------------
# BLOCOS DE CÁLCULO (todas as taxas são razões de somas)
# ----------------------------------------------------------------------------
def _pop(df: pd.DataFrame) -> int:
    return int(df["populacao"].sum())


def _nao_alf(df: pd.DataFrame) -> int:
    return int(df.loc[df["alfabetizacao"] == NAO_ALFABETIZADAS, "populacao"].sum())


def taxa_analfabetismo(df: pd.DataFrame) -> float | None:
    """% de pessoas não alfabetizadas = não alfabetizadas ÷ total × 100."""
    total = _pop(df)
    return None if total == 0 else _nao_alf(df) / total * 100


def kpis(df: pd.DataFrame) -> dict:
    total = _pop(df)
    nao = _nao_alf(df)
    taxa = None if total == 0 else nao / total * 100

    tx_h = taxa_analfabetismo(df[df["sexo"] == "Homens"])
    tx_m = taxa_analfabetismo(df[df["sexo"] == "Mulheres"])
    tx_pp = taxa_analfabetismo(df[df["cor_raca"].isin(["Preta", "Parda"])])
    tx_br = taxa_analfabetismo(df[df["cor_raca"] == "Branca"])

    return {
        "populacao": total,
        "taxa_alfabetizacao": None if taxa is None else 100 - taxa,
        "nao_alfabetizadas": nao,
        "gap_sexo_pp": None if tx_h is None or tx_m is None else tx_h - tx_m,
        "razao_racial": None if not tx_br or tx_pp is None else tx_pp / tx_br,
        "analfabetismo_65": taxa_analfabetismo(df[df["grupo_idade"] == IDOSOS]),
    }


def por_dimensao(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """População, não alfabetizadas e taxa (%) por categoria de `coluna`."""
    base = df.assign(nao=df["populacao"].where(df["alfabetizacao"] == NAO_ALFABETIZADAS, 0))
    g = base.groupby(coluna, observed=True).agg(populacao=("populacao", "sum"), nao_alfabetizadas=("nao", "sum"))
    g = g.reset_index()
    g[coluna] = g[coluna].astype(str)
    g["taxa_analfabetismo"] = np.where(g["populacao"] > 0, g["nao_alfabetizadas"] / g["populacao"] * 100, np.nan)
    return g


def composicao_alfabetizacao(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("alfabetizacao", observed=True)["populacao"].sum().reset_index()
    g["alfabetizacao"] = g["alfabetizacao"].astype(str)
    return g


def nao_alfabetizadas_por(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    g = (df[df["alfabetizacao"] == NAO_ALFABETIZADAS].groupby(coluna, observed=True)["populacao"].sum()
         .reset_index().rename(columns={"populacao": "nao_alfabetizadas"}))
    g[coluna] = g[coluna].astype(str)
    return g


def tabela_municipal(df: pd.DataFrame, dim_municipios: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por município: população, não alfabetizadas, taxa e coordenadas (para ranking e mapa)."""
    base = df.assign(nao=df["populacao"].where(df["alfabetizacao"] == NAO_ALFABETIZADAS, 0))
    g = base.groupby("id_municipio", observed=True).agg(populacao=("populacao", "sum"), nao_alfabetizadas=("nao", "sum"))
    g = g.reset_index()
    g["taxa_analfabetismo"] = np.where(g["populacao"] > 0, g["nao_alfabetizadas"] / g["populacao"] * 100, np.nan)
    return g.merge(dim_municipios, on="id_municipio", how="left")


# ----------------------------------------------------------------------------
# FORMATAÇÃO (pt-BR)
# ----------------------------------------------------------------------------
def formatar_int(v: float | int) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


def formatar_pct(v: float | None, casas: int = 1) -> str:
    return "—" if v is None else f"{v:.{casas}f}%".replace(".", ",")


def formatar_num(v: float | None, casas: int = 1, sufixo: str = "") -> str:
    return "—" if v is None else f"{v:.{casas}f}".replace(".", ",") + sufixo
