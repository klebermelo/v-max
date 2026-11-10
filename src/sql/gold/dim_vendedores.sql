-- Dimensão de vendedores (grão: um registro por seller_id).
CREATE OR REPLACE TABLE dim_vendedores AS
SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM silver.olist_sellers_dataset;
