"""
exemplos.py — 8 exemplos de visualização, cada um com uma versão RUIM (de propósito) e uma BOA da mesma pergunta,
mais quatro figuras extras do catálogo usadas na Seção 1 dos slides. Só Plotly + pandas, sem Streamlit.

Cada função de figura recebe os `Dados` (dados.carregar()) e a UF em destaque (sigla), e devolve um go.Figure.
As versões "ruins" repetem erros comuns; as "boas" aplicam as regras listadas em cada Exemplo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dados as dd
from estilo import (AZUL, AZUL_SUAVE, CINZA_LINHA, CINZA_PREENCHE, CINZA_SUAVE, COR_REGIAO, ESCALA_AZUL,
                    ESCALA_DIVERGENTE, LARANJA, MAPA_SEM_FUNDO, base, enquadrar_brasil)

ALTURA = 440
ALTURA_27 = 540            # gráficos com 27 linhas (uma por UF) precisam de mais altura para mostrar todos os rótulos
TICKS_REAIS = [5000, 10000, 20000, 50000, 100000, 500000]
TEXTO_REAIS = ["R$ 5 mil", "R$ 10 mil", "R$ 20 mil", "R$ 50 mil", "R$ 100 mil", "R$ 500 mil"]


# ----------------------------------------------------------------------------
# E1 — BARRAS: quais UFs têm o maior PIB?
# ----------------------------------------------------------------------------
def e1_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    u = d.uf.sort_values("sigla_uf")                                       # ordem alfabética: não responde nada
    fig = px.bar(u, x="sigla_uf", y="pib_bi", color="sigla_uf", color_discrete_sequence=px.colors.qualitative.Alphabet)
    fig.update_yaxes(range=[150, u["pib_bi"].max() * 1.02], title="PIB")   # eixo truncado: UFs pequenas somem
    fig.update_xaxes(title=None)
    return base(fig, ALTURA_27, showlegend=True, margin=dict(l=0, r=0, t=8, b=0), legend=dict(title="UF", font_size=10))


def e1_bom(d: dd.Dados, destaque: str) -> go.Figure:
    u = d.uf.sort_values("pib_bi", ascending=False)
    cores = [LARANJA if s == destaque else AZUL for s in u["sigla_uf"]]
    fig = go.Figure(go.Bar(x=u["pib_bi"], y=u["uf"], orientation="h", marker=dict(color=cores, cornerradius=3),
                           text=u["pib_bi"].map(dd.reais_bi), textposition="outside", cliponaxis=False,
                           hovertemplate="<b>%{y}</b><br>PIB: %{x:,.1f} bilhões de reais<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, u["pib_bi"].max() * 1.22], fixedrange=True)      # base em zero
    fig.update_yaxes(autorange="reversed", title=None, showgrid=False, ticks="", fixedrange=True, tickfont_size=13,
                     dtick=1)                                                # dtick=1: mostra TODOS os nomes, sem pular
    return base(fig, ALTURA_27, bargap=0.25, font=dict(size=13))


# ----------------------------------------------------------------------------
# E2 — LINHAS: como o PIB de cada UF evoluiu desde 2002?
# ----------------------------------------------------------------------------
def _indice(d: dd.Dados) -> pd.DataFrame:
    p = d.serie.pivot(index="ano", columns="sigla_uf", values="pib_mil_reais")
    p["Brasil"] = p.sum(axis=1)
    return p / p.iloc[0] * 100


def e2_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.line(d.serie, x="ano", y="pib_bi", color="sigla_uf")          # 27 linhas, escala de valores absolutos
    fig.update_yaxes(title="PIB (bi)")
    fig.update_xaxes(title=None)
    return base(fig, ALTURA, showlegend=True, legend=dict(title="UF", font_size=10))


def e2_bom(d: dd.Dados, destaque: str) -> go.Figure:
    idx = _indice(d)
    ultimo = idx.iloc[-1].drop("Brasil")
    rotulos = {destaque: LARANJA, "Brasil": AZUL, ultimo.idxmax(): CINZA_LINHA, ultimo.idxmin(): CINZA_LINHA}
    fig = go.Figure()
    for uf in idx.columns:
        if uf in rotulos:
            continue
        fig.add_trace(go.Scatter(x=idx.index, y=idx[uf], mode="lines", line=dict(color=CINZA_SUAVE, width=1),
                                 name=uf, hovertemplate=f"<b>{uf}</b> %{{x}}: %{{y:.0f}}<extra></extra>"))
    for uf, cor in rotulos.items():                                         # os destacados por cima, com rótulo direto
        largura = 3 if cor in (LARANJA, AZUL) else 1.8
        fig.add_trace(go.Scatter(x=idx.index, y=idx[uf], mode="lines+markers+text", name=uf,
                                 line=dict(color=cor, width=largura),
                                 marker=dict(size=[0] * (len(idx) - 1) + [9], color=cor),
                                 text=[""] * (len(idx) - 1) + [f"{uf}  {dd.inteiro(idx[uf].iloc[-1])}"],
                                 textposition="middle right", cliponaxis=False,
                                 hovertemplate=f"<b>{uf}</b> %{{x}}: %{{y:.0f}}<extra></extra>"))
    fig.update_xaxes(title=None, range=[idx.index.min(), idx.index.max() + 3.2], tickvals=[2005, 2010, 2015, 2020],
                     fixedrange=True)
    fig.update_yaxes(title="Índice (2002 = 100), PIB nominal", fixedrange=True)
    return base(fig, ALTURA, margin=dict(l=0, r=0, t=8, b=0))


# ----------------------------------------------------------------------------
# E3 — HISTOGRAMA: como se distribui o PIB per capita dos municípios?
# ----------------------------------------------------------------------------
def e3_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.histogram(d.mun, x="pib_per_capita", nbins=10)                # cauda longa: quase tudo numa barra só
    fig.update_xaxes(title="PIB per capita")
    fig.update_yaxes(title="count")
    return base(fig, ALTURA)


def e3_bom(d: dd.Dados, destaque: str) -> go.Figure:
    log = np.log10(d.mun["pib_per_capita"].dropna())
    contagem, bordas = np.histogram(log, bins=40)
    mediana = float(np.median(d.mun["pib_per_capita"].dropna()))
    lo, hi = 10 ** bordas[:-1], 10 ** bordas[1:]
    fig = go.Figure(go.Bar(x=(bordas[:-1] + bordas[1:]) / 2, y=contagem, width=(bordas[1] - bordas[0]) * 0.92,
                           marker=dict(color=AZUL, cornerradius=3), customdata=np.column_stack([lo, hi]),
                           hovertemplate="Municípios: <b>%{y}</b><br>De R$ %{customdata[0]:,.0f} a R$ %{customdata[1]:,.0f}"
                                         "<extra></extra>"))
    fig.add_vline(x=np.log10(mediana), line=dict(color=LARANJA, width=2),
                  annotation=dict(text=f"mediana {dd.reais_mil(mediana)}", yanchor="bottom"), annotation_position="top")
    fig.update_xaxes(tickvals=np.log10(TICKS_REAIS), ticktext=TEXTO_REAIS, title="PIB per capita do município (escala log)",
                     fixedrange=True)
    fig.update_yaxes(title="Nº de municípios", range=[0, contagem.max() * 1.18], fixedrange=True)
    return base(fig, ALTURA, margin=dict(l=0, r=0, t=28, b=0))


# ----------------------------------------------------------------------------
# E4 — BOX PLOT: como o PIB per capita varia entre regiões?
# ----------------------------------------------------------------------------
def e4_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.box(d.mun.sort_values("regiao"), x="regiao", y="pib_per_capita", color="regiao")
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="PIB per capita")
    return base(fig, ALTURA, showlegend=True)


def e4_bom(d: dd.Dados, destaque: str) -> go.Figure:
    regiao_destaque = d.uf.loc[d.uf["sigla_uf"] == destaque, "regiao"].iloc[0]
    med = d.mun.groupby("regiao")["pib_per_capita"].median().sort_values(ascending=False)
    fig = go.Figure()
    for regiao, m in med.items():
        x = d.mun[d.mun["regiao"] == regiao]
        cor = LARANJA if regiao == regiao_destaque else CINZA_LINHA
        fundo = "rgba(217, 89, 38, 0.30)" if regiao == regiao_destaque else CINZA_PREENCHE
        fig.add_trace(go.Box(y=x["pib_per_capita"], name=f"{regiao}<br>mediana {dd.reais_mil(m)}", text=x["municipio"],
                             boxpoints="outliers", line=dict(color=cor, width=1.6), fillcolor=fundo,
                             marker=dict(color=cor, size=4, opacity=0.7)))
    fig.update_yaxes(type="log", tickvals=TICKS_REAIS, ticktext=TEXTO_REAIS, title="PIB per capita do município (escala log)",
                     fixedrange=True)
    fig.update_xaxes(title=None, fixedrange=True)
    return base(fig, ALTURA)


# ----------------------------------------------------------------------------
# E5 — DISPERSÃO: população e PIB andam juntos?
# ----------------------------------------------------------------------------
def e5_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.scatter(d.mun, x="populacao", y="pib_mil_reais", color="regiao")   # tudo espremido no canto
    fig.update_xaxes(title="populacao")
    fig.update_yaxes(title="pib")
    return base(fig, ALTURA, showlegend=True)


def e5_bom(d: dd.Dados, destaque: str) -> go.Figure:
    m = d.mun.assign(pib_mi=d.mun["pib_mil_reais"] / 1e3)                      # R$ milhões
    fig = go.Figure(go.Scattergl(x=m["populacao"], y=m["pib_mi"], mode="markers",
                                 marker=dict(color=AZUL, size=6, opacity=0.35), text=m["municipio"] + " (" + m["sigla_uf"] + ")",
                                 customdata=m["pib_per_capita"],
                                 hovertemplate="<b>%{text}</b><br>População: %{x:,.0f}<br>PIB: R$ %{y:,.0f} mi<br>"
                                               "Per capita: R$ %{customdata:,.0f}<extra></extra>"))
    x0, x1 = m["populacao"].min() * 0.35, m["populacao"].max() * 3.2
    for pc in (10_000, 50_000, 200_000):                                        # retas de PIB per capita constante
        fig.add_trace(go.Scatter(x=[x0, x1], y=[pc * x0 / 1e6, pc * x1 / 1e6], mode="lines+text",
                                 line=dict(color=CINZA_SUAVE, width=1), text=[f"R$ {dd.inteiro(pc / 1000)} mil/hab.", ""],
                                 textposition="top right", textfont=dict(size=13, color=CINZA_LINHA), hoverinfo="skip"))
    casos = pd.concat([m.nlargest(3, "pib_mi"), m[m["populacao"] > 5000].nlargest(2, "pib_per_capita")])
    fig.add_trace(go.Scatter(x=casos["populacao"], y=casos["pib_mi"], mode="markers+text", text=casos["municipio"],
                             textposition=["middle left", "bottom right", "bottom left", "top right", "bottom right"],
                             marker=dict(color=LARANJA, size=9), textfont=dict(size=14), hoverinfo="skip"))
    fig.update_xaxes(type="log", tickvals=[1e3, 1e4, 1e5, 1e6, 1e7], ticktext=["1 mil", "10 mil", "100 mil", "1 milhão", "10 milhões"],
                     title="População (escala log)", range=[np.log10(x0), np.log10(x1)], fixedrange=True)
    fig.update_yaxes(type="log", tickvals=[10, 100, 1e3, 1e4, 1e5], ticktext=["R$ 10 mi", "R$ 100 mi", "R$ 1 bi", "R$ 10 bi", "R$ 100 bi"],
                     title="PIB (escala log)", fixedrange=True)
    return base(fig, ALTURA)


# ----------------------------------------------------------------------------
# E6 — MAPA: onde o PIB por habitante é maior?
# ----------------------------------------------------------------------------
def _mapa_base(d: dd.Dados, fig: go.Figure) -> go.Figure:
    centro, zoom = enquadrar_brasil(d.contornos)
    fig.update_layout(map=dict(style=MAPA_SEM_FUNDO, center=centro, zoom=zoom), dragmode=False)
    return fig


def _coropletico(d: dd.Dados, z: pd.Series, siglas: pd.Series, **kw) -> go.Choroplethmap:
    return go.Choroplethmap(geojson=d.contornos, featureidkey="properties.sigla_uf", locations=siglas, z=z,
                            marker=dict(line=dict(color=CINZA_LINHA, width=0.8)), **kw)


def e6_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = go.Figure(_coropletico(d, d.uf["pib_bi"], d.uf["sigla_uf"], colorscale="Jet",
                                 colorbar=dict(title="PIB", thickness=12)))       # valor absoluto + arco-íris
    return base(_mapa_base(d, fig), ALTURA, margin=dict(l=0, r=0, t=0, b=0))


def e6_bom(d: dd.Dados, destaque: str) -> go.Figure:
    u = d.uf.copy()
    u["classe"] = pd.qcut(u["pib_per_capita"], 5, labels=False)                   # 5 faixas com ~o mesmo nº de UFs
    fig = go.Figure()
    for c in range(5):
        g = u[u["classe"] == c]
        nome = f"R$ {dd.inteiro(g['pib_per_capita'].min() / 1000)} a {dd.inteiro(g['pib_per_capita'].max() / 1000)} mil"
        fig.add_trace(_coropletico(d, [c] * len(g), g["sigla_uf"], zmin=0, zmax=0,
                                   colorscale=[[0, ESCALA_AZUL[c]], [1, ESCALA_AZUL[c]]], showscale=False, name=nome,
                                   showlegend=True, hovertemplate="<b>%{location}</b><extra>" + nome + "</extra>"))
    so_ele = {"type": "FeatureCollection",
              "features": [f for f in d.contornos["features"] if f["properties"]["sigla_uf"] == destaque]}
    fig.add_trace(go.Choroplethmap(geojson=so_ele, featureidkey="properties.sigla_uf", locations=[destaque], z=[0],
                                   zmin=0, zmax=1, colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                                   showscale=False, marker=dict(line=dict(color=LARANJA, width=3)), hoverinfo="skip"))
    fig = _mapa_base(d, fig)
    return base(fig, ALTURA, showlegend=True, margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(title=dict(text="PIB per capita, 2021"), x=0.0, y=0.02, yanchor="bottom",
                            bgcolor="rgba(0,0,0,0)", font_size=14))


# ----------------------------------------------------------------------------
# E7 — COMPOSIÇÃO: quanto cada UF pesa no PIB do Brasil?
# ----------------------------------------------------------------------------
def e7_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.pie(d.uf, names="sigla_uf", values="pib_bi")                    # 27 fatias
    fig.update_traces(textinfo="percent")
    return base(fig, ALTURA, showlegend=True, legend=dict(font_size=10), margin=dict(l=0, r=0, t=24, b=36))


def e7_bom(d: dd.Dados, destaque: str) -> go.Figure:
    u = d.uf.sort_values("participacao", ascending=False)
    topo = u.head(8)
    resto = u.iloc[8:]
    nomes = list(topo["uf"]) + [f"Demais {len(resto)} UFs"]
    valores = list(topo["participacao"]) + [resto["participacao"].sum()]
    cores = [LARANJA if s == destaque else AZUL for s in topo["sigla_uf"]] + [CINZA_LINHA]
    top3 = topo["participacao"].head(3).sum()
    fig = go.Figure(go.Bar(x=valores, y=nomes, orientation="h", marker=dict(color=cores, cornerradius=3),
                           text=[dd.pct(v) for v in valores], textposition="outside", cliponaxis=False,
                           hovertemplate="<b>%{y}</b><br>%{x:.1f}% do PIB do Brasil<extra></extra>"))
    fig.add_annotation(text=f"<b>{', '.join(topo['sigla_uf'].head(3))}</b> somam {dd.pct(top3)} do PIB", x=1, y=0.42,
                       xref="paper", yref="paper", xanchor="right", showarrow=False, font=dict(size=16))
    fig.update_xaxes(visible=False, range=[0, max(valores) * 1.22], fixedrange=True)
    fig.update_yaxes(autorange="reversed", title=None, ticks="", fixedrange=True)
    return base(fig, ALTURA, bargap=0.35)


# ----------------------------------------------------------------------------
# E8 — HEATMAP: qual a estrutura econômica de cada UF?
# ----------------------------------------------------------------------------
def e8_ruim(d: dd.Dados, destaque: str) -> go.Figure:
    v = d.uf.sort_values("sigla_uf").set_index("sigla_uf")[list(dd.SETORES)] / 1e6
    fig = go.Figure(go.Heatmap(z=v.values, x=list(dd.SETORES.values()), y=v.index, colorscale="Jet",
                               colorbar=dict(title="bi", thickness=12)))     # valores absolutos + arco-íris + sem números
    fig.update_yaxes(autorange="reversed", title=None, tickfont_size=10, dtick=1)
    return base(fig, ALTURA_27)


def e8_bom(d: dd.Dados, destaque: str) -> go.Figure:
    p = dd.participacao_setores(d.uf).sort_values("Adm. pública", ascending=False)
    fig = go.Figure(go.Heatmap(z=p.values, x=list(p.columns), y=p.index, colorscale=ESCALA_AZUL, zmin=0, zmax=70,
                               text=np.vectorize(lambda v: f"{v:.0f}%")(p.values), texttemplate="%{text}",
                               textfont=dict(size=12), xgap=2, ygap=2, showscale=False,
                               hovertemplate="<b>%{y}</b> · %{x}<br>%{z:.1f}% do valor adicionado<extra></extra>"))
    fig.update_xaxes(side="top", title=None, fixedrange=True)
    fig.update_yaxes(autorange="reversed", title=None, tickfont_size=13, fixedrange=True,
                     ticktext=[f"<b>{s}</b>" if s == destaque else s for s in p.index], tickvals=list(p.index), dtick=1)
    return base(fig, ALTURA_27)


# ----------------------------------------------------------------------------
# CATÁLOGO — figuras extras para a Seção 1 dos slides (mesma base de dados)
# ----------------------------------------------------------------------------
def cat_area(d: dd.Dados, destaque: str) -> go.Figure:
    s = d.serie.groupby(["ano", "regiao"])["pib_bi"].sum().reset_index()
    ordem = s.groupby("regiao")["pib_bi"].sum().sort_values(ascending=False).index
    fig = go.Figure()
    for r in ordem:
        x = s[s["regiao"] == r]
        fig.add_trace(go.Scatter(x=x["ano"], y=x["pib_bi"] / 1000, name=r, mode="lines", stackgroup="pib",
                                 line=dict(color=COR_REGIAO[r], width=1.5),
                                 hovertemplate=f"<b>{r}</b> %{{x}}: R$ %{{y:.2f}} tri<extra></extra>"))
    fig.update_yaxes(title="PIB nominal (R$ trilhões)", fixedrange=True)
    fig.update_xaxes(title=None, fixedrange=True)
    return base(fig, 400, showlegend=True, legend=dict(orientation="h", y=1.1, x=0, font_size=15))


def cat_treemap(d: dd.Dados, destaque: str) -> go.Figure:
    fig = px.treemap(d.uf, path=["regiao", "sigla_uf"], values="pib_bi", color="regiao", color_discrete_map=COR_REGIAO)
    fig.update_traces(textinfo="label+percent root", marker=dict(line=dict(width=2, color="rgba(128,128,128,0.4)")),
                      root_color="rgba(0,0,0,0)", hovertemplate="<b>%{label}</b><br>R$ %{value:,.0f} bi<extra></extra>")
    return base(fig, 400, margin=dict(l=0, r=0, t=0, b=0), font=dict(size=15))


def cat_small_multiples(d: dd.Dados, destaque: str) -> go.Figure:
    s = d.serie.groupby(["ano", "regiao"])["pib_bi"].sum().reset_index()
    regioes = list(s.groupby("regiao")["pib_bi"].sum().sort_values(ascending=False).index)
    fig = make_subplots(rows=1, cols=len(regioes), shared_yaxes=True, subplot_titles=regioes, horizontal_spacing=0.02)
    for i, r in enumerate(regioes, 1):
        x = s[s["regiao"] == r]
        fig.add_trace(go.Scatter(x=x["ano"], y=x["pib_bi"] / 1000, mode="lines", line=dict(color=AZUL, width=2.5),
                                 hovertemplate=f"<b>{r}</b> %{{x}}: R$ %{{y:.2f}} tri<extra></extra>"), row=1, col=i)
    fig.update_xaxes(tickvals=[2002, 2012, 2022], fixedrange=True)
    fig.update_yaxes(title="R$ trilhões", col=1, fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return base(fig, 320, margin=dict(l=0, r=0, t=34, b=0), font=dict(size=14))


def cat_paletas(d: dd.Dados, destaque: str) -> go.Figure:
    linhas = [("Categórica: identidade (quem é quem)", [AZUL, LARANJA, "#199e70", "#c98500", "#d55181"]),
              ("Sequencial: magnitude (quanto)", ESCALA_AZUL),
              ("Divergente: dois lados de um ponto neutro", ESCALA_DIVERGENTE)]
    fig = go.Figure()
    for i, (nome, cores) in enumerate(linhas):
        y0 = 2 - i
        for j, c in enumerate(cores):
            fig.add_shape(type="rect", x0=j, x1=j + 0.92, y0=y0, y1=y0 + 0.62, fillcolor=c, line_width=0)
        fig.add_annotation(text=nome, x=0, y=y0 + 0.85, xanchor="left", showarrow=False, font=dict(size=17))
    fig.update_xaxes(visible=False, range=[-0.05, 5]); fig.update_yaxes(visible=False, range=[-0.1, 3.1])
    return base(fig, 300, margin=dict(l=0, r=0, t=0, b=0))


# ----------------------------------------------------------------------------
# REGISTRO
# ----------------------------------------------------------------------------
@dataclass
class Exemplo:
    id: str
    titulo: str
    pergunta: str
    ruim: Callable
    bom: Callable
    problemas: list[str]
    regras: list[str]
    mapa: bool = False          # usa mapa (precisa de espera extra ao capturar)
    mudou: str = ""             # resumo curto do que foi feito (mostrado nos slides)


EXEMPLOS: list[Exemplo] = [
    Exemplo("E1", "Barras", "Quais UFs têm o maior PIB?", e1_ruim, e1_bom,
            ["Ordem alfabética: o leitor não vê o ranking", "Uma cor por UF: cor sem significado e legenda de 27 itens",
             "Eixo truncado em R$ 150 bi: UFs menores desaparecem e as diferenças ficam exageradas"],
            ["Ordenar do maior para o menor", "Uma cor só; laranja apenas no destaque", "Base em zero",
             "Barras horizontais: nomes longos ficam legíveis", "Valor na ponta da barra, sem eixo redundante"]),
    Exemplo("E2", "Linhas", "Como o PIB de cada UF evoluiu desde 2002?", e2_ruim, e2_bom,
            ["27 linhas iguais: 'espaguete' ilegível", "Valor absoluto: só São Paulo aparece, o resto vira uma faixa plana",
             "Legenda com 27 cores para casar de cabeça"],
            ["Destacar 2 a 4 séries e deixar o resto em cinza (contexto)", "Índice base 2002 = 100: compara o ritmo, não o tamanho",
             "Rótulo direto no fim da linha, sem legenda", "Deixar claro que o PIB é nominal (preços correntes)"]),
    Exemplo("E3", "Histograma", "Como se distribui o PIB per capita dos municípios?", e3_ruim, e3_bom,
            ["Escala linear: a cauda longa (máx. 39× a mediana) espreme 5.500 municípios numa única barra",
             "Poucas faixas (10) escondem a forma da distribuição", "Título de eixo cru ('count')"],
            ["Escala log quando a distribuição é muito assimétrica", "Faixas suficientes para mostrar a forma (40)",
             "Marcar a mediana", "Eixos em reais legíveis (R$ 10 mil)"]),
    Exemplo("E4", "Box plot", "Como o PIB per capita varia entre as regiões?", e4_ruim, e4_bom,
            ["Escala linear: os pontos extremos esmagam as caixas", "Uma cor por região repete o que o eixo já diz",
             "Ordem alfabética das regiões"],
            ["Eixo log para ver as caixas", "Ordenar pela mediana", "Uma cor de destaque (região da UF escolhida), o resto cinza",
             "Mediana escrita no rótulo do eixo"]),
    Exemplo("E5", "Dispersão", "População e PIB andam juntos?", e5_ruim, e5_bom,
            ["Escala linear: 5.570 pontos amontoados no canto", "Pontos sobrepostos escondem a densidade",
             "Nenhum caso rotulado"],
            ["Log nos dois eixos (a relação é proporcional)", "Transparência para mostrar a densidade",
             "Retas de PIB per capita constante: a distância até a reta é a informação",
             "Rotular só os casos-chave"]),
    Exemplo("E6", "Mapa", "Onde o PIB por habitante é maior?", e6_ruim, e6_bom,
            ["Valor absoluto: o mapa só mostra onde há mais gente (SP, RJ, MG)", "Arco-íris: sem ordem natural, ruim para daltônicos",
             "Escala contínua difícil de ler"],
            ["Normalizar por habitante (PIB per capita)", "Escala sequencial de um só matiz", "5 faixas com o mesmo nº de UFs (quantis)",
             "Legenda com valores em reais", "Estado escolhido contornado em laranja"], mapa=True),
    Exemplo("E7", "Composição", "Quanto cada UF pesa no PIB do Brasil?", e7_ruim, e7_bom,
            ["27 fatias: impossível comparar ângulos", "Legenda com cores repetidas", "Fatias pequenas ilegíveis"],
            ["Top 8 + 'Demais', em barras ordenadas", "Percentual escrito na barra", "Uma frase com a conclusão (SP + RJ + MG)"]),
    Exemplo("E8", "Heatmap", "Qual a estrutura econômica de cada UF?", e8_ruim, e8_bom,
            ["Valores absolutos: São Paulo vermelho em tudo, o resto azul", "Arco-íris sem números", "Ordem alfabética"],
            ["Trabalhar com participação (%), que permite comparar UFs de tamanhos diferentes", "Escala sequencial de um matiz",
             "Valor escrito em cada célula", "Ordenar pela coluna que conta a história"]),
]

MUDOU = {"E1": "ordenar · base em zero · uma cor · valor na barra",
         "E2": "poucas séries · índice base 100 · rótulo direto",
         "E3": "escala log · 40 faixas · mediana marcada",
         "E4": "eixo log · ordem pela mediana · uma cor de destaque",
         "E5": "log-log · transparência · retas de referência",
         "E6": "per capita · um matiz · 5 faixas por quantis",
         "E7": "Top 8 e 'Demais' · barras ordenadas · frase-conclusão",
         "E8": "percentuais · um matiz · número na célula"}
for _e in EXEMPLOS:
    _e.mudou = MUDOU[_e.id]

CATALOGO: dict[str, Callable] = {"cat_area": cat_area, "cat_treemap": cat_treemap,
                                 "cat_small_multiples": cat_small_multiples, "cat_paletas": cat_paletas}


def figura(id_figura: str, d: dd.Dados, destaque: str = "GO") -> go.Figure:
    """Resolve ids como 'E3_ruim', 'E3_bom' ou 'cat_area'."""
    if id_figura in CATALOGO:
        return CATALOGO[id_figura](d, destaque)
    id_ex, lado = id_figura.split("_")
    ex = next(e for e in EXEMPLOS if e.id == id_ex)
    return (ex.ruim if lado == "ruim" else ex.bom)(d, destaque)
