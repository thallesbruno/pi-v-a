"""
app.py — Dashboard "Alfabetização no Brasil e em Goiás" (Censo 2022 / IBGE)
Aula 1: KPIs + gráficos de barras e de pizza.
Aula 2: histograma, box plot e mapa (seletor de visão).

Executar:   streamlit run app.py

Modelo mental do Streamlit: a CADA interação (mover um filtro, clicar em algo)
o script inteiro roda de novo, de cima para baixo. Por isso a leitura pesada
fica dentro de @st.cache_data.

Construção em sala (blocos numerados):
  BLOCO 0  configuração + carga da base (com cache)
  BLOCO 1  filtros na barra lateral
  BLOCO 2  KPIs (st.metric) com comparação contra o Brasil
  BLOCO 3  gráficos de barras e de pizza (Plotly)
  BLOCO 4  distribuição e mapa (aula 2): histograma, box plot e mapa, escolhidos num seletor
  BLOCO 5  tabela de conferência
"""
import streamlit as st

import dados
import graficos as g

# ----------------------------------------------------------------------------
# BLOCO 0 — configuração e carga
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Alfabetização — Censo 2022", page_icon="📖", layout="wide")


@st.cache_data(show_spinner="Carregando e ligando as tabelas (só na 1ª vez)...")
def carregar_tudo():
    df = dados.carregar()
    dim = dados.carregar_municipios()
    tm = dados.tabela_municipal(df, dim)            # 1 linha por município (ranking e mapa)
    kpis_brasil = dados.kpis(df)
    contornos = dados.carregar_contornos_uf()       # limites dos estados (None se o arquivo não existir)
    return df, tm, kpis_brasil, contornos


try:
    df, tm, k_brasil, contornos = carregar_tudo()
except (FileNotFoundError, ValueError) as erro:
    st.error(str(erro))
    st.stop()

st.title("📖 Alfabetização no Brasil e em Goiás")
st.caption("Fonte: IBGE, Censo Demográfico 2022 (pessoas de 15 anos ou mais) · dados tratados pela Base dos Dados · "
           "Alfabetizada = sabe ler e escrever ao menos um bilhete simples.")

# ----------------------------------------------------------------------------
# BLOCO 1 — filtros
# ----------------------------------------------------------------------------
st.sidebar.header("Filtros")
ufs = (df[["sigla_uf", "uf"]].drop_duplicates().astype(str).sort_values("uf"))
opcoes_uf = ["Brasil"] + ufs["uf"].tolist()
uf_nome = st.sidebar.selectbox("Abrangência", opcoes_uf, index=opcoes_uf.index("Goiás"))

if uf_nome == "Brasil":
    base = df
    tm_area = tm
    municipio = "Todos"
else:
    sigla = ufs.loc[ufs["uf"] == uf_nome, "sigla_uf"].iloc[0]
    base = df[df["sigla_uf"] == sigla]
    tm_area = tm[tm["sigla_uf"] == sigla]
    municipio = st.sidebar.selectbox("Município", ["Todos"] + sorted(tm_area["municipio"].astype(str)))

f = base if municipio == "Todos" else base[base["municipio"] == municipio]
recorte = municipio if municipio != "Todos" else uf_nome

min_pop = st.sidebar.number_input("População mínima (15+) nos rankings de taxa", min_value=0, max_value=100000,
                                  value=5000, step=1000,
                                  help="Municípios muito pequenos têm taxas instáveis (poucos casos mudam muito o %).")
st.sidebar.caption(f"{dados.formatar_int(len(f))} linhas do cubo no recorte atual")

if f["populacao"].sum() == 0:
    st.warning("Sem população para o recorte escolhido.")
    st.stop()

st.subheader(f"Recorte: {recorte}")

# ----------------------------------------------------------------------------
# BLOCO 2 — KPIs (razões de somas!)
# ----------------------------------------------------------------------------
k = dados.kpis(f)
comparar = uf_nome != "Brasil"                       # delta contra o Brasil só faz sentido fora dele


def delta_pp(valor, ref):
    if not comparar or valor is None or ref is None:
        return None
    return f"{valor - ref:+.1f} p.p. vs Brasil".replace(".", ",")


c1, c2, c3 = st.columns(3)
c1.metric("Pessoas de 15 anos ou mais", dados.formatar_int(k["populacao"]),
          help="Soma da coluna populacao no recorte (o cubo já vem com contagens).")
c2.metric("Taxa de alfabetização", dados.formatar_pct(k["taxa_alfabetizacao"]),
          delta=delta_pp(k["taxa_alfabetizacao"], k_brasil["taxa_alfabetizacao"]),
          help="alfabetizadas ÷ pessoas de 15+ × 100.")
c3.metric("Pessoas não alfabetizadas", dados.formatar_int(k["nao_alfabetizadas"]),
          help="Volume absoluto: onde há mais pessoas para atender (não é o mesmo que a maior taxa).")

c4, c5, c6 = st.columns(3)
gap = k["gap_sexo_pp"]
c4.metric("Gap de gênero (homens − mulheres)", "—" if gap is None else f"{gap:+.2f} p.p.".replace(".", ","),
          help="Taxa de analfabetismo dos homens menos a das mulheres. Positivo = homens com mais analfabetismo.")
rz = k["razao_racial"]
c5.metric("Razão racial (pretos e pardos ÷ brancos)", "—" if rz is None else f"{rz:.2f}×".replace(".", ","),
          help="Quantas vezes o analfabetismo de pretos e pardos é o de brancos. 1,00 = igualdade.")
c6.metric("Analfabetismo 65+ anos", dados.formatar_pct(k["analfabetismo_65"]),
          delta=delta_pp(k["analfabetismo_65"], k_brasil["analfabetismo_65"]), delta_color="inverse",
          help="% de não alfabetizados entre pessoas de 65 anos ou mais.")

st.divider()


# ----------------------------------------------------------------------------
# BLOCO 3 — gráficos (as figuras vivem em graficos.py; aqui só a montagem da página)
# ----------------------------------------------------------------------------
def cartao(onde, titulo, legenda=None):
    """Cartão com borda (st.container) + título + explicação; a borda e o texto seguem o tema do Streamlit."""
    caixa = onde.container(border=True)
    caixa.markdown(f"**{titulo}**")
    if legenda:
        caixa.caption(legenda)
    return caixa


linha1_a, linha1_b = st.columns([3, 2])

# 3.1 BARRAS — taxa por faixa etária (categoria ORDINAL: mantém a ordem natural)
por_idade = dados.por_dimensao(f, "grupo_idade")
cartao(linha1_a, "Analfabetismo por faixa etária",
       "% de pessoas que não sabem ler e escrever em cada faixa. A mais alta em destaque.").plotly_chart(
    g.barras_taxa_por_idade(por_idade), config=g.CONFIG)

# 3.2 PIZZA (rosca) — parte-todo com 2 fatias
comp = dados.composicao_alfabetizacao(f)
cartao(linha1_b, "Alfabetizadas × não alfabetizadas",
       "Pessoas de 15 anos ou mais no recorte.").plotly_chart(g.rosca_alfabetizacao(comp), config=g.CONFIG)

linha2_a, linha2_b = st.columns([3, 2])

# 3.3 BARRAS HORIZONTAIS — taxa por cor/raça (ordenadas)
por_cor = dados.por_dimensao(f, "cor_raca")
cartao(linha2_a, "Analfabetismo por cor ou raça",
       "% de não alfabetizados dentro de cada grupo. A mais alta em destaque.").plotly_chart(
    g.barras_taxa_por_cor(por_cor), config=g.CONFIG)

# 3.4 PIZZA (rosca) — quem são os não alfabetizados, por sexo
por_sexo = dados.nao_alfabetizadas_por(f, "sexo")
cartao(linha2_b, "Não alfabetizados por sexo",
       "Total de não alfabetizados, por sexo.").plotly_chart(
    g.rosca_sexo(por_sexo), config=g.CONFIG)

# 3.5 e 3.6 RANKINGS — volume x taxa (o contraste é o ponto didático)
st.markdown("#### Volume × taxa: onde estão as pessoas e onde está o problema proporcional")
if municipio != "Todos":
    st.info(f"Rankings mostram todos os municípios de {uf_nome} (ignoram o filtro de município).")

tm_area = tm_area.assign(rotulo=tm_area["municipio"].astype(str) +
                         (" (" + tm_area["sigla_uf"].astype(str) + ")" if uf_nome == "Brasil" else ""))
linha3_a, linha3_b = st.columns(2)

top_qtd = tm_area.nlargest(10, "nao_alfabetizadas")
cartao(linha3_a, "Top 10 municípios em número de não alfabetizados",
       "Volume: onde há mais pessoas para atender.").plotly_chart(g.ranking_volume(top_qtd), config=g.CONFIG)

top_taxa = tm_area[tm_area["populacao"] >= min_pop].nlargest(10, "taxa_analfabetismo")
cartao(linha3_b, "Top 10 municípios em taxa de analfabetismo",
       f"Proporção: onde o problema pesa mais. Só municípios com 15+ ≥ {dados.formatar_int(min_pop)}.").plotly_chart(
    g.ranking_taxa(top_taxa), config=g.CONFIG)

# ----------------------------------------------------------------------------
# BLOCO 4 — distribuição e mapa (aula 2), sobre a tabela municipal
# ----------------------------------------------------------------------------
st.markdown("#### Distribuição das taxas municipais e mapa")

tm_area_min = tm_area[tm_area["populacao"] >= min_pop]      # mesmo corte de população dos rankings
tm_min = tm[tm["populacao"] >= min_pop]
corte = f"com 15+ ≥ {dados.formatar_int(min_pop)}"

# Seletor em vez de st.tabs: numa aba oculta o mapa nasce com o tamanho errado (só uma fatia aparece).
# Com o seletor, só a visão escolhida é montada, já visível.
vista = st.segmented_control("Visão", ["Distribuição", "Por região", "Mapa"], default="Distribuição",
                             key="vista", label_visibility="collapsed") or "Distribuição"

# 4.1 HISTOGRAMA — como as taxas se distribuem entre os municípios do recorte
if vista == "Distribuição":
    if tm_area_min.empty:
        st.info("Nenhum município atinge a população mínima escolhida.")
    else:
        cartao(st, f"Como variam as taxas entre os municípios — {uf_nome}",
               f"{dados.formatar_int(len(tm_area_min))} municípios {corte}. Cada barra conta municípios numa faixa de taxa; "
               "a linha marca a mediana.").plotly_chart(
            g.histograma(tm_area_min["taxa_analfabetismo"]), config=g.CONFIG)

# 4.2 BOX PLOT — comparar a distribuição entre regiões (sempre o Brasil todo)
if vista == "Por região":
    if tm_min.empty:
        st.info("Nenhum município atinge a população mínima escolhida.")
    else:
        regiao_destaque = None if uf_nome == "Brasil" else tm_area["regiao"].iloc[0]
        cartao(st, "Taxa de analfabetismo dos municípios, por região do Brasil",
               f"Municípios {corte}. A caixa cobre a metade central dos municípios, o traço é a mediana e os pontos são "
               "casos extremos." + (f" Em destaque: região de {uf_nome}." if regiao_destaque else "")).plotly_chart(
            g.box_regioes(tm_min, regiao_destaque), config=g.CONFIG)

# 4.3 MAPA — bolha = população, cor = taxa (centroides do diretório de municípios) sobre os limites dos estados
if vista == "Mapa":
    if tm_area.dropna(subset=["lat", "lon", "taxa_analfabetismo"]).empty:
        st.info("Sem coordenadas para o recorte escolhido.")
    else:
        uf_sigla = None if uf_nome == "Brasil" else tm_area["sigla_uf"].iloc[0]
        caixa = cartao(st, f"Mapa dos municípios — {uf_nome}",
                       "Cada bolha é um município, na posição do seu centro (norte para cima): o tamanho cresce com a "
                       "população de 15+ e a cor mostra a taxa de analfabetismo. Roda do mouse para aproximar. "
                       "Limites estaduais: IBGE.")
        if contornos is None:
            caixa.warning("Contorno dos estados não encontrado: rode `python preparar_dados.py` para baixá-lo. "
                          "Enquanto isso, o mapa mostra só as bolhas.")
            caixa.plotly_chart(g.mapa(tm_area), config=g.CONFIG_MAPA)
        elif uf_sigla is None:
            caixa.plotly_chart(g.mapa(tm_area, contornos), config=g.CONFIG_MAPA)
        else:
            col_mapa, col_localizador = caixa.columns([4, 1])
            col_mapa.plotly_chart(g.mapa(tm_area, contornos, uf_sigla), config=g.CONFIG_MAPA)
            col_localizador.caption("Localização no Brasil")
            col_localizador.plotly_chart(g.mapa_localizador(contornos, uf_sigla), config=g.CONFIG_LOCALIZADOR)

# ----------------------------------------------------------------------------
# BLOCO 5 — conferência
# ----------------------------------------------------------------------------
with st.expander("Ver tabela municipal (base dos rankings, dos gráficos de distribuição e do mapa)"):
    st.dataframe(tm_area.drop(columns="rotulo").sort_values("nao_alfabetizadas", ascending=False))
