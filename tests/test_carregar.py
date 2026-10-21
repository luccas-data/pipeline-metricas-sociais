"""Testes da carga incremental, com um SQLite temporário (tmp_path)."""
import sqlite3

import pandas as pd

from pipeline.carregar import carregar_posts, criar_tabelas, registrar_carga
from pipeline.transformar import transformar


def posts_exemplo(ids):
    linhas = [{"canal": "Instagram", "id_post": i, "publicado_em": pd.Timestamp("2026-07-08 19:30"),
               "formato": "Reels", "tema": "Humor", "alcance": 1000, "visualizacoes": 1500,
               "curtidas": 100, "comentarios": 10, "compartilhamentos": 5,
               "salvamentos": 20, "cliques_link": 8, "arquivo_origem": "teste.csv"}
              for i in ids]
    return transformar(pd.DataFrame(linhas))


def abrir_banco(tmp_path):
    conn = sqlite3.connect(tmp_path / "teste.sqlite")
    criar_tabelas(conn)
    return conn


def contar(conn, tabela):
    return conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


def test_primeira_carga_insere_tudo(tmp_path):
    conn = abrir_banco(tmp_path)
    assert carregar_posts(conn, posts_exemplo(["P1", "P2"])) == 2
    assert contar(conn, "posts") == 2


def test_rodar_duas_vezes_nao_duplica(tmp_path):
    conn = abrir_banco(tmp_path)
    carregar_posts(conn, posts_exemplo(["P1", "P2"]))
    novas = carregar_posts(conn, posts_exemplo(["P1", "P2"]))
    assert novas == 0
    assert contar(conn, "posts") == 2


def test_segunda_carga_so_adiciona_os_novos(tmp_path):
    conn = abrir_banco(tmp_path)
    carregar_posts(conn, posts_exemplo(["P1", "P2"]))
    novas = carregar_posts(conn, posts_exemplo(["P2", "P3"]))
    assert novas == 1
    assert contar(conn, "posts") == 3


def test_registrar_carga(tmp_path):
    conn = abrir_banco(tmp_path)
    registrar_carga(conn, 26, 303, 54, 303)
    registrar_carga(conn, 26, 303, 54, 0)
    conn.commit()
    assert contar(conn, "cargas") == 2
    ultima = conn.execute("SELECT arquivos_lidos, linhas_validas, linhas_rejeitadas, linhas_novas"
                          " FROM cargas ORDER BY id DESC LIMIT 1").fetchone()
    assert ultima == (26, 303, 54, 0)


def test_valores_ausentes_viram_null(tmp_path):
    conn = abrir_banco(tmp_path)
    df = posts_exemplo(["P1"])
    df["salvamentos"] = None  # como no TikTok
    carregar_posts(conn, df)
    assert conn.execute("SELECT salvamentos FROM posts").fetchone()[0] is None
