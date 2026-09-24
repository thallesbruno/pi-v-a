# Boas práticas de visualização de dados

Material para demonstrar boas práticas de visualização (e sua relação com usabilidade) com dados públicos brasileiros:
**PIB e população dos municípios (IBGE)**. A pasta contém os **scripts** (Streamlit), a **referência à base de dados** e
um conjunto de **24 slides** em 2 seções.

## Como rodar

Com Python 3.10 ou superior, dentro desta pasta:

```bash
python -m venv .venv
.venv\Scripts\activate             # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python baixar_dados.py             # baixa PIB, população e limites dos estados (IBGE) para dados/
streamlit run app.py               # http://localhost:8501
```

Os CSVs e o GeoJSON já vêm versionados em `dados/`; `baixar_dados.py` só baixa o que faltar
(`--forcar` baixa tudo de novo). Sem internet, o app funciona com os arquivos que já estão na pasta.

Para regenerar os slides (opcional):

```bash
python gerar_imagens.py            # captura as figuras do app em slides/imagens/ (usa o Edge via Playwright)
python gerar_slides.py             # monta slides/boas_praticas_visualizacao.pptx
```

## O app

Barra lateral: **Visão geral**, **E1 a E8** e **Catálogo de gráficos**. Cada exemplo mostra a mesma pergunta em
**ANTES** (erros comuns, de propósito) e **DEPOIS** (boas práticas), com a lista do que mudou e a tabela de dados
(a versão acessível do gráfico). A **UF em destaque** (padrão: Goiás) escolhe o que aparece em laranja.

| Exemplo | Pergunta | Antes → Depois |
|---|---|---|
| E1 Barras | Quais UFs têm o maior PIB? | alfabética, arco-íris, eixo truncado → ordenadas, uma cor, base zero |
| E2 Linhas | Como o PIB de cada UF evoluiu desde 2002? | 27 linhas → poucas em destaque, índice base 100, rótulo direto |
| E3 Histograma | Como se distribui o PIB per capita dos municípios? | escala linear → escala log, mediana marcada |
| E4 Box plot | Como o PIB per capita varia entre as regiões? | escala linear → eixo log, ordem pela mediana |
| E5 Dispersão | População e PIB andam juntos? | pontos amontoados → log-log, transparência, retas de referência |
| E6 Mapa | Onde o PIB por habitante é maior? | valor absoluto + arco-íris → per capita, um matiz, quantis |
| E7 Composição | Quanto cada UF pesa no PIB do Brasil? | pizza de 27 fatias → Top 8 + "Demais" |
| E8 Heatmap | Qual a estrutura econômica de cada UF? | absoluto + arco-íris → percentuais, um matiz, número na célula |

## Os slides (`slides/boas_praticas_visualizacao.pptx`, 24 slides, com notas do apresentador)

| Slides | Conteúdo |
|---|---|
| 1 a 2 | Capa e agenda |
| **3 a 13 — Seção 1, conceitos** | 3 da pergunta ao gráfico · 4 barras · 5 linhas e áreas · 6 histograma · 7 box plot · 8 dispersão · 9 mapas · 10 composição · 11 heatmap e pequenos múltiplos · 12 cor, acessibilidade e tema claro/escuro · 13 o que evitar |
| **14 a 24 — Seção 2, na prática** | 14 a base e como rodar · 15 a 22 exemplos E1 a E8 (antes × depois, com dado-chave) · 23 temas claro e escuro · 24 checklist e fontes |

Os números citados nos slides são calculados dos dados por `gerar_slides.py`, não digitados.

## Arquivos

| Arquivo | Função |
|---|---|
| `baixar_dados.py` | baixa e trata PIB, população, área e limites dos estados (IBGE/SIDRA) |
| `dados.py` | leitura e cálculos (só pandas): per capita, agregações, formatação pt-BR |
| `estilo.py` | paleta e ajustes comuns das figuras |
| `exemplos.py` | as 8 figuras "antes" e "depois" e as extras do catálogo (só Plotly + pandas) |
| `app.py` | app Streamlit; com `?modo=imagem&fig=E3_bom` mostra só a figura pedida |
| `gerar_imagens.py` | captura as figuras do app em PNG para os slides |
| `gerar_slides.py` | monta o `.pptx` com python-pptx |
| `dados/` | CSVs, GeoJSON e `FONTES.md` (a referência à base de dados) |

## Base de dados

IBGE, API SIDRA: tabelas 5938 (PIB dos Municípios), 6579 (população estimada) e 4714 (área), mais a malha estadual.
Ano de referência **2021** (último com o valor adicionado por setor divulgado para todos os municípios). Tabelas,
variáveis, tratamento e URLs exatas em [`dados/FONTES.md`](dados/FONTES.md).

**Regra de ouro:** o PIB per capita de qualquer agregado é a soma do PIB dividida pela soma da população, nunca a média
dos municípios. O PIB é nominal (preços correntes).

## Decisões de técnica que os exemplos demonstram

- Figuras que funcionam nos temas **claro e escuro** do Streamlit sem detectar o tema (o Python não sabe com segurança
  qual está ativo): fundo transparente, texto herdado, cores com contraste ≥ 3:1 nos dois fundos, tons neutros com transparência.
- O mapa não usa camada de fundo (tiles), que seria clara ou escura, nunca as duas: os limites dos estados são polígonos cinza translúcidos.
- Seletor na barra lateral em vez de `st.tabs`: mapa dentro de aba oculta renderiza cortado.
