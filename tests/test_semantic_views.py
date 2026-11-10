"""Testes unitários para a Camada Semântica de Views em Português."""

from pathlib import Path

import duckdb
import pytest

from src.processing.semantic_views import (
    MAPA_VIEWS_SEMANTICAS,
    criar_todas_views_semanticas,
    executar_camada_semantica,
)


def _criar_silver_minima(db_path: Path) -> None:
    """Cria tabelas físicas mínimas simulando o banco Silver."""
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            """
            CREATE TABLE olist_orders_dataset AS
            SELECT 'ord_1' AS order_id, 'cust_1' AS customer_id, 'delivered' AS order_status;
            """
        )
        con.execute(
            """
            CREATE TABLE olist_order_items_dataset AS
            SELECT 'ord_1' AS order_id, 1 AS order_item_id, 'prod_1' AS product_id, 100.0 AS price;
            """
        )
        con.execute(
            """
            CREATE TABLE olist_customers_dataset AS
            SELECT 'cust_1' AS customer_id, 'SP' AS customer_state;
            """
        )
        con.execute(
            "CREATE TABLE olist_order_payments_dataset AS SELECT 'ord_1' AS order_id, 100.0 AS payment_value;"
        )
        con.execute(
            "CREATE TABLE olist_order_reviews_dataset AS SELECT 'ord_1' AS order_id, 5 AS review_score;"
        )
        con.execute(
            "CREATE TABLE olist_sellers_dataset AS SELECT 'sell_1' AS seller_id, 'SP' AS seller_state;"
        )
        con.execute(
            "CREATE TABLE olist_products_dataset AS SELECT 'prod_1' AS product_id, 'livros' AS product_category_name;"
        )
        con.execute(
            "CREATE TABLE product_category_name_translation AS SELECT 'livros' AS product_category_name, 'books' AS product_category_name_english;"
        )
        con.execute(
            "CREATE TABLE olist_geolocation_dataset AS SELECT '01000' AS geolocation_zip_code_prefix;"
        )


def test_criar_todas_views_semanticas_em_memoria() -> None:
    """Valida a criação e o JOIN de views semânticas em português em banco em memória."""
    with duckdb.connect(":memory:") as con:
        # Cria as tabelas na mesma conexão
        con.execute(
            """
            CREATE TABLE olist_orders_dataset AS
            SELECT 'ord_1' AS order_id, 'cust_1' AS customer_id, 'delivered' AS order_status;
            """
        )
        con.execute(
            """
            CREATE TABLE olist_order_items_dataset AS
            SELECT 'ord_1' AS order_id, 1 AS order_item_id, 'prod_1' AS product_id, 100.0 AS price;
            """
        )
        con.execute(
            """
            CREATE TABLE olist_customers_dataset AS
            SELECT 'cust_1' AS customer_id, 'SP' AS customer_state;
            """
        )
        con.execute(
            "CREATE TABLE olist_order_payments_dataset AS SELECT 'ord_1' AS order_id, 100.0 AS payment_value;"
        )
        con.execute(
            "CREATE TABLE olist_order_reviews_dataset AS SELECT 'ord_1' AS order_id, 5 AS review_score;"
        )
        con.execute(
            "CREATE TABLE olist_sellers_dataset AS SELECT 'sell_1' AS seller_id, 'SP' AS seller_state;"
        )
        con.execute(
            "CREATE TABLE olist_products_dataset AS SELECT 'prod_1' AS product_id, 'livros' AS product_category_name;"
        )
        con.execute(
            "CREATE TABLE product_category_name_translation AS SELECT 'livros' AS product_category_name, 'books' AS product_category_name_english;"
        )
        con.execute(
            "CREATE TABLE olist_geolocation_dataset AS SELECT '01000' AS geolocation_zip_code_prefix;"
        )

        total = criar_todas_views_semanticas(con)
        assert total == len(MAPA_VIEWS_SEMANTICAS)

        # Executa JOIN usando exclusivamente os nomes em português
        join_sql = """
            SELECT p.order_id, c.customer_state, i.price
            FROM pedidos AS p
            INNER JOIN clientes AS c ON p.customer_id = c.customer_id
            INNER JOIN itens_pedido AS i ON p.order_id = i.order_id;
        """
        resultado = con.execute(join_sql).fetchall()
        assert len(resultado) == 1
        assert resultado[0] == ("ord_1", "SP", 100.0)


def test_executar_camada_semantica_arquivos(tmp_path: Path) -> None:
    """Valida a execução ponta a ponta da criação de views em arquivos temporários."""
    silver_db = tmp_path / "silver_semantica.db"
    _criar_silver_minima(silver_db)

    total = executar_camada_semantica(silver_path=silver_db)
    assert total == 9

    with duckdb.connect(str(silver_db), read_only=True) as con:
        tabelas_views = {r[0] for r in con.execute("SHOW TABLES;").fetchall()}
        for view_pt in MAPA_VIEWS_SEMANTICAS:
            assert view_pt in tabelas_views


def test_executar_camada_semantica_arquivo_inexistente(tmp_path: Path) -> None:
    """Valida disparo de erro para arquivo inexistente."""
    caminho = tmp_path / "inexistente.db"
    with pytest.raises(FileNotFoundError, match="Banco Silver não encontrado"):
        executar_camada_semantica(silver_path=caminho)
