"""Gera exportações semanais SINTÉTICAS de Instagram (CSV) e TikTok (XLSX).

Os dados são inventados (marca fictícia "Marca Exemplo"), mas têm padrões
que dá para descobrir na análise:
  - Reels/vídeos engajam mais que imagem e stories
  - posts publicados entre 19h e 21h têm mais alcance e engajamento
  - leve tendência de crescimento ao longo das semanas

Também injeta problemas parecidos com os de exportações reais:
  1. nomes de coluna diferentes entre canais e entre semanas
  2. datas em formatos mistos (dd/mm/aaaa HH:MM e ISO)
  3. números como texto com separador de milhar ("1.234")
  4. linhas duplicadas dentro do mesmo arquivo
  5. um arquivo semanal reenviado (cópia idêntica)
  6. valores negativos, faltantes, curtidas > visualizações e data impossível

Uso: uv run python scripts/gerar_dados.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_SEMANAS = 12
INICIO = pd.Timestamp("2026-07-06")  # uma segunda-feira
PASTA_RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

TEMAS = ["Bastidores", "Promoção", "Educativo", "Lançamento", "Humor"]
FATOR_TEMA = {"Bastidores": 1.0, "Promoção": 0.8, "Educativo": 1.15,
              "Lançamento": 1.05, "Humor": 1.3}

# taxa de engajamento "base" de cada formato (Reels e vídeos engajam mais)
TAXA_BASE = {"Reels": 0.075, "Carrossel": 0.055, "Imagem": 0.035,
             "Stories": 0.02, "Vídeo": 0.09}
FATOR_ALCANCE_FORMATO = {"Reels": 1.5, "Carrossel": 1.0, "Imagem": 0.8,
                         "Stories": 0.6, "Vídeo": 1.0}

HORAS = list(range(8, 24))
# horários de pico (19-21h) são mais frequentes e rendem mais
PESO_HORA = np.array([3 if h in (19, 20, 21) else 1 for h in HORAS], dtype=float)
PESO_HORA = PESO_HORA / PESO_HORA.sum()


def fator_hora(hora):
    return 1.35 if hora in (19, 20, 21) else 0.85


# Nomes de coluna de cada canal. Versão "A" é o padrão; "B" é o que a
# plataforma passou a exportar em algumas semanas.
NOMES_COLUNAS = {
    "Instagram": {
        "A": {"id_post": "ID do Post", "publicado_em": "Data de publicação",
              "formato": "Formato", "tema": "Tema", "alcance": "Alcance",
              "visualizacoes": "Impressões", "curtidas": "Curtidas",
              "comentarios": "Comentários", "compartilhamentos": "Compartilhamentos",
              "salvamentos": "Salvamentos", "cliques_link": "Cliques no link"},
        "B": {"id_post": "post_id", "publicado_em": "data_hora",
              "formato": "formato", "tema": "tema", "alcance": "alcance_total",
              "visualizacoes": "impressoes", "curtidas": "curtidas",
              "comentarios": "comentarios", "compartilhamentos": "compartilhamentos",
              "salvamentos": "salvamentos", "cliques_link": "cliques_link"},
    },
    "TikTok": {
        "A": {"id_post": "ID do Vídeo", "publicado_em": "Data de publicação",
              "formato": "Formato", "tema": "Tema", "alcance": "Alcance",
              "visualizacoes": "Visualizações", "curtidas": "Curtidas",
              "comentarios": "Comentários", "compartilhamentos": "Compartilhamentos",
              "cliques_link": "Cliques no link"},
        "B": {"id_post": "video_id", "publicado_em": "data_hora",
              "formato": "formato", "tema": "tema", "alcance": "alcance_total",
              "visualizacoes": "visualizacoes", "curtidas": "curtidas",
              "comentarios": "comentarios", "compartilhamentos": "compartilhamentos",
              "cliques_link": "cliques_link"},
    },
}
SEMANAS_NOMES_B = {"Instagram": [3, 4, 8, 9], "TikTok": [5, 6, 10]}
# semanas que ganham uma linha duplicada dentro do arquivo
SEMANAS_COM_DUPLICATA = {"Instagram": [2, 7], "TikTok": [5]}


def gerar_posts(canal, rng):
    """Gera todos os posts de um canal nas N_SEMANAS, com números 'limpos'."""
    linhas = []
    contador = 1
    n_min, n_max = (14, 20) if canal == "Instagram" else (8, 12)
    alcance_base = 5000 if canal == "Instagram" else 12000
    formatos = ["Reels", "Carrossel", "Imagem", "Stories"] if canal == "Instagram" else ["Vídeo"]
    prob_formato = [0.30, 0.25, 0.25, 0.20] if canal == "Instagram" else [1.0]

    for semana in range(N_SEMANAS):
        crescimento = 1 + 0.025 * semana  # tendência leve de crescimento
        for _ in range(rng.integers(n_min, n_max + 1)):
            formato = rng.choice(formatos, p=prob_formato)
            tema = rng.choice(TEMAS)
            hora = int(rng.choice(HORAS, p=PESO_HORA))
            dia = int(rng.integers(0, 7))
            publicado = INICIO + pd.Timedelta(days=7 * semana + dia, hours=hora,
                                              minutes=int(rng.integers(0, 60)))

            alcance = (alcance_base * crescimento * FATOR_ALCANCE_FORMATO[formato]
                       * fator_hora(hora) * FATOR_TEMA[tema] * rng.lognormal(0, 0.3))
            taxa = (TAXA_BASE[formato] * fator_hora(hora) * FATOR_TEMA[tema]
                    * rng.lognormal(0, 0.2))
            fator_view = rng.uniform(1.1, 1.6) if canal == "Instagram" else rng.uniform(1.0, 1.25)
            curtidas = alcance * taxa * 0.70
            fator_salvar = 1.5 if formato == "Carrossel" else 1.0

            linhas.append({
                "id_post": f"P{contador:04d}",
                "publicado_em": publicado,
                "formato": formato,
                "tema": tema,
                "alcance": int(alcance),
                "visualizacoes": int(alcance * fator_view),
                "curtidas": int(curtidas),
                "comentarios": int(curtidas * rng.uniform(0.04, 0.09)),
                "compartilhamentos": int(curtidas * rng.uniform(0.05, 0.15)),
                "salvamentos": int(curtidas * rng.uniform(0.10, 0.30) * fator_salvar),
                "cliques_link": int(alcance * rng.uniform(0.004, 0.02)
                                    * (2 if formato == "Stories" else 1)),
                "semana": semana,
            })
            contador += 1
    return pd.DataFrame(linhas)


def injetar_problemas_numericos(df, rng):
    """Estraga de propósito algumas linhas (sorteadas, sem repetir linha)."""
    df = df.copy()
    sorteadas = rng.permutation(df.index)
    df.loc[sorteadas[0:3], "curtidas"] = -5                     # negativo
    df.loc[sorteadas[3:5], "curtidas"] = df.loc[sorteadas[3:5], "visualizacoes"] + 50  # curtidas > visualizações
    df["alcance"] = df["alcance"].astype(object)
    df.loc[sorteadas[5:8], "alcance"] = None                    # alcance faltante
    df.loc[sorteadas[8:10], "tema"] = None                      # tema faltante
    return df, sorteadas[10:12]  # linhas que terão data impossível


def formatar_numero(valor, rng):
    """Devolve o número como o export faria: às vezes texto com ponto de milhar."""
    if pd.isna(valor):
        return None
    valor = int(valor)
    if abs(valor) >= 1000 and rng.random() < 0.5:
        return f"{valor:,}".replace(",", ".")   # 1234 -> "1.234"
    return valor


def formatar_data(data, rng):
    """Mistura dois formatos de data: dd/mm/aaaa HH:MM e ISO."""
    if rng.random() < 0.4:
        return data.strftime("%d/%m/%Y %H:%M")
    return data.strftime("%Y-%m-%d %H:%M:%S")


def preparar_exportacao(df, canal, semana, rng):
    """Transforma os dados de uma semana no formato 'sujo' do arquivo exportado."""
    metricas = ["alcance", "visualizacoes", "curtidas", "comentarios",
                "compartilhamentos", "salvamentos", "cliques_link"]
    out = df.drop(columns="semana").copy()
    for col in metricas:
        out[col] = [formatar_numero(v, rng) for v in out[col]]
    out["publicado_em"] = [formatar_data(d, rng) for d in out["publicado_em"]]
    if canal == "TikTok":
        out = out.drop(columns="salvamentos")  # TikTok não exporta salvamentos

    versao = "B" if semana in SEMANAS_NOMES_B[canal] else "A"
    return out.rename(columns=NOMES_COLUNAS[canal][versao])


def salvar(df, canal, nome):
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_RAW / nome
    if canal == "Instagram":
        df.to_csv(caminho, index=False)
    else:
        df.to_excel(caminho, index=False)  # usa openpyxl


def main():
    rng = np.random.default_rng(SEED)
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    # evita misturar com uma geração anterior: avisa em vez de apagar
    if any(PASTA_RAW.iterdir()):
        print(f"Aviso: {PASTA_RAW} já tem arquivos; eles serão sobrescritos pelos de mesmo nome.")

    total = 0
    for canal in ["Instagram", "TikTok"]:
        posts = gerar_posts(canal, rng)
        posts, linhas_data_ruim = injetar_problemas_numericos(posts, rng)
        extensao = "csv" if canal == "Instagram" else "xlsx"

        for semana in range(N_SEMANAS):
            df_semana = posts[posts["semana"] == semana]
            export = preparar_exportacao(df_semana, canal, semana, rng)

            # data impossível (31/02) em algumas linhas
            col_data = NOMES_COLUNAS[canal]["B" if semana in SEMANAS_NOMES_B[canal] else "A"]["publicado_em"]
            for idx in linhas_data_ruim:
                if idx in export.index:
                    export.loc[idx, col_data] = "31/02/2026 19:00"

            # linha duplicada no mesmo arquivo
            if semana in SEMANAS_COM_DUPLICATA[canal]:
                export = pd.concat([export, export.iloc[[0]]], ignore_index=True)

            ano, sem_iso, _ = (INICIO + pd.Timedelta(weeks=semana)).isocalendar()
            nome = f"{canal.lower()}_{ano}-S{sem_iso:02d}.{extensao}"
            salvar(export, canal, nome)
            total += len(export)

            # arquivo semanal reenviado: mesma exportação, outro nome
            if semana == 3:
                salvar(export, canal, f"{canal.lower()}_{ano}-S{sem_iso:02d}_reenvio.{extensao}")
                total += len(export)

    print(f"Arquivos gerados em {PASTA_RAW}: {len(list(PASTA_RAW.iterdir()))} ({total} linhas no total)")


if __name__ == "__main__":
    main()
