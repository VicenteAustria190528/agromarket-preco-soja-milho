"""AgroMarket · site em Streamlit que lê o banco db/agromarket.db.

Visual inspirado em painéis financeiros: preço em destaque, selo de variação,
gráfico principal com seletor, quadro de indicadores e comparação entre praças.

Página principal (aberta pelo app/app.py).
"""
import sys, os
from datetime import date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DATA_ANALISE, JANELA_DIAS, ANOS_REFERENCIA, DB
from etl.analise import conectar, analisar, frase, SQL_JANELA

from estilo import aplicar, botao_tema
globals().update(aplicar())


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
t1, t2, t3, t4 = st.columns([2.2, 2.6, 1.6, .45], vertical_alignment="center")
botao_tema(t4)
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
    layout = dict(height=360, margin=dict(l=0, r=60, t=10, b=30), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", separators=",.",
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
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})
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
        lay = {**layout, "hovermode": "closest", "margin": dict(l=50, r=10, t=30, b=30)}
        lay["xaxis"] = dict(showgrid=True, gridcolor=GRADE, tickprefix="R$ ", range=[lo - (hi - lo) * .06, hi + (hi - lo) * .4])
        lay["yaxis"] = dict(showgrid=False, autorange="reversed")
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})
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
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})
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
st.markdown('<div class="secao">De onde vêm os números</div>', unsafe_allow_html=True)
st.page_link("fontes.py", label="Ver as fontes de dados, as planilhas e o caminho de cada preço até o banco", icon="🗄️")

st.markdown(f'<div class="rodape">Fontes: Notícias Agrícolas (mercado físico), CEPEA/ESALQ-USP (CC BY-NC 4.0), '
            f'Banco Central do Brasil (PTAX). Trabalho acadêmico do Grupo PREÇO 1 · UPF/ESAN · BI, Data Science & Big Data. '
            f'Não é recomendação de venda.</div>', unsafe_allow_html=True)
