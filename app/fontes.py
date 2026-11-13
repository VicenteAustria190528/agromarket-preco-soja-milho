"""Página "Fontes de dados": de onde vem cada número do site, com link, formato,
licença, planilha para baixar e o caminho de um preço da fonte até o banco."""
import sys, os, json
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RAIZ, RAW, DB, NA_URL, BCB_SGS_URL
from etl.analise import conectar
from etl.transformar import normalizar_praca
from estilo import aplicar, botao_tema

globals().update(aplicar())
PL = RAIZ / "planilhas"

st.markdown(f"""<style>
.fluxo {{ display: flex; align-items: stretch; gap: 8px; margin: 14px 0 6px; flex-wrap: wrap; }}
.fluxo .e {{ flex: 1; min-width: 150px; border: 1px solid {BORDA}; background: {CARTAO}; border-radius: 12px; padding: 12px 14px; }}
.fluxo .e b {{ display: block; color: {TXT}; font-weight: 500; margin-bottom: 2px; }}
.fluxo .e span {{ color: {CINZA}; font-size: .82rem; }}
.fluxo .e i {{ font-style: normal; font-size: 1.3rem; }}
.fluxo .s {{ align-self: center; color: {CINZA}; font-size: 1.3rem; }}
.fonte {{ border: 1px solid {BORDA}; background: {CARTAO}; border-radius: 12px; padding: 16px 18px; margin-top: 6px; }}
.fonte h3 {{ margin: 0 0 2px 0; font-size: 1.12rem; font-weight: 500; color: {TXT}; }}
.fonte .q {{ color: {VERDE}; font-size: .9rem; margin-bottom: 10px; }}
.fonte table {{ width: 100%; border-collapse: collapse; font-size: .88rem; border: none !important; }}
.fonte tr, .fonte td {{ border: none !important; background: transparent !important; }}
.fonte td {{ padding: 6px 0 !important; border-bottom: 1px solid {GRADE} !important; vertical-align: top; }}
.fonte td:first-child {{ color: {CINZA}; width: 34%; }}
.fonte td:last-child {{ color: {TXT}; }}
.fonte a {{ color: {AZUL}; word-break: break-all; }}
.passo {{ border-left: 3px solid {VERDE}; padding: 4px 0 4px 12px; margin: 8px 0; color: {TXT}; font-size: .92rem; }}
.passo small {{ color: {CINZA}; display: block; }}
.passo code {{ font-size: .85rem; }}
</style>""", unsafe_allow_html=True)


@st.cache_data
def ler(sql, params=()):
    con = conectar()
    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df


@st.cache_data
def bruto_na():
    return pd.read_csv(RAW / "noticias_agricolas_cotacoes.csv", sep=";", dtype=str, keep_default_na=False)


@st.cache_data
def bruto_bcb():
    return pd.DataFrame(json.loads((RAW / "bcb_ptax_sgs1.json").read_text()))


def dbr(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


# ------------------------------------------------------------------ topo
c1, c2 = st.columns([10, .6], vertical_alignment="center")
c1.markdown(f'<div class="trilha">AgroMarket › Fontes de dados</div><div class="titulo">De onde vêm os números</div>'
            f'<div class="sub">Tudo o que aparece no site sai destas fontes. Nada é digitado à mão: '
            f'a fonte vira planilha, a planilha vira banco de dados e o site lê o banco.</div>', unsafe_allow_html=True)
botao_tema(c2)

n_preco = ler("SELECT COUNT(*) n FROM fato_preco_diario").n[0]
n_ptax = ler("SELECT COUNT(*) n FROM fato_cambio_ptax").n[0]
n_praca = ler("SELECT COUNT(*) n FROM dim_praca").n[0]
carga = ler("SELECT MAX(executado_em) m FROM log_carga").m[0]
st.markdown(f"""<div class="fluxo">
  <div class="e"><i>🌐</i><b>1 · Fontes</b><span>CEPEA, Notícias Agrícolas, Banco Central e IBGE. Coleta em 05/11/2026.</span></div>
  <div class="s">→</div>
  <div class="e"><i>📄</i><b>2 · Planilhas</b><span>Uma por fonte, com os dados como vieram e já limpos.</span></div>
  <div class="s">→</div>
  <div class="e"><i>🗄️</i><b>3 · Banco SQLite</b><span>{n_preco} preços, {n_ptax} dias de dólar, {n_praca} praças. Carga: {carga[:16].replace('T', ' ')}.</span></div>
  <div class="s">→</div>
  <div class="e"><i>📊</i><b>4 · Site</b><span>Calcula a nota do preço com uma consulta SQL no banco.</span></div>
</div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ as fontes
FONTES = [
    dict(arq="01_CEPEA_indicadores_soja_milho.xlsx", icone="🌱", nome="CEPEA/ESALQ-USP · Indicadores de soja e milho",
         pergunta="Responde: olhando o preço em reais, hoje é dia de fechar negócio?",
         fonte_id="CEPEA", link="https://www.cepea.org.br/br/indicador/soja.aspx",
         sql="SELECT COUNT(*) n, MIN(data_referencia) a, MAX(data_referencia) b FROM fato_preco_diario WHERE id_fonte='CEPEA'"),
    dict(arq="02_Pracas_RS_mercado_fisico_soja_milho.xlsx", icone="🏘️", nome="Notícias Agrícolas · Preço nas praças do RS",
         pergunta="Responde: a cooperativa da minha cidade paga mais ou menos que a referência?",
         fonte_id="NA", link="https://www.noticiasagricolas.com.br/cotacoes/soja/soja-mercado-fisico-sindicatos-e-cooperativas",
         sql="SELECT COUNT(*) n, MIN(data_referencia) a, MAX(data_referencia) b FROM fato_preco_diario WHERE id_fonte='NA'"),
    dict(arq="03_BCB_dolar_PTAX.xlsx", icone="💵", nome="Banco Central do Brasil · Dólar PTAX",
         pergunta="Responde: o preço está baixo porque a soja caiu ou porque o dólar caiu?",
         fonte_id="BCB", link="https://dadosabertos.bcb.gov.br/dataset/dolar-americano-usd-todos-os-boletins-diarios",
         sql="SELECT COUNT(*) n, MIN(data_referencia) a, MAX(data_referencia) b FROM fato_cambio_ptax"),
    dict(arq="04_Dimensao_pracas_IBGE.xlsx", icone="📍", nome="IBGE · Códigos de município",
         pergunta="Liga o nome da praça escrito pela fonte ao código oficial do município.",
         fonte_id=None, link="https://servicodados.ibge.gov.br/api/v1/localidades/estados/RS/municipios",
         sql="SELECT COUNT(*) n, '' a, '' b FROM dim_praca"),
]

st.markdown('<div class="secao">As fontes</div>', unsafe_allow_html=True)
for i in range(0, len(FONTES), 2):
    cols = st.columns(2, gap="medium")
    for col, f in zip(cols, FONTES[i:i + 2]):
        sobre = dict(pd.read_excel(PL / f["arq"], sheet_name="sobre").values)
        q = ler(f["sql"]).iloc[0]
        periodo = f"{dbr(q.a)} a {dbr(q.b)}" if q.a else "—"
        linhas = [("Onde está", f'<a href="{sobre.get("Link") or sobre.get("Link original")}" target="_blank">'
                                f'{sobre.get("Link") or sobre.get("Link original")}</a>')]
        for k in ["Conjunto de dados", "Como foi coletado", "Formato original", "Por que esta fonte", "Praça principal",
                  "Limitações", "Licença", "Coleta", "Uso"]:
            if k in sobre:
                linhas.append((k, sobre[k]))
        linhas.append(("No banco", f"{q.n} linhas" + (f" · {periodo}" if q.a else "")))
        with col:
            st.markdown(f'<div class="fonte"><h3>{f["icone"]} {f["nome"]}</h3><div class="q">{f["pergunta"]}</div><table>' +
                        "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in linhas) + "</table></div>",
                        unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            b1.link_button("Abrir a fonte ↗", f["link"], use_container_width=True)
            b2.download_button("Baixar planilha (.xlsx)", (PL / f["arq"]).read_bytes(), f["arq"],
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key=f"dl_{f['arq']}", use_container_width=True)
            with st.expander("Ver os dados desta fonte"):
                t1, t2 = st.tabs(["Depois da limpeza", "Como veio da fonte"])
                t1.dataframe(pd.read_excel(PL / f["arq"], sheet_name="dados"), hide_index=True, use_container_width=True, height=260)
                t2.dataframe(pd.read_excel(PL / f["arq"], sheet_name="bruto"), hide_index=True, use_container_width=True, height=260)

# ------------------------------------------------------------------ rastreabilidade
st.markdown('<div class="secao">Siga um preço da fonte até o site</div>', unsafe_allow_html=True)
st.caption("Escolha um dia e uma praça: a página mostra o texto original da fonte, o link exato de onde veio, "
           "como ficou depois da limpeza e a linha gravada no banco.")
fatos = ler("""SELECT f.data_referencia, f.data_publicacao, f.id_praca, f.id_produto, f.id_fonte, f.preco_brl, f.alerta,
                      p.municipio || '/' || p.uf AS praca, p.codigo_ibge, p.informante
               FROM fato_preco_diario f JOIN dim_praca p ON p.id_praca = f.id_praca""")
r1, r2, r3 = st.columns([1, 2, 1.4])
prod = r1.selectbox("Produto", ["soja", "milho"], format_func=str.capitalize, key="rast_prod")
opc = fatos[fatos.id_produto == prod].drop_duplicates("id_praca").sort_values("id_praca", key=lambda s: s != "NMT")
pr = r2.selectbox("Praça", opc.id_praca, format_func=lambda k: f"{opc.set_index('id_praca').praca[k]} · {opc.set_index('id_praca').informante[k]}",
                  key="rast_praca")
datas = sorted(fatos[(fatos.id_produto == prod) & (fatos.id_praca == pr)].data_referencia, reverse=True)
dia = r3.selectbox("Dia", datas, format_func=dbr, key="rast_dia")
linha = fatos[(fatos.id_produto == prod) & (fatos.id_praca == pr) & (fatos.data_referencia == dia)].iloc[0]

# acha a linha bruta correspondente
raw = bruto_na()
tipo = "indicador" if linha.id_fonte == "CEPEA" else "mercado-fisico"
cand = raw[raw.pagina.str.contains(tipo) & raw.pagina.str.startswith(("indicador-cepea-esalq-" + prod) if tipo == "indicador" else prod)
           & (raw.data_consultada == dia)]
if tipo == "mercado-fisico":
    cand = cand[cand.praca_texto.map(lambda t: normalizar_praca(t + (" milho" if prod == "milho" else "")) == pr)]
br_ = cand.iloc[0] if len(cand) else None
ptax = ler("SELECT ptax_venda, alerta FROM fato_cambio_ptax WHERE data_referencia = ?", (dia,))
bcb = bruto_bcb()
bcb_lin = bcb[bcb.data == dbr(dia)]

passos = []
if br_ is not None:
    url = f"{NA_URL[br_.pagina]}/{br_.data_consultada}"
    passos.append(("1 · Na fonte", f'Página <a href="{url}" target="_blank">{url}</a><br>'
                   f'Texto lido: praça <code>{br_.praca_texto}</code> · preço <code>{br_.preco_texto}</code> · '
                   f'fechamento <code>{br_.fechamento}</code>'))
passos.append(("2 · Depois da limpeza (planilha)", f'{linha.praca} · IBGE <code>{linha.codigo_ibge or "—"}</code> · '
               f'{prod} · <code>{linha.preco_brl:.2f}</code> R$/saca · data {dbr(dia)}'
               + (f' · <span style="color:{AMAR}">alerta: {linha.alerta}</span>' if linha.alerta else "")))
passos.append(("3 · No banco (fato_preco_diario)", f'id_data <code>{dia.replace("-", "")}</code> · id_praca <code>{pr}</code> · '
               f'id_produto <code>{prod}</code> · id_fonte <code>{linha.id_fonte}</code> · preco_brl <code>{linha.preco_brl}</code> · '
               f'publicado em <code>{linha.data_publicacao}</code>'))
if len(ptax):
    api = BCB_SGS_URL.format(ini=dbr(dia), fim=dbr(dia))
    v = ptax.ptax_venda[0]
    passos.append(("4 · Dólar do mesmo dia (Banco Central)",
                   f'<a href="{api}" target="_blank">{api}</a><br>Veio <code>{bcb_lin.valor.iloc[0] if len(bcb_lin) else "—"}</code> → '
                   f'gravado <code>{v}</code> em fato_cambio_ptax · preço em dólar = {linha.preco_brl:.2f} ÷ {v} = '
                   f'<b>US$ {linha.preco_brl / v:.2f}</b>'))
st.markdown("".join(f'<div class="passo"><small>{a}</small>{b}</div>' for a, b in passos), unsafe_allow_html=True)

# ------------------------------------------------------------------ banco
st.markdown('<div class="secao">O banco de dados (modelo estrela)</div>', unsafe_allow_html=True)
m1, m2 = st.columns([1, 1.3], gap="large")
with m1:
    tabelas = ["fato_preco_diario", "fato_cambio_ptax", "dim_tempo", "dim_praca", "dim_produto", "dim_fonte", "log_carga"]
    papel = ["fato · preço por dia, praça e produto", "fato · dólar PTAX por dia", "dimensão · calendário, dia útil e feriado",
             "dimensão · praça com código IBGE", "dimensão · soja e milho", "dimensão · fonte, formato e licença", "registro de cada carga"]
    tab = pd.DataFrame({"tabela": tabelas, "papel": papel,
                        "linhas": [ler(f"SELECT COUNT(*) n FROM {t}").n[0] for t in tabelas]})
    st.dataframe(tab, hide_index=True, use_container_width=True)
    st.download_button("Baixar o banco (agromarket.db)", DB.read_bytes(), "agromarket.db", "application/x-sqlite3",
                       use_container_width=True)
with m2:
    st.markdown("**Dias com preço por praça e ano**")
    cob = ler("SELECT praca, id_produto AS produto, ano, COUNT(*) AS dias FROM vw_preco_completo GROUP BY 1,2,3")
    st.dataframe(cob.pivot_table(index=["praca", "produto"], columns="ano", values="dias", fill_value=0),
                 use_container_width=True)
    st.markdown("**Alertas de qualidade (valores para conferir)**")
    st.dataframe(ler("""SELECT data, praca, id_produto AS produto, preco_brl AS valor, alerta FROM vw_preco_completo WHERE alerta IS NOT NULL
                        UNION ALL SELECT data_referencia, 'Dólar PTAX', '', ptax_venda, alerta FROM fato_cambio_ptax WHERE alerta IS NOT NULL"""),
                 hide_index=True, use_container_width=True)

with st.expander("Regra de cálculo e consulta SQL"):
    from etl.analise import SQL_JANELA
    st.markdown("Nota do preço = % de dias da mesma época (15 dias antes e 15 depois) dos 5 anos anteriores, na mesma praça, "
                "em que o preço foi **menor** que o de hoje. Só entram dados publicados antes da data de análise.")
    st.code(SQL_JANELA.strip(), language="sql")

st.markdown(f'<div class="rodape">Licenças: CEPEA/ESALQ-USP CC BY-NC 4.0 · Banco Central ODbL · Notícias Agrícolas uso acadêmico com citação · '
            f'IBGE dados abertos. Código: github.com/VicenteAustria190528/agromarket-preco-soja-milho</div>', unsafe_allow_html=True)
