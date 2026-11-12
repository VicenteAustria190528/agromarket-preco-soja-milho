"""ETAPA 4 · Exporta a planilha consolidada LENDO O BANCO (nada é digitado à mão)."""
import sys, os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
sys.path.insert(0, os.path.dirname(__file__) + "/..")
from config import SAIDA, DATA_ANALISE, JANELA_DIAS, ANOS_REFERENCIA
from etl.analise import conectar, analisar, frase

VERDE = "1F6B3A"; CLARO = "E8F3EC"; CINZA = "F3F4F6"
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor=VERDE)
B = Border(bottom=Side(style="thin", color="D1D5DB"))
NUM = {"preco_brl": "#,##0.00", "ptax_venda": "0.0000", "preco_usd": "0.00", "media": "#,##0.00",
       "minimo": "#,##0.00", "maximo": "#,##0.00"}


def tabela(ws, linha, colunas, dados, larguras=None):
    for j, c in enumerate(colunas, 1):
        cel = ws.cell(linha, j, c); cel.font = H; cel.fill = HF; cel.alignment = Alignment(horizontal="center")
    for i, row in enumerate(dados, linha + 1):
        for j, v in enumerate(row, 1):
            cel = ws.cell(i, j, v); cel.border = B
            if colunas[j - 1] in NUM: cel.number_format = NUM[colunas[j - 1]]
    for j, c in enumerate(colunas, 1):
        ws.column_dimensions[get_column_letter(j)].width = (larguras or {}).get(c, max(12, len(c) + 3))
    ws.freeze_panes = ws.cell(linha + 1, 1)
    ws.auto_filter.ref = f"A{linha}:{get_column_letter(len(colunas))}{linha + len(dados)}"
    return linha + len(dados)


def copiar(con, wb, nome, sql, larguras=None):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    ws = wb.create_sheet(nome)
    tabela(ws, 1, cols, [tuple(r) for r in cur], larguras)
    return ws


def painel(wb, con):
    ws = wb.active; ws.title = "Painel"
    ws.sheet_view.showGridLines = False
    ws["A1"] = "AgroMarket · Hoje é dia de vender?"; ws["A1"].font = Font(bold=True, size=18, color=VERDE)
    ws["A2"] = (f"Data de análise {DATA_ANALISE[8:]}/{DATA_ANALISE[5:7]}/{DATA_ANALISE[:4]} · época = ±{JANELA_DIAS} dias "
                f"· {ANOS_REFERENCIA} anos anteriores · gerado do banco agromarket.db em {datetime.now():%d/%m/%Y %H:%M}")
    ws["A2"].font = Font(italic=True, color="6B7280")
    linha = 4
    for produto in ("soja", "milho"):
        r = analisar(con, "NMT", produto)
        ws.cell(linha, 1, f"{produto.upper()} · Não-Me-Toque/RS (Cotrijal)").font = Font(bold=True, size=13, color=VERDE)
        kpis = [("Preço hoje (R$/sc)", r["preco"], "#,##0.00"), ("Ganha de quantos dias", f'{r["dias_mais_baratos"]} de {r["dias"]}', None),
                ("Nota em R$ (0–100)", r["p_brl"], "0"), ("Nota em US$ (0–100)", r["p_usd"], "0"),
                ("Dólar hoje (PTAX)", r["ptax"], "0.0000"), ("Nota do dólar (0–100)", r["p_dolar"], "0"),
                ("Média da época (R$)", r["media"], "#,##0.00"), ("Preço c/ dólar normal", r["preco_com_dolar_normal"], "#,##0.00")]
        for k, (rot, val, fmt) in enumerate(kpis):
            c = 1 + (k % 4) * 2; l = linha + 1 + (k // 4) * 2
            ws.cell(l, c, rot).font = Font(color="6B7280", size=9)
            v = ws.cell(l + 1, c, val); v.font = Font(bold=True, size=14)
            if fmt: v.number_format = fmt
            for cc in (c, c + 1):
                ws.cell(l, cc).fill = PatternFill("solid", fgColor=CLARO); ws.cell(l + 1, cc).fill = PatternFill("solid", fgColor=CLARO)
        ws.cell(linha + 5, 1, "Leitura: " + frase(r)).font = Font(bold=True, color=VERDE)
        # tabela da régua (base dos gráficos)
        t0 = linha + 7
        tabela_regua = [(g["ano"], g["minimo"], g["media"], g["maximo"], f'{g["dias_abaixo"]} de {g["dias"]}') for g in r["regua"]]
        tabela_regua.append(("HOJE", r["preco"], r["preco"], r["preco"], ""))
        for j, c in enumerate(["Colheita", "Menor", "Média", "Maior", "Hoje ganha de"], 1):
            x = ws.cell(t0, j, c); x.font = H; x.fill = HF
        for i, row in enumerate(tabela_regua, t0 + 1):
            for j, v in enumerate(row, 1):
                x = ws.cell(i, j, v); x.border = B
                if j in (2, 3, 4): x.number_format = "#,##0.00"
        ch = BarChart(); ch.type = "col"; ch.title = f"{produto.capitalize()}: preço médio da época × hoje (R$/sc)"
        ch.add_data(Reference(ws, min_col=3, min_row=t0, max_row=t0 + len(tabela_regua)), titles_from_data=True)
        ch.set_categories(Reference(ws, min_col=1, min_row=t0 + 1, max_row=t0 + len(tabela_regua)))
        ch.legend = None; ch.height = 7; ch.width = 14; ch.y_axis.title = "R$/sc"
        ch.series[0].graphicalProperties.solidFill = VERDE
        ws.add_chart(ch, f"J{linha}")
        linha = t0 + len(tabela_regua) + 4
    for c in "ABCDEFGH": ws.column_dimensions[c].width = 16
    return linha


def grafico_linhas(wb, con):
    """Aba com o preço diário da soja NMT por ano (mesmo pregão do ano) para o gráfico de linhas."""
    ws = wb.create_sheet("Grafico_epoca")
    anos = [r[0] for r in con.execute("SELECT DISTINCT ano FROM vw_preco_completo WHERE id_praca='NMT' AND id_produto='soja' "
                                      "AND ano < ? ORDER BY ano", (int(DATA_ANALISE[:4]),))]
    series = {a: [r[0] for r in con.execute("SELECT preco_brl FROM vw_preco_completo WHERE id_praca='NMT' AND id_produto='soja' "
                                            "AND ano=? ORDER BY data", (a,))] for a in anos}
    n = min(len(v) for v in series.values())
    ws.append(["Pregão"] + [str(a) for a in anos])
    for i in range(n):
        ws.append([i + 1] + [series[a][i] for a in anos])
    ch = LineChart(); ch.title = "Soja Não-Me-Toque: preço na época (21/10–20/11) em cada ano"
    ch.add_data(Reference(ws, min_col=2, max_col=1 + len(anos), min_row=1, max_row=n + 1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=n + 1))
    ch.y_axis.title = "R$/sc"; ch.x_axis.title = "pregão da época"; ch.height = 9; ch.width = 20
    ws.add_chart(ch, "H2")


def exportar():
    SAIDA.mkdir(parents=True, exist_ok=True)
    con = conectar()
    wb = Workbook()
    painel(wb, con)
    grafico_linhas(wb, con)
    copiar(con, wb, "fato_preco (view)", "SELECT data, praca, informante, id_produto AS produto, id_fonte AS fonte, preco_brl, alerta, "
           "ptax_venda, preco_usd, data_referencia, data_publicacao FROM vw_preco_completo ORDER BY id_praca, id_produto, data",
           {"praca": 26, "informante": 20})
    copiar(con, wb, "fato_cambio_ptax", "SELECT data_referencia, ptax_venda, alerta, id_fonte, data_publicacao FROM fato_cambio_ptax ORDER BY 1")
    copiar(con, wb, "dim_praca", "SELECT * FROM dim_praca", {"municipio": 22, "informante": 20, "tipo": 22})
    copiar(con, wb, "dim_produto", "SELECT * FROM dim_produto", {"unidade": 24})
    copiar(con, wb, "dim_fonte", "SELECT * FROM dim_fonte", {"nome": 36, "url": 50, "formato": 32, "licenca": 40})
    copiar(con, wb, "dim_tempo", "SELECT * FROM dim_tempo")
    copiar(con, wb, "cobertura", "SELECT id_praca AS praca, id_produto AS produto, ano, COUNT(*) AS dias, "
           "ROUND(MIN(preco_brl),2) AS minimo, ROUND(AVG(preco_brl),2) AS media, ROUND(MAX(preco_brl),2) AS maximo "
           "FROM vw_preco_completo GROUP BY 1,2,3 ORDER BY 1,2,3")
    copiar(con, wb, "log_carga", "SELECT * FROM log_carga", {"executado_em": 22})
    destino = SAIDA / "AgroMarket_Base_Consolidada.xlsx"
    wb.save(destino)
    print(f"Planilha salva em {destino}")
    return destino


if __name__ == "__main__":
    exportar()
