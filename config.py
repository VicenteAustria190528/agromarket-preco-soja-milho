"""Configuração do projeto AgroMarket (Grupo PREÇO 1)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
RAW = RAIZ / "data" / "raw"
STAGING = RAIZ / "data" / "staging"
DB = RAIZ / "db" / "agromarket.db"
SAIDA = RAIZ / "saida"

# Data de análise ("hoje") e regra do percentil sazonal
DATA_ANALISE = "2026-11-05"
JANELA_DIAS = 15          # 15 dias antes e 15 depois
ANOS_REFERENCIA = 5       # sempre 5 anos anteriores

# Período coletado (janela em torno de 05/11 em cada ano)
ANOS_COLETA = [2021, 2022, 2023, 2024, 2025, 2026]
INICIO_JANELA = (10, 21)  # 21/10
FIM_JANELA = (11, 20)     # 20/11

# Feriados nacionais que caem na janela (sem pregão)
FERIADOS = {"11-02": "Finados", "11-15": "Proclamação da República", "11-20": "Consciência Negra"}

# Páginas do Notícias Agrícolas (uma página por data: <url>/AAAA-MM-DD)
NA_BASE = "https://www.noticiasagricolas.com.br/cotacoes"
NA_PAGINAS = {
    "soja-mercado-fisico-sindicatos-e-cooperativas": ("soja", "fisico"),
    "milho-mercado-fisico-sindicatos-e-cooperativas": ("milho", "fisico"),
    "indicador-cepea-esalq-soja-parana": ("soja", "cepea"),
    "indicador-cepea-esalq-milho": ("milho", "cepea"),
}
NA_URL = {
    "soja-mercado-fisico-sindicatos-e-cooperativas": NA_BASE + "/soja/soja-mercado-fisico-sindicatos-e-cooperativas",
    "milho-mercado-fisico-sindicatos-e-cooperativas": NA_BASE + "/milho/milho-mercado-fisico-sindicatos-e-cooperativas",
    "indicador-cepea-esalq-soja-parana": NA_BASE + "/soja/indicador-cepea-esalq-soja-parana",
    "indicador-cepea-esalq-milho": NA_BASE + "/milho/indicador-cepea-esalq-milho",
}

# API do Banco Central: PTAX venda, série SGS 1 (datas em dd/mm/aaaa)
BCB_SGS_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json&dataInicial={ini}&dataFinal={fim}"
