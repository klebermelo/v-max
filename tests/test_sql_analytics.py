"""Testes unitários para as consultas analíticas e otimizações da Camada Gold."""

from pathlib import Path

import duckdb
import pytest

from src.processing.gold_optimization import (
    INDICES_GOLD,
    atualizar_estatisticas,
    criar_indices_gold,
    otimizar_banco_gold,
)

SQL_DIR = Path("src/sql")
QUERIES = (
    "gmv_por_categoria",
    "scorecard_vendedores",
    "risco_churn",
    "produtos_sem_saida",
    "performance_geografica",
)


def _criar_gold_amostra(con: duckdb.DuckDBPyConnection) -> None:
    """Cria tabelas dimensionais e fato mínimas para execução das queries SQL."""
    con.execute(
        """
        CREATE TABLE dim_clientes AS
        SELECT * FROM (VALUES
            ('c1', 'u1', '01310', 'sao paulo', 'SP'),
            ('c2', 'u2', '20000', 'rio de janeiro', 'RJ')
        ) AS t(customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state);
        """
    )
    con.execute(
        """
        CREATE TABLE dim_produtos AS
        SELECT * FROM (VALUES
            ('p1', 'perfumaria', 'perfumery', 2, 500, 20, 15, 10),
            ('p2', 'informatica', 'computers', 1, 300, 10, 10, 10),
            ('p3', 'livros', 'books', 1, 200, 15, 10, 5)
        ) AS t(product_id, product_category_name, product_category_name_english,
               product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm);
        """
    )
    con.execute(
        """
        CREATE TABLE dim_vendedores AS
        SELECT * FROM (VALUES
            ('s1', '13000', 'campinas', 'SP'),
            ('s2', '20000', 'rio de janeiro', 'RJ')
        ) AS t(seller_id, seller_zip_code_prefix, seller_city, seller_state);
        """
    )
    con.execute(
        """
        CREATE TABLE dim_tempo AS
        SELECT * FROM (VALUES
            (DATE '2021-01-01', 2021, 1, 1, 1, 5, '2021-01', false),
            (DATE '2021-01-02', 2021, 1, 1, 2, 6, '2021-01', true)
        ) AS t(data, ano, trimestre, mes, dia, dia_semana_iso, ano_mes, fim_de_semana);
        """
    )
    con.execute(
        """
        CREATE TABLE fato_vendas AS
        SELECT * FROM (VALUES
            ('o1', 1, 'c1', 'p1', 's1', DATE '2021-01-01', 'delivered',
             CAST(100.00 AS DECIMAL(10,2)), CAST(15.00 AS DECIMAL(10,2)), CAST(115.00 AS DECIMAL(10,2)),
             TIMESTAMP '2021-01-01 10:00:00', TIMESTAMP '2021-01-10 12:00:00', TIMESTAMP '2021-01-04 00:00:00',
             9, 6, CAST(1.0 AS DECIMAL(3,2))),
            ('o2', 1, 'c2', 'p2', 's2', DATE '2021-01-02', 'delivered',
             CAST(200.00 AS DECIMAL(10,2)), CAST(20.00 AS DECIMAL(10,2)), CAST(220.00 AS DECIMAL(10,2)),
             TIMESTAMP '2021-01-02 11:00:00', TIMESTAMP '2021-01-05 14:00:00', TIMESTAMP '2021-01-08 00:00:00',
             3, -3, CAST(5.0 AS DECIMAL(3,2)))
        ) AS t(order_id, order_item_id, customer_id, product_id, seller_id, data_pedido, order_status,
               valor_produto, valor_frete, valor_total, order_purchase_timestamp, order_delivered_customer_date,
               order_estimated_delivery_date, lead_time_dias, atraso_entrega_dias, nota_avaliacao);
        """
    )


@pytest.mark.parametrize("query_name", QUERIES)
def test_queries_analiticas_execucao(query_name: str) -> None:
    """Verifica que cada query SQL analítica é sintaticamente válida e executa sem erros."""
    sql_file = SQL_DIR / f"{query_name}.sql"
    assert sql_file.exists(), f"Arquivo SQL não encontrado: {sql_file}"

    sql_content = sql_file.read_text(encoding="utf-8")
    with duckdb.connect(":memory:") as con:
        _criar_gold_amostra(con)
        res = con.execute(sql_content).fetchall()
        assert len(res) > 0, f"Query {query_name} não retornou linhas na amostra"


def test_otimizar_banco_gold_inexistente(tmp_path: Path) -> None:
    """Verifica erro ao tentar otimizar arquivo inexistente."""
    caminho_inexistente = tmp_path / "inexistente.db"
    with pytest.raises(FileNotFoundError, match="Banco Gold não encontrado"):
        otimizar_banco_gold(caminho_inexistente)


def test_otimizar_banco_gold_sucesso(tmp_path: Path) -> None:
    """Verifica criação de índices e atualização de estatísticas."""
    db_teste = tmp_path / "gold_teste.db"
    with duckdb.connect(str(db_teste)) as con:
        _criar_gold_amostra(con)
        total = criar_indices_gold(con)
        assert total == len(INDICES_GOLD)
        atualizar_estatisticas(con)

    total_otimizacao = otimizar_banco_gold(db_teste)
    assert total_otimizacao == len(INDICES_GOLD)
