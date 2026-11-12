"""Orquestra o pipeline: extrair -> transformar -> carregar -> exportar planilha.

Uso:
  python rodar_etl.py            # usa os arquivos já baixados em data/raw (coleta de 05/11/2026)
  python rodar_etl.py --baixar   # baixa de novo das fontes (BCB e Notícias Agrícolas) antes
"""
import sys
from etl import transformar, carregar_dw, exportar_excel

if "--baixar" in sys.argv:
    from etl import extrair_ptax, extrair_noticias_agricolas
    extrair_ptax.extrair()
    extrair_noticias_agricolas.extrair()

print("1/3 Transformando...")
transformar.transformar()
print("2/3 Carregando o banco...")
carregar_dw.carregar()
print("3/3 Exportando a planilha consolidada...")
exportar_excel.exportar()
print("Pronto. Para abrir o app: streamlit run app/app.py")
