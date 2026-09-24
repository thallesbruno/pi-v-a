"""
gerar_slides.py — monta slides/boas_praticas_visualizacao.pptx (24 slides, 2 seções) com python-pptx.

Uso:  python baixar_dados.py && python gerar_imagens.py && python gerar_slides.py

Os números citados nos slides são calculados dos dados (dados.py), não digitados. As imagens vêm de
slides/imagens/ (geradas por gerar_imagens.py a partir do próprio app Streamlit).
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import dados as dd
import exemplos as ex

RAIZ = Path(__file__).parent
IMG = RAIZ / "slides" / "imagens"
SAIDA = RAIZ / "slides" / "boas_praticas_visualizacao.pptx"

# Paleta do material (a mesma dos gráficos: azul = dados, laranja = destaque)
NAVY, INK, MUTED = "0B1F33", "1F2933", "5B6770"
AZUL, LARANJA = "3987E5", "D95926"
CARTAO, BORDA, BRANCO = "F1F5F9", "D9E0E7", "FFFFFF"
LARANJA_CLARO, AZUL_CLARO = "FCEBE3", "E6F0FD"
FONTE, MONO = "Calibri", "Courier New"
W, H = 13.333, 7.5
MARGEM = 0.6
TOTAL = 24


# ----------------------------------------------------------------------------
# AUXILIARES DE DESENHO
# ----------------------------------------------------------------------------
def rgb(hexa: str) -> RGBColor:
    return RGBColor.from_string(hexa)


def _formatar(run, tam, negrito=False, cor=INK, fonte=FONTE, italico=False):
    run.font.size = Pt(tam)
    run.font.bold = negrito
    run.font.italic = italico
    run.font.name = fonte
    run.font.color.rgb = rgb(cor)


def texto(slide, x, y, w, h, paragrafos, tam=16, negrito=False, cor=INK, alinh=PP_ALIGN.LEFT,
          ancora=MSO_ANCHOR.TOP, fonte=FONTE, espaco=0):
    """Caixa de texto sem margens internas. `paragrafos`: str ou lista de str / listas de (texto, estilo)."""
    caixa_ = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caixa_.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ancora
    if isinstance(paragrafos, str):
        paragrafos = [paragrafos]
    for i, par in enumerate(paragrafos):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = alinh
        if espaco and i < len(paragrafos) - 1:
            p.space_after = Pt(espaco)
        trechos = [(par, {})] if isinstance(par, str) else par
        for t, estilo in trechos:
            r = p.add_run()
            r.text = t
            _formatar(r, estilo.get("tam", tam), estilo.get("negrito", negrito), estilo.get("cor", cor),
                      estilo.get("fonte", fonte), estilo.get("italico", False))
    return caixa_


def marcadores(slide, x, y, w, h, itens, tam=16, cor=INK, espaco=8):
    """Lista com marcador de verdade (a:buChar), não um '•' digitado. Um item pode ter trecho em negrito: (negrito, resto)."""
    caixa_ = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caixa_.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, item in enumerate(itens):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if i < len(itens) - 1:
            p.space_after = Pt(espaco)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(Inches(0.28))))
        pPr.set("indent", str(-int(Inches(0.28))))
        bu_cor = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(bu_cor, qn("a:srgbClr")).set("val", LARANJA)
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•")
        trechos = [(item, False)] if isinstance(item, str) else [(item[0], True), (item[1], False)]
        for t, neg in trechos:
            r = p.add_run()
            r.text = t
            _formatar(r, tam, neg, cor)
    return caixa_


def forma(slide, x, y, w, h, preenche=CARTAO, borda=None, raio=0.05, tipo=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(tipo, Inches(x), Inches(y), Inches(w), Inches(h))
    estilo = s._element.find(qn("p:style"))
    if estilo is not None:                                  # tira sombra/contorno herdados do tema
        s._element.remove(estilo)
    if tipo == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = min(0.5, raio / min(w, h))
    if preenche is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(preenche)
    if borda:
        s.line.color.rgb = rgb(borda)
        s.line.width = Pt(1)
    else:
        s.line.fill.background()
    return s


def chip(slide, x, y, w, h, rotulo, fundo=AZUL, cor=BRANCO, tam=11):
    s = forma(slide, x, y, w, h, fundo, raio=h / 2)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = rotulo
    _formatar(r, tam, True, cor)
    return s


def imagem(slide, nome, x, y, w, h, moldura=True):
    """Coloca a imagem dentro da caixa (x, y, w, h), sem distorcer, centralizada. Devolve (x, y, w, h) usados."""
    caminho = IMG / f"{nome}.png"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho.name} não existe. Rode antes:  python gerar_imagens.py")
    iw, ih = Image.open(caminho).size
    esc = min(w / iw, h / ih)
    pw, ph = iw * esc, ih * esc
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    if moldura:
        forma(slide, px - 0.08, py - 0.08, pw + 0.16, ph + 0.16, BRANCO, BORDA, raio=0.08)
    slide.shapes.add_picture(str(caminho), Inches(px), Inches(py), Inches(pw), Inches(ph))
    return px, py, pw, ph


def fundo(slide, cor):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(cor)


def rodape(slide, n, escuro=False):
    cor = "9FB3C8" if escuro else MUTED
    texto(slide, MARGEM, 7.05, 8, 0.25, "Boas práticas de visualização de dados · dados do IBGE", tam=10, cor=cor)
    texto(slide, W - MARGEM - 1.5, 7.05, 1.5, 0.25, f"{n} / {TOTAL}", tam=10, cor=cor, alinh=PP_ALIGN.RIGHT)


def cabecalho(slide, secao, titulo, n):
    """Selo da seção (bolinha + rótulo), título grande e rodapé."""
    cor = AZUL if secao == 1 else LARANJA
    forma(slide, MARGEM, 0.42, 0.14, 0.14, cor, tipo=MSO_SHAPE.OVAL)
    rotulo = "SEÇÃO 1 · CONCEITOS" if secao == 1 else "SEÇÃO 2 · NA PRÁTICA"
    texto(slide, MARGEM + 0.24, 0.36, 5, 0.26, rotulo, tam=12, negrito=True, cor=cor)
    texto(slide, MARGEM, 0.72, W - 2 * MARGEM, 0.85, titulo, tam=32, negrito=True, cor=INK)
    rodape(slide, n)


def notas(slide, txt: str):
    slide.notes_slide.notes_text_frame.text = txt


def novo(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])            # layout em branco


# ----------------------------------------------------------------------------
# FATOS CALCULADOS DOS DADOS
# ----------------------------------------------------------------------------
def fatos() -> dict:
    d = dd.carregar()
    m, u = d.mun, d.uf
    idx = ex._indice(d)
    por_pib = u.sort_values("pib_bi", ascending=False).reset_index(drop=True)
    por_pc = u.sort_values("pib_per_capita").reset_index(drop=True)
    top3 = u.nlargest(3, "participacao")
    setores = dd.participacao_setores(u)
    med_reg = m.groupby("regiao")["pib_per_capita"].median()
    casos = m[m["populacao"] > 5000].nlargest(1, "pib_per_capita").iloc[0]
    maior_pc = m["pib_per_capita"].max()
    go = u[u["sigla_uf"] == "GO"].iloc[0]
    return dict(
        d=d, n_mun=len(m), n_uf=len(u), pib_tri=m["pib_mil_reais"].sum() / 1e9, pop=int(m["populacao"].sum()),
        go_nome=go["uf"], go_pos=int(por_pib.index[por_pib["sigla_uf"] == "GO"][0]) + 1, go_pib=go["pib_bi"],
        sp_pib=por_pib.iloc[0]["pib_bi"], pc_med=m["pib_per_capita"].median(), pc_max=maior_pc,
        razao=maior_pc / m["pib_per_capita"].median(), idx_br=idx["Brasil"].iloc[-1], idx_go=idx["GO"].iloc[-1],
        med_sul=med_reg["Sul"], med_ne=med_reg["Nordeste"], caso=casos,
        pc_min_uf=por_pc.iloc[0], pc_max_uf=por_pc.iloc[-1], top3=", ".join(top3["sigla_uf"]),
        share3=top3["participacao"].sum(), ap_adm=setores.loc["AP", "Adm. pública"], sp_adm=setores.loc["SP", "Adm. pública"],
        p_menores=(m["populacao"] < 20000).mean() * 100,
    )


# ----------------------------------------------------------------------------
# SLIDES
# ----------------------------------------------------------------------------
def s_capa(prs, f):
    s = novo(prs)
    fundo(s, NAVY)
    forma(s, 0.9, 1.05, 0.22, 0.22, LARANJA, tipo=MSO_SHAPE.OVAL)
    texto(s, 1.3, 0.98, 9, 0.4, "VISUALIZAÇÃO DE DADOS E USABILIDADE", tam=16, negrito=True, cor="9FB3C8")
    texto(s, 0.9, 2.0, 11.6, 2.2, ["Boas práticas de", "visualização de dados"], tam=54, negrito=True, cor=BRANCO)
    texto(s, 0.9, 4.15, 10.5, 1.0, "Do tipo de gráfico à leitura clara: conceitos e exemplos com dados públicos do IBGE",
          tam=22, cor="CADCFC")
    chip(s, 0.9, 5.75, 3.6, 0.42, f"PIB e população · {f['n_mun']:,} municípios".replace(",", "."), LARANJA, tam=13)
    chip(s, 4.7, 5.75, 3.2, 0.42, "Scripts em Streamlit", "1C3A5A", tam=13)
    rodape(s, 1, escuro=True)
    notas(s, "Abertura. Este material tem duas partes: primeiro os conceitos, sem depender de uma base específica; depois a "
             "prática, com os scripts em Streamlit desta pasta, sempre mostrando o mesmo dado num gráfico ruim e num bom.")


def s_agenda(prs, f):
    s = novo(prs)
    texto(s, MARGEM, 0.55, 9, 0.7, "O que vamos ver", tam=36, negrito=True)
    texto(s, MARGEM, 1.3, 11.5, 0.6, "Um gráfico é a resposta a uma pergunta. Se a resposta demora a aparecer, o gráfico falhou.",
          tam=18, cor=MUTED)
    cartoes = [(AZUL, AZUL_CLARO, "1", "Conceitos", "Os principais tipos de gráfico, quando usar cada um e as regras que os deixam claros.",
                "11 slides · barras, linhas, histograma, box plot, dispersão, mapa, composição, heatmap, cor"),
               (LARANJA, LARANJA_CLARO, "2", "Na prática", "Oito exemplos com os mesmos dados: o gráfico ruim ao lado do bom, feitos nos scripts em Streamlit.",
                "10 slides · da base do IBGE ao checklist final")]
    for i, (cor, claro, num, titulo, desc, detalhe) in enumerate(cartoes):
        x = MARGEM + i * 6.2
        forma(s, x, 2.35, 5.9, 4.3, claro, raio=0.12)
        forma(s, x + 0.4, 2.75, 0.9, 0.9, cor, tipo=MSO_SHAPE.OVAL)
        texto(s, x + 0.4, 2.75, 0.9, 0.9, num, tam=36, negrito=True, cor=BRANCO, alinh=PP_ALIGN.CENTER, ancora=MSO_ANCHOR.MIDDLE)
        texto(s, x + 1.55, 2.85, 4.0, 0.7, titulo, tam=30, negrito=True, cor=INK, ancora=MSO_ANCHOR.MIDDLE)
        texto(s, x + 0.4, 4.0, 5.1, 1.5, desc, tam=18, cor=INK)
        texto(s, x + 0.4, 5.6, 5.1, 0.8, detalhe, tam=14, cor=MUTED)
    rodape(s, 2)
    notas(s, "Seção 1 são 11 slides genéricos sobre tipos de gráfico. Seção 2 são 10 slides ligados aos scripts desta pasta. "
             "A ideia central: comece pela pergunta, escolha a forma, e só depois pense em cor e detalhes.")


def s_pergunta_grafico(prs, f, n):
    s = novo(prs)
    cabecalho(s, 1, "Comece pela pergunta, não pelo gráfico", n)
    itens = [("Comparar", "Qual é maior?", "Barras", AZUL), ("Evoluir no tempo", "Como mudou?", "Linhas · áreas", AZUL),
             ("Distribuir", "Como se espalham os valores?", "Histograma · box plot", AZUL),
             ("Relacionar", "Uma medida acompanha a outra?", "Dispersão · bolhas", AZUL),
             ("Compor", "Quanto cada parte pesa?", "Barras empilhadas · treemap", AZUL),
             ("Localizar", "Onde acontece?", "Mapa coroplético", AZUL)]
    cw, ch, gap = 3.9, 2.2, 0.25
    for i, (verbo, pergunta, graf, cor) in enumerate(itens):
        x = MARGEM - 0.03 + (i % 3) * (cw + gap)
        y = 1.85 + (i // 3) * (ch + gap)
        forma(s, x, y, cw, ch, CARTAO, raio=0.1)
        texto(s, x + 0.35, y + 0.3, cw - 0.7, 0.5, verbo, tam=24, negrito=True, cor=LARANJA)
        texto(s, x + 0.35, y + 0.92, cw - 0.7, 0.5, pergunta, tam=16, cor=MUTED)
        texto(s, x + 0.35, y + 1.5, cw - 0.7, 0.5, graf, tam=18, negrito=True, cor=INK)
    notas(s, "Antes de abrir qualquer ferramenta, escreva a pergunta que o gráfico deve responder. O verbo da pergunta escolhe a "
             "família de gráficos. Todos os exemplos seguintes seguem esta lógica.")


def s_conceito(prs, f, n, titulo, fig, quando, itens, cuidado, nota, img_esq=False):
    s = novo(prs)
    cabecalho(s, 1, titulo, n)
    wi, wt = 6.9, 4.9                                            # largura da imagem e da coluna de texto
    xi, xt = (MARGEM, MARGEM + wi + 0.33) if img_esq else (MARGEM + wt + 0.33, MARGEM)
    chip(s, xt, 1.85, 1.45, 0.34, "QUANDO USAR", AZUL, tam=11)
    texto(s, xt, 2.32, wt, 0.95, quando, tam=16, cor=INK)
    marcadores(s, xt, 3.3, wt, 2.4, itens, tam=15, espaco=8)
    forma(s, xt, 5.85, wt, 0.95, LARANJA_CLARO, raio=0.08)
    texto(s, xt + 0.25, 5.85, wt - 0.5, 0.95, [[("Cuidado: ", {"negrito": True, "cor": LARANJA}), (cuidado, {})]],
          tam=14, cor=INK, ancora=MSO_ANCHOR.MIDDLE)
    imagem(s, fig, xi, 1.85, wi, 4.95)
    notas(s, nota)
    return s


def s_dois_graficos(prs, f, n, titulo, figs, legendas, itens, nota):
    s = novo(prs)
    cabecalho(s, 1, titulo, n)
    x = MARGEM
    for nome, leg in zip(figs, legendas):
        imagem(s, nome, x, 1.85, 5.9, 3.75)
        texto(s, x, 5.78, 5.9, 0.35, leg, tam=15, negrito=True, cor=AZUL)
        x += 6.2
    marcadores(s, MARGEM, 6.2, 12.1, 0.75, itens, tam=14, espaco=2)
    notas(s, nota)


def s_evitar(prs, f, n):
    s = novo(prs)
    cabecalho(s, 1, "O que evitar", n)
    cards = [("E7_ruim", "Pizza com muitas fatias", "Ninguém compara ângulos. Use barras ordenadas."),
             ("E1_ruim", "Eixo truncado e cor sem função", "Exagera diferenças e obriga a decorar a legenda."),
             ("E6_ruim", "Arco-íris em valor absoluto", "Sem ordem natural e mostra só onde há mais gente.")]
    cw, gap = 3.9, 0.2
    for i, (fig, tit, txt) in enumerate(cards):
        x = MARGEM - 0.03 + i * (cw + gap)
        forma(s, x, 1.85, cw, 4.15, CARTAO, raio=0.1)
        imagem(s, fig, x + 0.2, 2.0, cw - 0.4, 2.35, moldura=False)
        texto(s, x + 0.3, 4.5, cw - 0.6, 0.4, tit, tam=17, negrito=True, cor=INK)
        texto(s, x + 0.3, 5.0, cw - 0.6, 0.9, txt, tam=14, cor=MUTED)
    texto(s, MARGEM, 6.3, 12.1, 0.5,
          [[("Também: ", {"negrito": True, "cor": LARANJA}), ("gráficos 3D, eixo duplo, rótulo em cada ponto e barras de tamanhos diferentes.", {})]],
          tam=16)
    notas(s, "Estes são os três erros mais comuns dos exemplos da Seção 2, mostrados na versão 'antes'. Eixo duplo e 3D não aparecem "
             "nos scripts, mas valem o alerta: o alinhamento das duas escalas é arbitrário e pode inventar uma correlação.")


def s_base(prs, f, n):
    s = novo(prs)
    cabecalho(s, 2, "A base: PIB e população dos municípios (IBGE)", n)
    stats = [(dd.inteiro(f["n_mun"]), "municípios"), (f"R$ {dd.decimal(f['pib_tri'], 1)} tri", "PIB do Brasil em 2021"),
             (f"{dd.decimal(f['pop'] / 1e6, 0)} mi", "habitantes (estimativa)"), (str(f["n_uf"]), "unidades da federação")]
    for i, (num, rot) in enumerate(stats):
        x, y = MARGEM + (i % 2) * 3.1, 1.95 + (i // 2) * 2.05
        forma(s, x, y, 2.9, 1.85, CARTAO, raio=0.1)
        texto(s, x + 0.25, y + 0.28, 2.5, 0.8, num, tam=34, negrito=True, cor=LARANJA)
        texto(s, x + 0.25, y + 1.2, 2.5, 0.5, rot, tam=14, cor=MUTED)
    forma(s, 7.0, 1.95, 5.73, 3.05, NAVY, raio=0.1)
    texto(s, 7.3, 2.15, 5.1, 0.35, "COMO RODAR", tam=12, negrito=True, cor="9FB3C8")
    texto(s, 7.3, 2.65, 5.2, 2.2, ["pip install -r requirements.txt", "python baixar_dados.py", "streamlit run app.py"],
          tam=16, cor=BRANCO, fonte=MONO, espaco=14)
    texto(s, 7.0, 5.25, 5.73, 1.6,
          ["Fonte: IBGE, SIDRA. Tabelas 5938 (PIB e valor adicionado), 6579 (população estimada) e 4714 (área).",
           "Limites dos estados: malha do IBGE. Detalhes em dados/FONTES.md."], tam=14, cor=MUTED, espaco=6)
    notas(s, "A base é pública e vem direto da API do IBGE, sem chave. Uso 2021 porque é o último ano com o valor adicionado por setor "
             "divulgado para todos os municípios. O PIB é nominal (preços correntes). O PIB per capita de qualquer agregado é a soma do "
             "PIB dividida pela soma da população, nunca a média dos municípios.")


def s_exemplo(prs, f, n, e, titulo, fato, nota):
    s = novo(prs)
    cabecalho(s, 2, titulo, n)
    texto(s, MARGEM, 1.4, 12.1, 0.4, [[("Pergunta: ", {"negrito": True, "cor": LARANJA}), (e.pergunta, {})]], tam=18)
    iw = 5.9
    for i, (lado, rot, cor) in enumerate((("ruim", "ANTES", "9A2B2B"), ("bom", "DEPOIS", AZUL))):
        x = MARGEM + i * (iw + 0.3)
        px, _, _, _ = imagem(s, f"{e.id}_{lado}", x, 2.3, iw, 3.72)
        chip(s, px - 0.08, 1.9, 1.0, 0.3, rot, cor, tam=11)             # alinhado à borda real da imagem
    texto(s, MARGEM, 6.15, 12.1, 0.32, [[("Dado-chave: ", {"negrito": True, "cor": LARANJA}), (fato, {})]], tam=15)
    texto(s, MARGEM, 6.55, 12.1, 0.32, [[("O que mudou: ", {"negrito": True, "cor": AZUL}), (e.mudou, {})]], tam=15)
    notas(s, f"{nota} Dado-chave: {fato}. O que atrapalha no 'antes': " + "; ".join(e.problemas) + ". O que foi feito no 'depois': "
             + "; ".join(e.regras) + f". Abra a página {e.id} do app para ver a tabela de dados e trocar a UF em destaque.")


def s_temas(prs, f, n):
    s = novo(prs)
    cabecalho(s, 2, "As mesmas figuras nos temas claro e escuro", n)
    linhas = [("Tema claro", ["E3_bom", "E4_bom", "E6_bom"], AZUL),
              ("Tema escuro", ["E3_bom_escuro", "E4_bom_escuro", "E6_bom_escuro"], NAVY)]
    for i, (rot, figs, cor) in enumerate(linhas):
        y = 1.75 + i * 2.35
        chip(s, MARGEM, y + 0.85, 1.35, 0.4, rot, cor, tam=13)
        for j, fig in enumerate(figs):
            imagem(s, fig, 2.15 + j * 3.6, y, 3.45, 2.2)
    texto(s, MARGEM, 6.5, 12.1, 0.45,
          "Sem detectar o tema: fundo transparente, texto herdado, cores com contraste ≥ 3:1 nos dois fundos e cinzas translúcidos.",
          tam=15, cor=MUTED)
    notas(s, "O Streamlit troca de tema no navegador e o Python não sabe com segurança qual está ativo. Por isso as figuras não dependem do "
             "tema: fundo transparente, texto e grade herdados, cores validadas contra fundo branco e escuro e tons neutros com "
             "transparência. O mapa não usa camada de fundo, que seria clara ou escura, nunca as duas.")


def s_checklist(prs, f, n):
    s = novo(prs)
    cabecalho(s, 2, "Checklist de boas práticas", n)
    itens = ["Qual é a pergunta?", "O tipo de gráfico responde a ela?", "Barras começam em zero?", "Ordenei e destaquei só o essencial?",
             "Normalizei (per capita, %)?", "As cores têm função e são acessíveis?", "Rótulos e unidades estão claros?",
             "Funciona em tema claro e escuro e há tabela?"]
    for i, it in enumerate(itens):
        x, y = MARGEM + (i // 4) * 3.75, 1.9 + (i % 4) * 1.2
        forma(s, x, y, 0.55, 0.55, LARANJA, tipo=MSO_SHAPE.OVAL)
        texto(s, x, y, 0.55, 0.55, str(i + 1), tam=18, negrito=True, cor=BRANCO, alinh=PP_ALIGN.CENTER, ancora=MSO_ANCHOR.MIDDLE)
        texto(s, x + 0.72, y - 0.03, 2.85, 0.75, it, tam=15, cor=INK, ancora=MSO_ANCHOR.MIDDLE)
    forma(s, 8.3, 1.85, 4.43, 4.95, CARTAO, raio=0.1)
    texto(s, 8.6, 2.05, 3.9, 0.35, "FONTES E LEITURA", tam=12, negrito=True, cor=LARANJA)
    texto(s, 8.6, 2.55, 3.9, 4.1,
          ["IBGE, SIDRA: PIB dos Municípios (t. 5938), população estimada (t. 6579), área (t. 4714).",
           "IBGE, malha estadual (GeoJSON).",
           "Wilke, C. Fundamentals of Data Visualization. O'Reilly, 2019.",
           "Cairo, A. The Truthful Art. New Riders, 2016.",
           "Tufte, E. The Visual Display of Quantitative Information. Graphics Press, 1983."],
          tam=13, cor=INK, espaco=8)
    notas(s, "Feche com o checklist: são as perguntas que fazemos antes de publicar qualquer gráfico. Os scripts, a base e os slides "
             "estão na pasta boas_praticas_visualizacao do repositório.")


# ----------------------------------------------------------------------------
# MONTAGEM
# ----------------------------------------------------------------------------
def montar() -> Presentation:
    f = fatos()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    ex_por_id = {e.id: e for e in ex.EXEMPLOS}

    s_capa(prs, f)
    s_agenda(prs, f)
    # ---- Seção 1 (3 a 13)
    s_pergunta_grafico(prs, f, 3)
    s_conceito(prs, f, 4, "Barras: a escolha segura para comparar", "E1_bom",
               "Comparar valores entre categorias: quem é maior e por quanto.",
               ["Ordene do maior para o menor", "A base em zero: o comprimento é o dado",
                "Horizontais quando os nomes são longos", "Uma cor só; destaque apenas o que importa"],
               "eixo truncado exagera diferenças e engana o leitor.",
               "Barras são o gráfico mais fácil de ler porque comparamos comprimentos alinhados. Por isso a base em zero é inegociável.")
    s_conceito(prs, f, 5, "Linhas e áreas: para mostrar tempo", "cat_area",
               "Evolução ao longo do tempo. Áreas empilhadas quando a soma das partes também importa.",
               ["Tempo sempre no eixo horizontal", "Poucas séries; destaque 2 a 4 e deixe o resto em cinza",
                "Rótulo direto no fim da linha ou legenda curta", "Diga se os valores são nominais ou reais"],
               "muitas linhas iguais viram espaguete ilegível.",
               "Linhas mostram a forma da mudança. Séries em dinheiro, como o PIB nominal, misturam crescimento real e inflação: "
               "avise o leitor.", img_esq=True)
    s_conceito(prs, f, 6, "Histograma: mostra a forma da distribuição", "E3_bom",
               "Ver como os valores de uma única medida se espalham: onde concentram e onde há cauda.",
               ["Escolha faixas suficientes para ver a forma", "Distribuição muito assimétrica pede escala log",
                "Marque a mediana ou uma referência", "Barras encostadas: cada uma é um intervalo"],
               "poucas faixas escondem a forma; muitas viram ruído.",
               "O histograma responde 'como se distribuem?'. Com dados muito assimétricos, como o PIB per capita municipal, "
               "a escala linear joga quase tudo numa barra.")
    s_conceito(prs, f, 7, "Box plot: compara distribuições entre grupos", "E4_bom",
               "Comparar várias distribuições lado a lado, com mediana, quartis e valores extremos.",
               ["A caixa guarda a metade central dos casos; o traço é a mediana", "Os pontos são casos extremos, não erros",
                "Ordene os grupos pela mediana", "Poucos dados por grupo? Prefira mostrar os pontos"],
               "sem explicar a leitura, o público não técnico não entende a caixa.",
               "O box plot resume uma distribuição em cinco números. Vale explicar a leitura uma vez, com um exemplo.", img_esq=True)
    s_conceito(prs, f, 8, "Dispersão: relação entre duas medidas", "E5_bom",
               "Ver se duas medidas andam juntas e quais casos fogem do padrão.",
               ["Correlação não é causa", "Escala log quando os dados variam em ordens de grandeza",
                "Transparência quando os pontos se sobrepõem", "Rotule só os casos-chave"],
               "milhares de pontos sem transparência viram uma mancha.",
               "A dispersão mostra padrão e exceções. Retas de referência ajudam a ler a distância até uma razão constante.")
    s_conceito(prs, f, 9, "Mapas: use quando o lugar importa", "E6_bom",
               "Comparar regiões quando a localização é parte da resposta.",
               ["Normalize: taxa per capita, não o total", "Coroplético pinta áreas; bolhas marcam pontos",
                "Escala de um matiz, em faixas por quantis", "Legenda com valores e unidades"],
               "mapa de valor absoluto quase sempre repete o mapa da população.",
               "Um mapa de totais mostra onde há mais gente. Para ver desigualdade, normalize por habitante.", img_esq=True)
    s_conceito(prs, f, 10, "Composição: partes de um todo", "cat_treemap",
               "Mostrar quanto cada parte pesa no total, ou como a composição muda entre grupos.",
               ["Pizza só com poucas fatias e diferenças grandes", "Barras empilhadas 100% comparam composições",
                "Treemap: hierarquia e proporção pela área", "Agrupe a cauda em 'Demais'"],
               "comparar ângulos de fatias é difícil para o olho.",
               "O olho compara comprimentos melhor que ângulos ou áreas. Barras ordenadas costumam vencer a pizza.")
    s_dois_graficos(prs, f, 11, "Muitos números? Use cor ou repita o gráfico", ["E8_bom", "cat_small_multiples"],
                    ["Heatmap: padrões numa tabela grande", "Pequenos múltiplos: uma forma por painel"],
                    ["Heatmap: escala de um matiz, valores escritos, linhas ordenadas",
                     "Pequenos múltiplos: mesmo eixo em todos os painéis, para comparar formas"],
                    "Heatmaps transformam uma tabela em padrões. Pequenos múltiplos evitam o espaguete: em vez de 5 linhas juntas, "
                    "cinco painéis com a mesma escala.")
    s_conceito(prs, f, 12, "Cor, acessibilidade e tema claro e escuro", "cat_paletas",
               "Cor é um canal de informação, não enfeite. Cada tipo de dado pede um tipo de paleta.",
               ["Categórica para identidade, sequencial para magnitude, divergente para dois lados",
                "Nunca só cor: use rótulo, posição ou forma também", "Cerca de 8% dos homens têm daltonismo; evite o arco-íris",
                "Teste em tema claro e escuro"],
               "verde e vermelho juntos falham para quem tem daltonismo.",
               "Regra prática: azul para os dados, laranja para o destaque, cinza para o contexto. É a que os scripts seguem.", img_esq=True)
    s_evitar(prs, f, 13)
    # ---- Seção 2 (14 a 24)
    s_base(prs, f, 14)
    fatos_ex = {
        "E1": (f"São Paulo, R$ {dd.inteiro(f['sp_pib'])} bi; {f['go_nome']} é a {f['go_pos']}ª com R$ {dd.inteiro(f['go_pib'])} bi",
               "Barras: ordenar, base zero e uma cor"),
        "E2": (f"Brasil {dd.inteiro(f['idx_br'])} e {f['go_nome']} {dd.inteiro(f['idx_go'])} (índice, 2002 = 100, nominal)",
               "Linhas: destacar poucas séries e rotular direto"),
        "E3": (f"mediana R$ {dd.inteiro(f['pc_med'] / 1000)} mil; máximo R$ {dd.inteiro(f['pc_max'] / 1000)} mil, {dd.inteiro(f['razao'])} vezes a mediana",
               "Histograma: a escala log revela a forma"),
        "E4": (f"mediana de R$ {dd.inteiro(f['med_sul'] / 1000)} mil no Sul e R$ {dd.inteiro(f['med_ne'] / 1000)} mil no Nordeste",
               "Box plot: eixo log e ordem pela mediana"),
        "E5": (f"{f['caso']['municipio']} ({f['caso']['sigla_uf']}) tem R$ {dd.inteiro(f['caso']['pib_per_capita'] / 1000)} mil por habitante com "
               f"{dd.inteiro(f['caso']['populacao'])} moradores", "Dispersão: log-log, transparência e retas de referência"),
        "E6": (f"o PIB per capita vai de R$ {dd.inteiro(f['pc_min_uf']['pib_per_capita'] / 1000)} mil ({f['pc_min_uf']['sigla_uf']}) a "
               f"R$ {dd.inteiro(f['pc_max_uf']['pib_per_capita'] / 1000)} mil ({f['pc_max_uf']['sigla_uf']})",
               "Mapa: per capita, um matiz e faixas por quantis"),
        "E7": (f"{f['top3']} somam {dd.pct(f['share3'])} do PIB", "Composição: Top 8 e 'Demais' em vez de 27 fatias"),
        "E8": (f"a administração pública pesa {dd.decimal(f['ap_adm'], 0)}% do valor adicionado no AP e {dd.decimal(f['sp_adm'], 0)}% em SP",
               "Heatmap: percentuais, um matiz e números na célula"),
    }
    notas_ex = {"E1": "Mesmo dado, duas leituras. À esquerda o leitor precisa decorar cores e adivinhar a ordem; à direita o ranking é imediato.",
                "E2": "Índice base 2002 = 100 compara o ritmo de crescimento, não o tamanho. O PIB é nominal: parte do crescimento é inflação.",
                "E3": "Com escala linear, 5.500 municípios caem numa barra. Na escala log a distribuição aparece e a mediana se destaca.",
                "E4": "O eixo log permite ver as caixas. A região da UF escolhida ganha cor; as demais ficam em cinza.",
                "E5": "As retas cinzas são PIB per capita constante: quanto mais acima da reta, mais rico por habitante.",
                "E6": "O mapa de valor absoluto e o de per capita contam histórias opostas. O da direita usa cinco faixas com o mesmo número de UFs.",
                "E7": "Em vez de 27 fatias, oito barras e um bloco 'Demais'. A frase de conclusão está no próprio gráfico.",
                "E8": "Com valores absolutos, São Paulo domina tudo. Com percentuais, cada UF mostra a sua estrutura."}
    for i, e in enumerate(ex.EXEMPLOS):
        fato, titulo = fatos_ex[e.id]
        s_exemplo(prs, f, 15 + i, ex_por_id[e.id], titulo, fato, notas_ex[e.id])
    s_temas(prs, f, 23)
    s_checklist(prs, f, 24)
    return prs


def main() -> None:
    prs = montar()
    n = len(prs.slides)
    assert n <= 25, f"{n} slides: o limite é 25"
    prs.save(SAIDA)
    print(f"Gravado: {SAIDA.relative_to(RAIZ)}  ({n} slides)")


if __name__ == "__main__":
    main()
