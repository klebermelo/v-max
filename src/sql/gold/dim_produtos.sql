-- Dimensão de produtos (grão: um registro por product_id),
-- enriquecida com a tradução da categoria para inglês.
CREATE OR REPLACE TABLE dim_produtos AS
SELECT
    p.product_id,
    COALESCE(p.product_category_name, 'nao_informada') AS product_category_name,
    COALESCE(
        t.product_category_name_english,
        p.product_category_name,
        'not_informed'
    ) AS product_category_name_english,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM silver.olist_products_dataset AS p
LEFT JOIN silver.product_category_name_translation AS t
    ON t.product_category_name = p.product_category_name;
