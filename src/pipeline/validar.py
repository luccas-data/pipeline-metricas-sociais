"""Etapa 2 - Validar: separa linhas válidas das rejeitadas (com o motivo)."""
import pandas as pd

# Sem estes campos a linha não serve para análise
OBRIGATORIOS = ["id_post", "publicado_em", "formato", "tema", "alcance",
                "visualizacoes", "curtidas", "comentarios", "compartilhamentos"]
# Todas as métricas numéricas (salvamentos e cliques são opcionais)
METRICAS = ["alcance", "visualizacoes", "curtidas", "comentarios",
            "compartilhamentos", "salvamentos", "cliques_link"]
TEXTOS = ["id_post", "formato", "tema"]


def converter_numero(coluna):
    """Texto -> número. "1.234" vira 1234. O que não for número vira NaN.

    Suposição: nas exportações o ponto é SEMPRE separador de milhar
    (são contagens inteiras, não existem casas decimais).
    """
    if pd.api.types.is_numeric_dtype(coluna):
        return coluna
    texto = coluna.astype("string").str.strip().str.replace(".", "", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def converter_data(coluna):
    """Aceita 'dd/mm/aaaa HH:MM' e ISO 'aaaa-mm-dd HH:MM:SS'. Não reconhecida vira NaT."""
    texto = coluna.astype("string").str.strip()
    br = pd.to_datetime(texto, format="%d/%m/%Y %H:%M", errors="coerce")
    iso = pd.to_datetime(texto, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    return br.fillna(iso)


def validar(df):
    """Devolve (df_validos, df_rejeitados).

    df_rejeitados mantém os valores ORIGINAIS (texto) e ganha a coluna 'motivo'.
    Uma linha pode ter mais de um motivo; eles ficam separados por '; '.
    """
    original = df.copy()
    df = df.copy()

    # 1) converte tipos (o que não converte vira NaN/NaT e é pego pelas regras)
    for col in METRICAS:
        df[col] = converter_numero(df[col])
    for col in TEXTOS:
        texto = df[col].astype("string").str.strip()
        df[col] = texto.where(texto != "")  # texto vazio vira faltante
    data_original_ausente = df["publicado_em"].isna()
    df["publicado_em"] = converter_data(df["publicado_em"])

    # 2) regras: cada uma gera uma máscara True = "linha com problema"
    motivos = pd.Series("", index=df.index)

    campos = [c for c in OBRIGATORIOS if c != "publicado_em"]
    ausente = df[campos].isna().any(axis=1) | data_original_ausente
    motivos[ausente] += "campo obrigatório ausente; "

    data_invalida = df["publicado_em"].isna() & ~data_original_ausente
    motivos[data_invalida] += "data inválida; "

    negativo = (df[METRICAS] < 0).any(axis=1)
    motivos[negativo] += "métrica negativa; "

    curtidas_demais = df["curtidas"] > df["visualizacoes"]
    motivos[curtidas_demais] += "curtidas maiores que visualizações; "

    # Duplicidade só entre linhas SEM outro problema: vale a primeira ocorrência
    # válida. Assim, se o original veio com erro e o reenvio veio certo, o reenvio entra.
    sem_problema = motivos == ""
    duplicado = pd.Series(False, index=df.index)
    duplicado[sem_problema] = df[sem_problema].duplicated(subset=["canal", "id_post"], keep="first")
    motivos[duplicado] += "duplicado (canal, id_post); "

    # 3) separa
    com_problema = motivos != ""
    validos = df[~com_problema].copy()
    for col in ["alcance", "visualizacoes", "curtidas", "comentarios", "compartilhamentos"]:
        # métricas obrigatórias: sem faltantes, então viram inteiro
        validos[col] = validos[col].astype("int64")
    rejeitados = original[com_problema].copy()
    rejeitados["motivo"] = motivos[com_problema].str.rstrip("; ")
    return validos, rejeitados
