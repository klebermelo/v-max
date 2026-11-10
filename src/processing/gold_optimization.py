"""Módulo de otimização e indexação da Camada Gold para aceleração do MCP.

Cria índices em chaves primárias e estrangeiras frequentemente consultadas
e executa ANALYZE para atualizar as estatísticas do otimizador DuckDB (CBO).
"""

import logging
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

GOLD_DB_PATH = Path("data/gold/gold.db")

INDICES_GOLD: tuple[tuple[str, str, str], ...] = (
    ("idx_fato_vendas_pedido", "fato_vendas", "order_id"),
    ("idx_fato_vendas_cliente", "fato_vendas", "customer_id"),
    ("idx_fato_vendas_produto", "fato_vendas", "product_id"),
    ("idx_fato_vendas_vendedor", "fato_vendas", "seller_id"),
)


def criar_indice(
    con: duckdb.DuckDBPyConnection,
    nome_indice: str,
    tabela: str,
    coluna: str,
) -> None:
    """Cria um índice em uma tabela da Gold caso ele ainda não exista.

    Args:
        con: Conexão ativa com o banco DuckDB.
        nome_indice: Nome identificador do índice.
        tabela: Nome da tabela de destino.
        coluna: Coluna a ser indexada.
    """
    logger.info("Criando índice %s na tabela %s(%s)", nome_indice, tabela, coluna)
    con.execute(f"CREATE INDEX IF NOT EXISTS {nome_indice} ON {tabela}({coluna});")


def criar_indices_gold(con: duckdb.DuckDBPyConnection) -> int:
    """Cria o conjunto completo de índices pré-definidos na camada Gold.

    Args:
        con: Conexão ativa com o banco DuckDB.

    Returns:
        Total de índices processados.
    """
    for nome_idx, tabela, coluna in INDICES_GOLD:
        criar_indice(con, nome_idx, tabela, coluna)
    logger.info("Todos os %d índices da Gold foram processados.", len(INDICES_GOLD))
    return len(INDICES_GOLD)


def atualizar_estatisticas(con: duckdb.DuckDBPyConnection) -> None:
    """Executa o comando ANALYZE para atualizar as estatísticas de custo do DuckDB.

    Args:
        con: Conexão ativa com o banco DuckDB.
    """
    logger.info("Executando ANALYZE para otimização de consultas...")
    con.execute("ANALYZE;")
    logger.info("Estatísticas atualizadas com sucesso.")


def otimizar_banco_gold(gold_db_path: Path = GOLD_DB_PATH) -> int:
    """Conecta ao banco Gold, aplica índices e atualiza estatísticas do CBO.

    Args:
        gold_db_path: Caminho para o banco DuckDB da camada Gold.

    Returns:
        Quantidade total de índices criados/garantidos.

    Raises:
        FileNotFoundError: Caso o arquivo gold.db não exista.
    """
    if not gold_db_path.exists():
        raise FileNotFoundError(f"Banco Gold não encontrado: {gold_db_path}")

    logger.info("Iniciando processo de otimização em %s", gold_db_path)
    with duckdb.connect(str(gold_db_path)) as con:
        total_indices = criar_indices_gold(con)
        atualizar_estatisticas(con)

    logger.info("Otimização da Camada Gold concluída com sucesso.")
    return total_indices


if __name__ == "__main__":
    otimizar_banco_gold()
