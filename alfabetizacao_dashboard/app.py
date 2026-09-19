"""
app.py — Dashboard "Alfabetização no Brasil e em Goiás" (Censo 2022 / IBGE)
Aula 1: KPIs + gráficos de barras e de pizza.

Executar:   streamlit run app.py

Modelo mental do Streamlit: a CADA interação (mover um filtro, clicar em algo)
o script inteiro roda de novo, de cima para baixo. Por isso a leitura pesada
fica dentro de @st.cache_data.

Construção em sala (blocos numerados):
  BLOCO 0  configuração + carga da base (com cache)
  BLOCO 1  filtros na barra lateral
  BLOCO 2  KPIs (st.metric) com comparação contra o Brasil
  BLOCO 3  gráficos de barras e de pizza (Plotly)
  BLOCO 4  tabela de conferência
  AULA 2   histograma, box plot e mapa  ->  ver comentários ao final
"""
import plotly.express as px
import streamlit as st

import dados

VERDE, OURO, CORAL, ESCURO = "#1F7A4D", "#F2B705", "#D1495B", "#0B3D2E"
COR_STATUS = {dados.ALFABETIZADAS: VERDE, dados.NAO_ALFABETIZADAS: CORAL}
COR_SEXO = {"Homens": ESCURO, "Mulheres": OURO}

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
    return df, tm, kpis_brasil


try:
    df, tm, k_brasil = carregar_tudo()
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
# BLOCO 3 — gráficos
# ----------------------------------------------------------------------------
def estilo(fig, titulo, legenda=False):
    fig.update_layout(title_text=titulo, showlegend=legenda, margin=dict(l=0, r=0, t=50, b=0), title_font_size=16)
    return fig


def barras(dados_df, x, y, titulo, horizontal=False, cor=VERDE, fmt=".1f"):
    fig = px.bar(dados_df, x=x, y=y, orientation="h" if horizontal else "v", text_auto=fmt,
                 color_discrete_sequence=[cor])
    if horizontal:
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(title=None)
    else:
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
    return estilo(fig, titulo)


linha1_a, linha1_b = st.columns([3, 2])

# 3.1 BARRAS — taxa por faixa etária (categoria ORDINAL: mantém a ordem natural)
por_idade = dados.por_dimensao(f, "grupo_idade")
linha1_a.plotly_chart(barras(por_idade, "grupo_idade", "taxa_analfabetismo",
                             "Taxa de analfabetismo por faixa etária (%)"))

# 3.2 PIZZA (rosca) — parte-todo com 2 fatias
comp = dados.composicao_alfabetizacao(f)
fig = px.pie(comp, names="alfabetizacao", values="populacao", hole=0.5, color="alfabetizacao",
             color_discrete_map=COR_STATUS)
fig.update_traces(textinfo="percent+label")
linha1_b.plotly_chart(estilo(fig, "Alfabetizadas × não alfabetizadas"))

linha2_a, linha2_b = st.columns([3, 2])

# 3.3 BARRAS HORIZONTAIS — taxa por cor/raça (ordenadas)
por_cor = dados.por_dimensao(f, "cor_raca").sort_values("taxa_analfabetismo", ascending=False)
linha2_a.plotly_chart(barras(por_cor, "taxa_analfabetismo", "cor_raca",
                             "Taxa de analfabetismo por cor ou raça (%)", horizontal=True))

# 3.4 PIZZA (rosca) — quem são os não alfabetizados, por sexo
por_sexo = dados.nao_alfabetizadas_por(f, "sexo")
fig = px.pie(por_sexo, names="sexo", values="nao_alfabetizadas", hole=0.5, color="sexo", color_discrete_map=COR_SEXO)
fig.update_traces(textinfo="percent+label")
linha2_b.plotly_chart(estilo(fig, "Não alfabetizados por sexo"))

# 3.5 e 3.6 RANKINGS — volume x taxa (o contraste é o ponto didático)
st.markdown("#### Volume × taxa: onde estão as pessoas e onde está o problema proporcional")
if municipio != "Todos":
    st.info(f"Rankings mostram todos os municípios de {uf_nome} (ignoram o filtro de município).")

tm_area = tm_area.assign(rotulo=tm_area["municipio"].astype(str) +
                         (" (" + tm_area["sigla_uf"].astype(str) + ")" if uf_nome == "Brasil" else ""))
linha3_a, linha3_b = st.columns(2)

top_qtd = tm_area.nlargest(10, "nao_alfabetizadas")
linha3_a.plotly_chart(barras(top_qtd, "nao_alfabetizadas", "rotulo",
                             "Top 10 municípios — nº de não alfabetizados", horizontal=True, fmt=",.0f"))

top_taxa = tm_area[tm_area["populacao"] >= min_pop].nlargest(10, "taxa_analfabetismo")
linha3_b.plotly_chart(barras(top_taxa, "taxa_analfabetismo", "rotulo",
                             f"Top 10 municípios — taxa de analfabetismo (%), 15+ ≥ {dados.formatar_int(min_pop)}",
                             horizontal=True, cor=CORAL))

# ----------------------------------------------------------------------------
# BLOCO 4 — conferência
# ----------------------------------------------------------------------------
with st.expander("Ver tabela municipal (base dos rankings e do mapa da aula 2)"):
    st.dataframe(tm_area.drop(columns="rotulo").sort_values("nao_alfabetizadas", ascending=False))

# ----------------------------------------------------------------------------
# AULA 2 (roteiro) — acrescentar abaixo, usando a tabela municipal `tm_area`:
#   px.histogram(tm_area, x="taxa_analfabetismo", nbins=30)          -> distribuição das taxas municipais
#   px.box(tm, x="regiao", y="taxa_analfabetismo")                   -> comparar distribuições por região
#   px.scatter_map(tm_area, lat="lat", lon="lon", size="populacao",
#                  color="taxa_analfabetismo", hover_name="municipio",
#                  zoom=5, map_style="carto-positron")               -> mapa (centroides já estão no diretório)
# ----------------------------------------------------------------------------
