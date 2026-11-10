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
    processar_clientes,
    processar_itens_pedido,
    processar_pagamentos,
    processar_pedidos,
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


def test_transformacoes_silver_em_banco_temporario(tmp_path: Path) -> None:
    """Testa a higienização e tipagem em banco DuckDB isolado."""
    bronze_db = tmp_path / "bronze_teste.db"
    silver_db = tmp_path / "silver_teste.db"

    with duckdb.connect(str(bronze_db)) as con:
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

    with duckdb.connect(str(silver_db)) as con_silver:
        con_silver.execute(f"ATTACH '{bronze_db}' AS con_bronze (READ_ONLY)")
        assert processar_pedidos(con_silver) == 1
        assert processar_itens_pedido(con_silver) == 1
        assert processar_pagamentos(con_silver) == 1
        assert processar_avaliacoes(con_silver) == 1
        assert processar_clientes(con_silver) == 1

        ordem = con_silver.execute(
            "SELECT order_id, order_status, CAST(order_purchase_timestamp AS VARCHAR) FROM olist_orders_dataset"
        ).fetchone()
        assert ordem == (
            "order_1",
            "delivered",
            "2021-01-01 10:00:00",
        )

        item = con_silver.execute(
            "SELECT price, freight_value FROM olist_order_items_dataset"
        ).fetchone()
        assert str(item[0]) == "129.99"
        assert str(item[1]) == "15.50"

        cliente = con_silver.execute(
            "SELECT customer_zip_code_prefix, customer_city, customer_state FROM olist_customers_dataset"
        ).fetchone()
        assert cliente == ("14409123", "franca", "SP")
