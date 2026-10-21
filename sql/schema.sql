-- Tabela principal: um post por linha.
-- A chave é (canal, id_post): o mesmo id pode existir em canais diferentes.
CREATE TABLE IF NOT EXISTS posts (
    canal             TEXT    NOT NULL,
    id_post           TEXT    NOT NULL,
    publicado_em      TEXT    NOT NULL,   -- 'aaaa-mm-dd HH:MM:SS'
    data              TEXT    NOT NULL,   -- 'aaaa-mm-dd'
    formato           TEXT    NOT NULL,
    tema              TEXT    NOT NULL,
    alcance           INTEGER NOT NULL,
    visualizacoes     INTEGER NOT NULL,
    curtidas          INTEGER NOT NULL,
    comentarios       INTEGER NOT NULL,
    compartilhamentos INTEGER NOT NULL,
    salvamentos       INTEGER,            -- NULL no TikTok
    cliques_link      INTEGER,
    taxa_engajamento  REAL,               -- NULL quando o alcance é 0
    taxa_engajamento_sem_salvos REAL,     -- idem; sem salvamentos, comparável entre canais
    dia_semana        TEXT    NOT NULL,
    hora              INTEGER NOT NULL,
    semana_iso        TEXT    NOT NULL,   -- ex.: '2026-W28'
    arquivo_origem    TEXT    NOT NULL,
    PRIMARY KEY (canal, id_post)
);

-- Histórico: uma linha por execução do pipeline.
CREATE TABLE IF NOT EXISTS cargas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    executado_em     TEXT    NOT NULL,
    arquivos_lidos   INTEGER NOT NULL,
    linhas_validas   INTEGER NOT NULL,
    linhas_rejeitadas INTEGER NOT NULL,
    linhas_novas     INTEGER NOT NULL     -- quantas realmente entraram em posts
);
