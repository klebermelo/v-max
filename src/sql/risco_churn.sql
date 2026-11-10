-- Clientes com risco de churn pós-incidente.
-- Banco: data/gold/gold.db
--
-- Incidente = pedido com atraso de entrega superior a 5 dias
--             (atraso_entrega_dias > 5) OU avaliação menor ou igual a 2
--             (nota_avaliacao <= 2).
--
-- Definições:
--   * Cliente = customer_unique_id (no Olist, customer_id muda a cada pedido).
--   * Análise no grão de PEDIDO (atraso e nota são do pedido, não do item).
--   * valor_em_risco = soma de valor_total (produto + frete) dos pedidos
--     com incidente.
--   * comprou_apos_incidente = o cliente fez alguma compra depois do último
--     incidente. Quem NÃO voltou a comprar aparece primeiro (maior risco).
--   * Limitação: pedidos não entregues têm atraso nulo e só entram aqui
--     se tiverem avaliação baixa.
WITH pedidos AS (
    SELECT
        f.order_id,
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        MIN(f.order_purchase_timestamp) AS data_compra,
        MAX(f.atraso_entrega_dias) AS atraso_dias,
        MAX(f.nota_avaliacao) AS nota,
        SUM(f.valor_total) AS valor_pedido
    FROM fato_vendas AS f
    INNER JOIN dim_clientes AS c
        ON c.customer_id = f.customer_id
    GROUP BY f.order_id, c.customer_unique_id, c.customer_city, c.customer_state
),

incidentes AS (
    SELECT
        *,
        CASE
            WHEN atraso_dias > 5 AND nota <= 2 THEN 'atraso_e_avaliacao_baixa'
            WHEN atraso_dias > 5 THEN 'atraso'
            ELSE 'avaliacao_baixa'
        END AS tipo_incidente
    FROM pedidos
    WHERE atraso_dias > 5 OR nota <= 2
),

clientes_com_incidente AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS qtd_pedidos_incidente,
        MAX(atraso_dias) AS maior_atraso_dias,
        MIN(nota) AS menor_nota,
        CAST(SUM(valor_pedido) AS DECIMAL(14, 2)) AS valor_em_risco,
        MAX(data_compra) AS data_ultimo_incidente,
        ARG_MAX(tipo_incidente, data_compra) AS tipo_ultimo_incidente
    FROM incidentes
    GROUP BY customer_unique_id
),

historico_cliente AS (
    SELECT
        customer_unique_id,
        COUNT(*) AS total_pedidos,
        MAX(data_compra) AS data_ultima_compra,
        ARG_MAX(customer_city, data_compra) AS cidade,
        ARG_MAX(customer_state, data_compra) AS uf
    FROM pedidos
    GROUP BY customer_unique_id
)

SELECT
    i.customer_unique_id,
    h.cidade,
    h.uf,
    h.total_pedidos,
    i.qtd_pedidos_incidente,
    i.tipo_ultimo_incidente,
    i.maior_atraso_dias,
    i.menor_nota,
    i.valor_em_risco,
    i.data_ultimo_incidente,
    h.data_ultima_compra > i.data_ultimo_incidente AS comprou_apos_incidente
FROM clientes_com_incidente AS i
INNER JOIN historico_cliente AS h
    ON h.customer_unique_id = i.customer_unique_id
ORDER BY comprou_apos_incidente, i.valor_em_risco DESC, i.customer_unique_id;
