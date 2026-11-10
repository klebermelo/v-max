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
    version="0.3.0",
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

    pergunta: str | None = Field(
        default=None, description="Pergunta de negócio formulada pelo usuário."
    )
    message: str | None = Field(
        default=None, description="Mensagem alternativa de consulta."
    )

    def obter_texto(self) -> str:
        """Obtém o texto sanitizado da pergunta."""
        return (self.pergunta or self.message or "").strip()


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
def api_kpis_gerais(ano: str | None = None, mes: str | None = None) -> dict[str, Any]:
    """Retorna os indicadores consolidados com filtro opcional de ano e mês."""
    condicoes = ["f.order_status NOT IN ('canceled', 'unavailable')"]
    params: list[Any] = []
    if ano:
        condicoes.append("STRFTIME(TRY_CAST(t.data AS DATE), '%Y') = ?")
        params.append(ano)
    if mes:
        condicoes.append("STRFTIME(TRY_CAST(t.data AS DATE), '%m') = ?")
        params.append(mes.zfill(2))

    where_clause = " AND ".join(condicoes)
    sql = f"""
        SELECT
            ROUND(SUM(f.valor_total), 2) AS gmv_total,
            COUNT(DISTINCT f.order_id) AS total_pedidos,
            ROUND(COALESCE(SUM(f.valor_total) / NULLIF(COUNT(DISTINCT f.order_id), 0), 0), 2) AS ticket_medio_geral,
            ROUND(AVG(f.lead_time_dias), 1) AS lead_time_medio_dias
        FROM fato_vendas AS f
        INNER JOIN dim_tempo AS t ON f.data_pedido = t.data
        WHERE {where_clause};
    """
    dados = executar_consulta_segura(sql, params=params if params else None)
    return (
        dados[0]
        if dados
        else {
            "gmv_total": 0.0,
            "total_pedidos": 0,
            "ticket_medio_geral": 0.0,
            "lead_time_medio_dias": 0.0,
        }
    )


@app.get("/api/comparativo/anual")
def api_comparativo_anual() -> list[dict[str, Any]]:
    """Retorna a matriz comparativa mensal de faturamento e volume entre os anos."""
    sql = _ler_arquivo_sql("comparativo_anual_mensal.sql")
    return executar_consulta_segura(sql)


@app.get("/api/metricas/uf")
def api_metricas_por_uf(ano: str | None = None) -> list[dict[str, Any]]:
    """Retorna métricas completas agregadas por estado com filtro opcional de ano."""
    sql = _ler_arquivo_sql("metricas_por_estado.sql")
    return executar_consulta_segura(sql, params=[ano, ano])


@app.get("/api/analytics/regioes")
def api_pedidos_por_regiao(ano: str | None = None) -> list[dict[str, Any]]:
    """Retorna faturamento e pedidos por macrorregião com filtro de ano."""
    sql = _ler_arquivo_sql("pedidos_por_regiao.sql")
    return executar_consulta_segura(sql, params=[ano, ano])


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


def _processar_pergunta_semantica(texto: str) -> dict[str, Any]:
    """Processa perguntas de negócio via roteador semântico sem vazamento técnico."""
    if not texto:
        return {
            "sucesso": False,
            "resumo_executivo": "Nenhuma pergunta foi enviada.",
            "tipo_grafico": "table",
            "titulo_visualizacao": "Consulta Vazia",
            "colunas": ["Mensagem"],
            "dados": [["Por favor, digite uma pergunta de negócio."]],
        }
    try:
        return rotear_pergunta_executiva(texto)
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


@app.post("/api/ask")
def api_pergunta_inteligente(
    payload: NaturalLanguageQueryRequest,
) -> dict[str, Any]:
    """Endpoint legado/compatível para perguntas executivas inteligentes."""
    return _processar_pergunta_semantica(payload.obter_texto())


@app.post("/api/chat")
def api_chat_executivo(
    payload: NaturalLanguageQueryRequest,
) -> dict[str, Any]:
    """Endpoint de chat executivo integrado com o servidor MCP e DuckDB."""
    return _processar_pergunta_semantica(payload.obter_texto())


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
