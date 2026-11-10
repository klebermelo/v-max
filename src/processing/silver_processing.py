"""Módulo de processamento da Camada Silver do projeto V-MAX.

Realiza a sanitização, tipagem estrita e enriquecimento com metadados de auditoria
a partir da Camada Bronze, persistindo os dados limpos em `data/silver/silver.db`.
"""

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BRONZE_DB_PATH = Path("data/bronze/bronze.db")
SILVER_DB_PATH = Path("data/silver/silver.db")


def limpar_telefones(valor: str | None) -> str | None:
    """Higieniza cadeias de telefone, mantendo apenas dígitos numéricos."""
    if valor is None:
        return None
    apenas_num = re.sub(r"\D", "", valor.strip())
    return apenas_num if apenas_num else None


def padronizar_moedas(valor: str | float | None) -> float | None:
    """Converte e arredonda valores financeiros para float com duas casas decimais."""
    if valor is None:
        return None
    try:
        val_str = str(valor).strip().replace("R$", "").replace(" ", "")
        if "." in val_str and "," in val_str:
            val_str = val_str.replace(".", "").replace(",", ".")
        elif "," in val_str:
            val_str = val_str.replace(",", ".")
        return round(float(val_str), 2)
    except ValueError:
        return None


def padronizar_texto(valor: str | None, minusculo: bool = False) -> str | None:
    """Remove espaços em branco extras e opcionalmente converte para minúsculas."""
    if valor is None:
        return None
    texto = valor.strip()
    return (texto.lower() if minusculo else texto) if texto else None


def processar_pedidos(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de pedidos (orders) para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_orders_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_orders_dataset AS
        SELECT
            TRIM(order_id) AS order_id,
            TRIM(customer_id) AS customer_id,
            LOWER(TRIM(order_status)) AS order_status,
            TRY_CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
            TRY_CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
            TRY_CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
            TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
            TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,
            ? AS _processed_at
        FROM con_bronze.olist_orders_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_orders_dataset").fetchone()[0]
    logger.info("Concluído: olist_orders_dataset (%d registros)", total)
    return total


def processar_itens_pedido(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de itens de pedido para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_order_items_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_order_items_dataset AS
        SELECT
            TRIM(order_id) AS order_id,
            TRY_CAST(order_item_id AS INTEGER) AS order_item_id,
            TRIM(product_id) AS product_id,
            TRIM(seller_id) AS seller_id,
            TRY_CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,
            TRY_CAST(price AS DECIMAL(10,2)) AS price,
            TRY_CAST(freight_value AS DECIMAL(10,2)) AS freight_value,
            ? AS _processed_at
        FROM con_bronze.olist_order_items_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_order_items_dataset").fetchone()[0]
    logger.info("Concluído: olist_order_items_dataset (%d registros)", total)
    return total


def processar_pagamentos(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de pagamentos de pedido para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_order_payments_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_order_payments_dataset AS
        SELECT
            TRIM(order_id) AS order_id,
            TRY_CAST(payment_sequential AS INTEGER) AS payment_sequential,
            LOWER(TRIM(payment_type)) AS payment_type,
            TRY_CAST(payment_installments AS INTEGER) AS payment_installments,
            TRY_CAST(payment_value AS DECIMAL(10,2)) AS payment_value,
            ? AS _processed_at
        FROM con_bronze.olist_order_payments_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_order_payments_dataset").fetchone()[
        0
    ]
    logger.info("Concluído: olist_order_payments_dataset (%d registros)", total)
    return total


def processar_avaliacoes(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de avaliações de pedidos para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_order_reviews_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_order_reviews_dataset AS
        SELECT
            TRIM(review_id) AS review_id,
            TRIM(order_id) AS order_id,
            TRY_CAST(review_score AS INTEGER) AS review_score,
            TRIM(review_comment_title) AS review_comment_title,
            TRIM(review_comment_message) AS review_comment_message,
            TRY_CAST(review_creation_date AS DATE) AS review_creation_date,
            TRY_CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,
            ? AS _processed_at
        FROM con_bronze.olist_order_reviews_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_order_reviews_dataset").fetchone()[
        0
    ]
    logger.info("Concluído: olist_order_reviews_dataset (%d registros)", total)
    return total


def processar_clientes(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de clientes para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_customers_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_customers_dataset AS
        SELECT
            TRIM(customer_id) AS customer_id,
            TRIM(customer_unique_id) AS customer_unique_id,
            REGEXP_REPLACE(TRIM(customer_zip_code_prefix), '[^0-9]', '', 'g') AS customer_zip_code_prefix,
            LOWER(TRIM(customer_city)) AS customer_city,
            UPPER(TRIM(customer_state)) AS customer_state,
            ? AS _processed_at
        FROM con_bronze.olist_customers_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_customers_dataset").fetchone()[0]
    logger.info("Concluído: olist_customers_dataset (%d registros)", total)
    return total


def processar_produtos(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de produtos para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_products_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_products_dataset AS
        SELECT
            TRIM(product_id) AS product_id,
            LOWER(TRIM(product_category_name)) AS product_category_name,
            TRY_CAST(product_name_lenght AS INTEGER) AS product_name_lenght,
            TRY_CAST(product_description_lenght AS INTEGER) AS product_description_lenght,
            TRY_CAST(product_photos_qty AS INTEGER) AS product_photos_qty,
            TRY_CAST(product_weight_g AS INTEGER) AS product_weight_g,
            TRY_CAST(product_length_cm AS INTEGER) AS product_length_cm,
            TRY_CAST(product_height_cm AS INTEGER) AS product_height_cm,
            TRY_CAST(product_width_cm AS INTEGER) AS product_width_cm,
            ? AS _processed_at
        FROM con_bronze.olist_products_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_products_dataset").fetchone()[0]
    logger.info("Concluído: olist_products_dataset (%d registros)", total)
    return total


def processar_vendedores(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de vendedores para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_sellers_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_sellers_dataset AS
        SELECT
            TRIM(seller_id) AS seller_id,
            REGEXP_REPLACE(TRIM(seller_zip_code_prefix), '[^0-9]', '', 'g') AS seller_zip_code_prefix,
            LOWER(TRIM(seller_city)) AS seller_city,
            UPPER(TRIM(seller_state)) AS seller_state,
            ? AS _processed_at
        FROM con_bronze.olist_sellers_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_sellers_dataset").fetchone()[0]
    logger.info("Concluído: olist_sellers_dataset (%d registros)", total)
    return total


def processar_geolocalizacao(con: duckdb.DuckDBPyConnection) -> int:
    """Processa e higieniza a tabela de geolocalização para a camada Silver."""
    logger.info("Iniciando processamento Silver: olist_geolocation_dataset")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE olist_geolocation_dataset AS
        SELECT
            REGEXP_REPLACE(TRIM(geolocation_zip_code_prefix), '[^0-9]', '', 'g') AS geolocation_zip_code_prefix,
            TRY_CAST(geolocation_lat AS DOUBLE) AS geolocation_lat,
            TRY_CAST(geolocation_lng AS DOUBLE) AS geolocation_lng,
            LOWER(TRIM(geolocation_city)) AS geolocation_city,
            UPPER(TRIM(geolocation_state)) AS geolocation_state,
            ? AS _processed_at
        FROM con_bronze.olist_geolocation_dataset
    """,
        [ts],
    )
    total = con.execute("SELECT COUNT(*) FROM olist_geolocation_dataset").fetchone()[0]
    logger.info("Concluído: olist_geolocation_dataset (%d registros)", total)
    return total


def processar_categorias_traducao(con: duckdb.DuckDBPyConnection) -> int:
    """Processa a tabela de tradução de categorias para a camada Silver."""
    logger.info("Iniciando: product_category_name_translation")
    ts = datetime.now(UTC).isoformat()
    con.execute(
        """
        CREATE OR REPLACE TABLE product_category_name_translation AS
        SELECT
            LOWER(TRIM(product_category_name)) AS product_category_name,
            LOWER(TRIM(product_category_name_english)) AS product_category_name_english,
            ? AS _processed_at
        FROM con_bronze.product_category_name_translation
    """,
        [ts],
    )
    total = con.execute(
        "SELECT COUNT(*) FROM product_category_name_translation"
    ).fetchone()[0]
    logger.info("Concluído: product_category_name_translation (%d registros)", total)
    return total


def _executar_transformacoes_silver(
    con: duckdb.DuckDBPyConnection,
) -> dict[str, int]:
    """Executa individualmente as transformações de cada tabela Silver."""
    return {
        "olist_orders_dataset": processar_pedidos(con),
        "olist_order_items_dataset": processar_itens_pedido(con),
        "olist_order_payments_dataset": processar_pagamentos(con),
        "olist_order_reviews_dataset": processar_avaliacoes(con),
        "olist_customers_dataset": processar_clientes(con),
        "olist_products_dataset": processar_produtos(con),
        "olist_sellers_dataset": processar_vendedores(con),
        "olist_geolocation_dataset": processar_geolocalizacao(con),
        "product_category_name_translation": processar_categorias_traducao(con),
    }


def executar_pipeline_silver(
    bronze_db_path: Path = BRONZE_DB_PATH,
    silver_db_path: Path = SILVER_DB_PATH,
) -> dict[str, int]:
    """Executa a sanitização completa das tabelas Bronze para a Camada Silver."""
    if not bronze_db_path.exists():
        raise FileNotFoundError(f"Banco Bronze não encontrado: {bronze_db_path}")

    silver_db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Pipeline Silver | Origem: %s | Destino: %s", bronze_db_path, silver_db_path
    )

    with duckdb.connect(str(silver_db_path)) as con_silver:
        con_silver.execute("ATTACH ? AS con_bronze (READ_ONLY)", [str(bronze_db_path)])
        tabelas = _executar_transformacoes_silver(con_silver)
        con_silver.execute("DETACH con_bronze")

    logger.info("Pipeline Silver finalizado com sucesso (%d tabelas).", len(tabelas))
    return tabelas


if __name__ == "__main__":
    executar_pipeline_silver()
