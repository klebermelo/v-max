SELECT 
    CASE 
        WHEN c.customer_state IN ('SP', 'RJ', 'MG', 'ES') THEN 'Sudeste'
        WHEN c.customer_state IN ('PR', 'SC', 'RS') THEN 'Sul'
        WHEN c.customer_state IN ('BA', 'PE', 'CE', 'MA', 'PB', 'RN', 'AL', 'SE', 'PI') THEN 'Nordeste'
        WHEN c.customer_state IN ('GO', 'MT', 'MS', 'DF') THEN 'Centro-Oeste'
        ELSE 'Norte'
    END AS regiao,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio
FROM fato_vendas f
INNER JOIN dim_clientes c ON f.customer_id = c.customer_id
INNER JOIN dim_tempo t ON f.data_pedido = t.data
WHERE (? IS NULL OR STRFTIME(TRY_CAST(t.data AS DATE), '%Y') = ?)
GROUP BY 1
ORDER BY total_pedidos DESC;
