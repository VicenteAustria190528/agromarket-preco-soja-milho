"""ETAPA 2 · Transformação: limpeza e padronização (raw -> staging).

Regras:
  1. Texto "s/ cotação" não é preço: vai para rejeitados.
  2. Se o "Fechamento" da página é de outro dia (feriado), a linha é repetida do dia anterior: rejeitada.
  3. Preço com vírgula decimal ("1.234,56") vira número.
  4. A praça vem escrita de jeitos diferentes: normalizamos para um id e o código IBGE (dim_praca).
  5. Variação maior que 10% de um dia para o outro na mesma série fica marcada como suspeita
     (não é apagada: quem decide é o analista).
"""
import csv, json, re, sys, unicodedata
from datetime import datetime
sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from config import RAW, STAGING, NA_PAGINAS

# Tabela de praças conhecidas (desafio do grupo PREÇO: "Cascavel (PR)", "Cascavel/PR", "CASCAVEL - PR"...)
PRACAS = {
    ("nao-me-toque", "RS"): "NMT",
    ("nonoai", "RS"): "NON",
    ("panambi", "RS"): "PAN",
    ("porto rio grande", "RS"): "PRG",
}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalizar_praca(texto):
    """'Não-Me-Toque/RS (Cotrijal)', 'Não-Me-Toque (RS)', 'NAO-ME-TOQUE - RS' -> 'NMT'."""
    t = sem_acento(texto).lower()
    t = re.sub(r"\(.*?\)", lambda m: " " + m.group(0) + " ", t)
    if t.strip().startswith("porto rio grande"):
        return "PRG" if ("disponivel" in t or "milho" in t) else None
    m = re.match(r"^\s*(.+?)\s*(?:/|\(|\s-\s)\s*([a-z]{2})\b", t)
    if not m:
        return None
    return PRACAS.get((m.group(1).strip(), m.group(2).upper()))


def numero_br(s):
    s = s.strip()
    if not re.search(r"\d", s):
        return None
    return float(s.replace(".", "").replace(",", "."))


def transformar():
    STAGING.mkdir(parents=True, exist_ok=True)
    ok, rej = [], []
    with open(RAW / "noticias_agricolas_cotacoes.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            produto, tipo = NA_PAGINAS[r["pagina"]]
            data = r["data_consultada"]
            fech = datetime.strptime(r["fechamento"], "%d/%m/%Y").date().isoformat() if r["fechamento"] else ""
            if fech != data:
                rej.append({**r, "motivo": "fechamento de outro dia (feriado ou sem pregão)"}); continue
            preco = numero_br(r["preco_texto"])
            if preco is None:
                rej.append({**r, "motivo": "sem cotação"}); continue
            if tipo == "cepea":
                praca, fonte = ("CPR" if produto == "soja" else "CMI"), "CEPEA"
            else:
                praca, fonte = normalizar_praca(r["praca_texto"] + (" milho" if produto == "milho" else "")), "NA"
                if praca is None:
                    rej.append({**r, "motivo": "praça fora do escopo (contrato futuro ou outra UF)"}); continue
            ok.append({"data_referencia": data, "data_publicacao": fech, "id_praca": praca,
                       "id_produto": produto, "id_fonte": fonte, "preco_brl": preco, "suspeito": ""})
    # duplicados e variação suspeita
    ok.sort(key=lambda x: (x["id_praca"], x["id_produto"], x["data_referencia"]))
    vistos, final, ant = set(), [], {}
    for x in ok:
        k = (x["data_referencia"], x["id_praca"], x["id_produto"])
        if k in vistos:
            continue
        vistos.add(k)
        s = (x["id_praca"], x["id_produto"])
        if s in ant and ant[s][0][:4] == x["data_referencia"][:4] and abs(x["preco_brl"] / ant[s][1] - 1) > 0.10:
            x["suspeito"] = f"variação de {100*(x['preco_brl']/ant[s][1]-1):+.1f}% sobre {ant[s][0]}"
        ant[s] = (x["data_referencia"], x["preco_brl"])
        final.append(x)
    # PTAX
    ptax = json.loads((RAW / "bcb_ptax_sgs1.json").read_text(encoding="utf-8"))
    px, antp = [], None
    for r in ptax:
        d = datetime.strptime(r["data"], "%d/%m/%Y").date().isoformat()
        v = float(r["valor"])
        sus = ""
        if antp and antp[0][:4] == d[:4] and abs(v / antp[1] - 1) > 0.05:
            sus = f"variação de {100*(v/antp[1]-1):+.1f}% sobre {antp[0]}"
        px.append({"data_referencia": d, "data_publicacao": d, "ptax_venda": v, "suspeito": sus})
        antp = (d, v)
    for nome, linhas in [("preco_tratado.csv", final), ("ptax_tratado.csv", px), ("rejeitados.csv", rej)]:
        if not linhas:
            continue
        with open(STAGING / nome, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
            w.writeheader(); w.writerows(linhas)
    print(f"Tratados: {len(final)} preços, {len(px)} dias de PTAX; rejeitados: {len(rej)}; "
          f"suspeitos: {sum(1 for x in final if x['suspeito'])} preços, {sum(1 for x in px if x['suspeito'])} PTAX")
    return len(final), len(px), len(rej)


if __name__ == "__main__":
    transformar()
