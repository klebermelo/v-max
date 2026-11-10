-- Scorecard de vendedores: ranking por faturamento e por nota de avaliação.
-- Banco: data/gold/gold.db
--
-- Definições:
--   * faturamento = soma de valor_produto (sem frete), excluindo pedidos
--     'canceled' e 'unavailable'.
--   * nota_media = média das notas por PEDIDO (não por item), evitando que
--     pedidos com muitos itens pesem mais.
--   * rank_faturamento  -> RANK()       (empates pulam posições: 1, 1, 3)
--   * rank_nota         -> DENSE_RANK() (empates não pulam: 1, 1, 2)
--   * rank_faturamento_uf -> RANK() dentro de cada estado do vendedor.
--   * posicao_scorecard -> combina os dois rankings (menor soma = melhor);
--     empate desempatado pelo faturamento.
--   * Vendedores com poucas avaliações podem ter nota extrema; use
--     qtd_avaliacoes para filtrar conforme a necessidade da análise.
WITH vendas_validas AS (
    SELECT
        f.seller_id,
        f.order_id,
        f.valor_produto,
        f.nota_avaliacao
    FROM fato_vendas AS f
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
),

pedidos_por_vendedor AS (
    SELECT
        seller_id,
        order_id,
        SUM(valor_produto) AS valor_pedido,
        MAX(nota_avaliacao) AS nota_pedido
    FROM vendas_validas
    GROUP BY seller_id, order_id
),

metricas_vendedor AS (
    SELECT
        seller_id,
        CAST(SUM(valor_pedido) AS DECIMAL(14, 2)) AS faturamento,
        COUNT(*) AS qtd_pedidos,
        COUNT(nota_pedido) AS qtd_avaliacoes,
        CAST(AVG(nota_pedido) AS DECIMAL(3, 2)) AS nota_media
    FROM pedidos_por_vendedor
    GROUP BY seller_id
),

rankings AS (
    SELECT
        m.seller_id,
        v.seller_city,
        v.seller_state,
        m.faturamento,
        m.qtd_pedidos,
        m.qtd_avaliacoes,
        m.nota_media,
        RANK() OVER (ORDER BY m.faturamento DESC) AS rank_faturamento,
        DENSE_RANK() OVER (ORDER BY m.nota_media DESC NULLS LAST) AS rank_nota,
        RANK() OVER (
            PARTITION BY v.seller_state
            ORDER BY m.faturamento DESC
        ) AS rank_faturamento_uf
    FROM metricas_vendedor AS m
    INNER JOIN dim_vendedores AS v
        ON v.seller_id = m.seller_id
)

SELECT
    RANK() OVER (
        ORDER BY rank_faturamento + rank_nota, faturamento DESC
    ) AS posicao_scorecard,
    seller_id,
    seller_city,
    seller_state,
    faturamento,
    qtd_pedidos,
    qtd_avaliacoes,
    nota_media,
    rank_faturamento,
    rank_nota,
    rank_faturamento_uf
FROM rankings
ORDER BY posicao_scorecard, seller_id;
