"""Regras de análise lidas DIRETO do banco (usadas pela planilha e pelo app).

Percentil sazonal: compara o preço de hoje com os dias da mesma época
(±15 dias da data de hoje) dos 5 anos anteriores, na mesma praça.
Só entram dados com data_publicacao < data de análise (sem "olhar o futuro").
"""
import sqlite3, sys, os
from datetime import date
from statistics import median
sys.path.insert(0, os.path.dirname(__file__) + "/..")
from config import DB, DATA_ANALISE, JANELA_DIAS, ANOS_REFERENCIA

SQL_JANELA = """
SELECT ano, data, preco_brl, ptax_venda, preco_usd
FROM vw_preco_completo
WHERE id_praca = :praca AND id_produto = :produto
  AND ano BETWEEN :ano - :anos AND :ano - 1
  AND ABS(julianday(data) - julianday(ano || substr(:hoje, 5))) <= :janela
  AND data_publicacao < :hoje
ORDER BY data
"""


def conectar():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def janela(con, praca, produto, hoje=DATA_ANALISE):
    p = dict(praca=praca, produto=produto, ano=int(hoje[:4]), anos=ANOS_REFERENCIA, hoje=hoje, janela=JANELA_DIAS)
    return [dict(r) for r in con.execute(SQL_JANELA, p)]


def ptax_do_dia(con, hoje=DATA_ANALISE):
    r = con.execute("SELECT ptax_venda, data_referencia FROM fato_cambio_ptax WHERE data_referencia <= ? "
                    "ORDER BY data_referencia DESC LIMIT 1", (hoje,)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def ultima_cotacao(con, praca, produto, hoje=DATA_ANALISE):
    r = con.execute("SELECT preco_brl, data_referencia FROM fato_preco_diario WHERE id_praca=? AND id_produto=? "
                    "AND data_referencia < ? ORDER BY data_referencia DESC LIMIT 1", (praca, produto, hoje)).fetchone()
    return (r[0], r[1]) if r else (None, None)


def percentil(valor, serie):
    """% de dias da época em que o valor foi MAIOR que o da série (dias estritamente menores)."""
    if not serie:
        return None
    return round(100 * sum(1 for v in serie if v < valor) / len(serie))


def analisar(con, praca, produto, oferta=None, hoje=DATA_ANALISE):
    dias = janela(con, praca, produto, hoje)
    ptax, ptax_data = ptax_do_dia(con, hoje)
    ult, ult_data = ultima_cotacao(con, praca, produto, hoje)
    preco = oferta if oferta else ult
    if not dias or preco is None:
        return None
    brl = [d["preco_brl"] for d in dias]
    usd = [d["preco_usd"] for d in dias if d["preco_usd"]]
    cam = [d["ptax_venda"] for d in dias if d["ptax_venda"]]
    preco_usd = preco / ptax if ptax else None
    med_ptax = median(cam) if cam else None
    anos = sorted({d["ano"] for d in dias})
    regua = []
    for a in anos:
        v = sorted(d["preco_brl"] for d in dias if d["ano"] == a)
        regua.append(dict(ano=a, dias=len(v), minimo=v[0], maximo=v[-1], media=sum(v) / len(v),
                          dias_abaixo=sum(1 for x in v if x < preco)))
    return dict(
        praca=praca, produto=produto, hoje=hoje, preco=preco, ultima=ult, ultima_data=ult_data,
        cotacao_velha=bool(ult_data and (date.fromisoformat(hoje) - date.fromisoformat(ult_data)).days > 10),
        ptax=ptax, ptax_data=ptax_data, preco_usd=preco_usd,
        dias=len(brl), dias_mais_baratos=sum(1 for v in brl if v < preco),
        p_brl=percentil(preco, brl), p_usd=percentil(preco_usd, usd) if preco_usd else None,
        p_dolar=percentil(ptax, cam) if ptax else None,
        media=sum(brl) / len(brl), minimo=min(brl), maximo=max(brl),
        ptax_mediana=med_ptax, preco_com_dolar_normal=(preco_usd * med_ptax) if med_ptax else None,
        anos=anos, regua=regua, serie=dias,
    )


def frase(r):
    """Leitura para o produtor, sem jargão."""
    p = r["p_brl"]
    if p >= 80:
        s = "Preço muito bom para a época. Bom momento para vender uma parte."
    elif p >= 60:
        s = "Preço acima do normal para a época. Vale vender uma parte."
    elif p >= 40:
        s = "Preço normal para a época. Sem pressa: dá para vender aos poucos."
    elif p >= 20:
        s = "Preço abaixo do normal para a época. Se puder, espere."
    else:
        s = "Preço fraco para a época. Se puder, segure."
    return s


if __name__ == "__main__":
    con = conectar()
    for pr, prod in [("NMT", "soja"), ("NMT", "milho")]:
        r = analisar(con, pr, prod)
        print(pr, prod, r["preco"], r["ultima_data"], r["dias_mais_baratos"], "/", r["dias"],
              "R$", r["p_brl"], "US$", r["p_usd"], "dólar", r["p_dolar"], round(r["preco_com_dolar_normal"], 2), frase(r))
        for g in r["regua"]: print("  ", g)
