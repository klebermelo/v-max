"""Módulo de criação da Camada Semântica de Views em Português no DuckDB.

Cria views com nomes amigáveis em português sem sobrecarga de armazenamento físico,
preservando a rastreabilidade das tabelas originais da Camada Silver e Gold.
"""

import logging
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SILVER_DB_PATH = Path("data/silver/silver.db")
GOLD_DB_PATH = Path("data/gold/gold.db")

MAPA_VIEWS_SEMANTICAS: dict[str, str] = {
    "pedidos": "olist_orders_dataset",
    "itens_pedido": "olist_order_items_dataset",
    "pagamentos": "olist_order_payments_dataset",
    "avaliacoes": "olist_order_reviews_dataset",
    "clientes": "olist_customers_dataset",
    "vendedores": "olist_sellers_dataset",
    "produtos": "olist_products_dataset",
    "traducao_categorias": "product_category_name_translation",
    "geolocalizacao": "olist_geolocation_dataset",
}


def criar_view_semantica(
    con: duckdb.DuckDBPyConnection,
    nome_view: str,
    tabela_origem: str,
) -> None:
    """Cria uma view semântica apontando para a tabela física de origem."""
    logger.info("Criando view semântica '%s' -> '%s'", nome_view, tabela_origem)
    con.execute(f"CREATE OR REPLACE VIEW {nome_view} AS SELECT * FROM {tabela_origem};")


def criar_todas_views_semanticas(con: duckdb.DuckDBPyConnection) -> int:
    """Cria o conjunto completo de 9 views semânticas na conexão ativa."""
    con.execute("BEGIN TRANSACTION;")
    try:
        for nome_view, tabela_origem in MAPA_VIEWS_SEMANTICAS.items():
            criar_view_semantica(con, nome_view, tabela_origem)
        con.execute("COMMIT;")
        logger.info(
            "Todas as %d views semânticas foram criadas.", len(MAPA_VIEWS_SEMANTICAS)
        )
        return len(MAPA_VIEWS_SEMANTICAS)
    except Exception as exc:
        con.execute("ROLLBACK;")
        logger.error("Falha ao criar views semânticas: %s", exc)
        raise


def executar_camada_semantica(silver_path: Path = SILVER_DB_PATH) -> int:
    """Aplica a camada semântica de views no banco Silver DuckDB."""
    if not silver_path.exists():
        raise FileNotFoundError(f"Banco Silver não encontrado: {silver_path}")

    logger.info("Iniciando camada semântica em %s", silver_path)
    with duckdb.connect(str(silver_path)) as con_silver:
        total = criar_todas_views_semanticas(con_silver)

    logger.info("Camada semântica concluída com sucesso.")
    return total


if __name__ == "__main__":
    executar_camada_semantica()
