"""Testes da leitura dos arquivos (usa arquivos CSV temporários em tmp_path)."""
import pytest

from pipeline.extrair import extrair_arquivo, extrair_tudo, listar_arquivos

CABECALHO = ("ID do Post,Data de publicação,Formato,Tema,Alcance,Impressões,"
             "Curtidas,Comentários,Compartilhamentos")
LINHA = "P1,2026-07-08 19:30:00,Reels,Humor,1000,1500,100,10,5"


def criar_csv(pasta, nome, texto):
    caminho = pasta / nome
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_padroniza_colunas_e_adiciona_canal_e_origem(tmp_path):
    caminho = criar_csv(tmp_path, "instagram_2026-S28.csv", f"{CABECALHO}\n{LINHA}\n")
    df = extrair_arquivo(caminho)
    assert "alcance" in df.columns and "visualizacoes" in df.columns
    assert df["canal"].iloc[0] == "Instagram"
    assert df["arquivo_origem"].iloc[0] == "instagram_2026-S28.csv"


def test_coluna_sem_mapeamento_gera_erro(tmp_path):
    caminho = criar_csv(tmp_path, "instagram_2026-S28.csv",
                        f"{CABECALHO},Coluna Nova\n{LINHA},x\n")
    with pytest.raises(ValueError, match="sem mapeamento"):
        extrair_arquivo(caminho)


def test_coluna_obrigatoria_faltando_gera_erro(tmp_path):
    cabecalho = CABECALHO.replace(",Curtidas", "")
    linha = "P1,2026-07-08 19:30:00,Reels,Humor,1000,1500,10,5"
    caminho = criar_csv(tmp_path, "instagram_2026-S28.csv", f"{cabecalho}\n{linha}\n")
    with pytest.raises(ValueError, match="faltam colunas obrigatórias"):
        extrair_arquivo(caminho)


def test_reenvio_vem_depois_do_original(tmp_path):
    for nome in ["instagram_2026-S31_reenvio.csv", "instagram_2026-S31.csv"]:
        criar_csv(tmp_path, nome, f"{CABECALHO}\n{LINHA}\n")
    nomes = [c.name for c in listar_arquivos(tmp_path)]
    assert nomes == ["instagram_2026-S31.csv", "instagram_2026-S31_reenvio.csv"]
    assert len(extrair_tudo(listar_arquivos(tmp_path))) == 2
