-- Consultas de negócio sobre data/metricas.sqlite (tabela posts).
-- Cada consulta tem um título numerado em comentário (o notebook usa isso para separá-las).
-- "Engajamento" = média da taxa_engajamento dos posts (ver pipeline/transformar.py).

-- Consulta 1: Qual formato engaja mais em cada canal?
SELECT canal,
       formato,
       COUNT(*)                        AS posts,
       ROUND(AVG(taxa_engajamento), 4) AS engajamento_medio
FROM posts
GROUP BY canal, formato
ORDER BY canal, engajamento_medio DESC;

-- Consulta 2: Qual a melhor faixa de horário para publicar?
-- CASE agrupa as horas em faixas; ordenamos pelo engajamento.
SELECT CASE
           WHEN hora BETWEEN 8 AND 11  THEN '1. 08h-11h'
           WHEN hora BETWEEN 12 AND 15 THEN '2. 12h-15h'
           WHEN hora BETWEEN 16 AND 18 THEN '3. 16h-18h'
           WHEN hora BETWEEN 19 AND 21 THEN '4. 19h-21h'
           WHEN hora >= 22 OR hora < 8 THEN '5. 22h-07h'
       END                              AS faixa_horario,
       COUNT(*)                         AS posts,
       ROUND(AVG(alcance), 0)           AS alcance_medio,
       ROUND(AVG(taxa_engajamento), 4)  AS engajamento_medio
FROM posts
GROUP BY faixa_horario
ORDER BY faixa_horario;

-- Consulta 3: Evolução semanal do alcance total por canal
-- Window function LAG: compara cada semana com a anterior do mesmo canal.
WITH semanal AS (
    SELECT canal,
           semana_iso,
           COUNT(*)               AS posts,
           SUM(alcance)           AS alcance_total,
           ROUND(AVG(alcance), 0) AS alcance_medio_por_post
    FROM posts
    GROUP BY canal, semana_iso
)
SELECT canal,
       semana_iso,
       posts,
       alcance_total,
       alcance_medio_por_post,
       LAG(alcance_total) OVER (PARTITION BY canal ORDER BY semana_iso) AS alcance_semana_anterior
FROM semanal
ORDER BY canal, semana_iso;

-- Consulta 4: Top 10 posts por engajamento
SELECT canal,
       id_post,
       data,
       formato,
       tema,
       alcance,
       ROUND(taxa_engajamento, 4) AS taxa_engajamento
FROM posts
WHERE taxa_engajamento IS NOT NULL
ORDER BY taxa_engajamento DESC
LIMIT 10;

-- Consulta 5: Engajamento por tema
SELECT tema,
       COUNT(*)                        AS posts,
       ROUND(AVG(alcance), 0)          AS alcance_medio,
       ROUND(AVG(taxa_engajamento), 4) AS engajamento_medio
FROM posts
GROUP BY tema
ORDER BY engajamento_medio DESC;

-- Consulta 6: Comparação entre canais, com a média geral como referência
-- Usa a taxa SEM salvamentos, porque o TikTok não exporta salvamentos.
-- A subconsulta entre parênteses devolve um único valor (a média geral).
SELECT canal,
       COUNT(*)                                   AS posts,
       ROUND(AVG(alcance), 0)                     AS alcance_medio,
       ROUND(AVG(taxa_engajamento_sem_salvos), 4) AS engajamento_sem_salvos,
       ROUND((SELECT AVG(taxa_engajamento_sem_salvos) FROM posts), 4) AS engajamento_geral,
       SUM(cliques_link)                          AS cliques_total
FROM posts
GROUP BY canal;

-- Consulta 7: Melhor dia da semana (engajamento médio)
SELECT dia_semana,
       COUNT(*)                        AS posts,
       ROUND(AVG(taxa_engajamento), 4) AS engajamento_medio
FROM posts
GROUP BY dia_semana
ORDER BY engajamento_medio DESC;
