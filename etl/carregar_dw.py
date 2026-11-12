"""ETAPA 3 · Carga: cria o banco SQLite (modelo estrela) e carrega dimensões e fatos."""
import csv, sqlite3, sys
from datetime import date, datetime, timedelta
sys.path.insert(0, __import__("os").path.dirname(__file__) + "/..")
from config import RAIZ, STAGING, DB, ANOS_COLETA, FERIADOS

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]

DIM_PRACA = [
    ("NMT", "Não-Me-Toque", "RS", "4312658", "Cotrijal", "balcão (cooperativa)"),
    ("NON", "Nonoai", "RS", "4312708", "Coopertradição", "balcão (cooperativa)"),
    ("PAN", "Panambi", "RS", "4313904", "Cotripal", "balcão (cooperativa)"),
    ("PRG", "Rio Grande (porto)", "RS", "4315602", "Insoy Commodities", "porto, disponível"),
    ("CPR", "Paraná (indicador)", "PR", None, "CEPEA/ESALQ", "indicador estadual"),
    ("CMI", "Campinas (indicador)", "SP", "3509502", "CEPEA/ESALQ", "indicador"),
]
DIM_PRODUTO = [("soja", "Soja em grão", "R$ por saca de 60 kg"), ("milho", "Milho em grão", "R$ por saca de 60 kg")]
DIM_FONTE = [
    ("NA", "Notícias Agrícolas · Mercado Físico", "https://www.noticiasagricolas.com.br/cotacoes",
     "Tabela HTML, uma página por data", "diária (dias úteis)", "mesmo dia (fechamento)",
     "Conteúdo jornalístico; uso acadêmico com citação"),
    ("CEPEA", "CEPEA/ESALQ-USP", "https://www.cepea.org.br", ".xls com vírgula decimal (R$ e US$)",
     "diária", "mesmo dia (fim da tarde)", "CC BY-NC 4.0"),
    ("BCB", "Banco Central do Brasil · PTAX", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json",
     "API JSON", "diária (dias úteis)", "mesmo dia (~13h)", "ODbL"),
]


def carregar():
    DB.parent.mkdir(parents=True, exist_ok=True)
    agora = datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    con.executescript((RAIZ / "sql" / "schema.sql").read_text(encoding="utf-8"))
    # dim_tempo: 01/10 a 30/11 de cada ano coletado
    tempo = []
    for ano in ANOS_COLETA:
        d = date(ano, 10, 1)
        while d <= date(ano, 11, 30):
            fer = FERIADOS.get(d.strftime("%m-%d"))
            tempo.append((int(d.strftime("%Y%m%d")), d.isoformat(), d.year, d.month, d.day, DIAS[d.weekday()],
                          int(d.weekday() < 5 and fer is None), fer))
            d += timedelta(days=1)
    con.executemany("INSERT INTO dim_tempo VALUES (?,?,?,?,?,?,?,?)", tempo)
    con.executemany("INSERT INTO dim_praca VALUES (?,?,?,?,?,?)", DIM_PRACA)
    con.executemany("INSERT INTO dim_produto VALUES (?,?,?)", DIM_PRODUTO)
    con.executemany("INSERT INTO dim_fonte VALUES (?,?,?,?,?,?,?)", DIM_FONTE)
    idd = lambda s: int(s.replace("-", ""))
    with open(STAGING / "preco_tratado.csv", encoding="utf-8") as f:
        precos = [(idd(r["data_referencia"]), r["id_praca"], r["id_produto"], r["id_fonte"], float(r["preco_brl"]), (r.get("suspeito") or None),
                   r["data_referencia"], r["data_publicacao"], agora) for r in csv.DictReader(f, delimiter=";")]
    con.executemany("INSERT INTO fato_preco_diario VALUES (?,?,?,?,?,?,?,?,?)", precos)
    with open(STAGING / "ptax_tratado.csv", encoding="utf-8") as f:
        ptax = [(idd(r["data_referencia"]), "BCB", float(r["ptax_venda"]), (r.get("suspeito") or None), r["data_referencia"], r["data_publicacao"], agora)
                for r in csv.DictReader(f, delimiter=";")]
    con.executemany("INSERT INTO fato_cambio_ptax VALUES (?,?,?,?,?,?,?)", ptax)
    log = [("carga", "dim_tempo", len(tempo), "", agora), ("carga", "dim_praca", len(DIM_PRACA), "", agora),
           ("carga", "fato_preco_diario", len(precos), "", agora), ("carga", "fato_cambio_ptax", len(ptax), "", agora)]
    con.executemany("INSERT INTO log_carga VALUES (?,?,?,?,?)", log)
    con.commit(); con.close()
    print(f"Banco {DB.name}: {len(precos)} preços, {len(ptax)} dias de PTAX, {len(tempo)} datas")


if __name__ == "__main__":
    carregar()
