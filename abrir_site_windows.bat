@echo off
REM AgroMarket - instala, monta o banco e abre o site
python -m pip install -r requirements.txt
python rodar_etl.py
python -m streamlit run app/app.py
pause
