"""
preparar_dados.py — confere se os dois CSVs estão em dados/ e monta o cache.

Uso:  python preparar_dados.py

Arquivos esperados na pasta dados/ :
  1. br_ibge_censo_2022_alfabetizacao_grupo_idade_sexo_raca.csv   (fato: ~780 mil linhas)
  2. br_bd_diretorios_brasil_municipio.csv                        (dimensão: ~5,6 mil municípios)

De onde vêm (Base dos Dados — basedosdados.org, dados tratados a partir do IBGE):
  • conjunto "Censo 2022", tabela alfabetizacao_grupo_idade_sexo_raca
  • conjunto "Diretórios Brasil", tabela municipio
Pode baixar pelo site ou pelo pacote Python `basedosdados`.
"""
import sys
import time

import dados


def main() -> int:
    faltando = dados.arquivos_disponiveis()
    if faltando:
        print("Faltam arquivos em dados/:")
        for p in faltando:
            print("  -", p.name)
        print(__doc__)
        return 1

    for p in (dados.CSV_CENSO, dados.CSV_MUNICIPIO):
        print(f"OK  {p.name}  ({p.stat().st_size / 1e6:.1f} MB)")

    t0 = time.time()
    df = dados.carregar()
    print(f"\nBase ligada em {time.time() - t0:.1f}s: {len(df):,} linhas, "
          f"{df['id_municipio'].nunique():,} municípios, {df['sigla_uf'].nunique()} UFs.")
    print("Cache gravado em dados/ (Parquet) — só ocorre se o pyarrow estiver instalado."
          if dados.PARQUET_FATO.exists() else "Sem pyarrow: rodando sem cache em Parquet (funciona, só é mais lento).")
    print("\nPróximo passo: python explorar_dataset.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
