SELECT 
    STRFTIME(TRY_CAST(t.data AS DATE), '%m') AS mes,
    STRFTIME(TRY_CAST(t.data AS DATE), '%Y') AS ano,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio
FROM fato_vendas f
INNER JOIN dim_tempo t ON f.data_pedido = t.data
GROUP BY 1, 2
ORDER BY 1, 2;
