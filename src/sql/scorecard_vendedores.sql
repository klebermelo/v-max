-- Scorecard de Vendedores
-- Pergunta: Quem são os melhores vendedores combinando faturamento, volume e avaliação?
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
        ROUND(SUM(valor_pedido), 2) AS faturamento,
        COUNT(*) AS qtd_pedidos,
        COUNT(nota_pedido) AS qtd_avaliacoes,
        ROUND(AVG(nota_pedido), 2) AS nota_media
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
        DENSE_RANK() OVER (ORDER BY m.faturamento DESC) AS rank_faturamento,
        DENSE_RANK() OVER (ORDER BY m.nota_media DESC NULLS LAST) AS rank_qualidade_nota
    FROM metricas_vendedor AS m
    INNER JOIN dim_vendedores AS v
        ON v.seller_id = m.seller_id
)

SELECT
    seller_id,
    seller_city,
    seller_state,
    faturamento,
    qtd_pedidos,
    qtd_avaliacoes,
    nota_media,
    rank_faturamento,
    rank_qualidade_nota
FROM rankings
ORDER BY rank_faturamento, rank_qualidade_nota;
