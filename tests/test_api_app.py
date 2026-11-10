"""Testes unitários para o Backend FastAPI do Dashboard."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_get_index_html() -> None:
    """Verifica se a rota raiz entrega o arquivo HTML do frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Executive Intelligence Dashboard" in response.text
    assert "Aviso Executivo:" in response.text


def test_api_schema_endpoint() -> None:
    """Verifica se o endpoint /api/schema retorna as tabelas da Gold."""
    response = client.get("/api/schema")
    assert response.status_code == 200
    data = response.json()
    assert "dim_clientes" in data
    assert "fato_vendas" in data


def test_api_kpis_endpoint() -> None:
    """Verifica se o endpoint /api/kpis retorna os indicadores consolidados."""
    response = client.get("/api/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "gmv_total" in data
    assert "total_pedidos" in data
    assert data["total_pedidos"] > 0


def test_api_analytics_endpoints() -> None:
    """Verifica se as rotas analíticas padrão respondem adequadamente."""
    for rota in [
        "/api/analytics/gmv-categoria",
        "/api/analytics/evolucao-mensal",
        "/api/analytics/scorecard",
        "/api/analytics/risco-churn",
    ]:
        response = client.get(rota)
        assert response.status_code == 200
        dados = response.json()
        assert isinstance(dados, list)
        assert len(dados) > 0


def test_api_query_permitida_e_bloqueada() -> None:
    """Testa execução de query segura e bloqueio de DDL/DML."""
    res_ok = client.post(
        "/api/query", json={"query": "SELECT COUNT(*) AS total FROM dim_clientes;"}
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "success"

    res_blocked = client.post("/api/query", json={"query": "DROP TABLE dim_clientes;"})
    assert res_blocked.status_code == 400


@pytest.mark.parametrize(
    ("pergunta", "termo_chave"),
    [
        ("Quem comprou mais, homem ou mulher?", "demográficos pessoais"),
        ("Quais produtos estão em estoque parado?", "controle de inventário"),
        ("Quais as categorias de maior GMV?", "GMV"),
        ("Scorecard dos melhores vendedores", "vendedores"),
    ],
)
def test_api_ask_perguntas_inteligentes(pergunta: str, termo_chave: str) -> None:
    """Testa o processamento de perguntas em linguagem natural e seus proxies analíticos."""
    response = client.post("/api/ask", json={"pergunta": pergunta})
    assert response.status_code == 200
    res_json = response.json()
    assert termo_chave.lower() in res_json["explicacao"].lower()
    assert len(res_json["dados"]) > 0
