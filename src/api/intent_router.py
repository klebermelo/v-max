"""Módulo de roteamento semântico de intenções analíticas para o Assistente Executivo.

Interpreta perguntas em linguagem natural, seleciona a consulta SQL analítica
adequada, executa no banco Gold e formata o payload executivo para o frontend.
"""

import json
import logging
import re
from typing import Any

from src.mcp.server import run_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _executar_query_mcp(sql: str) -> list[dict[str, Any]]:
    """Executa SQL via ferramenta run_query do servidor MCP e retorna lista de registros."""
    res_raw = run_query(sql)
    res_json = json.loads(res_raw)
    if res_json.get("status") == "error":
        raise ValueError(res_json.get("mensagem", "Erro na execução SQL"))
    return res_json.get("dados", [])


def _tratar_intencao_geografica() -> dict[str, Any]:
    """Processa consultas sobre distribuição geográfica e ranking de vendas por UF/estado."""
    sql = """
        SELECT
            c.customer_state AS estado,
            ROUND(SUM(f.valor_total), 2) AS faturamento,
            COUNT(DISTINCT f.order_id) AS qtd_pedidos
        FROM fato_vendas AS f
        INNER JOIN dim_clientes AS c ON f.customer_id = c.customer_id
        WHERE f.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY c.customer_state
        ORDER BY faturamento DESC
        LIMIT 10;
    """
    dados = _executar_query_mcp(sql)
    top_uf = dados[0]["estado"] if dados else "N/A"
    top_fat = dados[0]["faturamento"] if dados else 0
    return {
        "sucesso": True,
        "resumo_executivo": f"O estado de {top_uf} lidera o ranking nacional com R$ {top_fat:,.2f} faturados.",
        "tipo_grafico": "bar",
        "titulo_visualizacao": "Top 10 Estados (UF) por Faturamento (R$)",
        "colunas": ["Estado", "Faturamento (R$)", "Qtd Pedidos"],
        "dados": [
            [r["estado"], float(r["faturamento"]), int(r["qtd_pedidos"])] for r in dados
        ],
    }


def _tratar_intencao_categorias() -> dict[str, Any]:
    """Processa consultas sobre faturamento e desempenho por categoria de produto."""
    sql = """
        SELECT
            p.product_category_name AS categoria,
            ROUND(SUM(f.valor_produto), 2) AS gmv,
            COUNT(DISTINCT f.order_id) AS qtd_pedidos
        FROM fato_vendas AS f
        INNER JOIN dim_produtos AS p ON f.product_id = p.product_id
        WHERE f.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY p.product_category_name
        ORDER BY gmv DESC
        LIMIT 10;
    """
    dados = _executar_query_mcp(sql)
    top_cat = dados[0]["categoria"] if dados else "N/A"
    top_val = dados[0]["gmv"] if dados else 0
    return {
        "sucesso": True,
        "resumo_executivo": f"A categoria '{top_cat}' concentra o maior faturamento, totalizando R$ {top_val:,.2f}.",
        "tipo_grafico": "column",
        "titulo_visualizacao": "Top 10 Categorias por Faturamento (R$)",
        "colunas": ["Categoria", "Faturamento (R$)", "Qtd Pedidos"],
        "dados": [
            [r["categoria"], float(r["gmv"]), int(r["qtd_pedidos"])] for r in dados
        ],
    }


def _tratar_intencao_vendedores() -> dict[str, Any]:
    """Processa consultas de scorecard e ranking dos melhores vendedores."""
    sql = """
        SELECT
            v.seller_id AS vendedor,
            v.seller_city || ' (' || v.seller_state || ')' AS localizacao,
            ROUND(SUM(f.valor_produto), 2) AS faturamento,
            COUNT(DISTINCT f.order_id) AS qtd_pedidos,
            ROUND(AVG(f.nota_avaliacao), 2) AS nota_media
        FROM fato_vendas AS f
        INNER JOIN dim_vendedores AS v ON f.seller_id = v.seller_id
        WHERE f.order_status NOT IN ('canceled', 'unavailable')
        GROUP BY v.seller_id, v.seller_city, v.seller_state
        ORDER BY faturamento DESC, nota_media DESC
        LIMIT 10;
    """
    dados = _executar_query_mcp(sql)
    return {
        "sucesso": True,
        "resumo_executivo": "Apresentando os principais vendedores avaliados por volume financeiro e reputação.",
        "tipo_grafico": "table",
        "titulo_visualizacao": "Scorecard dos Melhores Vendedores",
        "colunas": [
            "Vendedor",
            "Localização",
            "Faturamento (R$)",
            "Pedidos",
            "Nota Média",
        ],
        "dados": [
            [
                r["vendedor"][:8] + "...",
                r["localizacao"],
                float(r["faturamento"]),
                int(r["qtd_pedidos"]),
                float(r["nota_media"] or 0),
            ]
            for r in dados
        ],
    }


def _tratar_intencao_churn() -> dict[str, Any]:
    """Processa consultas de incidentes operacionais, atrasos na entrega e churn."""
    sql = """
        SELECT
            f.order_id AS pedido,
            c.customer_state AS uf,
            f.atraso_entrega_dias AS dias_atraso,
            f.nota_avaliacao AS nota,
            ROUND(f.valor_total, 2) AS valor_total
        FROM fato_vendas AS f
        INNER JOIN dim_clientes AS c ON f.customer_id = c.customer_id
        WHERE f.atraso_entrega_dias > 5 OR f.nota_avaliacao <= 2
        ORDER BY f.atraso_entrega_dias DESC NULLS LAST, f.valor_total DESC
        LIMIT 10;
    """
    dados = _executar_query_mcp(sql)
    total_criticos = len(dados)
    return {
        "sucesso": True,
        "resumo_executivo": f"Identificados {total_criticos} pedidos com alerta de churn ou atraso logístico superior a 5 dias.",
        "tipo_grafico": "table",
        "titulo_visualizacao": "Monitoramento de Entregas Críticas e Churn",
        "colunas": [
            "ID Pedido",
            "UF",
            "Atraso (Dias)",
            "Avaliação",
            "Valor Total (R$)",
        ],
        "dados": [
            [
                r["pedido"][:8] + "...",
                r["uf"],
                int(r["dias_atraso"] or 0),
                float(r["nota"] or 0),
                float(r["valor_total"]),
            ]
            for r in dados
        ],
    }


def _tratar_intencao_temporal() -> dict[str, Any]:
    """Processa consultas de série temporal e evolução mensal da receita."""
    sql = "SELECT ano_mes, receita_total, volume_pedidos FROM kpi_sumario_mensal ORDER BY ano_mes;"
    dados = _executar_query_mcp(sql)
    return {
        "sucesso": True,
        "resumo_executivo": "Evolução temporal mensal consolidando faturamento e volume total de pedidos.",
        "tipo_grafico": "line",
        "titulo_visualizacao": "Histórico Mensal de Faturamento e Pedidos",
        "colunas": ["Mês", "Receita (R$)", "Pedidos"],
        "dados": [
            [r["ano_mes"], float(r["receita_total"]), int(r["volume_pedidos"])]
            for r in dados
        ],
    }


INTENT_MATCHERS = [
    (
        r"\b(uf|estado|estados|onde|regiao|região|geografico|geografica|geográfico|geográfica)\b",
        _tratar_intencao_geografica,
    ),
    (
        r"\b(categoria|categorias|produto|produtos|item|itens|vendido|vendidos)\b",
        _tratar_intencao_categorias,
    ),
    (
        r"\b(vendedor|vendedores|seller|sellers|scorecard|ranking)\b",
        _tratar_intencao_vendedores,
    ),
    (
        r"\b(atraso|atrasos|entrega|entregas|churn|insatisfacao|insatisfação|reclamacao|reclamação)\b",
        _tratar_intencao_churn,
    ),
]


def rotear_pergunta_executiva(pergunta: str) -> dict[str, Any]:
    """Analisa semanticamente a pergunta e encaminha para o handler analítico.

    Args:
        pergunta: Frase formulada em linguagem natural pelo usuário.

    Returns:
        Dicionário formatado com resumo executivo, dados higienizados e gráfico.
    """
    texto = pergunta.lower().strip()
    logger.info("Roteador semântico acionado | Pergunta: '%s'", pergunta)

    for pattern, handler in INTENT_MATCHERS:
        if re.search(pattern, texto):
            return handler()

    logger.info("Intenção identificada: Padrão Temporal Mensal")
    return _tratar_intencao_temporal()
