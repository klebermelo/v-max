"""Testes unitários para o Backend FastAPI e Roteador Semântico."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.intent_router import rotear_pergunta_executiva

client = TestClient(app)


def test_get_index_html() -> None:
    """Verifica se a rota raiz entrega o HTML sem vazamento de detalhes técnicos."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Executive Intelligence Dashboard" in response.text
    assert "Aviso Executivo:" in response.text
    # Assegura que elementos de debug/SQL não estão no template
    assert "SQL Executado:" not in response.text


def test_roteador_semantico_intencoes() -> None:
    """Valida o mapeamento semântico de intenções pelo roteador."""
    # 1. Intenção Geográfica
    res_geo = rotear_pergunta_executiva("Qual estado (UF) que mais vendeu?")
    assert res_geo["sucesso"] is True
    assert res_geo["tipo_grafico"] == "bar"
    assert "Estado" in res_geo["colunas"]
    assert len(res_geo["dados"]) > 0

    # 2. Intenção Categorias
    res_cat = rotear_pergunta_executiva(
        "Quais as categorias de produtos mais vendidas?"
    )
    assert res_cat["sucesso"] is True
    assert res_cat["tipo_grafico"] == "column"
    assert "Categoria" in res_cat["colunas"]

    # 3. Intenção Vendedores
    res_vend = rotear_pergunta_executiva("Quais os melhores vendedores do scorecard?")
    assert res_vend["sucesso"] is True
    assert res_vend["tipo_grafico"] == "table"

    # 4. Intenção Churn / Atraso
    res_churn = rotear_pergunta_executiva(
        "Pedidos com atraso na entrega e insatisfação"
    )
    assert res_churn["sucesso"] is True
    assert res_churn["tipo_grafico"] == "table"

    # 5. Intenção Temporal
    res_tempo = rotear_pergunta_executiva("Histórico e evolução mensal de vendas")
    assert res_tempo["sucesso"] is True
    assert res_tempo["tipo_grafico"] == "line"


@pytest.mark.parametrize(
    ("pergunta", "tipo_esperado"),
    [
        ("Qual a UF com maior faturamento?", "bar"),
        ("Top produtos e categorias mais vendidas", "column"),
        ("Scorecard de vendedores", "table"),
        ("Quais entregas tiveram atraso crítico?", "table"),
    ],
)
def test_api_ask_roteamento_executivo(pergunta: str, tipo_esperado: str) -> None:
    """Verifica o payload sanitizado da rota /api/ask."""
    response = client.post("/api/ask", json={"pergunta": pergunta})
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["sucesso"] is True
    assert res_json["tipo_grafico"] == tipo_esperado
    assert "resumo_executivo" in res_json
    assert "colunas" in res_json
    assert len(res_json["dados"]) > 0
    # Valida ausência de query SQL no payload de resposta para o usuário
    assert "query_executada" not in res_json


def test_api_endpoints_adicionais() -> None:
    """Cobre as demais rotas da API para garantir cobertura abrangente."""
    assert client.get("/api/schema").status_code == 200
    assert client.get("/api/kpis").status_code == 200
    assert client.get("/api/kpis?ano=2017").status_code == 200
    assert client.get("/api/kpis?ano=2017&mes=03").status_code == 200
    assert client.get("/api/comparativo/anual").status_code == 200
    assert client.get("/api/metricas/uf").status_code == 200
    assert client.get("/api/metricas/uf?ano=2017").status_code == 200
    assert client.get("/api/analytics/regioes").status_code == 200
    assert client.get("/api/analytics/regioes?ano=2018").status_code == 200
    assert client.get("/api/analytics/gmv-categoria").status_code == 200
    assert client.get("/api/analytics/evolucao-mensal").status_code == 200
    assert client.get("/api/analytics/scorecard").status_code == 200
    assert client.get("/api/analytics/risco-churn").status_code == 200

    # Teste de chat executivo (/api/chat)
    chat_res = client.post("/api/chat", json={"message": "Total de pedidos por região"})
    assert chat_res.status_code == 200
    assert chat_res.json()["sucesso"] is True

    # Query permitida e proibida
    assert client.post("/api/query", json={"query": "SELECT 1"}).status_code == 200
    assert client.post("/api/query", json={"query": "DROP TABLE x"}).status_code == 400


def test_roteador_semantico_regiao_e_metricas() -> None:
    """Valida diferenciação entre volume/faturamento e macrorregião/estado."""
    # 1. Total de pedidos por região (volume)
    res_reg_vol = rotear_pergunta_executiva("Total de pedidos por região")
    assert res_reg_vol["sucesso"] is True
    assert res_reg_vol["tipo_grafico"] == "column"
    assert "Macrorregião" in res_reg_vol["colunas"]
    assert "Qtd Pedidos" in res_reg_vol["colunas"]
    assert "pedidos" in res_reg_vol["resumo_executivo"].lower()

    # 2. Faturamento por região
    res_reg_fat = rotear_pergunta_executiva("Qual o faturamento por região?")
    assert res_reg_fat["sucesso"] is True
    assert "Faturamento (R$)" in res_reg_fat["colunas"]

    # 3. Volume de pedidos por estado
    res_est_vol = rotear_pergunta_executiva("Quantidade de pedidos por estado (UF)")
    assert res_est_vol["sucesso"] is True
    assert res_est_vol["tipo_grafico"] == "bar"
    assert "Qtd Pedidos" in res_est_vol["colunas"]


def test_api_ask_fallback_e_erro() -> None:
    """Testa fallback de erro e perguntas genéricas na rota /api/ask."""
    res_gen = client.post("/api/ask", json={"pergunta": "relatorio geral"})
    assert res_gen.status_code == 200
    assert res_gen.json()["tipo_grafico"] == "line"

    res_erro = client.post("/api/ask", json={"pergunta": ""})
    assert res_erro.status_code == 200
    assert res_erro.json()["sucesso"] is False
