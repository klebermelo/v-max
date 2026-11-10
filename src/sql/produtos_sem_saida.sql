-- Produtos sem Saída ou Baixa Rotação
-- Pergunta: Quais produtos estão há mais tempo sem registrar saída ou nunca registraram venda?
WITH data_referencia AS (
    SELECT MAX(order_purchase_timestamp) AS max_data
    FROM fato_vendas
),

ultima_venda_produto AS (
    SELECT
        product_id,
        MAX(order_purchase_timestamp) AS ultima_venda,
        COUNT(DISTINCT order_id) AS total_pedidos_historico,
        SUM(valor_produto) AS receita_historica
    FROM fato_vendas
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY product_id
)

SELECT
    p.product_id,
    p.product_category_name AS categoria,
    p.product_category_name_english AS categoria_en,
    u.ultima_venda,
    u.total_pedidos_historico,
    ROUND(u.receita_historica, 2) AS receita_historica,
    DATEDIFF('day', u.ultima_venda, r.max_data) AS dias_sem_vender
FROM dim_produtos AS p
CROSS JOIN data_referencia AS r
LEFT JOIN ultima_venda_produto AS u
    ON u.product_id = p.product_id
ORDER BY dias_sem_vender DESC NULLS FIRST, p.product_id;
