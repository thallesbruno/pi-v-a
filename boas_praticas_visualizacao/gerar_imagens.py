"""
gerar_imagens.py — captura cada figura do app (modo imagem) em PNG, para usar nos slides.

Uso:  python gerar_imagens.py                      (tema claro para todas + tema escuro para as versões "depois")
      python gerar_imagens.py --figuras E5_bom,E7_bom   (só essas, nos dois temas)

Sobe o Streamlit em segundo plano, abre cada figura com Playwright (Edge ou Chromium) e salva em
slides/imagens/<id>.png (claro) e <id>_escuro.png (escuro). Requer:  pip install playwright
(se não houver o Edge: playwright install chromium).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import exemplos as ex

RAIZ = Path(__file__).parent
SAIDA = RAIZ / "slides" / "imagens"
PORTA = 8611
LARGURA = {}                                                # largura da captura, em px (padrão: 700)


def subir_app() -> subprocess.Popen:
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true",
                             "--server.port", str(PORTA), "--browser.gatherUsageStats", "false"],
                            cwd=RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"http://localhost:{PORTA}/", timeout=2)
            return proc
        except Exception:
            time.sleep(1)
    proc.terminate()
    raise RuntimeError("O app Streamlit não subiu em 60 s.")


def abrir_navegador(p):
    try:
        return p.chromium.launch(channel="msedge", headless=True)
    except Exception:
        return p.chromium.launch(headless=True)


def capturar(nav, id_figura: str, tema: str, destino: Path, mapa: bool) -> None:
    pg = nav.new_page(viewport={"width": LARGURA.get(id_figura, 700), "height": 900}, device_scale_factor=2,
                      color_scheme=tema)
    try:
        pg.goto(f"http://localhost:{PORTA}/?embed=true&modo=imagem&fig={id_figura}&uf=GO", wait_until="networkidle")
        alvo = pg.locator('[data-testid="stPlotlyChart"]').first
        alvo.wait_for(state="visible", timeout=60000)
        pg.wait_for_timeout(5500 if mapa else 2200)              # mapas (WebGL) demoram mais para desenhar
        alvo.screenshot(path=str(destino))
    finally:
        pg.close()


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description="Captura as figuras do app em PNG para os slides.")
    ap.add_argument("--figuras", help="ids separados por vírgula (ex.: E5_bom,E7_bom); padrão: todas")
    escolhidas = ap.parse_args().figuras
    SAIDA.mkdir(parents=True, exist_ok=True)
    mapas = {f"{e.id}_{l}" for e in ex.EXEMPLOS if e.mapa for l in ("ruim", "bom")}
    claro = [f"{e.id}_{l}" for e in ex.EXEMPLOS for l in ("ruim", "bom")] + list(ex.CATALOGO)
    escuro = [f"{e.id}_bom" for e in ex.EXEMPLOS]
    if escolhidas:
        pedidas = escolhidas.split(",")
        claro = [f for f in claro if f in pedidas]
        escuro = [f for f in pedidas if f in escuro]
    proc = subir_app()
    try:
        with sync_playwright() as p:
            nav = abrir_navegador(p)
            for id_figura in claro:
                capturar(nav, id_figura, "light", SAIDA / f"{id_figura}.png", id_figura in mapas)
                print("OK  ", id_figura)
            for id_figura in escuro:
                capturar(nav, id_figura, "dark", SAIDA / f"{id_figura}_escuro.png", id_figura in mapas)
                print("OK  ", id_figura, "(escuro)")
            nav.close()
    finally:
        proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
