-- GMV (Gross Merchandise Volume) por categoria de produto.
-- Banco: data/gold/gold.db
--
-- Definições:
--   * GMV = soma do valor dos produtos vendidos (valor_produto), sem frete.
--   * Pedidos 'canceled' e 'unavailable' são excluídos, mesmo critério do
--     kpi_sumario_mensal.
--   * participacao_pct = fatia da categoria no GMV total.
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
        SUM(v.valor_produto) AS gmv,
        COUNT(DISTINCT v.order_id) AS qtd_pedidos,
        COUNT(*) AS qtd_itens
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
    CAST(g.gmv AS DECIMAL(14, 2)) AS gmv,
    g.qtd_pedidos,
    g.qtd_itens,
    CAST(g.gmv / g.qtd_itens AS DECIMAL(10, 2)) AS preco_medio_item,
    CAST(100 * g.gmv / t.gmv_geral AS DECIMAL(5, 2)) AS participacao_pct
FROM gmv_categoria AS g
CROSS JOIN gmv_total AS t
ORDER BY g.gmv DESC, g.categoria;
