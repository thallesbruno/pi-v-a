# Fontes dos dados

Todos os dados são **públicos e abertos**, do IBGE, obtidos pela API SIDRA (sem chave).
Para baixar de novo: `python baixar_dados.py --forcar`.

| Arquivo em `dados/` | Origem | Conteúdo |
|---|---|---|
| `pib_municipios_2021.csv` | SIDRA, tabela **5938** (PIB dos Municípios, referência 2010), ano 2021; tabela **6579** (população residente estimada), ano 2021; tabela **4714** (Censo 2022, área territorial) | 1 linha por município (5.570): PIB e valor adicionado bruto por setor (agropecuária, indústria, serviços, administração pública), em mil reais correntes; população; área em km² |
| `pib_uf_serie.csv` | SIDRA, tabela **5938**, nível UF, 2002 a 2023 | PIB a preços correntes de cada UF, ano a ano |
| `br_uf_contornos.geojson` | API de Malhas do IBGE (`servicodados.ibge.gov.br/api/v3/malhas`), malha estadual, qualidade intermediária | limites dos 27 estados |

## Como os dados foram tratados

- **Ano de referência: 2021.** É o último ano com o valor adicionado por setor divulgado para todos os municípios
  (em 2022 e 2023 o IBGE só publicou o PIB total). Não há estimativa de população para 2022 e 2023 (anos de Censo).
- Código do município (`id_municipio`) é texto de 7 dígitos. UF = 2 primeiros dígitos; **região = 1º dígito**
  (1 Norte, 2 Nordeste, 3 Sudeste, 4 Sul, 5 Centro-Oeste).
- Valores especiais do SIDRA (`...`, `-`, `X`) viram nulo.
- Os valores são **nominais** (preços correntes): parte do crescimento entre anos é inflação.
- **PIB per capita** de qualquer agregado = soma do PIB ÷ soma da população (razão de somas), nunca a média
  dos PIBs per capita dos municípios.
- Um município tem valor adicionado da indústria negativo (−R$ 477 milhões); nas participações por setor ele conta como zero.
- Checagens: a soma dos PIBs municipais (R$ 9,01 tri) coincide com a soma das UFs, e a população soma 213,3 milhões.

## Referências das URLs

- PIB: `https://apisidra.ibge.gov.br/values/t/5938/n6/all/v/37,513,517,6575,525/p/2021`
- População: `https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/2021`
- Área: `https://apisidra.ibge.gov.br/values/t/4714/n6/all/v/6318/p/2022`
- Série por UF: `https://apisidra.ibge.gov.br/values/t/5938/n3/all/v/37/p/all`
- Malha: `https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?intrarregiao=UF&formato=application/vnd.geo+json&qualidade=intermediaria`

Fonte: IBGE. Dados acessados em setembro de 2026.
