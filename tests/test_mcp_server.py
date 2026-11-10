"""Testes unitários para o Servidor MCP DuckDB Gold."""

import json
from pathlib import Path

import duckdb
import pytest

from src.mcp.server import (
    SQLSecurityError,
    _conectar_gold,
    executar_consulta_segura,
    get_schema,
    obter_schema_tabelas,
    run_query,
    validar_apenas_select,
)


def _criar_banco_gold_minimo(db_path: Path) -> None:
    """Cria um banco Gold temporário para testes das ferramentas MCP."""
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            """
            CREATE TABLE dim_clientes AS
            SELECT 'c1' AS customer_id, 'sao paulo' AS customer_city;
            """
        )
        con.execute(
            """
            CREATE TABLE fato_vendas AS
            SELECT 'o1' AS order_id, 'c1' AS customer_id, CAST(150.50 AS DECIMAL(10,2)) AS valor_total;
            """
        )


def test_validar_apenas_select_permitidos() -> None:
    """Verifica que consultas SELECT, WITH, DESCRIBE e EXPLAIN são aceitas."""
    validar_apenas_select("SELECT * FROM fato_vendas;")
    validar_apenas_select("WITH cte AS (SELECT 1) SELECT * FROM cte;")
    validar_apenas_select("DESCRIBE fato_vendas;")
    validar_apenas_select("-- comentario inicial\nSELECT COUNT(*) FROM dim_clientes;")


@pytest.mark.parametrize(
    "query_invalida",
    [
        "",
        "   ",
        "DROP TABLE fato_vendas;",
        "INSERT INTO dim_clientes VALUES ('x', 'y');",
        "UPDATE fato_vendas SET valor_total = 0;",
        "DELETE FROM dim_clientes;",
        "ALTER TABLE dim_clientes ADD COLUMN teste INT;",
        "SELECT * FROM fato_vendas; DROP TABLE fato_vendas;",
        "ATTACH 'outro.db' AS db;",
    ],
)
def test_validar_apenas_select_rejeita_mutacoes(query_invalida: str) -> None:
    """Garante que qualquer instrução com mutação ou DDL seja rejeitada com SQLSecurityError."""
    with pytest.raises(SQLSecurityError):
        validar_apenas_select(query_invalida)


def test_conectar_gold_inexistente(tmp_path: Path) -> None:
    """Verifica erro ao conectar em banco inexistente."""
    caminho = tmp_path / "nao_existe.db"
    with pytest.raises(FileNotFoundError, match="Banco Gold não encontrado"):
        _conectar_gold(caminho)


def test_obter_schema_tabelas(tmp_path: Path) -> None:
    """Verifica a extração de esquemas das tabelas da Gold."""
    db_path = tmp_path / "gold_mcp.db"
    _criar_banco_gold_minimo(db_path)

    schemas = obter_schema_tabelas(db_path)
    assert "dim_clientes" in schemas
    assert "fato_vendas" in schemas
    cols_fato = [c["coluna"] for c in schemas["fato_vendas"]]
    assert "order_id" in cols_fato
    assert "valor_total" in cols_fato


def test_executar_consulta_segura(tmp_path: Path) -> None:
    """Verifica execução de query segura com serialização correta."""
    db_path = tmp_path / "gold_mcp.db"
    _criar_banco_gold_minimo(db_path)

    resultado = executar_consulta_segura(
        "SELECT customer_id, valor_total FROM fato_vendas", db_path
    )
    assert len(resultado) == 1
    assert resultado[0]["customer_id"] == "c1"
    assert resultado[0]["valor_total"] == 150.50


def test_tools_mcp_formato_json(tmp_path: Path) -> None:
    """Testa os wrappers de tools get_schema e run_query expostos pelo servidor MCP."""
    db_path = tmp_path / "gold_mcp.db"
    _criar_banco_gold_minimo(db_path)

    schema_json = get_schema(db_path=db_path)
    schema_dict = json.loads(schema_json)
    assert "dim_clientes" in schema_dict

    res_sucesso = json.loads(
        run_query("SELECT COUNT(*) AS total FROM dim_clientes", db_path=db_path)
    )
    assert res_sucesso["status"] == "success"
    assert res_sucesso["dados"][0]["total"] == 1

    res_erro = json.loads(run_query("DROP TABLE dim_clientes", db_path=db_path))
    assert res_erro["status"] == "error"
    assert (
        "Operação não permitida" in res_erro["mensagem"]
        or "proibidos" in res_erro["mensagem"]
    )
