"""ETAPA 1b · Extração: preços do Notícias Agrícolas (uma página por data).

Páginas: mercado físico de soja e milho (preço de balcão das cooperativas) e
indicadores CEPEA/ESALQ republicados. Guarda todas as linhas do RS e os indicadores
em data/raw/noticias_agricolas_cotacoes.csv, com o texto exatamente como veio.

O site não tem arquivo para baixar: é preciso ler a tabela HTML de cada dia.
Pausa entre pedidos para não sobrecarregar o site.
"""
import csv, re, sys, time
from datetime import date, timedelta
import requests
from bs4 import BeautifulSoup
sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from config import RAW, NA_URL, ANOS_COLETA, INICIO_JANELA, FIM_JANELA, DATA_ANALISE

CABECALHO = ["pagina", "data_consultada", "fechamento", "praca_texto", "preco_texto", "coletado_em"]


def dias_da_janela():
    hoje = date.fromisoformat(DATA_ANALISE)
    for ano in ANOS_COLETA:
        d = date(ano, *INICIO_JANELA)
        fim = min(date(ano, *FIM_JANELA), hoje)
        while d <= fim:
            if d.weekday() < 5:
                yield d
            d += timedelta(days=1)


def ler_pagina(html, pagina):
    """Devolve (fechamento, [(praca_texto, preco_texto)]) da primeira tabela de cotação."""
    sopa = BeautifulSoup(html, "html.parser")
    bloco = sopa.select_one(".cotacao")
    if bloco is None:
        return None, []
    m = re.search(r"Fechamento:\s*(\d\d/\d\d/\d{4})", bloco.get_text(" "))
    linhas = []
    for tr in bloco.select("tbody tr"):
        td = [x.get_text(strip=True) for x in tr.select("td")]
        if len(td) < 2:
            continue
        if pagina.startswith("indicador") or "/RS" in td[0] or "Rio Grande" in td[0]:
            linhas.append((td[0], td[1]))
    return (m.group(1) if m else None), linhas


def extrair():
    saida = RAW / "noticias_agricolas_cotacoes.csv"
    hoje = date.today().isoformat()
    sessao = requests.Session()
    sessao.headers["User-Agent"] = "AgroMarket-UPF (trabalho academico)"
    total = 0
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CABECALHO)
        for d in dias_da_janela():
            for pagina, url in NA_URL.items():
                r = sessao.get(f"{url}/{d.isoformat()}", timeout=60)
                fech, linhas = ler_pagina(r.text, pagina)
                for praca, preco in linhas:
                    w.writerow([pagina, d.isoformat(), fech or "", praca, preco, hoje])
                    total += 1
                time.sleep(0.3)
            print(d, "ok")
    print(f"Notícias Agrícolas: {total} linhas gravadas em {saida.name}")


if __name__ == "__main__":
    extrair()
