"""Gera UMA PLANILHA POR FONTE (xlsx) a partir do que foi coletado em data/raw/.

Cada planilha tem 3 abas:
  dados  -> tabela limpa, pronta para o banco (uma linha por dia)
  bruto  -> exatamente como veio da fonte (texto, vírgula decimal)
  sobre  -> fonte, link, formato, licença e data da coleta
"""
import csv, json, sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__) + "/..")
from config import RAW, STAGING, RAIZ

PASTA = RAIZ / "planilhas"
PRACAS = pd.DataFrame([
    ("NMT", "Não-Me-Toque", "RS", "4312658", "Cotrijal", "balcão (cooperativa)"),
    ("NON", "Nonoai", "RS", "4312708", "Coopertradição", "balcão (cooperativa)"),
    ("PAN", "Panambi", "RS", "4313904", "Cotripal", "balcão (cooperativa)"),
    ("PRG", "Rio Grande (porto)", "RS", "4315602", "Insoy Commodities", "porto, disponível"),
    ("CPR", "Paraná (indicador estadual)", "PR", "", "CEPEA/ESALQ", "indicador"),
    ("CMI", "Campinas (indicador)", "SP", "3509502", "CEPEA/ESALQ", "indicador"),
], columns=["id_praca", "municipio", "uf", "codigo_ibge", "informante", "tipo"])


def salvar(nome, dados, bruto, sobre):
    PASTA.mkdir(exist_ok=True)
    with pd.ExcelWriter(PASTA / nome, engine="openpyxl") as w:
        dados.to_excel(w, sheet_name="dados", index=False)
        bruto.to_excel(w, sheet_name="bruto", index=False)
        pd.DataFrame(sobre, columns=["campo", "valor"]).to_excel(w, sheet_name="sobre", index=False)
        for ws in w.book.worksheets:
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or "")) for c in col) + 2))
            ws.freeze_panes = "A2"
    print("planilha:", nome, len(dados), "linhas")


def montar():
    raw = pd.read_csv(RAW / "noticias_agricolas_cotacoes.csv", sep=";", dtype=str)
    trat = pd.read_csv(STAGING / "preco_tratado.csv", sep=";", dtype={"suspeito": str, "id_fonte": str}, keep_default_na=False)
    trat["preco_brl"] = trat["preco_brl"].astype(float)
    trat["suspeito"] = trat["suspeito"].replace("", None)
    trat = trat.rename(columns={"data_referencia": "data", "id_produto": "produto", "id_fonte": "fonte", "preco_brl": "preco_rs_saca",
                                "suspeito": "alerta"})
    trat = trat.merge(PRACAS[["id_praca", "municipio", "uf", "codigo_ibge", "informante"]], on="id_praca")
    cols = ["data", "data_publicacao", "produto", "id_praca", "municipio", "uf", "codigo_ibge", "informante", "preco_rs_saca", "alerta"]

    cepea = trat[trat.fonte == "CEPEA"][cols].sort_values(["produto", "data"])
    salvar("01_CEPEA_indicadores_soja_milho.xlsx", cepea,
           raw[raw.pagina.str.startswith("indicador")],
           [("Fonte", "CEPEA/ESALQ-USP · Indicador da soja Paraná e Indicador do milho ESALQ/BM&FBovespa (Campinas)"),
            ("Link original", "https://www.cepea.org.br/br/indicador/series/soja.aspx?id=12 · https://www.cepea.org.br/br/indicador/series/milho.aspx?id=77"),
            ("Como foi coletado", "Republicação diária em https://www.noticiasagricolas.com.br/cotacoes/soja/indicador-cepea-esalq-soja-parana/AAAA-MM-DD"),
            ("Formato original", ".xls (Excel 97-2003), vírgula decimal, R$ e US$ por saca de 60 kg"),
            ("Período", "21/10 a 20/11 de 2021 a 2025 + 21/10 a 05/11/2026"),
            ("Licença", "CC BY-NC 4.0 (uso acadêmico com citação)"), ("Coleta", "05/11/2026")])

    fis = trat[trat.fonte == "NA"][cols].sort_values(["produto", "id_praca", "data"])
    salvar("02_Pracas_RS_mercado_fisico_soja_milho.xlsx", fis,
           raw[raw.pagina.str.contains("mercado-fisico")],
           [("Fonte", "Notícias Agrícolas · Mercado físico (sindicatos e cooperativas), praças do RS"),
            ("Link", "https://www.noticiasagricolas.com.br/cotacoes/soja/soja-mercado-fisico-sindicatos-e-cooperativas/AAAA-MM-DD"),
            ("Por que esta fonte", "O Agrolink mostra a praça só no dia, sem histórico para baixar; aqui há uma página por data"),
            ("Formato original", "Tabela HTML por data; praça escrita como 'Cidade/UF (Informante)'; vírgula decimal"),
            ("Praça principal", "Não-Me-Toque/RS · Cotrijal · IBGE 4312658 (única do RS com os 5 anos)"),
            ("Limitações", "Nonoai só 2023+; Panambi só 2021-2022; 2026 com poucas cotações em Não-Me-Toque"),
            ("Licença", "Conteúdo jornalístico; uso acadêmico com citação"), ("Coleta", "05/11/2026")])

    ptax_raw = pd.DataFrame(json.loads((RAW / "bcb_ptax_sgs1.json").read_text()))
    ptax = pd.read_csv(STAGING / "ptax_tratado.csv", sep=";", dtype={"suspeito": str}).rename(
        columns={"data_referencia": "data", "ptax_venda": "dolar_ptax_venda", "suspeito": "alerta"})
    salvar("03_BCB_dolar_PTAX.xlsx", ptax, ptax_raw,
           [("Fonte", "Banco Central do Brasil · Dólar PTAX de venda (série SGS 1)"),
            ("Link", "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados?formato=json&dataInicial=21/10/2021&dataFinal=05/11/2026"),
            ("Conjunto de dados", "Dólar comercial (venda e compra) – cotações diárias · dadosabertos.bcb.gov.br"),
            ("Formato original", "API JSON (data dd/mm/aaaa, valor com ponto)"), ("Licença", "ODbL"), ("Coleta", "05/11/2026")])

    salvar("04_Dimensao_pracas_IBGE.xlsx", PRACAS, PRACAS,
           [("Fonte", "IBGE · API de localidades (códigos de município)"),
            ("Link", "https://servicodados.ibge.gov.br/api/v1/localidades/estados/RS/municipios"),
            ("Uso", "Liga o nome da praça escrito pela fonte ao código IBGE (chave da dim_praca)")])


if __name__ == "__main__":
    montar()
