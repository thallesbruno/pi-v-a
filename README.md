# Projeto Integrador V-A - Big Data e Inteligência Artificial

Este repositório contém dois projetos diferentes, com objetivos e dados distintos:

- `alfabetizacao_dashboard/`: dashboard em Streamlit sobre alfabetização no Brasil e em Goiás, usando dados do Censo 2022 do IBGE.
- `boas_praticas_visualizacao/`: projeto de estudo sobre boas práticas de visualização de dados, com exemplos, app em Streamlit e slides sobre PIB e população dos municípios.

## 1) Dashboard de alfabetização

Entre na pasta `alfabetizacao_dashboard/` e siga os passos abaixo:

```bash
cd alfabetizacao_dashboard
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, em PowerShell, use:

```powershell
.venv\Scripts\Activate.ps1
```

Verifique se a pasta `dados/` contém os arquivos:

- `br_ibge_censo_2022_alfabetizacao_grupo_idade_sexo_raca.csv`
- `br_bd_diretorios_brasil_municipio.csv`

Depois rode:

```bash
python preparar_dados.py
python -m streamlit run app.py
```

O dashboard abre em `http://localhost:8501`.

Para inspecionar os dados antes de abrir o app, use:

```bash
python explorar_dataset.py
```

Opcionalmente, rode:

```bash
python big_numbers.py
```

Isso gera um resumo em `big_numbers.json`.

## 2) Projeto de boas práticas de visualização

Entre na pasta `boas_praticas_visualizacao/` e siga os passos abaixo:

```bash
cd boas_praticas_visualizacao
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, em PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Para iniciar o app:

```bash
streamlit run app.py
```

O app fica em `http://localhost:8501`.

Se quiser gerar os slides, veja o README interno da pasta `boas_praticas_visualizacao/`.

## Observação

Os dois projetos são independentes. Cada uma das pastas tem seu próprio README, requisitos e dados. O README principal serve só para orientar a entrada no repositório.
