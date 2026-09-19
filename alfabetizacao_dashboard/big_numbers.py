"""
big_numbers.py — calcula os "big numbers" reais (Goiás x Brasil) e grava big_numbers.json.

Uso:  python big_numbers.py

O JSON é a fonte dos números do slide de big numbers. Rode de novo se trocar a base.
Todas as taxas são razões de somas (nunca médias de linhas).
"""
import json
from pathlib import Path

import dados


def calcular() -> dict:
    df = dados.carregar()
    dim = dados.carregar_municipios()
    go = df[df["sigla_uf"] == "GO"]
    k_br, k_go = dados.kpis(df), dados.kpis(go)

    tm = dados.tabela_municipal(df, dim)
    tm_go = tm[tm["sigla_uf"] == "GO"]
    ufs = dados.por_dimensao(df, "sigla_uf").sort_values("taxa_analfabetismo").reset_index(drop=True)
    topo_qtd = tm_go.nlargest(1, "nao_alfabetizadas").iloc[0]
    topo_taxa = tm_go[tm_go["populacao"] >= 5000].nlargest(1, "taxa_analfabetismo").iloc[0]
    menor_taxa = tm_go.nsmallest(1, "taxa_analfabetismo").iloc[0]

    return {
        "brasil": k_br,
        "goias": k_go,
        "extras": {
            "linhas_fato": int(len(df)),
            "municipios_brasil": int(df["id_municipio"].nunique()),
            "municipios_goias": int(go["id_municipio"].nunique()),
            "municipios_go_acima_media_br_pct": float((tm_go["taxa_analfabetismo"] > 100 - k_br["taxa_alfabetizacao"]).mean() * 100),
            "mediana_municipal_go_pct": float(tm_go["taxa_analfabetismo"].median()),
            "ranking_go_entre_ufs": int(ufs.index[ufs["sigla_uf"] == "GO"][0] + 1),
            "n_ufs": int(len(ufs)),
            "go_maior_qtd_municipio": topo_qtd["municipio"], "go_maior_qtd": int(topo_qtd["nao_alfabetizadas"]),
            "go_maior_qtd_taxa": float(topo_qtd["taxa_analfabetismo"]),
            "go_maior_taxa_municipio": topo_taxa["municipio"], "go_maior_taxa": float(topo_taxa["taxa_analfabetismo"]),
            "go_menor_taxa_municipio": menor_taxa["municipio"], "go_menor_taxa": float(menor_taxa["taxa_analfabetismo"]),
        },
    }


if __name__ == "__main__":
    r = calcular()
    ordem = ["populacao", "taxa_alfabetizacao", "nao_alfabetizadas", "gap_sexo_pp", "razao_racial", "analfabetismo_65"]
    print(f"{'KPI':22s} {'Goiás':>14s} {'Brasil':>14s}")
    for k in ordem:
        print(f"{k:22s} {r['goias'][k]:14,.3f} {r['brasil'][k]:14,.3f}")
    print()
    for k, v in r["extras"].items():
        print(f"{k:34s} {v}")
    Path(__file__).with_name("big_numbers.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nGravado: big_numbers.json")
