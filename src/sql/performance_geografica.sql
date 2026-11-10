-- Performance Geográfica
-- Pergunta: Como se distribui a receita, ticket médio e prazos médios de entrega por estado dos clientes?
SELECT
    c.customer_state AS uf,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    COUNT(*) AS total_itens,
    ROUND(SUM(f.valor_produto), 2) AS receita_produtos,
    ROUND(SUM(f.valor_frete), 2) AS receita_frete,
    ROUND(SUM(f.valor_total), 2) AS faturamento_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio_pedido,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio_item,
    ROUND(AVG(f.lead_time_dias), 1) AS prazo_medio_entrega_dias
FROM fato_vendas AS f
INNER JOIN dim_clientes AS c
    ON c.customer_id = f.customer_id
WHERE f.order_status NOT IN ('canceled', 'unavailable')
GROUP BY c.customer_state
ORDER BY faturamento_total DESC;
