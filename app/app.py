"""AgroMarket · site em Streamlit que lê o banco db/agromarket.db.

Rodar:  streamlit run app/app.py
"""
import sys, os
from datetime import date
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB, DATA_ANALISE, JANELA_DIAS, ANOS_REFERENCIA
from etl.analise import conectar, analisar, frase, SQL_JANELA

st.set_page_config(page_title="AgroMarket · Hoje é dia de vender?", page_icon="🌱", layout="wide")
VERDE, AMARELO, VERMELHO, CINZA = "#1F6B3A", "#C99A06", "#B42318", "#9CA3AF"
CORES_ANO = {2021: "#9CA3AF", 2022: "#6B7280", 2023: "#C99A06", 2024: "#2563EB", 2025: "#1F6B3A", 2026: "#B42318"}

st.markdown("""<style>
.veredito{border-radius:14px;padding:18px 22px;color:white;margin-bottom:8px}
.veredito h2{margin:0;color:white;font-size:1.7rem}
.veredito p{margin:4px 0 0 0;font-size:1.05rem}
div[data-testid="stMetricValue"]{font-size:1.6rem}
</style>""", unsafe_allow_html=True)

if not DB.exists():
    st.error("Banco não encontrado. Rode antes: `python rodar_etl.py`")
    st.stop()


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


def cor(p):
    return VERDE if p >= 60 else (AMARELO if p >= 40 else VERMELHO)


# ---------------- Barra lateral ----------------
pracas = ler("""SELECT p.id_praca, p.municipio, p.uf, p.informante, p.codigo_ibge, f.id_produto,
                COUNT(DISTINCT t.ano) AS anos
             FROM dim_praca p JOIN fato_preco_diario f ON f.id_praca = p.id_praca
             JOIN dim_tempo t ON t.id_data = f.id_data AND t.ano < 2026
             GROUP BY 1,2,3,4,5,6""")
st.sidebar.title("🌱 AgroMarket")
st.sidebar.caption("Grupo PREÇO 1 · UPF/ESAN · BI, Data Science & Big Data")
produto = st.sidebar.radio("Produto", ["soja", "milho"], format_func=str.capitalize, horizontal=True)
opc = pracas[pracas.id_produto == produto].copy()
opc["ordem"] = (opc.id_praca != "NMT").astype(int) * 10 - opc.anos + opc.informante.str.startswith("CEPEA") * 20
opc = opc.sort_values("ordem")
rotulo = {r.id_praca: (f"Indicador {r.informante} · {r.uf}" if r.informante.startswith("CEPEA")
                       else f"{r.municipio}/{r.uf} · {r.informante}") for r in opc.itertuples()}
praca = st.sidebar.selectbox("Praça (onde você vende)", list(rotulo), format_func=rotulo.get)
hoje = st.sidebar.date_input("Data de análise (\"hoje\")", value=date.fromisoformat(DATA_ANALISE),
                             min_value=date(2026, 10, 22), max_value=date.fromisoformat(DATA_ANALISE), format="DD/MM/YYYY").isoformat()
oferta = st.sidebar.number_input("Preço que te ofereceram (R$/saca)", min_value=0.0, value=0.0, step=0.5,
                                 help="Deixe 0 para usar a última cotação publicada da praça.")
custo = st.sidebar.number_input("Seu custo por saca (R$) · opcional", min_value=0.0, value=0.0, step=1.0)
anos_praca = int(opc.loc[opc.id_praca == praca, "anos"].iloc[0])
if anos_praca < ANOS_REFERENCIA:
    st.sidebar.warning(f"Esta praça só tem {anos_praca} ano(s) de histórico. A regra pede {ANOS_REFERENCIA}.")
st.sidebar.divider()
st.sidebar.caption(f"Época = {JANELA_DIAS} dias antes e depois da data, nos {ANOS_REFERENCIA} anos anteriores, "
                   "mesma praça. Fonte dos dados: banco `agromarket.db`.")

r = analise(praca, produto, oferta, hoje)
if r is None:
    st.warning("Sem dados suficientes para esta combinação de praça, produto e data.")
    st.stop()

if r["cotacao_velha"] and not oferta:
    st.warning(f"Esta praça não publica preço desde {dbr(r['ultima_data'])}. "
               "Digite na barra lateral o preço que te ofereceram para fazer a análise.")
    st.stop()

aba1, aba2, aba3, aba4 = st.tabs(["🌾 Hoje é dia de vender?", "📊 Painel BI", "💵 É a soja ou o dólar?", "🗄️ Dados e banco"])

# ---------------- 1. Produtor ----------------
with aba1:
    origem = "preço que te ofereceram" if oferta else f"última cotação publicada ({dbr(r['ultima_data'])})"
    st.markdown(f"""<div class="veredito" style="background:{cor(r['p_brl'])}">
      <h2>R$ {br(r['preco'])} a saca · {frase(r)}</h2>
      <p>Esse preço ganha de <b>{r['dias_mais_baratos']} dos {r['dias']} dias</b> da mesma época nos últimos
      {len(r['anos'])} anos ({r['anos'][0]}–{r['anos'][-1]}). Base: {origem}.</p></div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nota do preço (0 a 100)", r["p_brl"], help="% de dias da época em que o preço foi menor que o de hoje")
    d = r["preco"] - r["media"]
    c2.metric(f"Hoje vs média da época (R$ {br(r['media'])})", f"{'+' if d >= 0 else '−'} R$ {br(abs(d))}")
    c3.metric("Pior / melhor dia da época", f"{br(r['minimo'], 0)} / {br(r['maximo'], 0)}")
    if custo:
        c4.metric("Sua margem por saca", f"R$ {br(r['preco'] - custo)}", f"{br(100 * (r['preco'] - custo) / custo, 1)}%")
    else:
        c4.metric("Dólar hoje (PTAX)", f"R$ {br(r['ptax'], 4)}", help=f"PTAX de {dbr(r['ptax_data'])}")

    st.subheader("Régua das últimas colheitas")
    st.caption("Cada barra mostra do pior ao melhor preço da época naquele ano. A linha é o preço de hoje.")
    fig = go.Figure()
    for g in r["regua"]:
        fig.add_trace(go.Bar(y=[str(g["ano"])], x=[g["maximo"] - g["minimo"] or 0.6], base=[g["minimo"] - (0.3 if g["maximo"] == g["minimo"] else 0)],
                             orientation="h", marker_color=CORES_ANO.get(g["ano"], CINZA), showlegend=False,
                             hovertemplate=f"{g['ano']}: R$ {br(g['minimo'])} a R$ {br(g['maximo'])}<extra></extra>",
                             text=f"hoje ganha de {g['dias_abaixo']} de {g['dias']} dias", textposition="outside"))
    fig.add_vline(x=r["preco"], line_width=3, line_color="#111827",
                  annotation_text=f"Hoje R$ {br(r['preco'])}", annotation_position="top")
    lo, hi = min(r["minimo"], r["preco"]), max(r["maximo"], r["preco"])
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), xaxis_title="R$ por saca",
                      xaxis_range=[lo - (hi - lo) * 0.08, hi + (hi - lo) * 0.35], plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    melhores = [g["ano"] for g in r["regua"] if g["dias_abaixo"] == g["dias"]]
    piores = [g["ano"] for g in r["regua"] if g["dias_abaixo"] == 0]
    partes = []
    if melhores: partes.append(f"está **melhor que todos os dias** de {', '.join(map(str, melhores))}")
    if piores: partes.append(f"está **pior que todos os dias** de {', '.join(map(str, piores))}")
    if partes: st.info("O preço de hoje " + " e ".join(partes) + ".")

# ---------------- 2. Painel BI ----------------
with aba2:
    serie = pd.DataFrame(r["serie"])
    serie["data"] = pd.to_datetime(serie["data"])
    serie["dia_epoca"] = pd.to_datetime("2000-" + serie["data"].dt.strftime("%m-%d"))
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Dias na época", r["dias"])
    k2.metric("Anos de referência", len(r["anos"]))
    k3.metric("Nota em R$", r["p_brl"])
    k4.metric("Nota em US$", r["p_usd"])
    k5.metric("Nota do dólar", r["p_dolar"])

    g1, g2 = st.columns(2)
    with g1:
        fig = px.line(serie, x="dia_epoca", y="preco_brl", color=serie["ano"].astype(str),
                      color_discrete_map={str(k): v for k, v in CORES_ANO.items()}, markers=True,
                      labels={"dia_epoca": "dia da época", "preco_brl": "R$/saca", "color": "ano"},
                      title="Preço na mesma época, ano a ano")
        fig.add_hline(y=r["preco"], line_dash="dash", line_color="#111827", annotation_text="hoje")
        fig.update_layout(height=380, plot_bgcolor="white", legend_title_text="", xaxis_tickformat="%d/%m")
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig = px.box(serie, x=serie["ano"].astype(str), y="preco_brl", points="all",
                     color=serie["ano"].astype(str), color_discrete_map={str(k): v for k, v in CORES_ANO.items()},
                     labels={"x": "ano", "preco_brl": "R$/saca"}, title="Distribuição do preço por ano (época)")
        fig.add_hline(y=r["preco"], line_dash="dash", line_color="#111827", annotation_text="hoje")
        fig.update_layout(height=380, plot_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        comp = ler("""SELECT praca, ano, ROUND(AVG(preco_brl),2) AS media FROM vw_preco_completo
                      WHERE id_produto = ? AND ano < ? GROUP BY 1,2 ORDER BY 2""", (produto, int(hoje[:4])))
        fig = px.line(comp, x="ano", y="media", color="praca", markers=True,
                     labels={"media": "R$/saca (média da época)", "praca": ""}, title="Comparativo entre praças e indicador CEPEA")
        fig.update_layout(height=380, plot_bgcolor="white", legend=dict(orientation="h", y=-0.25), xaxis_dtick=1)
        st.plotly_chart(fig, use_container_width=True)
    with g4:
        ptax = ler("SELECT t.data, t.ano, c.ptax_venda FROM fato_cambio_ptax c JOIN dim_tempo t ON t.id_data=c.id_data ORDER BY 1")
        ptax["dia_epoca"] = pd.to_datetime("2000-" + pd.to_datetime(ptax["data"]).dt.strftime("%m-%d"))
        fig = px.line(ptax, x="dia_epoca", y="ptax_venda", color=ptax["ano"].astype(str),
                      color_discrete_map={str(k): v for k, v in CORES_ANO.items()},
                      labels={"dia_epoca": "dia da época", "ptax_venda": "R$ por US$", "color": "ano"},
                      title="Dólar PTAX na mesma época (BCB)")
        fig.update_layout(height=380, plot_bgcolor="white", legend_title_text="", xaxis_tickformat="%d/%m")
        st.plotly_chart(fig, use_container_width=True)

# ---------------- 3. Soja ou dólar ----------------
with aba3:
    st.subheader("O preço está bom por causa do grão ou por causa do dólar?")
    fig = go.Figure(go.Bar(x=[r["p_brl"], r["p_usd"], r["p_dolar"]],
                           y=["Preço em reais", "Preço em dólar (sem o efeito do câmbio)", "Dólar (PTAX)"],
                           orientation="h", marker_color=[cor(r["p_brl"]), cor(r["p_usd"]), "#2563EB"],
                           text=[r["p_brl"], r["p_usd"], r["p_dolar"]], textposition="outside"))
    fig.add_vline(x=50, line_dash="dot", line_color=CINZA, annotation_text="normal da época")
    fig.update_layout(height=280, xaxis_range=[0, 105], xaxis_title="nota de 0 a 100 (vs. mesma época dos anos anteriores)",
                      plot_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
    dif = r["preco"] - r["preco_com_dolar_normal"]
    if r["p_dolar"] >= 55 and r["p_usd"] < r["p_brl"]:
        txt = (f"**O dólar alto está ajudando.** Com o dólar no normal da época (R$ {br(r['ptax_mediana'], 4)}), "
               f"essa saca valeria cerca de **R$ {br(r['preco_com_dolar_normal'])}** ({br(dif)} a menos). "
               "Se o dólar cair, o preço tende a cair junto.")
    elif r["p_dolar"] <= 45 and r["p_usd"] > r["p_brl"]:
        txt = (f"**O dólar baixo está atrapalhando.** Com o dólar no normal da época, a saca valeria cerca de "
               f"**R$ {br(r['preco_com_dolar_normal'])}** ({br(-dif)} a mais).")
    else:
        txt = "O dólar está perto do normal da época; o preço reflete principalmente o mercado do grão."
    st.markdown(txt.replace("$", "\\$"))
    c1, c2, c3 = st.columns(3)
    c1.metric("Preço em US$ por saca", f"US$ {br(r['preco_usd'])}")
    c2.metric("Dólar hoje", f"R$ {br(r['ptax'], 4)}")
    c3.metric("Dólar normal da época (mediana)", f"R$ {br(r['ptax_mediana'], 4)}")
    st.caption("Preço em US\\$ = preço em R\\$ ÷ PTAX de venda do mesmo dia (Banco Central).")

# ---------------- 4. Dados ----------------
with aba4:
    st.subheader("De onde vêm os números")
    st.markdown("""
**Fonte → ETL (Python) → Banco (SQLite, modelo estrela) → Planilha e Site**

1. `etl/extrair_*.py` baixa as fontes e guarda o arquivo bruto em `data/raw/` (sem mexer).
2. `etl/transformar.py` limpa: troca vírgula por ponto, normaliza o nome da praça para o código IBGE,
   descarta "s/ cotação", marca saltos fora do normal.
3. `etl/carregar_dw.py` grava no banco `db/agromarket.db` (dimensões + fatos + log da carga).
4. `etl/exportar_excel.py` gera a planilha a partir do banco, e este site consulta o mesmo banco.
""")
    fontes = ler("SELECT nome AS fonte, formato, frequencia, defasagem, licenca, url FROM dim_fonte")
    st.dataframe(fontes, hide_index=True, use_container_width=True)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**Cobertura: dias com preço por praça e ano**")
        cob = ler("SELECT praca, id_produto AS produto, ano, COUNT(*) AS dias FROM vw_preco_completo GROUP BY 1,2,3")
        piv = cob.pivot_table(index=["praca", "produto"], columns="ano", values="dias", fill_value=0)
        st.dataframe(piv, use_container_width=True)
    with c2:
        st.markdown("**Alertas de qualidade (conferir)**")
        al = ler("""SELECT data, praca, id_produto AS produto, preco_brl AS valor, alerta FROM vw_preco_completo WHERE alerta IS NOT NULL
                    UNION ALL SELECT data_referencia, 'PTAX', 'dólar', ptax_venda, alerta FROM fato_cambio_ptax WHERE alerta IS NOT NULL""")
        st.dataframe(al, hide_index=True, use_container_width=True)
        log = ler("SELECT tabela, linhas, executado_em FROM log_carga")
        st.markdown("**Última carga do banco**")
        st.dataframe(log, hide_index=True, use_container_width=True)

    with st.expander("Ver a consulta SQL usada no cálculo"):
        st.code(SQL_JANELA.strip(), language="sql")
        st.caption(f"Parâmetros: praça={praca}, produto={produto}, hoje={hoje}, anos={ANOS_REFERENCIA}, janela=±{JANELA_DIAS} dias")
    with st.expander("Explorar a tabela fato (vw_preco_completo)"):
        fato = ler("SELECT data, praca, id_produto AS produto, id_fonte AS fonte, preco_brl, ptax_venda, preco_usd, "
                   "data_publicacao FROM vw_preco_completo WHERE id_produto=? ORDER BY data DESC", (produto,))
        st.dataframe(fato, hide_index=True, use_container_width=True, height=320)
        st.download_button("Baixar CSV", fato.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           f"agromarket_{produto}.csv", "text/csv")
