"""
app.py — Boas práticas de visualização de dados, com PIB e população do IBGE (Streamlit).

Executar:   streamlit run app.py

Páginas (barra lateral): visão geral · E1 a E8 (cada exemplo mostra ANTES × DEPOIS da mesma pergunta) · catálogo.
Usa um seletor na barra lateral e não st.tabs: mapa dentro de aba oculta renderiza cortado.

Modo imagem (usado por gerar_imagens.py para os slides):  ?modo=imagem&fig=E3_bom&uf=GO
mostra só a figura pedida, sem menus.
"""
import pandas as pd
import streamlit as st

import dados as dd
import exemplos as ex
from estilo import CONFIG

st.set_page_config(page_title="Boas práticas de visualização", page_icon="📊", layout="wide")


@st.cache_resource(show_spinner="Carregando a base do IBGE...")
def carregar() -> dd.Dados:
    return dd.carregar()


try:
    d = carregar()
except FileNotFoundError as erro:
    st.error(str(erro))
    st.stop()

# ----------------------------------------------------------------------------
# MODO IMAGEM — só a figura, para captura automática
# ----------------------------------------------------------------------------
params = st.query_params
if params.get("modo") == "imagem":
    st.markdown("<style>.block-container{padding:8px 8px 0 8px} footer{display:none}"
                '[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none}</style>',
                unsafe_allow_html=True)
    st.plotly_chart(ex.figura(params.get("fig", "E1_bom"), d, params.get("uf", "GO")), config=CONFIG)
    st.stop()

# ----------------------------------------------------------------------------
# NAVEGAÇÃO
# ----------------------------------------------------------------------------
PAGINAS = ["Visão geral"] + [f"{e.id} · {e.titulo}" for e in ex.EXEMPLOS] + ["Catálogo de gráficos"]
pagina = st.sidebar.radio("Página", PAGINAS)
nomes = d.uf.sort_values("uf").set_index("sigla_uf")["uf"]
destaque = st.sidebar.selectbox("UF em destaque", nomes.index, index=list(nomes.index).index("GO"),
                                format_func=lambda s: nomes[s],
                                help="Nos gráficos 'depois', a UF escolhida aparece em laranja: destaque só onde importa.")
st.sidebar.caption(f"Fonte: IBGE (PIB dos Municípios e estimativas de população), ano {dd.ANO}.")


def cartao(coluna, titulo: str, legenda: str | None = None):
    caixa = coluna.container(border=True)
    caixa.markdown(f"**{titulo}**")
    if legenda:
        caixa.caption(legenda)
    return caixa


TABELAS = {
    "E1": lambda: d.uf[["uf", "regiao", "pib_bi", "populacao"]].sort_values("pib_bi", ascending=False),
    "E2": lambda: d.serie.pivot(index="ano", columns="sigla_uf", values="pib_bi"),
    "E3": lambda: d.mun[["municipio", "sigla_uf", "populacao", "pib_per_capita"]].sort_values("pib_per_capita"),
    "E4": lambda: d.mun.groupby("regiao")["pib_per_capita"].describe(percentiles=[0.25, 0.5, 0.75]).round(0),
    "E5": lambda: d.mun[["municipio", "sigla_uf", "populacao", "pib_mil_reais", "pib_per_capita"]],
    "E6": lambda: d.uf[["uf", "regiao", "pib_bi", "populacao", "pib_per_capita"]].sort_values("pib_per_capita"),
    "E7": lambda: d.uf[["uf", "pib_bi", "participacao"]].sort_values("participacao", ascending=False),
    "E8": lambda: dd.participacao_setores(d.uf).round(1),
}

# ----------------------------------------------------------------------------
# VISÃO GERAL
# ----------------------------------------------------------------------------
if pagina == "Visão geral":
    st.title("📊 Boas práticas de visualização de dados")
    st.caption("Exemplos com dados públicos brasileiros: PIB e população dos municípios (IBGE). "
               "Cada exemplo mostra o mesmo dado num gráfico ruim e num gráfico bom.")
    m = d.mun
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PIB do Brasil, 2021", dd.reais_bi(m["pib_mil_reais"].sum() / 1e6))
    c2.metric("População estimada", dd.inteiro(m["populacao"].sum()))
    c3.metric("PIB per capita", dd.reais_mil(m["pib_mil_reais"].sum() * 1000 / m["populacao"].sum()),
              help="Soma do PIB ÷ soma da população (razão de somas, não média dos municípios).")
    c4.metric("Municípios", dd.inteiro(len(m)))
    st.markdown("#### Os exemplos")
    st.dataframe(pd.DataFrame([{"Exemplo": f"{e.id} · {e.titulo}", "Pergunta": e.pergunta} for e in ex.EXEMPLOS]),
                 hide_index=True, width="stretch")
    st.info("Use a barra lateral para navegar. A **UF em destaque** muda o que aparece em laranja nos gráficos 'depois'.")
    st.markdown("#### Sobre a base")
    st.markdown("PIB municipal e valor adicionado por setor (tabela 5938 do SIDRA), população estimada (tabela 6579), "
                "área territorial (tabela 4714) e limites estaduais do IBGE. Detalhes em `dados/FONTES.md`. "
                "Para baixar de novo: `python baixar_dados.py --forcar`.")

# ----------------------------------------------------------------------------
# CATÁLOGO
# ----------------------------------------------------------------------------
elif pagina == "Catálogo de gráficos":
    st.title("Catálogo de gráficos")
    st.caption("Outros tipos de gráfico com a mesma base. Os demais estão nos exemplos E1 a E8.")
    esquerda, direita = st.columns(2)
    itens = [("cat_area", "Área empilhada: PIB por região ao longo do tempo", "Composição que muda no tempo."),
             ("cat_treemap", "Treemap: PIB por região e UF", "Hierarquia e proporção; a área é o valor."),
             ("cat_small_multiples", "Pequenos múltiplos: uma região por painel", "Mesma escala em todos os painéis."),
             ("cat_paletas", "Os três tipos de paleta", "Categórica, sequencial e divergente.")]
    for i, (fig_id, titulo, legenda) in enumerate(itens):
        cartao(esquerda if i % 2 == 0 else direita, titulo, legenda).plotly_chart(ex.figura(fig_id, d, destaque), config=CONFIG)

# ----------------------------------------------------------------------------
# EXEMPLOS E1..E8
# ----------------------------------------------------------------------------
else:
    e = next(x for x in ex.EXEMPLOS if pagina.startswith(x.id))
    st.title(f"{e.id} · {e.titulo}")
    st.markdown(f"##### Pergunta: {e.pergunta}")
    col_ruim, col_bom = st.columns(2)
    cartao(col_ruim, "❌ Antes", "Erros comuns, de propósito.").plotly_chart(e.ruim(d, destaque), config=CONFIG)
    cartao(col_bom, "✅ Depois", "Mesmos dados, boas práticas.").plotly_chart(e.bom(d, destaque), config=CONFIG)
    col_p, col_r = st.columns(2)
    col_p.markdown("**O que atrapalha**\n\n" + "\n".join(f"- {p}" for p in e.problemas))
    col_r.markdown("**O que foi feito**\n\n" + "\n".join(f"- {r}" for r in e.regras))
    with st.expander("Ver os dados (a tabela é a versão acessível do gráfico)"):
        st.dataframe(TABELAS[e.id](), width="stretch")
