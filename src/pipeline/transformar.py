"""Etapa 3 - Transformar: cria as métricas derivadas."""
import pandas as pd

DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def calcular_engajamento(df):
    """Taxa de engajamento = (curtidas + comentários + compartilhamentos + salvamentos) / alcance.

    - Salvamentos faltantes (TikTok não tem) contam como 0.
    - Alcance 0 daria divisão por zero: nesse caso devolvemos NaN
      (taxa "indefinida"), e não 0 nem infinito.
    """
    interacoes = (df["curtidas"].astype(float) + df["comentarios"]
                  + df["compartilhamentos"] + df["salvamentos"].fillna(0))
    alcance = df["alcance"].astype(float).where(df["alcance"] > 0)  # zero -> NaN
    return interacoes / alcance


def calcular_engajamento_sem_salvos(df):
    """(curtidas + comentários + compartilhamentos) / alcance.

    O TikTok não exporta salvamentos; esta taxa não usa salvamentos e por isso
    pode ser comparada entre os dois canais. Alcance 0 -> NaN, como acima.
    """
    interacoes = (df["curtidas"].astype(float) + df["comentarios"]
                  + df["compartilhamentos"])
    alcance = df["alcance"].astype(float).where(df["alcance"] > 0)
    return interacoes / alcance


def transformar(df):
    """Acrescenta taxa_engajamento, taxa_engajamento_sem_salvos, data, dia_semana, hora e semana_iso."""
    df = df.copy()
    df["taxa_engajamento"] = calcular_engajamento(df)
    df["taxa_engajamento_sem_salvos"] = calcular_engajamento_sem_salvos(df)
    df["data"] = df["publicado_em"].dt.strftime("%Y-%m-%d")
    df["dia_semana"] = df["publicado_em"].dt.dayofweek.map(lambda i: DIAS_SEMANA[i])
    df["hora"] = df["publicado_em"].dt.hour
    iso = df["publicado_em"].dt.isocalendar()
    df["semana_iso"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    return df
