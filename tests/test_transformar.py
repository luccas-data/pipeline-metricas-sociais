"""Testes do cálculo de engajamento e das colunas de data."""
import math

import pandas as pd

from pipeline.transformar import calcular_engajamento, calcular_engajamento_sem_salvos, transformar


def df_exemplo(**mudancas):
    base = {"alcance": [1000], "curtidas": [80], "comentarios": [10],
            "compartilhamentos": [5], "salvamentos": [5],
            "publicado_em": [pd.Timestamp("2026-07-08 19:30")]}  # quarta-feira
    base.update(mudancas)
    return pd.DataFrame(base)


def test_engajamento_soma_quatro_interacoes_sobre_alcance():
    # (80 + 10 + 5 + 5) / 1000
    assert calcular_engajamento(df_exemplo()).iloc[0] == 0.1


def test_salvamentos_faltantes_contam_como_zero():
    taxa = calcular_engajamento(df_exemplo(salvamentos=[None]))
    assert taxa.iloc[0] == 0.095  # (80 + 10 + 5) / 1000


def test_alcance_zero_gera_nan_sem_dividir_por_zero():
    taxa = calcular_engajamento(df_exemplo(alcance=[0]))
    assert math.isnan(taxa.iloc[0])


def test_colunas_de_data():
    resultado = transformar(df_exemplo())
    assert resultado["dia_semana"].iloc[0] == "quarta"
    assert resultado["hora"].iloc[0] == 19
    assert resultado["semana_iso"].iloc[0] == "2026-W28"
    assert resultado["data"].iloc[0] == "2026-07-08"


def test_engajamento_sem_salvos_ignora_salvamentos():
    # (80 + 10 + 5) / 1000, mesmo com 5 salvamentos
    assert calcular_engajamento_sem_salvos(df_exemplo()).iloc[0] == 0.095


def test_engajamento_sem_salvos_alcance_zero_gera_nan():
    assert math.isnan(calcular_engajamento_sem_salvos(df_exemplo(alcance=[0])).iloc[0])
