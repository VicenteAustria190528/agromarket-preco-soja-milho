"""AgroMarket · site em Streamlit que lê o banco db/agromarket.db.

Rodar:  streamlit run app/app.py
"""
import streamlit as st

st.set_page_config(page_title="AgroMarket · Hoje é dia de vender?", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")
if "escuro" not in st.session_state:
    st.session_state.escuro = st.query_params.get("tema", "escuro") != "claro"

pg = st.navigation([st.Page("painel.py", title="Hoje é dia de vender?", icon="🌾", default=True),
                    st.Page("fontes.py", title="Fontes de dados", icon="🗄️")], position="top")
pg.run()
