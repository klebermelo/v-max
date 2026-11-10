-- Risco de Churn de Clientes
-- Pergunta: Quais clientes foram impactados por atrasos logísticos e deram notas críticas?
WITH pedidos_consolidados AS (
    SELECT
        f.order_id,
        c.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        f.order_purchase_timestamp,
        DATEDIFF('day', CAST(f.order_estimated_delivery_date AS DATE), CAST(f.order_delivered_customer_date AS DATE)) AS dias_atraso,
        f.nota_avaliacao,
        SUM(f.valor_total) AS valor_total_pedido
    FROM fato_vendas AS f
    INNER JOIN dim_clientes AS c
        ON c.customer_id = f.customer_id
    GROUP BY
        f.order_id,
        c.customer_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        f.order_purchase_timestamp,
        f.order_estimated_delivery_date,
        f.order_delivered_customer_date,
        f.nota_avaliacao
)

SELECT
    order_id,
    customer_unique_id,
    customer_city,
    customer_state,
    order_purchase_timestamp,
    dias_atraso,
    nota_avaliacao,
    ROUND(valor_total_pedido, 2) AS valor_total_pedido,
    CASE
        WHEN dias_atraso > 5 AND nota_avaliacao <= 2 THEN 'Risco Crítico'
        WHEN dias_atraso > 5 THEN 'Risco Alto'
        WHEN nota_avaliacao <= 2 THEN 'Alerta Operacional'
        ELSE 'Sem Risco'
    END AS classificacao_risco
FROM pedidos_consolidados
WHERE dias_atraso > 5 OR nota_avaliacao <= 2
ORDER BY
    CASE
        WHEN dias_atraso > 5 AND nota_avaliacao <= 2 THEN 1
        WHEN dias_atraso > 5 THEN 2
        ELSE 3
    END,
    dias_atraso DESC NULLS LAST,
    valor_total_pedido DESC;
