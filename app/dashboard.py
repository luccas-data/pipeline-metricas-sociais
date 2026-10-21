"""Dashboard simples (Streamlit) sobre data/metricas.sqlite.

Uso: uv run streamlit run app/dashboard.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

CAMINHO_DB = Path(__file__).resolve().parents[1] / "data" / "metricas.sqlite"

st.set_page_config(page_title="Métricas sociais - Marca Exemplo", layout="wide")
st.title("Métricas sociais - Marca Exemplo")
st.caption("Dados 100% sintéticos, inspirados em um fluxo real de relatórios de social media.")

if not CAMINHO_DB.exists():
    st.error("Banco não encontrado. Rode antes: uv run python -m pipeline.main")
    st.stop()

conn = sqlite3.connect(CAMINHO_DB)
posts = pd.read_sql("SELECT * FROM posts", conn, parse_dates=["publicado_em"])
conn.close()

# --- Filtros (barra lateral) ---
st.sidebar.header("Filtros")
canais = st.sidebar.multiselect("Canal", sorted(posts["canal"].unique()),
                                default=sorted(posts["canal"].unique()))
data_min = posts["publicado_em"].min().date()
data_max = posts["publicado_em"].max().date()
periodo = st.sidebar.date_input("Período", value=(data_min, data_max),
                                min_value=data_min, max_value=data_max)

# date_input devolve 1 data enquanto o usuário ainda não escolheu o fim do período
if len(periodo) != 2:
    st.info("Selecione a data inicial e a final.")
    st.stop()
inicio, fim = periodo

filtro = (posts["canal"].isin(canais)
          & (posts["publicado_em"].dt.date >= inicio)
          & (posts["publicado_em"].dt.date <= fim))
df = posts[filtro]

if df.empty:
    st.warning("Nenhum post com esses filtros.")
    st.stop()

# --- Indicadores ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Posts", len(df))
col2.metric("Alcance total", f"{df['alcance'].sum():,}".replace(",", "."))
col3.metric("Engajamento médio", f"{df['taxa_engajamento'].mean() * 100:.1f}%")
col4.metric("Cliques no link", f"{int(df['cliques_link'].sum()):,}".replace(",", "."))

# --- Gráficos ---
st.subheader("Alcance total por semana")
semanal = df.pivot_table(index="semana_iso", columns="canal", values="alcance", aggfunc="sum")
st.line_chart(semanal)

esquerda, direita = st.columns(2)
with esquerda:
    st.subheader("Engajamento médio por formato")
    st.bar_chart(df.groupby("formato")["taxa_engajamento"].mean())
with direita:
    st.subheader("Engajamento médio por hora de publicação")
    st.bar_chart(df.groupby("hora")["taxa_engajamento"].mean())
