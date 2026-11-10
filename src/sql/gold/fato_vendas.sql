-- Fato de vendas (grão: um registro por item de pedido).
-- Lead time = dias corridos entre a compra e a entrega ao cliente
-- (nulo quando o pedido ainda não foi entregue).
-- Atraso = dias entre a data estimada e a data real de entrega
-- (valores positivos indicam entrega atrasada).
CREATE OR REPLACE TABLE fato_vendas AS
WITH avaliacoes_por_pedido AS (
    SELECT
        order_id,
        CAST(AVG(review_score) AS DECIMAL(3, 2)) AS nota_avaliacao
    FROM silver.olist_order_reviews_dataset
    GROUP BY order_id
)
SELECT
    i.order_id,
    i.order_item_id,
    o.customer_id,
    i.product_id,
    i.seller_id,
    CAST(o.order_purchase_timestamp AS DATE) AS data_pedido,
    o.order_status,
    i.price AS valor_produto,
    i.freight_value AS valor_frete,
    CAST(i.price + i.freight_value AS DECIMAL(10, 2)) AS valor_total,
    o.order_purchase_timestamp,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    DATE_DIFF(
        'day',
        CAST(o.order_purchase_timestamp AS DATE),
        CAST(o.order_delivered_customer_date AS DATE)
    ) AS lead_time_dias,
    DATE_DIFF(
        'day',
        CAST(o.order_estimated_delivery_date AS DATE),
        CAST(o.order_delivered_customer_date AS DATE)
    ) AS atraso_entrega_dias,
    a.nota_avaliacao
FROM silver.olist_order_items_dataset AS i
INNER JOIN silver.olist_orders_dataset AS o
    ON o.order_id = i.order_id
LEFT JOIN avaliacoes_por_pedido AS a
    ON a.order_id = i.order_id;
