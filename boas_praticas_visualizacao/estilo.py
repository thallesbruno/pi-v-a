"""
estilo.py — paleta e ajustes comuns das figuras (só Plotly + numpy, sem Streamlit).

As figuras "boas" funcionam nos temas claro e escuro do Streamlit sem detectar o tema:
  • fundo transparente; texto, grade e eixos herdados do tema (st.plotly_chart aplica theme="streamlit");
  • cores das marcas com contraste >= 3:1 contra #ffffff e #0e1117 (validadas com validate_palette.js);
  • tons neutros e "suaves" com transparência (rgba), que assumem o fundo do tema ativo;
  • mapa sem camada de fundo (tiles), que seria claro ou escuro, nunca os dois.

SEMÂNTICA DAS CORES: azul = os dados · laranja = o destaque (o que o leitor deve olhar) · cinza = contexto.
"""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

AZUL = "#3987e5"
LARANJA = "#d95926"
AQUA = "#199e70"
AMARELO = "#c98500"
MAGENTA = "#d55181"
CINZA_LINHA = "rgba(128, 128, 128, 0.85)"
CINZA_SUAVE = "rgba(128, 128, 128, 0.45)"
CINZA_PREENCHE = "rgba(128, 128, 128, 0.22)"
AZUL_SUAVE = "rgba(57, 135, 229, 0.30)"
LARANJA_SUAVE = "rgba(217, 89, 38, 0.30)"

# escala sequencial de UM matiz (claro -> escuro) e divergente (azul <- cinza -> laranja)
ESCALA_AZUL = ["#c9defa", "#8fbcf0", "#5598e7", "#2a78d6", "#184f95"]
ESCALA_DIVERGENTE = ["#184f95", "#5598e7", "#c9c9c9", "#ee9a70", "#a83d12"]
# ordem fixa das categorias (as cores seguem a entidade, não o ranking)
COR_REGIAO = {"Sudeste": AZUL, "Sul": LARANJA, "Nordeste": AQUA, "Centro-Oeste": AMARELO, "Norte": MAGENTA}

CONFIG = {"displayModeBar": False}
MAPA_SEM_FUNDO = {"version": 8, "sources": {},
                  "layers": [{"id": "fundo", "type": "background", "paint": {"background-color": "rgba(0,0,0,0)"}}]}


def base(fig: go.Figure, altura: int, **layout) -> go.Figure:
    """Aparência comum: fundo transparente, fonte 16 (legível nos slides), números no padrão pt-BR (1.234,5)."""
    padrao = dict(height=altura, margin=dict(l=0, r=0, t=8, b=0), showlegend=False,
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  separators=",.", font=dict(size=16))
    fig.update_layout(**{**padrao, **layout})
    return fig


def anel_principal(feicao: dict) -> list:
    """Contorno do maior polígono do estado (ilhas distantes não esticam o enquadramento)."""
    geo = feicao["geometry"]
    poligonos = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
    return max((p[0] for p in poligonos), key=len)


def enquadrar_brasil(contornos: dict, largura_px: int = 700, altura_px: int = 440) -> tuple[dict, float]:
    """Centro e zoom que cabem o Brasil (Mercator: 512 px × 2^zoom cobrem 360°)."""
    pontos = [p for f in contornos["features"] for p in anel_principal(f)]
    lons, lats = [p[0] for p in pontos], [p[1] for p in pontos]
    lat0, lat1, lon0, lon1 = min(lats), max(lats), min(lons), max(lons)
    esticar = 1 / np.cos(np.radians((lat0 + lat1) / 2))
    z = min(np.log2(largura_px / 512 * 360 / (lon1 - lon0)), np.log2(altura_px / 512 * 360 / ((lat1 - lat0) * esticar)))
    return {"lat": (lat0 + lat1) / 2, "lon": (lon0 + lon1) / 2}, float(z - 0.1)
