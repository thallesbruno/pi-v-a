# Alfabetização no Brasil e em Goiás — Censo 2022 (Projeto Integrador)

Dashboard em Streamlit sobre alfabetização de pessoas de 15 anos ou mais (IBGE, Censo 2022),
com dados tratados pela Base dos Dados. Recorte padrão: Goiás, comparado ao Brasil.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python preparar_dados.py           # confere os 2 CSVs em dados/ e liga as tabelas
python explorar_dataset.py         # perfilamento e teste contra os números do IBGE
python big_numbers.py              # big numbers (Goiás x Brasil)
streamlit run app.py               # dashboard em http://localhost:8501
```

## Arquivos
| Arquivo | Função |
|---|---|
| `dados/` | os dois CSVs (fato do censo e diretório de municípios) |
| `dados.py` | leitura, tratamento, junção e KPIs (só pandas, sem Streamlit) |
| `app.py` | dashboard (KPIs, barras e rosca) |
| `explorar_dataset.py` | perfilamento das duas tabelas |
| `preparar_dados.py` | confere arquivos e monta o cache |
| `big_numbers.py` | calcula os big numbers e grava `big_numbers.json` |

## Regra de ouro
A tabela já vem agregada (contagens de pessoas). Toda taxa é **soma do numerador ÷ soma do denominador**,
nunca a média das linhas.

Fontes: IBGE (Censo Demográfico 2022) e Base dos Dados (dados tratados e diretório de municípios).
