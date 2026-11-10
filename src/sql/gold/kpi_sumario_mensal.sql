-- KPI mensal pré-agregado (materializado como tabela).
-- Receita = soma de valor_total (produto + frete) dos itens.
-- Pedidos com status 'canceled' ou 'unavailable' são excluídos.
-- Ticket médio = receita / quantidade de pedidos distintos.
CREATE OR REPLACE TABLE kpi_sumario_mensal AS
SELECT
    t.ano_mes,
    t.ano,
    t.mes,
    CAST(SUM(f.valor_total) AS DECIMAL(14, 2)) AS receita_total,
    COUNT(DISTINCT f.order_id) AS volume_pedidos,
    CAST(
        SUM(f.valor_total) / COUNT(DISTINCT f.order_id) AS DECIMAL(12, 2)
    ) AS ticket_medio
FROM fato_vendas AS f
INNER JOIN dim_tempo AS t
    ON t.data = f.data_pedido
WHERE f.order_status NOT IN ('canceled', 'unavailable')
GROUP BY t.ano_mes, t.ano, t.mes
ORDER BY t.ano_mes;
