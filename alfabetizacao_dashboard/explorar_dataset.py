"""
explorar_dataset.py — perfilamento (EDA) das duas tabelas. Roda ANTES de qualquer gráfico.

Uso:  python explorar_dataset.py

Seções e a decisão que cada uma alimenta:
  1. Tamanho e tipos            -> a base cabe na memória? tipos corretos?
  2. Nulos                      -> o que significa 'populacao' vazia?
  3. Cardinalidade e cubo       -> as combinações estão todas presentes?
  4. Integridade da chave       -> o join fato x município perde linhas?
  5. Teste de sanidade          -> nossos totais batem com o IBGE?
  6. Recorte de Goiás           -> foco da aula
"""
import pandas as pd

import dados

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 30)

# Valores oficiais divulgados pelo IBGE (Censo 2022, pessoas de 15 anos ou mais)
REFERENCIA_IBGE = {"analfabetismo Brasil (%)": 7.0, "não alfabetizadas Brasil (milhões)": 11.4,
                   "analfabetismo 65+ (%)": 20.3, "analfabetismo pretos (%)": 10.1,
                   "analfabetismo brancos (%)": 4.3}


def titulo(t: str) -> None:
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


def main() -> None:
    bruto = pd.read_csv(dados.CSV_CENSO, dtype={"id_municipio": str})
    dim = pd.read_csv(dados.CSV_MUNICIPIO, dtype=str)

    titulo("1. TAMANHO E TIPOS")
    print(f"censo (fato)  : {bruto.shape[0]:,} linhas x {bruto.shape[1]} colunas | "
          f"{dados.CSV_CENSO.stat().st_size / 1e6:.1f} MB em disco | {bruto.memory_usage(deep=True).sum() / 1e6:.0f} MB na memória")
    print(f"municípios    : {dim.shape[0]:,} linhas x {dim.shape[1]} colunas | {dados.CSV_MUNICIPIO.stat().st_size / 1e6:.1f} MB")
    print("\nTipos do censo:\n" + bruto.dtypes.to_string())

    titulo("2. NULOS")
    print((bruto.isna().sum()).to_string())
    nulos = bruto["populacao"].isna()
    print(f"\npopulacao nula: {nulos.sum():,} linhas ({nulos.mean():.1%}).  Mínimo entre os não nulos: {bruto['populacao'].min():.0f}")
    print("-> Nenhum valor é 0: as combinações SEM pessoas vieram como nulo. Decisão: nulo = 0.")

    titulo("3. CARDINALIDADE E O 'CUBO'")
    card = {c: bruto[c].nunique() for c in ["id_municipio", "cor_raca", "sexo", "grupo_idade", "alfabetizacao"]}
    for k, v in card.items():
        print(f"{k:15s} {v:>6,} valores distintos")
    prod = 1
    for v in card.values():
        prod *= v
    print(f"\nProduto das cardinalidades = {prod:,}   |   linhas do arquivo = {len(bruto):,}   ->  "
          f"{'cubo COMPLETO (toda combinação existe)' if prod == len(bruto) else 'há combinações ausentes'}")
    for c in ["cor_raca", "sexo", "grupo_idade", "alfabetizacao"]:
        print(f"\n--- {c}\n{bruto[c].value_counts().to_string()}")

    titulo("4. INTEGRIDADE DA CHAVE (id_municipio)")
    sem_par = set(bruto["id_municipio"]) - set(dim["id_municipio"])
    extra = set(dim["id_municipio"]) - set(bruto["id_municipio"])
    print(f"ids do censo sem par no diretório : {len(sem_par)}")
    print(f"ids do diretório sem dados no censo: {len(extra)} -> "
          f"{dim.loc[dim['id_municipio'].isin(extra), ['id_municipio', 'nome', 'sigla_uf']].values.tolist()}")
    print(f"comprimento dos ids no censo: {bruto['id_municipio'].str.len().value_counts().to_dict()} (sempre 7 dígitos, tratar como TEXTO)")

    titulo("5. TESTE DE SANIDADE CONTRA O IBGE")
    df = dados.carregar()
    k = dados.kpis(df)
    por_cor = dados.por_dimensao(df, "cor_raca").set_index("cor_raca")["taxa_analfabetismo"]
    obtido = {"analfabetismo Brasil (%)": 100 - k["taxa_alfabetizacao"],
              "não alfabetizadas Brasil (milhões)": k["nao_alfabetizadas"] / 1e6,
              "analfabetismo 65+ (%)": k["analfabetismo_65"],
              "analfabetismo pretos (%)": por_cor["Preta"], "analfabetismo brancos (%)": por_cor["Branca"]}
    print(f"{'indicador':38s} {'IBGE':>8s} {'nosso':>8s}")
    for nome, ref in REFERENCIA_IBGE.items():
        print(f"{nome:38s} {ref:8.1f} {obtido[nome]:8.1f}")
    print("\nSe os números batem, o tratamento (nulo = 0, razão de somas) está correto.")

    titulo("6. RECORTE DE GOIÁS")
    go = df[df["sigla_uf"] == "GO"]
    kg = dados.kpis(go)
    print(f"linhas: {len(go):,} | municípios: {go['id_municipio'].nunique()} | pessoas 15+: {kg['populacao']:,}")
    print(f"taxa de analfabetismo GO: {100 - kg['taxa_alfabetizacao']:.2f}%  (Brasil: {100 - k['taxa_alfabetizacao']:.2f}%)")
    print("\nPor faixa etária (GO):")
    print(dados.por_dimensao(go, "grupo_idade").round(2).to_string(index=False))


if __name__ == "__main__":
    main()
