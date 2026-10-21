"""Testes das regras de validação (uma por regra)."""
import pandas as pd

from pipeline.validar import converter_numero, validar


def linha(**mudancas):
    """Uma linha válida (tudo como texto, como sai do extrair). Cada teste muda só o que quer."""
    base = {"canal": "Instagram", "id_post": "P0001", "publicado_em": "2026-07-08 19:30:00",
            "formato": "Reels", "tema": "Humor", "alcance": "1000", "visualizacoes": "1500",
            "curtidas": "100", "comentarios": "10", "compartilhamentos": "5",
            "salvamentos": "20", "cliques_link": "8", "arquivo_origem": "teste.csv"}
    base.update(mudancas)
    return base


def rodar(*linhas):
    return validar(pd.DataFrame(list(linhas)))


def test_linha_valida_passa():
    validos, rejeitados = rodar(linha())
    assert len(validos) == 1
    assert rejeitados.empty


def test_campo_obrigatorio_ausente():
    validos, rejeitados = rodar(linha(alcance=None), linha(id_post="P0002", tema=None))
    assert validos.empty
    assert all("campo obrigatório ausente" in m for m in rejeitados["motivo"])


def test_campos_opcionais_podem_faltar():
    # TikTok não tem salvamentos e o link pode não ter cliques
    validos, _ = rodar(linha(salvamentos=None, cliques_link=None))
    assert len(validos) == 1


def test_data_em_dois_formatos():
    validos, _ = rodar(linha(publicado_em="08/07/2026 19:30"),
                       linha(id_post="P0002", publicado_em="2026-07-08 19:30:00"))
    assert len(validos) == 2
    assert (validos["publicado_em"] == pd.Timestamp("2026-07-08 19:30")).all()


def test_data_invalida():
    validos, rejeitados = rodar(linha(publicado_em="31/02/2026 19:00"))
    assert validos.empty
    assert rejeitados["motivo"].iloc[0] == "data inválida"


def test_metrica_negativa():
    validos, rejeitados = rodar(linha(comentarios="-3"))
    assert validos.empty
    assert rejeitados["motivo"].iloc[0] == "métrica negativa"


def test_curtidas_maiores_que_visualizacoes():
    validos, rejeitados = rodar(linha(curtidas="2000", visualizacoes="1500"))
    assert validos.empty
    assert "curtidas maiores que visualizações" in rejeitados["motivo"].iloc[0]


def test_duplicidade_mantem_primeira_e_rejeita_repeticao():
    validos, rejeitados = rodar(linha(), linha(arquivo_origem="reenvio.csv"))
    assert len(validos) == 1
    assert validos["arquivo_origem"].iloc[0] == "teste.csv"
    assert "duplicado" in rejeitados["motivo"].iloc[0]


def test_original_invalido_e_reenvio_valido_entra_o_reenvio():
    original_ruim = linha(comentarios="-3", arquivo_origem="original.csv")
    reenvio_bom = linha(arquivo_origem="reenvio.csv")
    validos, rejeitados = rodar(original_ruim, reenvio_bom)
    assert validos["arquivo_origem"].tolist() == ["reenvio.csv"]
    assert rejeitados["motivo"].tolist() == ["métrica negativa"]


def test_mesmo_id_em_canais_diferentes_nao_e_duplicado():
    validos, _ = rodar(linha(), linha(canal="TikTok"))
    assert len(validos) == 2


def test_separador_de_milhar():
    assert converter_numero(pd.Series(["1.234", "50", "abc"])).iloc[:2].tolist() == [1234, 50]
    validos, _ = rodar(linha(alcance="12.345", visualizacoes="20.000"))
    assert validos["alcance"].iloc[0] == 12345


def test_rejeitado_guarda_valor_original():
    _, rejeitados = rodar(linha(publicado_em="31/02/2026 19:00"))
    assert rejeitados["publicado_em"].iloc[0] == "31/02/2026 19:00"
