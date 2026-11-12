#!/bin/sh
# AgroMarket - instala, monta o banco e abre o site
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
python3 rodar_etl.py
python3 -m streamlit run app/app.py
