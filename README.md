# Alfabetização no Brasil e em Goiás

Dashboard em Streamlit com dados de alfabetização do Censo 2022 (IBGE).

## Como executar

Com Python 3.10 ou superior instalado, execute a partir da raiz do projeto:

```bash
cd alfabetizacao_dashboard
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows (PowerShell), substitua a ativação por `.venv\Scripts\Activate.ps1`.

Confira se a pasta `alfabetizacao_dashboard/dados/` contém os arquivos:

- `br_ibge_censo_2022_alfabetizacao_grupo_idade_sexo_raca.csv`
- `br_bd_diretorios_brasil_municipio.csv`

No mesmo terminal, prepare os dados e inicie o dashboard:

```bash
python preparar_dados.py
python -m streamlit run app.py
```

Acesse **http://localhost:8501**. Para encerrar, pressione `Ctrl+C`.

Para conferir os dados antes de abrir o dashboard, execute `python explorar_dataset.py`
na pasta `alfabetizacao_dashboard/`, com o ambiente virtual ativo. O script mostra
no terminal os tipos das colunas, valores nulos, correspondência entre municípios,
comparação dos indicadores com referências do IBGE e um resumo de Goiás.

Opcional: execute `python big_numbers.py` para gerar o resumo de indicadores em
`big_numbers.json`.
