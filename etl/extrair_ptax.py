"""ETAPA 1a · Extração: dólar PTAX venda (Banco Central, API SGS série 1).

Grava a resposta da API como veio em data/raw/bcb_ptax_sgs1.json.
"""
import json, sys
from datetime import date
import requests
sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from config import RAW, BCB_SGS_URL, ANOS_COLETA


def extrair():
    ini = date(min(ANOS_COLETA), 10, 1).strftime("%d/%m/%Y")
    fim = date.today().strftime("%d/%m/%Y")
    url = BCB_SGS_URL.format(ini=ini, fim=fim)
    print("Baixando", url)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dados = r.json()
    (RAW / "bcb_ptax_sgs1.json").write_text(json.dumps(dados, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"PTAX: {len(dados)} dias gravados em data/raw/bcb_ptax_sgs1.json")


if __name__ == "__main__":
    extrair()
