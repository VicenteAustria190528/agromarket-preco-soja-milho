# AgroMarket · "Hoje é dia de vender?"

Trabalho final de **BI, Data Science & Big Data** (UPF/ESAN, 2026/2) · Grupo **PREÇO 1**
Marco Antônio Dal Zotto · Henrique De Souza Mello · Vicente Dos Santos Austria · Kerlon Mateus Goetz Alves

O projeto pega o preço da soja e do milho nas praças do RS e o dólar do Banco Central, grava tudo
num banco de dados (modelo estrela) e mostra num site se o preço de hoje está bom **para a época**,
comparando com os mesmos dias (±15) dos **5 anos anteriores**, na mesma praça.

## Arquitetura

```
FONTES                      ETL (Python)                 BANCO                     SAÍDAS
Notícias Agrícolas  ─┐   etl/extrair_*.py  → data/raw/      db/agromarket.db   ┌─► saida/AgroMarket_Base_Consolidada.xlsx
CEPEA/ESALQ         ─┼─► etl/transformar.py → data/staging/ ─► (modelo estrela) ─┤
BCB PTAX (API)      ─┘   etl/carregar_dw.py                                      └─► site Streamlit (app/app.py)
```

| Etapa | Arquivo | O que faz |
|---|---|---|
| Extrair | `etl/extrair_ptax.py`, `etl/extrair_noticias_agricolas.py` | Baixa as fontes e guarda o bruto em `data/raw/`, sem alterar |
| Transformar | `etl/transformar.py` | Vírgula → ponto, praça → código IBGE, descarta "s/ cotação" e fechamento de outro dia, remove duplicados, marca saltos > 10% (preço) e > 5% (dólar) |
| Carregar | `etl/carregar_dw.py` + `sql/schema.sql` | Cria o banco SQLite e carrega dimensões, fatos e `log_carga` |
| Analisar | `etl/analise.py` | Percentil sazonal em SQL, lido do banco (usado pela planilha e pelo site) |
| Exportar | `etl/exportar_excel.py` | Gera a planilha consolidada a partir do banco, com painel e gráficos |
| Apresentar | `app/app.py` | Site em Streamlit que consulta o banco |

### Modelo estrela (`db/agromarket.db`)
- **Dimensões:** `dim_tempo` (dia útil, feriado), `dim_praca` (código IBGE), `dim_produto`, `dim_fonte` (licença, defasagem)
- **Fatos:** `fato_preco_diario` (R$/saca) e `fato_cambio_ptax` (R$/US$); ambos com `data_referencia` e `data_publicacao` para não "olhar o futuro"
- **View:** `vw_preco_completo` junta preço, praça e dólar do dia e calcula o preço em US$

## Como rodar

```bash
pip install -r requirements.txt
python rodar_etl.py            # usa os dados brutos já coletados (05/11/2026) e recria banco + planilha
python rodar_etl.py --baixar   # baixa de novo das fontes antes (precisa de internet)
streamlit run app/app.py       # abre o site no navegador (http://localhost:8501)
```

Atalho: no Windows, dê dois cliques em `abrir_site_windows.bat` (no Mac/Linux, `./abrir_site_mac_linux.sh`). É preciso ter o Python 3.10+ instalado.

## O site
Site publicado: https://agromarket-upf.streamlit.app

Visual de painel financeiro, em uma página só:
- **Preço em destaque** com selo verde/vermelho da variação contra a média da época
- **Veredito em linguagem de produtor** e uma régua de "fraco" a "muito bom"
- **Gráfico com seletor**: esta época ano a ano · régua das colheitas · dólar
- **Resumo** (média, pior e melhor dia, preço em dólar, dólar normal) e **simulador de oferta e margem**
- **Por que o preço está assim?** separa o efeito do dólar do efeito do grão
- **Compare com outras praças**, com botão para trocar de praça
- **Sobre os dados**: arquitetura, fontes e licenças, cobertura, alertas de qualidade, consulta SQL e download da tabela

Prints na pasta `prints/`.

## Regra de cálculo
- Época = 15 dias antes e 15 depois da data de análise, nos 5 anos anteriores, mesma praça e produto
- Nota (percentil) = % de dias da época com preço **menor** que o de hoje
- Preço em US$ = preço em R$ ÷ PTAX de venda do mesmo dia

## Dados e limitações
- Praça principal: **Não-Me-Toque/RS (Cotrijal, IBGE 4312658)**, a única do RS com os 5 anos completos
- Nonoai só tem 2023 em diante e Panambi só 2021–2022 (o site avisa)
- Feriados sem pregão: 02/11, 15/11 e 20/11
- Alertas para conferir: milho Não-Me-Toque em 30/10/2026 (R$ 72) e PTAX de 26/10/2026 (+9,2%)
- O Agrolink não tem histórico para baixar; o CEPEA foi lido pela republicação no Notícias Agrícolas
- Os extratores foram escritos para rodar no computador do grupo; a coleta usada foi feita em 05/11/2026

## Fontes e licenças
- CEPEA/ESALQ-USP · CC BY-NC 4.0 (uso acadêmico com citação)
- Banco Central do Brasil · PTAX, série SGS 1
- Notícias Agrícolas · cotações do mercado físico (uso acadêmico com citação)
- IBGE · códigos de município
