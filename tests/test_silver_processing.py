"""Testes unitários para o módulo de processamento da Camada Silver."""

from pathlib import Path

import duckdb
import pytest

from src.processing.silver_processing import (
    executar_pipeline_silver,
    limpar_telefones,
    padronizar_moedas,
    padronizar_texto,
    processar_avaliacoes,
    processar_categorias_traducao,
    processar_clientes,
    processar_geolocalizacao,
    processar_itens_pedido,
    processar_pagamentos,
    processar_pedidos,
    processar_produtos,
    processar_vendedores,
)


def test_limpar_telefones_formato_padrao() -> None:
    """Verifica se caracteres especiais, parênteses e traços são removidos."""
    assert limpar_telefones("(11) 98765-4321") == "11987654321"
    assert limpar_telefones("+55 21 9999-0000") == "552199990000"


def test_limpar_telefones_valores_nulos_e_vazios() -> None:
    """Verifica o comportamento para strings vazias e valores nulos."""
    assert limpar_telefones(None) is None
    assert limpar_telefones("   ") is None
    assert limpar_telefones("---") is None


def test_padronizar_moedas_com_simbolos_e_virgulas() -> None:
    """Verifica a conversão de moedas com vírgula e símbolo R$."""
    assert padronizar_moedas("R$ 1.250,50") == 1250.50
    assert padronizar_moedas(" 99,9 ") == 99.90
    assert padronizar_moedas(150.758) == 150.76


def test_padronizar_moedas_invalidos_e_nulos() -> None:
    """Verifica que strings inválidas retornam None."""
    assert padronizar_moedas(None) is None
    assert padronizar_moedas("invalido") is None


def test_padronizar_texto_espacos_e_minusculas() -> None:
    """Verifica remoção de espaços e conversão opcional para minúsculas."""
    assert padronizar_texto("  Eletrônicos  ", minusculo=True) == "eletrônicos"
    assert padronizar_texto("  São Paulo  ", minusculo=False) == "São Paulo"
    assert padronizar_texto(None) is None
    assert padronizar_texto("    ") is None


def test_executar_pipeline_silver_arquivo_inexistente(tmp_path: Path) -> None:
    """Garante que tentar processar banco inexistente dispara FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Banco Bronze não encontrado"):
        executar_pipeline_silver(
            bronze_db_path=tmp_path / "nao_existe.db",
            silver_db_path=tmp_path / "silver.db",
        )


def _criar_bronze_completo(caminho_db: Path) -> None:
    """Cria banco DuckDB simulando todas as 9 tabelas da Camada Bronze."""
    with duckdb.connect(str(caminho_db)) as con:
        con.execute(
            """
            CREATE TABLE olist_orders_dataset AS
            SELECT
                ' order_1 ' AS order_id,
                ' cust_1 ' AS customer_id,
                ' DELIVERED ' AS order_status,
                '2021-01-01 10:00:00' AS order_purchase_timestamp,
                '2021-01-01 11:00:00' AS order_approved_at,
                '2021-01-02 12:00:00' AS order_delivered_carrier_date,
                '2021-01-05 15:00:00' AS order_delivered_customer_date,
                '2021-01-10 00:00:00' AS order_estimated_delivery_date
            """
        )
        con.execute(
            """
            CREATE TABLE olist_order_items_dataset AS
            SELECT
                ' order_1 ' AS order_id,
                '1' AS order_item_id,
                ' prod_1 ' AS product_id,
                ' sell_1 ' AS seller_id,
                '2021-01-03 10:00:00' AS shipping_limit_date,
                '129.99' AS price,
                '15.50' AS freight_value
            """
        )
        con.execute(
            """
            CREATE TABLE olist_order_payments_dataset AS
            SELECT
                ' order_1 ' AS order_id,
                '1' AS payment_sequential,
                ' CREDIT_CARD ' AS payment_type,
                '3' AS payment_installments,
                '145.49' AS payment_value
            """
        )
        con.execute(
            """
            CREATE TABLE olist_order_reviews_dataset AS
            SELECT
                ' rev_1 ' AS review_id,
                ' order_1 ' AS order_id,
                '5' AS review_score,
                ' Bom ' AS review_comment_title,
                ' Gostei ' AS review_comment_message,
                '2021-01-06 00:00:00' AS review_creation_date,
                '2021-01-06 18:00:00' AS review_answer_timestamp
            """
        )
        con.execute(
            """
            CREATE TABLE olist_customers_dataset AS
            SELECT
                ' cust_1 ' AS customer_id,
                ' uniq_1 ' AS customer_unique_id,
                '14.409-123' AS customer_zip_code_prefix,
                ' FRANCA ' AS customer_city,
                ' sp ' AS customer_state
            """
        )
        con.execute(
            """
            CREATE TABLE olist_products_dataset AS
            SELECT
                ' prod_1 ' AS product_id,
                ' PERFUMARIA ' AS product_category_name,
                '40' AS product_name_lenght,
                '280' AS product_description_lenght,
                '2' AS product_photos_qty,
                '500' AS product_weight_g,
                '20' AS product_length_cm,
                '15' AS product_height_cm,
                '10' AS product_width_cm
            """
        )
        con.execute(
            """
            CREATE TABLE olist_sellers_dataset AS
            SELECT
                ' sell_1 ' AS seller_id,
                '14400-000' AS seller_zip_code_prefix,
                ' FRANCA ' AS seller_city,
                ' sp ' AS seller_state
            """
        )
        con.execute(
            """
            CREATE TABLE olist_geolocation_dataset AS
            SELECT
                '14.409-123' AS geolocation_zip_code_prefix,
                '-20.53' AS geolocation_lat,
                '-47.40' AS geolocation_lng,
                ' FRANCA ' AS geolocation_city,
                ' sp ' AS geolocation_state
            """
        )
        con.execute(
            """
            CREATE TABLE product_category_name_translation AS
            SELECT
                ' PERFUMARIA ' AS product_category_name,
                ' PERFUMERY ' AS product_category_name_english
            """
        )


def test_transformacoes_individuais_silver(tmp_path: Path) -> None:
    """Testa individualmente as funções de transformação de todas as tabelas."""
    bronze_db = tmp_path / "bronze_individual.db"
    silver_db = tmp_path / "silver_individual.db"
    _criar_bronze_completo(bronze_db)

    with duckdb.connect(str(silver_db)) as con:
        con.execute("ATTACH ? AS con_bronze (READ_ONLY)", [str(bronze_db)])
        assert processar_pedidos(con) == 1
        assert processar_itens_pedido(con) == 1
        assert processar_pagamentos(con) == 1
        assert processar_avaliacoes(con) == 1
        assert processar_clientes(con) == 1
        assert processar_produtos(con) == 1
        assert processar_vendedores(con) == 1
        assert processar_geolocalizacao(con) == 1
        assert processar_categorias_traducao(con) == 1

        prod = con.execute(
            "SELECT product_id, product_category_name, product_weight_g FROM olist_products_dataset"
        ).fetchone()
        assert prod == ("prod_1", "perfumaria", 500)

        seller = con.execute(
            "SELECT seller_id, seller_zip_code_prefix, seller_city, seller_state FROM olist_sellers_dataset"
        ).fetchone()
        assert seller == ("sell_1", "14400000", "franca", "SP")

        geo = con.execute(
            "SELECT geolocation_zip_code_prefix, geolocation_city, geolocation_state FROM olist_geolocation_dataset"
        ).fetchone()
        assert geo == ("14409123", "franca", "SP")

        trans = con.execute(
            "SELECT product_category_name, product_category_name_english FROM product_category_name_translation"
        ).fetchone()
        assert trans == ("perfumaria", "perfumery")


def test_executar_pipeline_silver_completo(tmp_path: Path) -> None:
    """Testa a execução ponta a ponta do pipeline silver gerando as 9 tabelas."""
    bronze_db = tmp_path / "bronze_pipeline.db"
    silver_db = tmp_path / "silver_pipeline.db"
    _criar_bronze_completo(bronze_db)

    resultado = executar_pipeline_silver(
        bronze_db_path=bronze_db,
        silver_db_path=silver_db,
    )

    assert len(resultado) == 9
    assert all(qtd == 1 for qtd in resultado.values())

    with duckdb.connect(str(silver_db), read_only=True) as con:
        tabelas = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        assert len(tabelas) == 9
