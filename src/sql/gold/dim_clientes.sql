-- Dimensão de clientes (grão: um registro por customer_id).
-- Observação: no dataset Olist, customer_id é gerado por pedido;
-- customer_unique_id identifica a pessoa física.
CREATE OR REPLACE TABLE dim_clientes AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM silver.olist_customers_dataset;
