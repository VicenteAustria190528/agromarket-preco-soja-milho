"""Paleta (escura/clara) e CSS do site. Chamado no começo de cada página."""
import streamlit as st


def aplicar():

    # ------------------------------------------------------------------ estilo
    # Botão lua/sol: começa escuro; ?tema=claro no link abre claro
    if "escuro" not in st.session_state:
        st.session_state.escuro = st.query_params.get("tema", "escuro") != "claro"
    ESCURO = st.session_state.escuro
    if ESCURO:   # paleta escura (fundo grafite, cartões cinza, verde/vermelho suaves)
        TXT, CINZA, BORDA, FUNDO, CARTAO, GRADE, TRILHO = "#e8eaed", "#9aa0a6", "#3c4043", "#202124", "#28292c", "#35363a", "#3c4043"
        VERDE, VERDE_BG = "#81c995", "rgba(129,201,149,.16)"
        VERM, VERM_BG = "#f28b82", "rgba(242,139,130,.16)"
        AMAR, AMAR_BG = "#fdd663", "rgba(253,214,99,.14)"
        AZUL, AZUL_FILL = "#8ab4f8", "rgba(138,180,248,.12)"
        ANOS_CINZA = {2021: "#4a4d51", 2022: "#5f6368", 2023: "#80868b", 2024: "#9aa0a6", 2025: "#bdc1c6"}
    else:        # paleta clara
        TXT, CINZA, BORDA, FUNDO, CARTAO, GRADE, TRILHO = "#202124", "#5f6368", "#dadce0", "#ffffff", "#ffffff", "#eef0f2", "#eceff1"
        VERDE, VERDE_BG = "#137333", "#e6f4ea"
        VERM, VERM_BG = "#c5221f", "#fce8e6"
        AMAR, AMAR_BG = "#b06000", "#fef7e0"
        AZUL, AZUL_FILL = "#1a73e8", "rgba(26,115,232,.08)"
        ANOS_CINZA = {2021: "#c8ccd0", 2022: "#b3b8bd", 2023: "#9aa0a6", 2024: "#80868b", 2025: "#5f6368"}

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    html, body, [class*="css"], .stMarkdown, button, input {{ font-family: 'Roboto', sans-serif; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    .block-container {{ padding-top: 2.2rem; max-width: 1180px; }}
    .marca {{ font-size: 1.35rem; font-weight: 500; color: {TXT}; }}
    .marca b {{ color: {VERDE}; }}
    .trilha {{ color: {CINZA}; font-size: .85rem; margin: .2rem 0 .1rem; }}
    .titulo {{ font-size: 1.6rem !important; color: {TXT}; margin: 0; line-height: 1.3; }}
    .preco {{ font-size: 2.6rem; font-weight: 500; color: {TXT}; line-height: 1.1; margin-top: .4rem; }}
    .preco small {{ font-size: 1rem; color: {CINZA}; font-weight: 400; }}
    .selo {{ display: inline-block; padding: 2px 9px; border-radius: 8px; font-weight: 500; font-size: .95rem; margin-left: 6px; }}
    .sub {{ color: {CINZA}; font-size: .85rem; margin-top: .25rem; }}
    .veredito {{ margin: 1rem 0 .4rem; padding: 14px 16px; border-radius: 12px; border: 1px solid {BORDA}; }}
    .veredito .t {{ font-size: 1.1rem; font-weight: 500; }}
    .veredito .d {{ color: {CINZA}; font-size: .92rem; margin-top: 2px; }}
    .regua {{ position: relative; height: 8px; border-radius: 4px; margin: 14px 0 4px;
              background: linear-gradient(90deg, {VERM} 0%, #f29900 45%, {VERDE} 100%); opacity: .85; }}
    .regua .m {{ position: absolute; top: -6px; width: 4px; height: 20px; background: {TXT}; border-radius: 2px; }}
    .regua-l {{ display: flex; justify-content: space-between; color: {CINZA}; font-size: .75rem; }}
    .card {{ border: 1px solid {BORDA}; border-radius: 12px; padding: 14px 16px; background: {CARTAO}; }}
    .card h4 {{ margin: 0 0 6px 0; font-size: 1rem; font-weight: 500; color: {TXT}; }}
    .fatos {{ width: 100%; border-collapse: collapse; font-size: .9rem; border: none !important; margin: 0; }}
    .fatos tr, .fatos td {{ border: none !important; background: transparent !important; }}
    .fatos td {{ padding: 9px 0 !important; border-bottom: 1px solid {GRADE} !important; }}
    .fatos td:first-child {{ color: {CINZA}; }}
    .fatos td:last-child {{ text-align: right; font-weight: 500; color: {TXT}; }}
    .mini {{ border: 1px solid {BORDA}; background: {CARTAO}; border-radius: 12px; padding: 12px 14px; height: 150px; margin-bottom: 6px; }}
    .mini .selo {{ margin-left: 0; }}
    .mini .n {{ font-size: .85rem; color: {CINZA}; }}
    .mini .p {{ font-size: 1.25rem; font-weight: 500; color: {TXT}; margin: 4px 0; }}
    .mini .a {{ font-size: .8rem; color: {CINZA}; }}
    .secao {{ font-size: 1.15rem; font-weight: 500; color: {TXT}; margin: 1.6rem 0 .6rem; }}
    .barra {{ display: flex; align-items: center; gap: 10px; margin: 8px 0; font-size: .9rem; }}
    .barra .r {{ width: 210px; color: {CINZA}; }}
    .barra .f {{ flex: 1; height: 10px; background: {TRILHO}; border-radius: 5px; position: relative; }}
    .barra .f i {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 5px; }}
    .barra .v {{ width: 40px; text-align: right; font-weight: 500; }}
    .rodape {{ color: {CINZA}; font-size: .78rem; margin-top: 2rem; }}
    div[data-testid="stPopover"] button {{ border-radius: 18px; }}
    </style>""", unsafe_allow_html=True)

    if not ESCURO:
        st.markdown(f"""<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: {FUNDO} !important; color: {TXT}; }}
    .stApp [data-testid="stMarkdownContainer"], .stApp label, .stApp label p, [data-testid="stWidgetLabel"] p,
    [data-testid="stCaptionContainer"], [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p {{ color: {TXT} !important; }}
    [data-testid="stCaptionContainer"] {{ color: {CINZA} !important; }}
    [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="input"] > div, .stNumberInput input,
    .stDateInput input, [data-baseweb="base-input"] {{ background: #f1f3f4 !important; color: {TXT} !important; border-color: #f1f3f4 !important; }}
    [data-baseweb="select"] svg, .stNumberInput button {{ color: {TXT} !important; fill: {TXT} !important; }}
    .stNumberInput button {{ background: #f1f3f4 !important; }}
    .stButton button, [data-testid="stPopover"] button, [data-testid="stBaseButton-segmented_control"],
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-tertiary"] {{ background: {CARTAO} !important; color: {TXT} !important; border-color: {BORDA} !important; }}
    [data-testid="stBaseButton-segmented_controlActive"] {{ background: {VERDE_BG} !important; color: {VERDE} !important; border-color: {VERDE} !important; }}
    [data-testid="stExpander"] details, [data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {BORDA} !important; background: {CARTAO}; }}
    [data-baseweb="popover"] *, [data-baseweb="menu"] {{ background-color: {CARTAO}; color: {TXT}; }}
    pre, code {{ background: #f1f3f4 !important; color: {TXT} !important; }}
    [data-testid="stExpander"] summary {{ background: transparent !important; }}
    [data-testid="stNumberInputContainer"], [data-testid="stNumberInput"] > div > div {{ border-color: #f1f3f4 !important; }}
    [data-testid="stAlert"] {{ color: {TXT}; }}
    </style>""", unsafe_allow_html=True)
    return {k: v for k, v in locals().items() if k.isupper()}


def botao_tema(container):
    escuro = st.session_state.escuro
    container.button("☀️" if escuro else "🌙", key="tema_btn", help="Modo claro" if escuro else "Modo escuro",
                     on_click=lambda: st.session_state.update(escuro=not st.session_state.escuro))
