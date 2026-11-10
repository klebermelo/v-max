"""Orquestrador da Camada Gold (modelagem dimensional) do projeto V-MAX.

Lê as tabelas higienizadas de `data/silver/silver.db`, executa os modelos SQL
de `src/sql/gold/` (dimensões, fato e KPI mensal), valida a integridade
referencial entre a fato e as dimensões e persiste o resultado em
`data/gold/gold.db`. Toda a construção ocorre dentro de uma transação: se a
validação falhar, nada é gravado e uma exceção é disparada.
"""

import logging
import re
from pathlib import Path

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SILVER_DB_PATH = Path("data/silver/silver.db")
GOLD_DB_PATH = Path("data/gold/gold.db")
SQL_GOLD_DIR = Path(__file__).resolve().parents[1] / "sql" / "gold"

ORDEM_MODELOS: tuple[str, ...] = (
    "dim_clientes",
    "dim_produtos",
    "dim_vendedores",
    "dim_tempo",
    "fato_vendas",
    "kpi_sumario_mensal",
)

CHAVES_ESTRANGEIRAS: tuple[tuple[str, str, str], ...] = (
    ("customer_id", "dim_clientes", "customer_id"),
    ("product_id", "dim_produtos", "product_id"),
    ("seller_id", "dim_vendedores", "seller_id"),
    ("data_pedido", "dim_tempo", "data"),
)

IDENTIFICADOR_VALIDO = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class IntegridadeReferencialError(Exception):
    """Disparada quando a fato possui chaves sem correspondência nas dimensões."""


def ler_sql(nome_modelo: str, sql_dir: Path = SQL_GOLD_DIR) -> str:
    """Lê o conteúdo de um arquivo `.sql` de modelo da Camada Gold.

    Args:
        nome_modelo: Nome do modelo (arquivo sem a extensão `.sql`).
        sql_dir: Diretório onde ficam os arquivos SQL da Gold.

    Returns:
        Texto SQL do modelo.

    Raises:
        FileNotFoundError: Se o arquivo SQL não existir.
    """
    caminho = sql_dir / f"{nome_modelo}.sql"
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {caminho}")
    return caminho.read_text(encoding="utf-8")


def _validar_identificador(nome: str) -> str:
    """Garante que um nome de tabela/coluna é um identificador SQL seguro.

    Args:
        nome: Identificador a ser validado.

    Returns:
        O próprio identificador, se válido.

    Raises:
        ValueError: Se o identificador contiver caracteres não permitidos.
    """
    if not IDENTIFICADOR_VALIDO.match(nome):
        raise ValueError(f"Identificador SQL inválido: {nome}")
    return nome


def criar_modelo(
    con: duckdb.DuckDBPyConnection,
    nome_modelo: str,
    sql_dir: Path = SQL_GOLD_DIR,
) -> int:
    """Executa o SQL de um modelo Gold e retorna a quantidade de registros.

    Args:
        con: Conexão DuckDB com o banco Gold (com a Silver anexada como `silver`).
        nome_modelo: Nome do modelo/tabela a ser criado.
        sql_dir: Diretório onde ficam os arquivos SQL da Gold.

    Returns:
        Quantidade de registros da tabela criada.
    """
    tabela = _validar_identificador(nome_modelo)
    logger.info("Construindo modelo Gold: %s", tabela)
    con.execute(ler_sql(tabela, sql_dir))
    resultado = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()
    total = resultado[0] if resultado else 0
    logger.info("Modelo concluído: %s (%d registros)", tabela, total)
    return total


def contar_orfaos(
    con: duckdb.DuckDBPyConnection,
    coluna_fato: str,
    dimensao: str,
    chave_dimensao: str,
    tabela_fato: str = "fato_vendas",
) -> int:
    """Conta registros da fato cuja chave é nula ou inexistente na dimensão.

    Args:
        con: Conexão DuckDB com o banco Gold.
        coluna_fato: Coluna de chave estrangeira na tabela fato.
        dimensao: Nome da tabela de dimensão.
        chave_dimensao: Coluna de chave primária na dimensão.
        tabela_fato: Nome da tabela fato.

    Returns:
        Quantidade de registros órfãos.
    """
    fk, dim, pk, fato = (
        _validar_identificador(n)
        for n in (coluna_fato, dimensao, chave_dimensao, tabela_fato)
    )
    consulta = f"""
        SELECT COUNT(*) FROM {fato} AS f
        WHERE f.{fk} IS NULL
           OR NOT EXISTS (SELECT 1 FROM {dim} AS d WHERE d.{pk} = f.{fk})
    """
    resultado = con.execute(consulta).fetchone()
    return resultado[0] if resultado else 0


def validar_integridade_referencial(con: duckdb.DuckDBPyConnection) -> None:
    """Verifica se todas as chaves da fato existem nas respectivas dimensões.

    Args:
        con: Conexão DuckDB com o banco Gold.

    Raises:
        IntegridadeReferencialError: Se houver qualquer chave órfã ou nula.
    """
    violacoes: list[str] = []
    for coluna_fato, dimensao, chave_dimensao in CHAVES_ESTRANGEIRAS:
        orfaos = contar_orfaos(con, coluna_fato, dimensao, chave_dimensao)
        if orfaos > 0:
            violacoes.append(f"fato_vendas.{coluna_fato} -> {dimensao}: {orfaos}")
        logger.info(
            "Integridade fato_vendas.%s -> %s.%s: %d órfãos",
            coluna_fato,
            dimensao,
            chave_dimensao,
            orfaos,
        )
    if violacoes:
        mensagem = "Falha de integridade referencial: " + "; ".join(violacoes)
        logger.error(mensagem)
        raise IntegridadeReferencialError(mensagem)
    logger.info("Integridade referencial validada com sucesso.")


def _construir_modelos_em_transacao(
    con: duckdb.DuckDBPyConnection, sql_dir: Path
) -> dict[str, int]:
    """Constrói os modelos Gold e valida a integridade numa única transação.

    Se qualquer etapa falhar (inclusive a validação de integridade), a
    transação é revertida e nenhum modelo é gravado.

    Args:
        con: Conexão DuckDB com o banco Gold (com a Silver anexada).
        sql_dir: Diretório onde ficam os arquivos SQL da Gold.

    Returns:
        Dicionário com a quantidade de registros por modelo.

    Raises:
        IntegridadeReferencialError: Se a validação de integridade falhar.
    """
    con.execute("BEGIN TRANSACTION")
    try:
        totais = {nome: criar_modelo(con, nome, sql_dir) for nome in ORDEM_MODELOS}
        validar_integridade_referencial(con)
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        logger.error("Pipeline Gold abortado; alterações revertidas.")
        raise
    return totais


def executar_pipeline_gold(
    silver_db_path: Path = SILVER_DB_PATH,
    gold_db_path: Path = GOLD_DB_PATH,
    sql_dir: Path = SQL_GOLD_DIR,
) -> dict[str, int]:
    """Executa a modelagem dimensional completa da Silver para a Gold.

    Args:
        silver_db_path: Caminho do banco DuckDB da Camada Silver.
        gold_db_path: Caminho de destino do banco DuckDB da Camada Gold.
        sql_dir: Diretório onde ficam os arquivos SQL da Gold.

    Returns:
        Dicionário com a quantidade de registros por modelo.

    Raises:
        FileNotFoundError: Se o banco Silver não existir.
        IntegridadeReferencialError: Se a validação de integridade falhar.
    """
    if not silver_db_path.exists():
        raise FileNotFoundError(f"Banco Silver não encontrado: {silver_db_path}")
    gold_db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Pipeline Gold | Origem: %s | Destino: %s", silver_db_path, gold_db_path
    )

    with duckdb.connect(str(gold_db_path)) as con:
        con.execute("ATTACH ? AS silver (READ_ONLY)", [str(silver_db_path)])
        try:
            totais = _construir_modelos_em_transacao(con, sql_dir)
        finally:
            con.execute("DETACH silver")

    logger.info("Pipeline Gold finalizado com sucesso (%d modelos).", len(totais))
    return totais


if __name__ == "__main__":
    executar_pipeline_gold()
