"""
baixar_dados.py — baixa PIB e população do IBGE (API SIDRA, sem chave) e grava CSVs tratados em dados/.

Uso:  python baixar_dados.py            (não baixa de novo o que já existe)
      python baixar_dados.py --forcar   (baixa tudo outra vez)

Gera em dados/:
  pib_municipios_2021.csv   1 linha por município: PIB, valor adicionado por setor, população e área
  pib_uf_serie.csv          PIB por UF, ano a ano (2002 em diante), a preços correntes
  br_uf_contornos.geojson   limites dos 27 estados (malha do IBGE), para o mapa

Por que 2021? É o último ano com o valor adicionado por setor divulgado para todos os municípios
(em 2022 e 2023 o IBGE só publicou o PIB total). Fontes e tabelas: dados/FONTES.md.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).parent / "dados"
ANO = 2021
SIDRA = "https://apisidra.ibge.gov.br/values"
URL_PIB_MUN = f"{SIDRA}/t/5938/n6/all/v/37,513,517,6575,525/p/{ANO}?formato=json"
URL_POP_MUN = f"{SIDRA}/t/6579/n6/all/v/9324/p/{ANO}?formato=json"
URL_AREA_MUN = f"{SIDRA}/t/4714/n6/all/v/6318/p/2022?formato=json"
URL_PIB_UF = f"{SIDRA}/t/5938/n3/all/v/37/p/all?formato=json"
URL_CONTORNOS = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
                 "?intrarregiao=UF&formato=application/vnd.geo+json&qualidade=intermediaria")

CSV_MUNICIPIOS = PASTA / f"pib_municipios_{ANO}.csv"
CSV_UF = PASTA / "pib_uf_serie.csv"
GEOJSON_UF = PASTA / "br_uf_contornos.geojson"

REGIOES = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}   # 1º dígito do código
SETORES = {"513": "vab_agropecuaria", "517": "vab_industria", "6575": "vab_servicos", "525": "vab_adm_publica"}


def _baixar(url: str) -> bytes:
    pedido = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pedido, timeout=120) as resposta:
        bruto = resposta.read()
    return gzip.decompress(bruto) if bruto[:2] == b"\x1f\x8b" else bruto


def _sidra(url: str) -> pd.DataFrame:
    """Tabela SIDRA como DataFrame. A 1ª linha do JSON é o cabeçalho; valores como '...', '-' e 'X' viram nulo."""
    linhas = json.loads(_baixar(url))[1:]
    df = pd.DataFrame(linhas)
    df["V"] = pd.to_numeric(df["V"], errors="coerce")
    return df


def montar_municipios() -> pd.DataFrame:
    pib = _sidra(URL_PIB_MUN)
    largo = pib.pivot(index="D1C", columns="D2C", values="V").rename(columns={"37": "pib_mil_reais", **SETORES})
    nomes = pib.drop_duplicates("D1C").set_index("D1C")["D1N"]                       # "Município - UF"
    pop = _sidra(URL_POP_MUN).set_index("D1C")["V"].rename("populacao")
    area = _sidra(URL_AREA_MUN).set_index("D1C")["V"].rename("area_km2")

    df = largo.join(pop).join(area).reset_index().rename(columns={"D1C": "id_municipio"})
    partes = df["id_municipio"].map(nomes).str.rsplit(" - ", n=1, expand=True)
    df["municipio"], df["sigla_uf"] = partes[0], partes[1]
    df["regiao"] = df["id_municipio"].str[0].map(REGIOES)
    df["populacao"] = df["populacao"].astype("Int64")
    colunas = ["id_municipio", "municipio", "sigla_uf", "regiao", "populacao", "area_km2", "pib_mil_reais",
               *SETORES.values()]
    return df[colunas].sort_values("id_municipio").reset_index(drop=True)


def montar_uf() -> pd.DataFrame:
    d = _sidra(URL_PIB_UF).rename(columns={"D1C": "cod_uf", "D1N": "uf", "D3N": "ano", "V": "pib_mil_reais"})
    d["ano"] = d["ano"].astype(int)
    d["regiao"] = d["cod_uf"].str[0].map(REGIOES)
    return d[["cod_uf", "uf", "regiao", "ano", "pib_mil_reais"]].sort_values(["cod_uf", "ano"]).reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--forcar", action="store_true", help="baixa de novo mesmo que os arquivos existam")
    forcar = ap.parse_args().forcar
    PASTA.mkdir(exist_ok=True)

    tarefas = [
        (CSV_MUNICIPIOS, lambda: montar_municipios().to_csv(CSV_MUNICIPIOS, index=False)),
        (CSV_UF, lambda: montar_uf().to_csv(CSV_UF, index=False)),
        (GEOJSON_UF, lambda: GEOJSON_UF.write_bytes(_baixar(URL_CONTORNOS))),
    ]
    for caminho, gerar in tarefas:
        if caminho.exists() and not forcar:
            print(f"OK   {caminho.name} (já existe; use --forcar para baixar de novo)")
            continue
        print(f"Baixando {caminho.name} ...")
        try:
            gerar()
        except Exception as erro:
            print(f"ERRO ao gerar {caminho.name}: {erro}\nVerifique a conexão com a internet e tente de novo.")
            return 1
        print(f"OK   {caminho.name} ({caminho.stat().st_size / 1e3:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
