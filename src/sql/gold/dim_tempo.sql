-- Dimensão de tempo (grão: um registro por dia), contínua entre a
-- primeira e a última data de compra existentes na Silver.
CREATE OR REPLACE TABLE dim_tempo AS
WITH limites AS (
    SELECT
        CAST(MIN(order_purchase_timestamp) AS DATE) AS data_inicio,
        CAST(MAX(order_purchase_timestamp) AS DATE) AS data_fim
    FROM silver.olist_orders_dataset
),
calendario AS (
    SELECT
        CAST(
            UNNEST(generate_series(data_inicio, data_fim, INTERVAL 1 DAY)) AS DATE
        ) AS data
    FROM limites
)
SELECT
    data,
    CAST(YEAR(data) AS INTEGER) AS ano,
    CAST(QUARTER(data) AS INTEGER) AS trimestre,
    CAST(MONTH(data) AS INTEGER) AS mes,
    CAST(DAY(data) AS INTEGER) AS dia,
    CAST(ISODOW(data) AS INTEGER) AS dia_semana_iso,
    STRFTIME(data, '%Y-%m') AS ano_mes,
    ISODOW(data) IN (6, 7) AS fim_de_semana
FROM calendario;
