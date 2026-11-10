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

SQL_REGIOES = """
    SELECT
        CASE 
            WHEN c.customer_state IN ('SP', 'RJ', 'MG', 'ES') THEN 'Sudeste'
            WHEN c.customer_state IN ('PR', 'SC', 'RS') THEN 'Sul'
            WHEN c.customer_state IN ('BA', 'PE', 'CE', 'MA', 'PB', 'RN', 'AL', 'SE', 'PI') THEN 'Nordeste'
            WHEN c.customer_state IN ('GO', 'MT', 'MS', 'DF') THEN 'Centro-Oeste'
            ELSE 'Norte'
        END AS regiao,
        COUNT(DISTINCT f.order_id) AS qtd_pedidos,
        ROUND(SUM(f.valor_total), 2) AS faturamento
    FROM fato_vendas AS f
    INNER JOIN dim_clientes AS c ON f.customer_id = c.customer_id
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
"""

SQL_ESTADOS = """
    SELECT
        c.customer_state AS estado,
        COUNT(DISTINCT f.order_id) AS qtd_pedidos,
        ROUND(SUM(f.valor_total), 2) AS faturamento
    FROM fato_vendas AS f
    INNER JOIN dim_clientes AS c ON f.customer_id = c.customer_id
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY c.customer_state
"""

SQL_CATEGORIAS = """
    SELECT
        p.product_category_name AS categoria,
        COUNT(DISTINCT f.order_id) AS qtd_pedidos,
        ROUND(SUM(f.valor_produto), 2) AS faturamento
    FROM fato_vendas AS f
    INNER JOIN dim_produtos AS p ON f.product_id = p.product_id
    WHERE f.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY p.product_category_name
"""


def _executar_query_mcp(sql: str) -> list[dict[str, Any]]:
    """Executa SQL via ferramenta run_query do servidor MCP e retorna lista de registros."""
    res_raw = run_query(sql)
    res_json = json.loads(res_raw)
    if res_json.get("status") == "error":
        raise ValueError(res_json.get("mensagem", "Erro na execução SQL"))
    return res_json.get("dados", [])


def _is_volume_metric(texto: str) -> bool:
    """Verifica se a pergunta prioriza volume de pedidos em vez de faturamento monetário."""
    tem_vol = bool(
        re.search(
            r"\b(pedido|pedidos|volume|quantidade|qtd|quantos|numero|número)\b",
            texto,
        )
    )
    tem_fat = bool(
        re.search(
            r"\b(faturamento|faturou|receita|gmv|valor|reais|r\$|ticket)\b",
            texto,
        )
    )
    return tem_vol and not tem_fat


def _formatar_resposta_metrica(
    dados: list[dict[str, Any]],
    chave_dim: str,
    nome_dim: str,
    titulo: str,
    volume: bool,
    tipo_grafico: str,
) -> dict[str, Any]:
    """Formata o retorno analítico para visualização gráfica."""
    top_item = dados[0][chave_dim] if dados else "N/A"
    if volume:
        top_val = dados[0]["qtd_pedidos"] if dados else 0
        resumo = f"{nome_dim} '{top_item}' lidera em pedidos com {top_val:,} compras."
        colunas = [nome_dim, "Qtd Pedidos", "Faturamento (R$)"]
        linhas = [
            [r[chave_dim], int(r["qtd_pedidos"]), float(r["faturamento"])]
            for r in dados
        ]
    else:
        top_val = dados[0]["faturamento"] if dados else 0
        resumo = f"{nome_dim} '{top_item}' lidera com R$ {top_val:,.2f} faturados."
        colunas = [nome_dim, "Faturamento (R$)", "Qtd Pedidos"]
        linhas = [
            [r[chave_dim], float(r["faturamento"]), int(r["qtd_pedidos"])]
            for r in dados
        ]

    return {
        "sucesso": True,
        "resumo_executivo": resumo,
        "tipo_grafico": tipo_grafico,
        "titulo_visualizacao": f"{titulo} por {'Volume' if volume else 'Faturamento'}",
        "colunas": colunas,
        "dados": linhas,
    }


def _tratar_intencao_regioes(texto: str) -> dict[str, Any]:
    """Processa consultas sobre distribuição pelas 5 macrorregiões brasileiras."""
    volume = _is_volume_metric(texto)
    order_col = "qtd_pedidos" if volume else "faturamento"
    sql = f"{SQL_REGIOES} ORDER BY {order_col} DESC;"
    dados = _executar_query_mcp(sql)
    return _formatar_resposta_metrica(
        dados, "regiao", "Macrorregião", "Macrorregiões", volume, "column"
    )


def _tratar_intencao_estados(texto: str) -> dict[str, Any]:
    """Processa consultas sobre distribuição geográfica por UF/estado."""
    volume = _is_volume_metric(texto)
    order_col = "qtd_pedidos" if volume else "faturamento"
    sql = f"{SQL_ESTADOS} ORDER BY {order_col} DESC LIMIT 10;"
    dados = _executar_query_mcp(sql)
    return _formatar_resposta_metrica(
        dados, "estado", "Estado", "Top 10 Estados (UF)", volume, "bar"
    )


def _tratar_intencao_categorias(texto: str) -> dict[str, Any]:
    """Processa consultas sobre desempenho por categoria de produto."""
    volume = _is_volume_metric(texto)
    order_col = "qtd_pedidos" if volume else "faturamento"
    sql = f"{SQL_CATEGORIAS} ORDER BY {order_col} DESC LIMIT 10;"
    dados = _executar_query_mcp(sql)
    return _formatar_resposta_metrica(
        dados,
        "categoria",
        "Categoria",
        "Top 10 Categorias",
        volume,
        "column",
    )


def _tratar_intencao_vendedores(_texto: str = "") -> dict[str, Any]:
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


def _tratar_intencao_churn(_texto: str = "") -> dict[str, Any]:
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
    return {
        "sucesso": True,
        "resumo_executivo": f"Identificados {len(dados)} pedidos com alerta de churn ou atraso crítico.",
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


def _tratar_intencao_temporal(_texto: str = "") -> dict[str, Any]:
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
        r"\b(regiao|região|regioes|regiões|macrorregiao|macrorregião|macrorregioes|macrorregiões)\b",
        _tratar_intencao_regioes,
    ),
    (
        r"\b(uf|ufs|estado|estados|onde|geografico|geografica|geográfico|geográfica)\b",
        _tratar_intencao_estados,
    ),
    (
        r"\b(categoria|categorias|produto|produtos|item|itens)\b",
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
            return handler(texto)

    logger.info("Intenção identificada: Padrão Temporal Mensal")
    return _tratar_intencao_temporal(texto)
