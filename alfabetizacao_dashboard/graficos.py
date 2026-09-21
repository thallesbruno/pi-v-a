"""
graficos.py — figuras Plotly do dashboard (só Plotly + pandas, sem Streamlit).

COERÊNCIA ENTRE TEMA CLARO E ESCURO
O Streamlit troca de tema no navegador, sem rodar o script de novo, e o Python não
tem como saber o tema com segurança (st.context.theme pode vir defasado logo após a
troca). Por isso nenhuma figura depende do tema:
  • fundo transparente e textos, grades e eixos herdados do tema (st.plotly_chart
    aplica theme="streamlit" no navegador);
  • cores das marcas escolhidas para funcionar nos DOIS fundos (contraste >= 3:1 contra
    #ffffff e #0e1117, validadas com validate_palette.js, inclusive para daltonismo);
  • tons "suaves" e neutros feitos com transparência (rgba), que assumem o fundo do
    tema ativo sozinhos;
  • mapa sem camada de fundo (tiles), que seria claro ou escuro, nunca os dois: os limites dos
    estados (IBGE) são polígonos cinza translúcidos desenhados por baixo das bolhas.

SEMÂNTICA DAS CORES (a mesma em todo o dashboard)
  laranja   = taxa de analfabetismo (%)      verde-água = volume (nº de pessoas)
  azul / magenta = homens / mulheres         cinza      = contexto, sem destaque
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dados

COR_TAXA = "#d95926"
COR_VOLUME = "#199e70"
COR_HOMENS = "#3987e5"
COR_MULHERES = "#d55181"
TAXA_SUAVE = "rgba(217, 89, 38, 0.38)"        # laranja esmaecido: barras sem destaque
CINZA_LINHA = "rgba(128, 128, 128, 0.90)"
CINZA_PREENCHE = "rgba(128, 128, 128, 0.30)"
# amarelo -> vermelho: luminosidade parecida em toda a rampa, para nenhum extremo sumir no fundo claro
# nem no escuro (o mapa não tem tiles); os valores mais altos são os que mais importam.
ESCALA_TAXA = ["#eeaa3a", "#ee8236", "#e5572f", "#dc3a35", "#cf1f3a"]

FUNDO_ESTADO = "rgba(128, 128, 128, 0.10)"
LINHA_ESTADO = "rgba(128, 128, 128, 0.70)"
FUNDO_ESTADO_ATIVO = "rgba(217, 89, 38, 0.14)"

CONFIG = {"displayModeBar": False}
CONFIG_MAPA = {"displayModeBar": False, "scrollZoom": True}
CONFIG_LOCALIZADOR = {"displayModeBar": False, "staticPlot": True}
_MAPA_SEM_FUNDO = {"version": 8, "sources": {},
                   "layers": [{"id": "fundo", "type": "background", "paint": {"background-color": "rgba(0,0,0,0)"}}]}


def _base(fig: go.Figure, altura: int, **layout) -> go.Figure:
    padrao = dict(height=altura, margin=dict(l=0, r=0, t=8, b=0), showlegend=False,
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  separators=",.", font=dict(size=13))                     # ",." = pt-BR (1.234,5)
    fig.update_layout(**{**padrao, **layout})
    return fig


def _curto(faixa: str) -> str:
    """'15 a 19 anos' -> '15 a 19'; '65 anos ou mais' -> '65+' (rótulos curtos no eixo)."""
    return faixa.replace(" anos ou mais", "+").replace(" anos", "")


def _destaque_maximo(valores: pd.Series) -> list[str]:
    """Ênfase: a maior barra na cor cheia, as demais esmaecidas."""
    return [COR_TAXA if v == valores.max() else TAXA_SUAVE for v in valores]


def _barras(rotulos, valores, textos, cores, horizontal: bool, hover: str, altura: int) -> go.Figure:
    valores = list(valores)
    teto = max(valores, default=0) * 1.22 or 1                            # folga para o rótulo fora da barra
    eixo_x, eixo_y = (valores, rotulos) if horizontal else (rotulos, valores)
    fig = go.Figure(go.Bar(x=eixo_x, y=eixo_y, orientation="h" if horizontal else "v", text=textos,
                           textposition="outside", cliponaxis=False,
                           marker=dict(color=cores, cornerradius=4), hovertemplate=hover + "<extra></extra>"))
    valor = dict(visible=False, range=[0, teto], fixedrange=True)
    categoria = dict(title=None, showgrid=False, showline=False, ticks="", fixedrange=True, automargin=True)
    if horizontal:
        fig.update_layout(xaxis=valor, yaxis=dict(autorange="reversed", **categoria))
    else:
        fig.update_layout(xaxis=categoria, yaxis=valor)
    return _base(fig, altura, bargap=0.4)


def barras_taxa_por_idade(por_idade: pd.DataFrame, altura: int = 340) -> go.Figure:
    d = por_idade.dropna(subset=["taxa_analfabetismo"])
    v = d["taxa_analfabetismo"]
    return _barras(d["grupo_idade"].map(_curto), v, v.map(dados.formatar_pct), _destaque_maximo(v), False,
                   "<b>%{x} anos</b><br>Analfabetismo: %{y:.1f}%", altura)


def barras_taxa_por_cor(por_cor: pd.DataFrame, altura: int = 340) -> go.Figure:
    d = por_cor.dropna(subset=["taxa_analfabetismo"]).sort_values("taxa_analfabetismo", ascending=False)
    v = d["taxa_analfabetismo"]
    return _barras(d["cor_raca"], v, v.map(dados.formatar_pct), _destaque_maximo(v), True,
                   "<b>%{y}</b><br>Analfabetismo: %{x:.1f}%", altura)


def ranking_volume(top: pd.DataFrame, altura: int = 400) -> go.Figure:
    v = top["nao_alfabetizadas"]
    return _barras(top["rotulo"], v, v.map(dados.formatar_int), COR_VOLUME, True,
                   "<b>%{y}</b><br>Não alfabetizados: %{x:,.0f}", altura)


def ranking_taxa(top: pd.DataFrame, altura: int = 400) -> go.Figure:
    v = top["taxa_analfabetismo"]
    return _barras(top["rotulo"], v, v.map(dados.formatar_pct), COR_TAXA, True,
                   "<b>%{y}</b><br>Analfabetismo: %{x:.1f}%", altura)


def rosca(rotulos, valores, cores, destaque: str, legenda_centro: str, altura: int = 340) -> go.Figure:
    """Rosca com o número principal no centro (`destaque`) e rótulos fora das fatias."""
    fig = go.Figure(go.Pie(labels=rotulos, values=valores, hole=0.66, sort=False, direction="clockwise",
                           marker=dict(colors=cores), textposition="outside",
                           texttemplate="%{label}<br><b>%{percent:.1%}</b>",
                           hovertemplate="<b>%{label}</b><br>%{value:,.0f} pessoas · %{percent:.1%}<extra></extra>"))
    fig.add_annotation(text=f"<span style='font-size:24px'><b>{destaque}</b></span><br>{legenda_centro}",
                       x=0.5, y=0.5, showarrow=False, align="center")
    return _base(fig, altura, margin=dict(l=72, r=72, t=24, b=24))


def rosca_alfabetizacao(comp: pd.DataFrame, altura: int = 340) -> go.Figure:
    """Ênfase no problema: 'Não alfabetizadas' em laranja, 'Alfabetizadas' em cinza (evita verde × vermelho)."""
    cores = {dados.ALFABETIZADAS: CINZA_PREENCHE, dados.NAO_ALFABETIZADAS: COR_TAXA}
    total = comp["populacao"].sum()
    nao = comp.loc[comp["alfabetizacao"] == dados.NAO_ALFABETIZADAS, "populacao"].sum()
    return rosca(comp["alfabetizacao"], comp["populacao"], [cores[a] for a in comp["alfabetizacao"]],
                 dados.formatar_pct(nao / total * 100 if total else None), "não alfabetizadas", altura)


def rosca_sexo(por_sexo: pd.DataFrame, altura: int = 340) -> go.Figure:
    cores = {"Homens": COR_HOMENS, "Mulheres": COR_MULHERES}
    return rosca(por_sexo["sexo"], por_sexo["nao_alfabetizadas"], [cores[s] for s in por_sexo["sexo"]],
                 dados.formatar_int(por_sexo["nao_alfabetizadas"].sum()), "não alfabetizados", altura)


def histograma(taxas: pd.Series, altura: int = 360, faixas: int = 30) -> go.Figure:
    """Distribuição das taxas municipais, com a mediana marcada."""
    taxas = taxas.dropna()
    contagem, bordas = np.histogram(taxas, bins=faixas)
    largura = bordas[1] - bordas[0]
    mediana = float(np.median(taxas))
    fig = go.Figure(go.Bar(x=(bordas[:-1] + bordas[1:]) / 2, y=contagem, width=largura * 0.92,
                           marker=dict(color=COR_TAXA, cornerradius=3),
                           customdata=np.column_stack([bordas[:-1], bordas[1:]]),
                           hovertemplate="Municípios: <b>%{y}</b><br>Taxa de %{customdata[0]:.1f}% a "
                                         "%{customdata[1]:.1f}%<extra></extra>"))
    fig.add_vline(x=mediana, line=dict(color=CINZA_LINHA, width=2),
                  annotation=dict(text=f"mediana {dados.formatar_pct(mediana)}", yanchor="bottom"),
                  annotation_position="top")
    fig.update_xaxes(ticksuffix="%", title="Taxa de analfabetismo do município", fixedrange=True)
    fig.update_yaxes(title="Nº de municípios", range=[0, contagem.max() * 1.18], fixedrange=True)
    return _base(fig, altura, margin=dict(l=0, r=0, t=28, b=0))


def box_regioes(tm: pd.DataFrame, regiao_destaque: str | None = None, altura: int = 400) -> go.Figure:
    """Um box por região, da maior para a menor mediana. Com `regiao_destaque`, só ela ganha cor."""
    ordem = tm.groupby("regiao")["taxa_analfabetismo"].median().sort_values(ascending=False).index
    fig = go.Figure()
    for regiao in ordem:
        d = tm[tm["regiao"] == regiao]
        ativa = regiao_destaque is None or regiao == regiao_destaque
        linha, fundo = (COR_TAXA, TAXA_SUAVE) if ativa else (CINZA_LINHA, CINZA_PREENCHE)
        fig.add_trace(go.Box(y=d["taxa_analfabetismo"], name=regiao, text=d["municipio"], boxpoints="outliers",
                             line=dict(color=linha, width=1.6), fillcolor=fundo,
                             marker=dict(color=linha, size=4, opacity=0.75)))
    fig.update_xaxes(title=None, fixedrange=True)
    fig.update_yaxes(ticksuffix="%", title="Taxa de analfabetismo do município", rangemode="tozero",
                     fixedrange=True)
    return _base(fig, altura)


def _enquadrar(caixa: tuple[float, float, float, float], largura_px: int = 900, altura_px: int = 560,
               folga: float = 0.15) -> tuple[dict, float]:
    """Centro e zoom que cabem a caixa (lat0, lat1, lon0, lon1); 512 px × 2^zoom cobrem 360° (Mercator).
    `folga` é quanto se afasta o zoom (em níveis) para sobrar margem."""
    lat0, lat1, lon0, lon1 = caixa
    esticar = 1 / np.cos(np.radians((lat0 + lat1) / 2))
    z_lon = np.log2(largura_px / 512 * 360 / max(lon1 - lon0, 0.5))
    z_lat = np.log2(altura_px / 512 * 360 / (max(lat1 - lat0, 0.5) * esticar))
    return {"lat": (lat0 + lat1) / 2, "lon": (lon0 + lon1) / 2}, float(min(z_lon, z_lat) - folga)


def _anel_principal(feicao: dict) -> list:
    """Contorno externo do maior polígono do estado: ilhas distantes (Fernando de Noronha, Trindade)
    ficam de fora e não esticam o enquadramento."""
    geo = feicao["geometry"]
    poligonos = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    return max((p[0] for p in poligonos), key=len)


def _caixa(contornos: dict, sigla: str | None = None) -> tuple[float, float, float, float]:
    """Caixa (lat0, lat1, lon0, lon1) de um estado, ou do Brasil quando `sigla` é None."""
    pontos = [pt for f in contornos["features"] if sigla in (None, f["properties"]["sigla_uf"])
              for pt in _anel_principal(f)]
    lons, lats = [p[0] for p in pontos], [p[1] for p in pontos]
    return min(lats), max(lats), min(lons), max(lons)


def _tracos_estados(contornos: dict, destaque: str | None) -> list[go.Choroplethmap]:
    """Polígonos dos 27 estados (cinza) e, por cima, o estado em foco (laranja, contorno mais grosso).
    Sem hover e sem escala: são só o cenário. Cores translúcidas servem nos dois temas."""
    def traco(geojson, siglas, fundo, linha, largura):
        return go.Choroplethmap(geojson=geojson, featureidkey="properties.sigla_uf", locations=siglas,
                                z=[0] * len(siglas), zmin=0, zmax=1, colorscale=[[0, fundo], [1, fundo]],
                                marker=dict(line=dict(color=linha, width=largura)), showscale=False,
                                hoverinfo="skip")
    tracos = [traco(contornos, [f["properties"]["sigla_uf"] for f in contornos["features"]],
                    FUNDO_ESTADO, LINHA_ESTADO, 1)]
    if destaque:
        so_ele = {"type": "FeatureCollection",
                  "features": [f for f in contornos["features"] if f["properties"]["sigla_uf"] == destaque]}
        tracos.append(traco(so_ele, [destaque], FUNDO_ESTADO_ATIVO, COR_TAXA, 2.5))
    return tracos


def _rotulos_estados(contornos: dict, excluir: str | None) -> go.Scattermap:
    """Sigla de cada estado (menos `excluir`) no centro do seu maior polígono, em cinza translúcido."""
    lat, lon, sigla = [], [], []
    for f in contornos["features"]:
        if f["properties"]["sigla_uf"] == excluir:
            continue
        anel = _anel_principal(f)
        lon.append(sum(p[0] for p in anel) / len(anel))
        lat.append(sum(p[1] for p in anel) / len(anel))
        sigla.append(f["properties"]["sigla_uf"])
    return go.Scattermap(lat=lat, lon=lon, text=sigla, mode="text", textfont=dict(size=12, color=CINZA_LINHA),
                         hoverinfo="skip", showlegend=False)


def mapa(tm: pd.DataFrame, contornos: dict | None = None, uf: str | None = None, altura: int = 560) -> go.Figure:
    """Bolhas nos centroides: tamanho cresce com a população 15+, cor = taxa. Maiores desenhadas primeiro.
    Com `contornos`, desenha os limites dos estados por baixo; com `uf`, enquadra esse estado deixando os
    vizinhos visíveis ao redor (sem `uf`, enquadra o Brasil)."""
    d = tm.dropna(subset=["lat", "lon", "taxa_analfabetismo"]).sort_values("populacao", ascending=False)
    d = d.assign(tamanho=np.sqrt(d["populacao"]))       # raiz: sem ela Goiânia engole os municípios pequenos
    if contornos:
        centro, zoom = _enquadrar(_caixa(contornos, uf), largura_px=760 if uf else 900, altura_px=altura,
                                  folga=0.7 if uf else 0.15)
    else:
        centro, zoom = _enquadrar((d["lat"].min(), d["lat"].max(), d["lon"].min(), d["lon"].max()),
                                  altura_px=altura)
    bolhas = px.scatter_map(d, lat="lat", lon="lon", size="tamanho", size_max=26, opacity=0.9,
                            color="taxa_analfabetismo", color_continuous_scale=ESCALA_TAXA, hover_name="municipio",
                            custom_data=["populacao", "nao_alfabetizadas", "taxa_analfabetismo"],
                            center=centro, zoom=zoom, map_style=_MAPA_SEM_FUNDO)
    bolhas.update_traces(marker_sizemin=3, hovertemplate="<b>%{hovertext}</b><br>Analfabetismo: %{customdata[2]:.1f}%<br>"
                                                         "Pessoas 15+: %{customdata[0]:,.0f}<br>"
                                                         "Não alfabetizadas: %{customdata[1]:,.0f}<extra></extra>")
    # go.Figure(data=[...]) e não fig.data = ...: o Plotly não deixa acrescentar traços por atribuição
    cenario = ([*_tracos_estados(contornos, uf), *([_rotulos_estados(contornos, uf)] if uf else [])]
               if contornos else [])                      # siglas dos vizinhos só quando há um estado em foco
    fig = go.Figure(data=[*cenario, *bolhas.data], layout=bolhas.layout)
    fig.update_layout(coloraxis_colorbar=dict(title=dict(text="Analfabetismo"), ticksuffix="%", thickness=10,
                                              len=0.6, outlinewidth=0))
    return _base(fig, altura, margin=dict(l=0, r=0, t=0, b=0))


def mapa_localizador(contornos: dict, uf: str, altura: int = 230) -> go.Figure:
    """Miniatura estática do Brasil com o estado `uf` em destaque (onde ele fica em relação aos demais)."""
    centro, zoom = _enquadrar(_caixa(contornos), largura_px=150, altura_px=altura, folga=0.1)   # coluna estreita: ~170 px
    fig = go.Figure(_tracos_estados(contornos, uf))
    fig.update_layout(map=dict(style=_MAPA_SEM_FUNDO, center=centro, zoom=zoom), dragmode=False)
    return _base(fig, altura, margin=dict(l=0, r=0, t=0, b=0))
