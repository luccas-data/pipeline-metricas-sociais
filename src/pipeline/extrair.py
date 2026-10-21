"""Etapa 1 - Extrair: lê todos os arquivos de data/raw/ e padroniza os nomes de coluna."""
from pathlib import Path

import pandas as pd

# Dicionário explícito: nome que aparece nos arquivos -> nome padrão do pipeline.
# Se aparecer uma coluna nova, o pipeline para e avisa (melhor que ignorar em silêncio).
MAPA_COLUNAS = {
    # id do post
    "ID do Post": "id_post", "ID do Vídeo": "id_post",
    "post_id": "id_post", "video_id": "id_post",
    # data de publicação
    "Data de publicação": "publicado_em", "data_hora": "publicado_em",
    # descrição do post
    "Formato": "formato", "formato": "formato",
    "Tema": "tema", "tema": "tema",
    # métricas
    "Alcance": "alcance", "alcance_total": "alcance",
    "Impressões": "visualizacoes", "impressoes": "visualizacoes",
    "Visualizações": "visualizacoes", "visualizacoes": "visualizacoes",
    "Curtidas": "curtidas", "curtidas": "curtidas",
    "Comentários": "comentarios", "comentarios": "comentarios",
    "Compartilhamentos": "compartilhamentos", "compartilhamentos": "compartilhamentos",
    "Salvamentos": "salvamentos", "salvamentos": "salvamentos",
    "Cliques no link": "cliques_link", "cliques_link": "cliques_link",
}

# Colunas que o arquivo precisa ter depois da renomeação (salvamentos e cliques são opcionais)
COLUNAS_OBRIGATORIAS = ["id_post", "publicado_em", "formato", "tema", "alcance",
                        "visualizacoes", "curtidas", "comentarios", "compartilhamentos"]

# O canal é identificado pelo começo do nome do arquivo
PREFIXO_CANAL = {"instagram": "Instagram", "tiktok": "TikTok"}


def listar_arquivos(pasta):
    """Lista os CSV/XLSX da pasta em ordem estável.

    Ordenamos pelo nome SEM a extensão: "instagram_2026-S31" vem antes de
    "instagram_2026-S31_reenvio" (o texto menor sempre vem antes do maior).
    Assim o original é lido antes do reenvio, e na validação vale o primeiro.
    """
    pasta = Path(pasta)
    arquivos = list(pasta.glob("*.csv")) + list(pasta.glob("*.xlsx"))
    return sorted(arquivos, key=lambda c: c.stem)


def extrair_arquivo(caminho):
    """Lê um arquivo, renomeia as colunas e acrescenta canal e arquivo_origem."""
    # dtype=str: lemos tudo como texto para não perder nada ("1.234" viraria 1.234).
    # A conversão para número é feita na etapa de validação.
    if caminho.suffix == ".csv":
        df = pd.read_csv(caminho, dtype=str)
    else:
        df = pd.read_excel(caminho, dtype=str)

    desconhecidas = [c for c in df.columns if c not in MAPA_COLUNAS]
    if desconhecidas:
        raise ValueError(f"{caminho.name}: colunas sem mapeamento: {desconhecidas}")
    df = df.rename(columns=MAPA_COLUNAS)

    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(f"{caminho.name}: faltam colunas obrigatórias: {faltando}")

    prefixo = caminho.name.split("_")[0].lower()
    if prefixo not in PREFIXO_CANAL:
        raise ValueError(f"{caminho.name}: não sei de qual canal é este arquivo")
    df["canal"] = PREFIXO_CANAL[prefixo]
    df["arquivo_origem"] = caminho.name
    return df


def extrair_tudo(arquivos):
    """Junta os arquivos (lista de caminhos, de listar_arquivos) em um único DataFrame."""
    quadros = [extrair_arquivo(c) for c in arquivos]
    # colunas que um canal não tem (ex.: salvamentos no TikTok) viram NaN
    return pd.concat(quadros, ignore_index=True)
