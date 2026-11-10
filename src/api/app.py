"""Backend FastAPI para o Dashboard Executivo V-MAX e integração com MCP."""

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.api.intent_router import rotear_pergunta_executiva
from src.mcp.server import (
    SQLSecurityError,
    executar_consulta_segura,
    obter_schema_tabelas,
    run_query,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
SQL_DIR = Path(__file__).resolve().parents[1] / "sql"

app = FastAPI(
    title="V-MAX Executive Dashboard & MCP API",
    description="API analítica conectada ao banco DuckDB da camada Gold e servidor MCP nativo.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Payload para submissão de query SQL ad-hoc ao servidor MCP."""

    query: str = Field(..., description="Instrução SQL em modo leitura (SELECT/WITH).")


class NaturalLanguageQueryRequest(BaseModel):
    """Payload para envio de pergunta em linguagem natural."""

    pergunta: str = Field(
        ..., description="Pergunta de negócio formulada pelo usuário."
    )


def _ler_arquivo_sql(nome_arquivo: str, limit: int | None = None) -> str:
    """Lê um arquivo SQL presente no repositório de queries e opcionalmente aplica limite."""
    caminho = SQL_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {caminho}")
    conteudo = caminho.read_text(encoding="utf-8").strip()
    if conteudo.endswith(";"):
        conteudo = conteudo[:-1].strip()
    return f"{conteudo}\nLIMIT {limit};" if limit else f"{conteudo};"


@app.get("/api/schema")
def api_get_schema() -> dict[str, list[dict[str, str]]]:
    """Retorna a estrutura das tabelas da camada Gold consumindo a tool do MCP."""
    try:
        return obter_schema_tabelas()
    except (ValueError, KeyError, RuntimeError) as exc:
        logger.error("Erro ao obter schema via MCP: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/query")
def api_run_query(payload: QueryRequest) -> dict[str, Any]:
    """Valida e executa uma query SQL dinâmica no banco Gold através do servidor MCP."""
    try:
        resultado_str = run_query(payload.query)
        res_json = json.loads(resultado_str)
        if res_json.get("status") == "error":
            raise HTTPException(status_code=400, detail=res_json.get("mensagem"))
        return res_json
    except HTTPException:
        raise
    except SQLSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (ValueError, KeyError, RuntimeError) as exc:
        logger.error("Erro inesperado na execução da query: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/kpis")
def api_kpis_gerais() -> dict[str, Any]:
    """Retorna os indicadores consolidados de faturamento, pedidos e ticket médio."""
    sql = """
        SELECT
            ROUND(SUM(valor_total), 2) AS gmv_total,
            COUNT(DISTINCT order_id) AS total_pedidos,
            ROUND(SUM(valor_total) / COUNT(DISTINCT order_id), 2) AS ticket_medio_geral,
            ROUND(AVG(lead_time_dias), 1) AS lead_time_medio_dias
        FROM fato_vendas
        WHERE order_status NOT IN ('canceled', 'unavailable');
    """
    dados = executar_consulta_segura(sql)
    return dados[0] if dados else {}


@app.get("/api/analytics/gmv-categoria")
def api_gmv_por_categoria() -> list[dict[str, Any]]:
    """Retorna os dados analíticos de GMV e share por categoria de produto."""
    sql = _ler_arquivo_sql("gmv_por_categoria.sql")
    return executar_consulta_segura(sql)


@app.get("/api/analytics/evolucao-mensal")
def api_evolucao_mensal() -> list[dict[str, Any]]:
    """Retorna a série temporal mensal de faturamento e volume de pedidos."""
    sql = "SELECT ano_mes, receita_total, volume_pedidos, ticket_medio FROM kpi_sumario_mensal ORDER BY ano_mes;"
    return executar_consulta_segura(sql)


@app.get("/api/analytics/scorecard")
def api_scorecard_vendedores() -> list[dict[str, Any]]:
    """Retorna o ranking dos melhores vendedores avaliados."""
    sql = _ler_arquivo_sql("scorecard_vendedores.sql", limit=20)
    return executar_consulta_segura(sql)


@app.get("/api/analytics/risco-churn")
def api_risco_churn() -> list[dict[str, Any]]:
    """Retorna os pedidos críticos e clientes com maior propensão ao churn."""
    sql = _ler_arquivo_sql("risco_churn.sql", limit=50)
    return executar_consulta_segura(sql)


@app.post("/api/ask")
def api_pergunta_inteligente(payload: NaturalLanguageQueryRequest) -> dict[str, Any]:
    """Processa perguntas de negócio via roteador semântico sem vazamento de detalhes técnicos."""
    try:
        return rotear_pergunta_executiva(payload.pergunta)
    except (ValueError, KeyError, RuntimeError) as exc:
        logger.error("Falha no roteamento semântico: %s", exc)
        return {
            "sucesso": False,
            "resumo_executivo": "Não foi possível processar a pergunta solicitada.",
            "tipo_grafico": "table",
            "titulo_visualizacao": "Erro no Processamento",
            "colunas": ["Mensagem"],
            "dados": [[str(exc)]],
        }


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def get_index() -> FileResponse:
    """Serve a página principal do dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=404, detail="Frontend index.html não encontrado."
        )
    return FileResponse(str(index_file))
