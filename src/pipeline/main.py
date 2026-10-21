"""Orquestra o pipeline: extrair -> validar -> transformar -> carregar.

Uso: uv run python -m pipeline.main
"""
import sqlite3
from pathlib import Path

from pipeline.carregar import carregar_posts, criar_tabelas, registrar_carga
from pipeline.extrair import extrair_tudo, listar_arquivos
from pipeline.transformar import transformar
from pipeline.validar import validar

RAIZ = Path(__file__).resolve().parents[2]
PASTA_RAW = RAIZ / "data" / "raw"
CAMINHO_DB = RAIZ / "data" / "metricas.sqlite"
CAMINHO_REJEITADOS = RAIZ / "data" / "rejeitados.csv"


def main():
    arquivos = listar_arquivos(PASTA_RAW)
    if not arquivos:
        print("Nenhum arquivo em data/raw/. Rode antes: uv run python scripts/gerar_dados.py")
        return

    bruto = extrair_tudo(arquivos)
    validos, rejeitados = validar(bruto)
    rejeitados.to_csv(CAMINHO_REJEITADOS, index=False)
    posts = transformar(validos)

    conn = sqlite3.connect(CAMINHO_DB)
    criar_tabelas(conn)
    novas = carregar_posts(conn, posts)
    registrar_carga(conn, len(arquivos), len(validos), len(rejeitados), novas)
    conn.commit()  # um único commit: posts e registro da carga entram juntos
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    conn.close()

    print("Resumo da execução")
    print(f"  Arquivos lidos:      {len(arquivos)}")
    print(f"  Linhas lidas:        {len(bruto)}")
    print(f"  Linhas válidas:      {len(validos)}")
    print(f"  Linhas rejeitadas:   {len(rejeitados)} (ver data/rejeitados.csv)")
    print(f"  Posts novos no banco: {novas}")
    print(f"  Total de posts no banco: {total}")
    if len(rejeitados):
        print("  Motivos de rejeição:")
        for motivo, qtd in rejeitados["motivo"].value_counts().items():
            print(f"    {qtd:3d}  {motivo}")


if __name__ == "__main__":
    main()
