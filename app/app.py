"""AgroMarket · site em Streamlit que lê o banco db/agromarket.db.

Visual inspirado em painéis financeiros: preço em destaque, selo de variação,
gráfico principal com seletor, quadro de indicadores e comparação entre praças.

Rodar:  streamlit run app/app.py
"""
import sys, os
from datetime import date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_ANALISE, JANELA_DIAS, ANOS_REFERENCIA, DB
from etl.analise import conectar, analisar, frase, SQL_JANELA

st.set_page_config(page_title="AgroMarket · Hoje é dia de vender?", page_icon="🌱", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ estilo
try:
    ESCURO = (st.context.theme.type == "dark")
except Exception:
    ESCURO = False
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

if not DB.exists():
    st.error("Banco não encontrado. Rode antes: `python rodar_etl.py`")
    st.stop()


# ------------------------------------------------------------------ dados
@st.cache_data
def ler(sql, params=()):
    con = conectar()
    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df


@st.cache_data
def analise(praca, produto, oferta, hoje):
    con = conectar()
    r = analisar(con, praca, produto, oferta or None, hoje)
    con.close()
    return r


def br(v, casas=2):
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dbr(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


def tom(p):
    if p >= 60: return VERDE, VERDE_BG
    if p >= 40: return AMAR, AMAR_BG
    return VERM, VERM_BG


def selo(txt, p=None, cores=None):
    c, bg = cores or tom(p)
    return f'<span class="selo" style="color:{c};background:{bg}">{txt}</span>'


PRACAS = ler("""SELECT p.id_praca, p.municipio, p.uf, p.informante, p.codigo_ibge, p.tipo, f.id_produto,
                       COUNT(DISTINCT t.ano) AS anos
                FROM dim_praca p JOIN fato_preco_diario f ON f.id_praca = p.id_praca
                JOIN dim_tempo t ON t.id_data = f.id_data AND t.ano < 2026
                GROUP BY 1,2,3,4,5,6,7""")


def nome_praca(row):
    if row.informante.startswith("CEPEA"):
        return f"Indicador CEPEA · {row.uf}"
    return f"{row.municipio}/{row.uf}"


# ------------------------------------------------------------------ topo
t1, t2, t3 = st.columns([2.2, 2.6, 1.6], vertical_alignment="center")
t1.markdown('<div class="marca">🌱 Agro<b>Market</b></div>', unsafe_allow_html=True)
produto = t3.segmented_control("Produto", ["soja", "milho"], default="soja", format_func=str.capitalize,
                               label_visibility="collapsed") or "soja"
opc = PRACAS[PRACAS.id_produto == produto].copy()
opc["ordem"] = (opc.id_praca != "NMT").astype(int) * 10 - opc.anos + opc.informante.str.startswith("CEPEA") * 20
opc = opc.sort_values("ordem")
rotulo = {r.id_praca: f"{nome_praca(r)} · {r.informante}" for r in opc.itertuples()}
if st.session_state.get("praca") not in rotulo:
    st.session_state.praca = list(rotulo)[0]
praca = t2.selectbox("Praça", list(rotulo), format_func=lambda k: "🔎  " + rotulo[k], key="praca",
                     label_visibility="collapsed")
info = opc[opc.id_praca == praca].iloc[0]

# ------------------------------------------------------------------ análise
hoje = st.session_state.get("hoje", date.fromisoformat(DATA_ANALISE)).isoformat()
oferta = st.session_state.get("oferta", 0.0)
custo = st.session_state.get("custo", 0.0)
r = analise(praca, produto, oferta, hoje)

st.markdown(f'<div class="trilha">Mercado físico › {produto.capitalize()} › {info.uf} · IBGE {info.codigo_ibge or "—"}</div>',
            unsafe_allow_html=True)

if r is None or (r["cotacao_velha"] and not oferta):
    st.markdown(f'<div class="titulo">{produto.capitalize()} · {nome_praca(info)} ({info.informante})</div>', unsafe_allow_html=True)
    msg = ("Esta praça não publica preço desde " + dbr(r["ultima_data"]) + "." if r else "Sem dados para esta combinação.")
    st.warning(msg + " Digite abaixo o preço que te ofereceram para fazer a análise.")
    st.number_input("Preço que te ofereceram (R$/saca)", min_value=0.0, step=0.5, key="oferta")
    st.stop()

esq, dir_ = st.columns([2.05, 1], gap="large")

# ------------------------------------------------------------------ coluna esquerda
with esq:
    st.markdown(f'<div class="titulo">{produto.capitalize()} em grão · {nome_praca(info)} '
                f'<span style="color:{CINZA};font-size:1rem">({info.informante})</span></div>', unsafe_allow_html=True)
    d = r["preco"] - r["media"]
    pct = 100 * d / r["media"]
    seta = "▲" if d >= 0 else "▼"
    cor_var = (VERDE, VERDE_BG) if d >= 0 else (VERM, VERM_BG)
    origem = "Preço que te ofereceram" if oferta else f"Cotação de {dbr(r['ultima_data'])}"
    st.markdown(f"""
      <div class="preco">R$ {br(r['preco'])} <small>/saca</small>
        {selo(f"{seta} {br(abs(pct), 1)}%", cores=cor_var)}
        <span style="font-size:1rem;color:{cor_var[0]};font-weight:500">{'+' if d >= 0 else '−'}R$ {br(abs(d))}</span>
      </div>
      <div class="sub">Variação contra a média da época (R$ {br(r['media'])}) · {origem} · saca de 60 kg · comparado com {r['dias']} dias da mesma época de {r['anos'][0]} a {r['anos'][-1]}</div>
    """, unsafe_allow_html=True)

    c, bg = tom(r["p_brl"])
    st.markdown(f"""
      <div class="veredito" style="background:{bg};border-color:{bg}">
        <div class="t" style="color:{c}">{frase(r)}</div>
        <div class="d">Hoje o preço está melhor que <b>{r['dias_mais_baratos']} dos {r['dias']} dias</b> desta época nos últimos {len(r['anos'])} anos.</div>
        <div class="regua"><div class="m" style="left:calc({r['p_brl']}% - 2px)"></div></div>
        <div class="regua-l"><span>Fraco para a época</span><span>Normal</span><span>Muito bom</span></div>
      </div>""", unsafe_allow_html=True)

    vista = st.segmented_control("Gráfico", ["Esta época, ano a ano", "Régua das colheitas", "Dólar"],
                                 default="Esta época, ano a ano", label_visibility="collapsed") or "Esta época, ano a ano"
    layout = dict(height=360, margin=dict(l=0, r=10, t=10, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=",.",
                  font=dict(family="Roboto", color=CINZA, size=12), hovermode="x unified", showlegend=False,
                  hoverlabel=dict(bgcolor=CARTAO, font_color=TXT, bordercolor=BORDA),
                  yaxis=dict(gridcolor=GRADE, zeroline=False, side="right", tickprefix="R$ "),
                  xaxis=dict(showgrid=False, tickformat="%d/%m", linecolor=BORDA))

    if vista == "Esta época, ano a ano":
        s = pd.DataFrame(r["serie"])
        s["x"] = pd.to_datetime("2000-" + pd.to_datetime(s["data"]).dt.strftime("%m-%d"))
        atual = ler("""SELECT data, preco_brl FROM vw_preco_completo WHERE id_praca=? AND id_produto=? AND ano=?
                       AND data < ? ORDER BY data""", (praca, produto, int(hoje[:4]), hoje))
        fig = go.Figure()
        for ano, g in s.groupby("ano"):
            fig.add_trace(go.Scatter(x=g.x, y=g.preco_brl, name=str(ano), mode="lines",
                                     line=dict(color=ANOS_CINZA.get(ano, CINZA), width=1.6),
                                     hovertemplate=f"{ano}: R$ %{{y:.2f}}<extra></extra>"))
            fig.add_annotation(x=g.x.iloc[-1], y=g.preco_brl.iloc[-1], text=str(ano), showarrow=False,
                               xanchor="left", xshift=4, font=dict(size=11, color=ANOS_CINZA.get(ano, CINZA)))
        if len(atual):
            atual["x"] = pd.to_datetime("2000-" + pd.to_datetime(atual["data"]).dt.strftime("%m-%d"))
            fig.add_trace(go.Scatter(x=atual.x, y=atual.preco_brl, name=hoje[:4], mode="lines+markers",
                                     line=dict(color=c, width=3), marker=dict(size=7),
                                     hovertemplate=f"{hoje[:4]}: R$ %{{y:.2f}}<extra></extra>"))
        fig.add_hline(y=r["preco"], line_dash="dot", line_color=TXT, line_width=1,
                      annotation_text=f"hoje R$ {br(r['preco'])}", annotation_position="top left",
                      annotation_font=dict(color=TXT, size=11))
        x_hoje = pd.Timestamp("2000-" + hoje[5:])
        fig.add_vline(x=x_hoje, line_color=BORDA, line_width=1)
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(f"Linhas cinza: preço nos mesmos dias ({JANELA_DIAS} antes e {JANELA_DIAS} depois) de cada ano anterior. "
                   f"Linha colorida: {hoje[:4]}. Pontilhado: preço de hoje.")

    elif vista == "Régua das colheitas":
        fig = go.Figure()
        for g in r["regua"]:
            cor_b = VERDE if g["dias_abaixo"] == g["dias"] else (VERM if g["dias_abaixo"] == 0 else AMAR)
            larg = max(g["maximo"] - g["minimo"], 0.6)
            fig.add_trace(go.Bar(y=[str(g["ano"])], x=[larg], base=[g["minimo"] - (0.3 if g["maximo"] == g["minimo"] else 0)],
                                 orientation="h", marker=dict(color=cor_b, opacity=.75), width=.5,
                                 hovertemplate=f"{g['ano']}: R$ {br(g['minimo'])} a R$ {br(g['maximo'])}<extra></extra>",
                                 text=f"  melhor que {g['dias_abaixo']} de {g['dias']} dias", textposition="outside",
                                 textfont=dict(color=CINZA, size=11)))
        fig.add_vline(x=r["preco"], line_width=2, line_color=TXT,
                      annotation_text=f"hoje R$ {br(r['preco'])}", annotation_position="top")
        lo, hi = min(r["minimo"], r["preco"]), max(r["maximo"], r["preco"])
        lay = {**layout, "hovermode": "closest", "margin": dict(l=0, r=10, t=30, b=0)}
        lay["xaxis"] = dict(showgrid=True, gridcolor=GRADE, tickprefix="R$ ", range=[lo - (hi - lo) * .06, hi + (hi - lo) * .4])
        lay["yaxis"] = dict(showgrid=False, autorange="reversed")
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Cada barra vai do pior ao melhor preço da época naquele ano. Verde: hoje é melhor que todos os dias daquele ano; "
                   "vermelho: hoje é pior que todos.")

    else:
        ptax = ler("SELECT t.data, t.ano, c.ptax_venda FROM fato_cambio_ptax c JOIN dim_tempo t ON t.id_data=c.id_data "
                   "WHERE t.data <= ? ORDER BY 1", (hoje,))
        ptax["x"] = pd.to_datetime("2000-" + pd.to_datetime(ptax["data"]).dt.strftime("%m-%d"))
        fig = go.Figure()
        for ano, g in ptax.groupby("ano"):
            atual_ano = ano == int(hoje[:4])
            fig.add_trace(go.Scatter(x=g.x, y=g.ptax_venda, mode="lines",
                                     line=dict(color=AZUL if atual_ano else ANOS_CINZA.get(ano, CINZA), width=3 if atual_ano else 1.6),
                                     fill="tozeroy" if atual_ano else None, fillcolor=AZUL_FILL,
                                     hovertemplate=f"{ano}: R$ %{{y:.4f}}<extra></extra>"))
            fig.add_annotation(x=g.x.iloc[-1], y=g.ptax_venda.iloc[-1], text=str(ano), showarrow=False, xanchor="left",
                               xshift=4, font=dict(size=11, color=AZUL if atual_ano else CINZA))
        lay = {**layout}
        lay["yaxis"] = dict(gridcolor=GRADE, side="right", tickprefix="R$ ", range=[ptax.ptax_venda.min() - .1, ptax.ptax_venda.max() + .1])
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption("Dólar oficial do Banco Central (PTAX de venda) nos mesmos dias de cada ano. Azul: ano atual.")

# ------------------------------------------------------------------ coluna direita
with dir_:
    with st.popover(f"📅  Data de análise: {dbr(hoje)}", use_container_width=True):
        st.date_input("Analisar como se hoje fosse", value=date.fromisoformat(DATA_ANALISE), key="hoje",
                      min_value=date(2026, 10, 22), max_value=date.fromisoformat(DATA_ANALISE), format="DD/MM/YYYY")
        st.caption("Só entram dados publicados antes dessa data, para não usar informação do futuro.")

    linhas = [
        ("Média da época", f"R$ {br(r['media'])}"),
        ("Pior dia da época", f"R$ {br(r['minimo'])}"),
        ("Melhor dia da época", f"R$ {br(r['maximo'])}"),
        ("Dias comparados", f"{r['dias']} ({len(r['anos'])} anos)"),
        ("Nota do preço (0 a 100)", selo(str(r["p_brl"]), r["p_brl"])),
        ("Preço em dólar", f"US$ {br(r['preco_usd'])}"),
        ("O dólar hoje", f"R$ {br(r['ptax'], 4)}"),
        ("Dólar normal da época", f"R$ {br(r['ptax_mediana'], 4)}"),
    ]
    st.markdown('<div class="card"><h4>Resumo</h4><table class="fatos">' +
                "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in linhas) + "</table></div>",
                unsafe_allow_html=True)
    if info.anos < ANOS_REFERENCIA:
        st.warning(f"Esta praça só tem {info.anos} ano(s) de histórico; a regra pede {ANOS_REFERENCIA}.")

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**Simular uma oferta**")
        st.number_input("Preço que te ofereceram (R$/saca)", min_value=0.0, step=0.5, key="oferta",
                        help="Deixe 0 para usar a última cotação da praça.")
        st.number_input("Seu custo por saca (R$)", min_value=0.0, step=1.0, key="custo")
        if custo:
            m = r["preco"] - custo
            st.markdown(f"Margem: **R$ {br(m)} por saca** " + selo(f"{br(100 * m / custo, 1)}%",
                        cores=(VERDE, VERDE_BG) if m >= 0 else (VERM, VERM_BG)), unsafe_allow_html=True)

# ------------------------------------------------------------------ por que
st.markdown('<div class="secao">Por que o preço está assim?</div>', unsafe_allow_html=True)
p1, p2 = st.columns([1.25, 1], gap="large")
with p1:
    dif = r["preco"] - r["preco_com_dolar_normal"]
    if r["p_dolar"] >= 55 and r["p_usd"] < r["p_brl"]:
        txt = (f"<b>O dólar alto está ajudando.</b> Se o dólar estivesse no normal da época, essa saca valeria cerca de "
               f"<b>R$ {br(r['preco_com_dolar_normal'])}</b>, ou seja, o dólar está colocando <b>R$ {br(dif)}</b> a mais em cada saca. "
               "Se o dólar cair, o preço tende a cair junto.")
    elif r["p_dolar"] <= 45 and r["p_usd"] > r["p_brl"]:
        txt = (f"<b>O dólar baixo está atrapalhando.</b> Com o dólar no normal da época, a saca valeria cerca de "
               f"<b>R$ {br(r['preco_com_dolar_normal'])}</b>: o dólar está tirando <b>R$ {br(-dif)}</b> de cada saca.")
    else:
        txt = "O dólar está perto do normal da época. O preço reflete principalmente o mercado do grão."
    st.markdown(f'<div class="card" style="font-size:.95rem;line-height:1.5">{txt}</div>', unsafe_allow_html=True)
with p2:
    barras = [("Preço em reais", r["p_brl"], tom(r["p_brl"])[0]),
              ("Preço sem o efeito do dólar", r["p_usd"], tom(r["p_usd"])[0]),
              ("O dólar", r["p_dolar"], AZUL)]
    st.markdown("".join(f'<div class="barra"><span class="r">{n}</span><span class="f"><i style="width:{v}%;background:{c}"></i></span>'
                        f'<span class="v" style="color:{c}">{v}</span></div>' for n, v, c in barras) +
                f'<div class="sub">Nota de 0 a 100 comparando com a mesma época dos anos anteriores. 50 = normal.</div>',
                unsafe_allow_html=True)

# ------------------------------------------------------------------ outras praças
st.markdown(f'<div class="secao">Compare com outras praças · {produto}</div>', unsafe_allow_html=True)
outras = [p for p in opc.itertuples() if p.id_praca != praca]
cols = st.columns(max(len(outras), 1))
for col, p in zip(cols, outras):
    ro = analise(p.id_praca, produto, 0.0, hoje)
    with col:
        if ro is None or ro["cotacao_velha"]:
            corpo = f'<div class="p" style="color:{CINZA}">—</div><div class="a">sem cotação recente</div>'
        else:
            corpo = (f'<div class="p">R$ {br(ro["preco"])}</div>{selo("nota " + str(ro["p_brl"]), ro["p_brl"])}'
                     f'<div class="a" style="margin-top:6px">melhor que {ro["dias_mais_baratos"]} de {ro["dias"]} dias</div>')
        st.markdown(f'<div class="mini"><div class="n">{nome_praca(p)} · {p.informante}</div>{corpo}</div>',
                    unsafe_allow_html=True)
        st.button("Ver esta praça", key=f"ver_{p.id_praca}", use_container_width=True,
                  on_click=lambda k=p.id_praca: st.session_state.update(praca=k))

# ------------------------------------------------------------------ dados e banco
st.markdown('<div class="secao">Sobre os dados</div>', unsafe_allow_html=True)
with st.expander("De onde vêm os números · fonte → ETL → banco → site"):
    st.markdown("""
1. `etl/extrair_*.py` baixa as fontes e guarda o arquivo bruto em `data/raw/` (sem mexer).
2. `etl/transformar.py` limpa: troca vírgula por ponto, liga o nome da praça ao código IBGE,
   descarta "s/ cotação" e marca saltos fora do normal.
3. `etl/carregar_dw.py` grava no banco `db/agromarket.db` (modelo estrela: dimensões, fatos e log da carga).
4. `etl/exportar_excel.py` gera a planilha a partir do banco, e este site consulta o mesmo banco.
""")
    st.dataframe(ler("SELECT nome AS fonte, formato, frequencia, defasagem, licenca, url FROM dim_fonte"),
                 hide_index=True, use_container_width=True)
with st.expander("Cobertura e alertas de qualidade"):
    a1, a2 = st.columns([3, 2])
    cob = ler("SELECT praca, id_produto AS produto, ano, COUNT(*) AS dias FROM vw_preco_completo GROUP BY 1,2,3")
    a1.markdown("**Dias com preço por praça e ano**")
    a1.dataframe(cob.pivot_table(index=["praca", "produto"], columns="ano", values="dias", fill_value=0),
                 use_container_width=True)
    a2.markdown("**Para conferir**")
    a2.dataframe(ler("""SELECT data, praca, id_produto AS produto, preco_brl AS valor, alerta FROM vw_preco_completo WHERE alerta IS NOT NULL
                        UNION ALL SELECT data_referencia, 'Dólar PTAX', '', ptax_venda, alerta FROM fato_cambio_ptax WHERE alerta IS NOT NULL"""),
                 hide_index=True, use_container_width=True)
    a2.markdown("**Última carga do banco**")
    a2.dataframe(ler("SELECT tabela, linhas, executado_em FROM log_carga"), hide_index=True, use_container_width=True)
with st.expander("Consulta SQL do cálculo e tabela de dados"):
    st.code(SQL_JANELA.strip(), language="sql")
    st.caption(f"Parâmetros: praça={praca}, produto={produto}, hoje={hoje}, anos={ANOS_REFERENCIA}, janela=±{JANELA_DIAS} dias. "
               "Nota = % de dias da época com preço menor que o de hoje. Preço em US$ = R$ ÷ PTAX do mesmo dia.")
    fato = ler("SELECT data, praca, id_produto AS produto, id_fonte AS fonte, preco_brl, ptax_venda, preco_usd, "
               "data_publicacao FROM vw_preco_completo WHERE id_produto=? ORDER BY data DESC", (produto,))
    st.dataframe(fato, hide_index=True, use_container_width=True, height=300)
    st.download_button("Baixar CSV", fato.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       f"agromarket_{produto}.csv", "text/csv")

st.markdown(f'<div class="rodape">Fontes: Notícias Agrícolas (mercado físico), CEPEA/ESALQ-USP (CC BY-NC 4.0), '
            f'Banco Central do Brasil (PTAX). Trabalho acadêmico do Grupo PREÇO 1 · UPF/ESAN · BI, Data Science & Big Data. '
            f'Não é recomendação de venda.</div>', unsafe_allow_html=True)
