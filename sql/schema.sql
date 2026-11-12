-- AgroMarket · Data warehouse do domínio PREÇO (modelo estrela)
-- Regra do projeto: todo fato guarda data_referencia e data_publicacao.

DROP VIEW IF EXISTS vw_preco_completo;
DROP TABLE IF EXISTS fato_preco_diario;
DROP TABLE IF EXISTS fato_cambio_ptax;
DROP TABLE IF EXISTS dim_tempo;
DROP TABLE IF EXISTS dim_praca;
DROP TABLE IF EXISTS dim_produto;
DROP TABLE IF EXISTS dim_fonte;
DROP TABLE IF EXISTS log_carga;

CREATE TABLE dim_tempo (
  id_data        INTEGER PRIMARY KEY,      -- AAAAMMDD
  data           TEXT NOT NULL,            -- AAAA-MM-DD
  ano            INTEGER NOT NULL,
  mes            INTEGER NOT NULL,
  dia            INTEGER NOT NULL,
  dia_semana     TEXT NOT NULL,
  dia_util_br    INTEGER NOT NULL,         -- 1 = dia útil no Brasil
  feriado        TEXT
);

CREATE TABLE dim_praca (
  id_praca       TEXT PRIMARY KEY,
  municipio      TEXT NOT NULL,
  uf             TEXT NOT NULL,
  codigo_ibge    TEXT,
  informante     TEXT,
  tipo           TEXT                      -- balcão, porto, indicador
);

CREATE TABLE dim_produto (
  id_produto     TEXT PRIMARY KEY,
  nome           TEXT NOT NULL,
  unidade        TEXT NOT NULL
);

CREATE TABLE dim_fonte (
  id_fonte       TEXT PRIMARY KEY,
  nome           TEXT NOT NULL,
  url            TEXT,
  formato        TEXT,
  frequencia     TEXT,
  defasagem      TEXT,
  licenca        TEXT
);

CREATE TABLE fato_preco_diario (
  id_data          INTEGER NOT NULL REFERENCES dim_tempo(id_data),
  id_praca         TEXT    NOT NULL REFERENCES dim_praca(id_praca),
  id_produto       TEXT    NOT NULL REFERENCES dim_produto(id_produto),
  id_fonte         TEXT    NOT NULL REFERENCES dim_fonte(id_fonte),
  preco_brl        REAL    NOT NULL,       -- R$ por saca de 60 kg
  alerta           TEXT,                   -- preenchido quando varia > 10% sobre o pregão anterior
  data_referencia  TEXT    NOT NULL,
  data_publicacao  TEXT    NOT NULL,
  carregado_em     TEXT    NOT NULL,
  PRIMARY KEY (id_data, id_praca, id_produto)
);

CREATE TABLE fato_cambio_ptax (
  id_data          INTEGER PRIMARY KEY REFERENCES dim_tempo(id_data),
  id_fonte         TEXT    NOT NULL REFERENCES dim_fonte(id_fonte),
  ptax_venda       REAL    NOT NULL,       -- R$ por US$
  alerta           TEXT,                   -- preenchido quando varia > 5% sobre o dia anterior
  data_referencia  TEXT    NOT NULL,
  data_publicacao  TEXT    NOT NULL,
  carregado_em     TEXT    NOT NULL
);

CREATE TABLE log_carga (
  etapa        TEXT,
  tabela       TEXT,
  linhas       INTEGER,
  observacao   TEXT,
  executado_em TEXT
);

-- Visão analítica: preço em R$, dólar do dia e preço em US$ (dólar implícito)
CREATE VIEW vw_preco_completo AS
SELECT f.id_data, t.data, t.ano, f.id_praca, p.municipio || ' (' || p.uf || ')' AS praca, p.informante,
       f.id_produto, f.id_fonte, f.preco_brl, f.alerta, c.ptax_venda,
       ROUND(f.preco_brl / c.ptax_venda, 4) AS preco_usd,
       f.data_referencia, f.data_publicacao
FROM fato_preco_diario f
JOIN dim_tempo t   ON t.id_data = f.id_data
JOIN dim_praca p   ON p.id_praca = f.id_praca
LEFT JOIN fato_cambio_ptax c ON c.id_data = f.id_data;
