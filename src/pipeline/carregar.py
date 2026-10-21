"""Etapa 4 - Carregar: grava no SQLite de forma incremental (rodar 2x não duplica)."""
from datetime import datetime
from pathlib import Path

COLUNAS_POSTS = ["canal", "id_post", "publicado_em", "data", "formato", "tema",
                 "alcance", "visualizacoes", "curtidas", "comentarios",
                 "compartilhamentos", "salvamentos", "cliques_link",
                 "taxa_engajamento", "taxa_engajamento_sem_salvos", "dia_semana", "hora", "semana_iso",
                 "arquivo_origem"]

CAMINHO_SCHEMA = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


def criar_tabelas(conn, caminho_schema=CAMINHO_SCHEMA):
    """Cria as tabelas (se ainda não existirem) a partir do schema.sql."""
    conn.executescript(Path(caminho_schema).read_text(encoding="utf-8"))


def carregar_posts(conn, df):
    """Insere os posts novos e devolve quantos entraram. NÃO faz commit (o main faz).

    INSERT OR IGNORE: se (canal, id_post) já existe, a linha é ignorada.
    Por isso uma segunda execução com os mesmos arquivos não duplica nada.
    """
    df = df[COLUNAS_POSTS].copy()
    df["publicado_em"] = df["publicado_em"].dt.strftime("%Y-%m-%d %H:%M:%S")
    # NaN/NA viram None (NULL no SQLite); astype(object) devolve tipos Python simples
    df = df.astype(object).where(df.notna(), None)

    antes = conn.total_changes
    colunas = ", ".join(COLUNAS_POSTS)
    marcadores = ", ".join("?" for _ in COLUNAS_POSTS)
    conn.executemany(
        f"INSERT OR IGNORE INTO posts ({colunas}) VALUES ({marcadores})",
        df.values.tolist(),
    )
    return conn.total_changes - antes


def registrar_carga(conn, arquivos_lidos, linhas_validas, linhas_rejeitadas, linhas_novas):
    """Registra esta execução na tabela cargas (o commit é feito pelo main)."""
    conn.execute(
        "INSERT INTO cargas (executado_em, arquivos_lidos, linhas_validas,"
        " linhas_rejeitadas, linhas_novas) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), arquivos_lidos,
         linhas_validas, linhas_rejeitadas, linhas_novas),
    )
