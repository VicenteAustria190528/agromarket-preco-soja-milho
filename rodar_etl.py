"""Orquestra o pipeline: extrair -> transformar -> carregar -> exportar planilha.

Uso:
  python rodar_etl.py            # usa os arquivos já baixados em data/raw (coleta de 05/11/2026)
  python rodar_etl.py --baixar   # baixa de novo das fontes (BCB e Notícias Agrícolas) antes
"""
import sys
from etl import transformar, montar_planilhas, exportar_excel
import planilhas_para_sqlite

if "--baixar" in sys.argv:
    from etl import extrair_ptax, extrair_noticias_agricolas
    extrair_ptax.extrair()
    extrair_noticias_agricolas.extrair()

print("1/4 Transformando...")
transformar.transformar()
print("2/4 Gravando uma planilha por fonte (planilhas/)...")
montar_planilhas.montar()
print("3/4 Convertendo as planilhas em banco SQLite...")
planilhas_para_sqlite.main()
print("4/4 Exportando a planilha consolidada...")
exportar_excel.exportar()
print("Pronto. Para abrir o app: streamlit run app/app.py")
