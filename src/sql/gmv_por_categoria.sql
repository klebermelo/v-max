-- GMV por Categoria de Produto
-- Pergunta: Quais categorias geram maior faturamento (GMV), ticket médio por item e share percentual?
WITH vendas_validas AS (
    SELECT
        f.order_id,
        f.product_id,
        f.valor_produto
    FROM fato_vendas AS f
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
),

gmv_categoria AS (
    SELECT
        p.product_category_name AS categoria,
        p.product_category_name_english AS categoria_en,
        ROUND(SUM(v.valor_produto), 2) AS gmv,
        COUNT(DISTINCT v.order_id) AS qtd_pedidos,
        COUNT(*) AS qtd_itens,
        ROUND(AVG(v.valor_produto), 2) AS ticket_medio_item
    FROM vendas_validas AS v
    INNER JOIN dim_produtos AS p
        ON p.product_id = v.product_id
    GROUP BY p.product_category_name, p.product_category_name_english
),

gmv_total AS (
    SELECT SUM(gmv) AS gmv_geral
    FROM gmv_categoria
)

SELECT
    g.categoria,
    g.categoria_en,
    g.gmv,
    g.qtd_pedidos,
    g.qtd_itens,
    g.ticket_medio_item,
    ROUND(100.0 * g.gmv / t.gmv_geral, 2) AS participacao_pct
FROM gmv_categoria AS g
CROSS JOIN gmv_total AS t
ORDER BY g.gmv DESC, g.categoria;
