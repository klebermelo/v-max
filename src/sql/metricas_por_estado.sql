SELECT 
    c.customer_state AS uf,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio,
    ROUND(AVG(f.lead_time_dias), 1) AS lead_time_medio
FROM fato_vendas f
INNER JOIN dim_clientes c ON f.customer_id = c.customer_id
INNER JOIN dim_tempo t ON f.data_pedido = t.data
WHERE (? IS NULL OR STRFTIME(TRY_CAST(t.data AS DATE), '%Y') = ?)
GROUP BY c.customer_state
ORDER BY gmv_total DESC;
