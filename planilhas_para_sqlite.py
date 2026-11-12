"""Converte as planilhas da pasta planilhas/ em um banco SQLite (modelo estrela).

Uso:  python planilhas_para_sqlite.py
Saída: db/agromarket.db  (abre no DB Browser for SQLite, DBeaver ou Python)
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent
PL = RAIZ / "planilhas"
DB = RAIZ / ("banco" if (RAIZ / "banco").exists() else "db") / "agromarket.db"
FERIADOS = {"11-02": "Finados", "11-15": "Proclamação da República", "11-20": "Consciência Negra"}
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def main():
    agora = datetime.now().isoformat(timespec="seconds")
    precos = pd.concat([pd.read_excel(PL / "01_CEPEA_indicadores_soja_milho.xlsx", "dados").assign(id_fonte="CEPEA"),
                        pd.read_excel(PL / "02_Pracas_RS_mercado_fisico_soja_milho.xlsx", "dados").assign(id_fonte="NA")])
    ptax = pd.read_excel(PL / "03_BCB_dolar_PTAX.xlsx", "dados")
    pracas = pd.read_excel(PL / "04_Dimensao_pracas_IBGE.xlsx", "dados", dtype=str)
    for df in (precos, ptax):
        df["data"] = pd.to_datetime(df["data"]).dt.strftime("%Y-%m-%d")
        df["data_publicacao"] = pd.to_datetime(df["data_publicacao"]).dt.strftime("%Y-%m-%d")
        df["id_data"] = df["data"].str.replace("-", "").astype(int)
        df["alerta"] = df["alerta"].where(df["alerta"].notna(), None)

    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript((RAIZ / "sql" / "schema.sql").read_text(encoding="utf-8"))
    datas = pd.date_range(f"{precos.data.min()[:4]}-10-01", f"{precos.data.max()[:4]}-11-30")
    tempo = [(int(d.strftime("%Y%m%d")), d.strftime("%Y-%m-%d"), d.year, d.month, d.day, DIAS[d.weekday()],
              int(d.weekday() < 5 and d.strftime("%m-%d") not in FERIADOS), FERIADOS.get(d.strftime("%m-%d")))
             for d in datas if d.month in (10, 11)]
    con.executemany("INSERT INTO dim_tempo VALUES (?,?,?,?,?,?,?,?)", tempo)
    con.executemany("INSERT INTO dim_praca VALUES (?,?,?,?,?,?)",
                    pracas[["id_praca", "municipio", "uf", "codigo_ibge", "informante", "tipo"]].fillna("").values.tolist())
    con.executemany("INSERT INTO dim_produto VALUES (?,?,?)", [("soja", "Soja em grão", "R$ por saca de 60 kg"),
                                                               ("milho", "Milho em grão", "R$ por saca de 60 kg")])
    fontes = []
    for arq, idf in [("01_CEPEA_indicadores_soja_milho.xlsx", "CEPEA"), ("02_Pracas_RS_mercado_fisico_soja_milho.xlsx", "NA"),
                     ("03_BCB_dolar_PTAX.xlsx", "BCB")]:
        s = dict(pd.read_excel(PL / arq, "sobre").values)
        fontes.append((idf, s.get("Fonte"), s.get("Link") or s.get("Link original"), s.get("Formato original"),
                       "diária (dias úteis)", "mesmo dia", s.get("Licença")))
    con.executemany("INSERT INTO dim_fonte VALUES (?,?,?,?,?,?,?)", fontes)
    con.executemany("INSERT INTO fato_preco_diario VALUES (?,?,?,?,?,?,?,?,?)",
                    precos[["id_data", "id_praca", "produto", "id_fonte", "preco_rs_saca", "alerta", "data", "data_publicacao"]]
                    .assign(carregado_em=agora).values.tolist())
    con.executemany("INSERT INTO fato_cambio_ptax VALUES (?,?,?,?,?,?,?)",
                    ptax.assign(id_fonte="BCB", carregado_em=agora)[["id_data", "id_fonte", "dolar_ptax_venda", "alerta", "data",
                                                                     "data_publicacao", "carregado_em"]].values.tolist())
    con.executemany("INSERT INTO log_carga VALUES (?,?,?,?,?)", [
        ("planilhas_para_sqlite", "dim_tempo", len(tempo), "", agora),
        ("planilhas_para_sqlite", "dim_praca", len(pracas), "04_Dimensao_pracas_IBGE.xlsx", agora),
        ("planilhas_para_sqlite", "fato_preco_diario", len(precos), "01 + 02 (aba dados)", agora),
        ("planilhas_para_sqlite", "fato_cambio_ptax", len(ptax), "03 (aba dados)", agora)])
    con.commit()
    for t in ["dim_tempo", "dim_praca", "dim_produto", "dim_fonte", "fato_preco_diario", "fato_cambio_ptax"]:
        print(f"{t:20s} {con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:5d} linhas")
    con.close()
    print("Banco criado em", DB)


if __name__ == "__main__":
    main()
