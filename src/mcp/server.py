"""Servidor MCP Nativo (Model Context Protocol) para exploração da Camada Gold.

Disponibiliza tools para assistentes de IA realizarem inspeção de schemas (DDL)
e execução controlada de consultas analíticas ad-hoc no banco DuckDB `gold.db`.
"""

import json
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb
from mcp.server.mcpserver import MCPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

GOLD_DB_PATH = Path("data/gold/gold.db")
server = MCPServer("v-max-gold-mcp")

DML_DDL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|ATTACH|DETACH|EXECUTE)\b",
    re.IGNORECASE,
)


class SQLSecurityError(ValueError):
    """Exceção levantada quando uma consulta não autorizada ou mutativa é submetida."""


def _conectar_gold(db_path: Path = GOLD_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Abre conexão estritamente em modo leitura com o banco da camada Gold.

    Args:
        db_path: Caminho do arquivo DuckDB da Gold.

    Returns:
        Conexão ativa em modo READ_ONLY.

    Raises:
        FileNotFoundError: Se o banco gold.db não for encontrado.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Banco Gold não encontrado: {db_path}")
    return duckdb.connect(str(db_path), read_only=True)


def _serializar_valor(valor: Any) -> Any:
    """Serializa tipos não-nativos para representações JSON válidas."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def validar_apenas_select(query: str) -> None:
    """Valida se uma consulta SQL é estritamente de leitura (SELECT / WITH).

    Args:
        query: Consulta SQL a ser avaliada.

    Raises:
        SQLSecurityError: Se a query for vazia, não iniciar com SELECT/WITH ou
            contiver palavras-chave de mutação (DROP, INSERT, DELETE, etc.).
    """
    query_limpa = query.strip()
    if not query_limpa:
        raise SQLSecurityError("Consulta SQL vazia não permitida.")

    query_sem_comentarios = re.sub(
        r"--.*?$|/\*.*?\*/", "", query_limpa, flags=re.MULTILINE | re.DOTALL
    ).strip()
    primeira_palavra = (
        query_sem_comentarios.split()[0].upper() if query_sem_comentarios else ""
    )

    if primeira_palavra not in ("SELECT", "WITH", "DESCRIBE", "EXPLAIN"):
        raise SQLSecurityError(
            f"Operação não permitida: '{primeira_palavra}'. Apenas consultas SELECT são autorizadas."
        )

    if DML_DDL_PATTERN.search(query_sem_comentarios):
        raise SQLSecurityError(
            "Consulta contém comandos de modificação ou DDL proibidos."
        )


def obter_schema_tabelas(
    db_path: Path = GOLD_DB_PATH,
) -> dict[str, list[dict[str, str]]]:
    """Inspeciona o catálogo da Camada Gold e retorna a estrutura de cada tabela.

    Args:
        db_path: Caminho do banco DuckDB da Gold.

    Returns:
        Dicionário com nomes de tabelas mapeados para suas respectivas colunas e tipos.
    """
    logger.info("Executando tool: get_schema")
    with _conectar_gold(db_path) as con:
        tabelas = [r[0] for r in con.execute("SHOW TABLES;").fetchall()]
        schemas: dict[str, list[dict[str, str]]] = {}
        for tabela in tabelas:
            colunas = con.execute(f"DESCRIBE {tabela};").fetchall()
            schemas[tabela] = [
                {"coluna": col[0], "tipo": col[1], "nulo": col[2]} for col in colunas
            ]
    return schemas


def executar_consulta_segura(
    query: str, db_path: Path = GOLD_DB_PATH
) -> list[dict[str, Any]]:
    """Executa com segurança uma consulta SELECT e retorna os registros como lista de dicionários.

    Args:
        query: Query SQL a ser executada.
        db_path: Caminho do banco DuckDB da Gold.

    Returns:
        Lista de registros serializados.
    """
    validar_apenas_select(query)
    logger.info("Executando tool: run_query | SQL: %s", query[:100])
    with _conectar_gold(db_path) as con:
        resultado = con.execute(query).fetchall()
        colunas = [c[0] for c in con.description] if con.description else []
        return [
            {colunas[i]: _serializar_valor(row[i]) for i in range(len(colunas))}
            for row in resultado
        ]


@server.tool()
def get_schema(db_path: Path | None = None) -> str:
    """Retorna o esquema descritivo (DDL/colunas/tipos) das tabelas da Camada Gold."""
    caminho = db_path if db_path is not None else GOLD_DB_PATH
    return json.dumps(obter_schema_tabelas(caminho), indent=2, ensure_ascii=False)


@server.tool()
def run_query(query: str, db_path: Path | None = None) -> str:
    """Executa uma consulta SQL read-only no banco Gold e retorna o resultado em formato JSON."""
    caminho = db_path if db_path is not None else GOLD_DB_PATH
    try:
        dados = executar_consulta_segura(query, caminho)
        return json.dumps(
            {"status": "success", "total_linhas": len(dados), "dados": dados},
            ensure_ascii=False,
        )
    except (SQLSecurityError, duckdb.Error, ValueError) as exc:
        logger.warning("Falha ao executar query via MCP: %s", exc)
        return json.dumps({"status": "error", "mensagem": str(exc)}, ensure_ascii=False)


def run_server() -> None:
    """Inicia o servidor MCP via standard input/output para integração nativa com IAs."""
    logger.info("Iniciando Servidor MCP DuckDB Gold via stdio transport...")
    server.run(transport="stdio")


if __name__ == "__main__":
    run_server()
