"""Testes da Camada Gold: modelagem dimensional, lead time, KPI e integridade."""

import logging
from pathlib import Path

import duckdb
import pytest

from src.processing.gold_processing import (
    IntegridadeReferencialError,
    contar_orfaos,
    executar_pipeline_gold,
    ler_sql,
    validar_integridade_referencial,
)

PEDIDOS_SQL = """
CREATE TABLE olist_orders_dataset AS
SELECT * FROM (VALUES
    ('o1', 'c1', 'delivered', TIMESTAMP '2021-01-01 10:00:00',
     TIMESTAMP '2021-01-05 18:00:00', TIMESTAMP '2021-01-03 00:00:00'),
    ('o2', 'c2', 'shipped', TIMESTAMP '2021-01-10 09:00:00',
     NULL, TIMESTAMP '2021-01-20 00:00:00'),
    ('o3', 'c1', 'canceled', TIMESTAMP '2021-02-02 12:00:00',
     NULL, TIMESTAMP '2021-02-12 00:00:00')
) AS t(order_id, customer_id, order_status, order_purchase_timestamp,
       order_delivered_customer_date, order_estimated_delivery_date)
"""

ITENS_SQL = """
CREATE TABLE olist_order_items_dataset AS
SELECT order_id, order_item_id, product_id, seller_id,
       CAST(price AS DECIMAL(10,2)) AS price,
       CAST(freight_value AS DECIMAL(10,2)) AS freight_value
FROM (VALUES
    ('o1', 1, 'p1', 's1', '100.00', '10.00'),
    ('o1', 2, '{produto_o1_item2}', 's1', '50.00', '5.00'),
    ('o2', 1, 'p2', 's2', '200.00', '20.00'),
    ('o3', 1, 'p2', 's2', '999.00', '1.00')
) AS t(order_id, order_item_id, product_id, seller_id, price, freight_value)
"""

DEMAIS_TABELAS_SQL = [
    """CREATE TABLE olist_order_reviews_dataset AS
       SELECT * FROM (VALUES ('o1', 5), ('o1', 4), ('o2', 1))
       AS t(order_id, review_score)""",
    """CREATE TABLE olist_customers_dataset AS
       SELECT * FROM (VALUES ('c1', 'u1', '01310', 'sao paulo', 'SP'),
                             ('c2', 'u2', '20000', 'rio de janeiro', 'RJ'))
       AS t(customer_id, customer_unique_id, customer_zip_code_prefix,
            customer_city, customer_state)""",
    """CREATE TABLE olist_products_dataset AS
       SELECT * FROM (VALUES ('p1', 'perfumaria', 1, 100, 10, 10, 10),
                             ('p2', NULL, 1, 200, 20, 20, 20))
       AS t(product_id, product_category_name, product_photos_qty,
            product_weight_g, product_length_cm, product_height_cm,
            product_width_cm)""",
    """CREATE TABLE olist_sellers_dataset AS
       SELECT * FROM (VALUES ('s1', '13000', 'campinas', 'SP'),
                             ('s2', '30000', 'belo horizonte', 'MG'))
       AS t(seller_id, seller_zip_code_prefix, seller_city, seller_state)""",
    """CREATE TABLE product_category_name_translation AS
       SELECT * FROM (VALUES ('perfumaria', 'perfumery'))
       AS t(product_category_name, product_category_name_english)""",
]


def criar_silver_teste(caminho: Path, produto_o1_item2: str = "p1") -> Path:
    """Cria um banco Silver mínimo e determinístico para os testes.

    Args:
        caminho: Caminho do arquivo DuckDB a ser criado.
        produto_o1_item2: product_id do 2º item do pedido o1 (permite
            injetar uma chave órfã).

    Returns:
        Caminho do banco criado.
    """
    with duckdb.connect(str(caminho)) as con:
        con.execute(PEDIDOS_SQL)
        con.execute(ITENS_SQL.format(produto_o1_item2=produto_o1_item2))
        for sql in DEMAIS_TABELAS_SQL:
            con.execute(sql)
    return caminho


@pytest.fixture
def gold_db(tmp_path: Path) -> Path:
    """Executa o pipeline Gold completo sobre a Silver de teste."""
    silver = criar_silver_teste(tmp_path / "silver.db")
    gold = tmp_path / "gold.db"
    executar_pipeline_gold(silver_db_path=silver, gold_db_path=gold)
    return gold


def test_ler_sql_existente_e_inexistente(tmp_path: Path) -> None:
    """Lê um modelo existente e falha para um arquivo inexistente."""
    assert "CREATE OR REPLACE TABLE fato_vendas" in ler_sql("fato_vendas")
    with pytest.raises(FileNotFoundError, match="Arquivo SQL não encontrado"):
        ler_sql("nao_existe", sql_dir=tmp_path)


def test_pipeline_sem_banco_silver(tmp_path: Path) -> None:
    """Dispara FileNotFoundError se a Silver não existir."""
    with pytest.raises(FileNotFoundError, match="Banco Silver não encontrado"):
        executar_pipeline_gold(
            silver_db_path=tmp_path / "x.db", gold_db_path=tmp_path / "g.db"
        )


def test_pipeline_cria_todos_os_modelos(gold_db: Path) -> None:
    """Todas as tabelas dimensionais, a fato e o KPI são criados."""
    with duckdb.connect(str(gold_db), read_only=True) as con:
        tabelas = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        assert tabelas == {
            "dim_clientes",
            "dim_produtos",
            "dim_vendedores",
            "dim_tempo",
            "fato_vendas",
            "kpi_sumario_mensal",
        }
        assert con.execute("SELECT COUNT(*) FROM fato_vendas").fetchone()[0] == 4


def test_lead_time_e_atraso_calculados(gold_db: Path) -> None:
    """Lead time = compra→entrega em dias; nulo se não entregue."""
    with duckdb.connect(str(gold_db), read_only=True) as con:
        linhas = dict(
            con.execute(
                "SELECT order_id, lead_time_dias FROM fato_vendas "
                "WHERE order_item_id = 1"
            ).fetchall()
        )
        assert linhas == {"o1": 4, "o2": None, "o3": None}
        atraso = con.execute(
            "SELECT DISTINCT atraso_entrega_dias FROM fato_vendas WHERE order_id = 'o1'"
        ).fetchone()[0]
        assert atraso == 2


def test_valor_total_e_nota_media(gold_db: Path) -> None:
    """valor_total = produto + frete; nota = média das avaliações do pedido."""
    with duckdb.connect(str(gold_db), read_only=True) as con:
        valor, nota = con.execute(
            "SELECT valor_total, nota_avaliacao FROM fato_vendas "
            "WHERE order_id = 'o1' AND order_item_id = 1"
        ).fetchone()
        assert str(valor) == "110.00"
        assert str(nota) == "4.50"


def test_kpi_sumario_mensal_exclui_cancelados(gold_db: Path) -> None:
    """Receita, volume e ticket médio por mês, sem pedidos cancelados."""
    with duckdb.connect(str(gold_db), read_only=True) as con:
        kpis = con.execute(
            "SELECT ano_mes, receita_total, volume_pedidos, ticket_medio "
            "FROM kpi_sumario_mensal ORDER BY ano_mes"
        ).fetchall()
    assert len(kpis) == 1
    ano_mes, receita, volume, ticket = kpis[0]
    assert ano_mes == "2021-01"
    assert str(receita) == "385.00"
    assert volume == 2
    assert str(ticket) == "192.50"


def test_dim_tempo_continua_e_dim_produtos_sem_nulos(gold_db: Path) -> None:
    """dim_tempo cobre todos os dias; categorias nulas recebem padrão."""
    with duckdb.connect(str(gold_db), read_only=True) as con:
        dias = con.execute("SELECT COUNT(*) FROM dim_tempo").fetchone()[0]
        assert dias == 33  # 2021-01-01 até 2021-02-02
        categorias = dict(
            con.execute(
                "SELECT product_id, product_category_name_english FROM dim_produtos"
            ).fetchall()
        )
        assert categorias == {"p1": "perfumery", "p2": "not_informed"}


def test_validar_integridade_dispara_excecao_e_loga(
    gold_db: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Uma chave órfã na fato gera exceção e log de erro."""
    with duckdb.connect(str(gold_db)) as con:
        con.execute(
            "INSERT INTO fato_vendas (order_id, order_item_id, customer_id, "
            "product_id, seller_id, data_pedido) "
            "VALUES ('o9', 1, 'c_inexistente', 'p1', 's1', DATE '2021-01-01')"
        )
        assert contar_orfaos(con, "customer_id", "dim_clientes", "customer_id") == 1
        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(IntegridadeReferencialError, match="dim_clientes: 1"),
        ):
            validar_integridade_referencial(con)
    assert "Falha de integridade referencial" in caplog.text


def test_pipeline_reverte_transacao_quando_integridade_falha(tmp_path: Path) -> None:
    """Com produto órfão na Silver, o pipeline falha e não grava a Gold."""
    silver = criar_silver_teste(tmp_path / "silver.db", produto_o1_item2="p_orfao")
    gold = tmp_path / "gold.db"
    with pytest.raises(IntegridadeReferencialError, match="dim_produtos: 1"):
        executar_pipeline_gold(silver_db_path=silver, gold_db_path=gold)
    with duckdb.connect(str(gold), read_only=True) as con:
        assert con.execute("SHOW TABLES").fetchall() == []


def test_contar_orfaos_rejeita_identificador_invalido(gold_db: Path) -> None:
    """Identificadores com caracteres perigosos são rejeitados."""
    with (
        duckdb.connect(str(gold_db), read_only=True) as con,
        pytest.raises(ValueError, match="Identificador SQL inválido"),
    ):
        contar_orfaos(con, "customer_id; DROP TABLE x", "dim_clientes", "id")
