"""
dados.py — leitura e cálculos sobre PIB e população (IBGE). Só pandas, sem Streamlit.

Base: dados/pib_municipios_2021.csv (1 linha por município), dados/pib_uf_serie.csv (PIB por UF, 2002-2023)
e dados/br_uf_contornos.geojson (limites dos estados). Veja dados/FONTES.md e `python baixar_dados.py`.

REGRA DE OURO: PIB per capita de qualquer agregado (UF, região, Brasil) = SOMA do PIB ÷ SOMA da população.
Nunca a média dos PIBs per capita dos municípios (um município minúsculo pesaria como uma metrópole).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).parent / "dados"
CSV_MUNICIPIOS = PASTA / "pib_municipios_2021.csv"
CSV_UF = PASTA / "pib_uf_serie.csv"
GEOJSON_UF = PASTA / "br_uf_contornos.geojson"
ANO = 2021
SETORES = {"vab_agropecuaria": "Agropecuária", "vab_industria": "Indústria",
           "vab_servicos": "Serviços", "vab_adm_publica": "Adm. pública"}


@dataclass
class Dados:
    mun: pd.DataFrame       # 1 linha por município (2021)
    uf: pd.DataFrame        # 1 linha por UF (2021), agregada por razão de somas
    serie: pd.DataFrame     # PIB por UF, ano a ano (nominal)
    contornos: dict         # GeoJSON dos estados com properties.sigla_uf


def carregar() -> Dados:
    if not (CSV_MUNICIPIOS.exists() and CSV_UF.exists() and GEOJSON_UF.exists()):
        raise FileNotFoundError("Dados não encontrados em dados/. Rode antes:  python baixar_dados.py")
    mun = pd.read_csv(CSV_MUNICIPIOS, dtype={"id_municipio": str})
    mun["pib_per_capita"] = mun["pib_mil_reais"] * 1000 / mun["populacao"]          # R$ por habitante
    mun["densidade"] = mun["populacao"] / mun["area_km2"]                           # hab/km²

    serie = pd.read_csv(CSV_UF, dtype={"cod_uf": str})
    cod_para_sigla = (mun.assign(cod_uf=mun["id_municipio"].str[:2]).drop_duplicates("cod_uf")
                      .set_index("cod_uf")["sigla_uf"])
    serie["sigla_uf"] = serie["cod_uf"].map(cod_para_sigla)
    serie["pib_bi"] = serie["pib_mil_reais"] / 1e6

    contornos = json.loads(GEOJSON_UF.read_text(encoding="utf-8"))
    for f in contornos["features"]:
        f["properties"]["sigla_uf"] = cod_para_sigla[f["properties"]["codarea"]]
    return Dados(mun=mun, uf=agregar(mun, ["sigla_uf", "regiao"], serie), serie=serie, contornos=contornos)


def agregar(mun: pd.DataFrame, chaves: list[str], serie: pd.DataFrame | None = None) -> pd.DataFrame:
    """Soma PIB, população e setores; per capita = razão de somas. Com `serie`, traz o nome completo da UF."""
    soma = mun.groupby(chaves).agg(populacao=("populacao", "sum"), pib_mil_reais=("pib_mil_reais", "sum"),
                                   **{c: (c, "sum") for c in SETORES}).reset_index()
    soma["pib_bi"] = soma["pib_mil_reais"] / 1e6
    soma["pib_per_capita"] = soma["pib_mil_reais"] * 1000 / soma["populacao"]
    soma["participacao"] = soma["pib_mil_reais"] / soma["pib_mil_reais"].sum() * 100
    if serie is not None and "sigla_uf" in chaves:
        nomes = serie.drop_duplicates("sigla_uf").set_index("sigla_uf")["uf"]
        soma.insert(1, "uf", soma["sigla_uf"].map(nomes))
    return soma


def participacao_setores(uf: pd.DataFrame) -> pd.DataFrame:
    """% de cada setor no valor adicionado de cada UF. Negativos (1 município da base) contam como 0."""
    v = uf[list(SETORES)].clip(lower=0)
    return (v.div(v.sum(axis=1), axis=0) * 100).rename(columns=SETORES).set_index(uf["sigla_uf"])


# ----------------------------------------------------------------------------
# FORMATAÇÃO (pt-BR)
# ----------------------------------------------------------------------------
def inteiro(v: float) -> str:
    return f"{int(round(v)):,}".replace(",", ".")


def decimal(v: float, casas: int = 1) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def reais_bi(v: float) -> str:
    """R$ 2.720 bi (sem casas a partir de 100 bi) — v em bilhões."""
    return f"R$ {inteiro(v)} bi" if v >= 100 else f"R$ {decimal(v, 1)} bi"


def reais_mil(v: float) -> str:
    """R$ 23 mil (v em reais)."""
    return f"R$ {inteiro(v / 1000)} mil"


def pct(v: float, casas: int = 1) -> str:
    return f"{decimal(v, casas)}%"
