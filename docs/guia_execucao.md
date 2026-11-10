# Guia de Execução e Operação — Projeto V-MAX

Este guia apresenta todos os comandos necessários para instalar o ambiente, processar a esteira completa de dados, validar a suíte de testes e iniciar o servidor MCP e o Dashboard Executivo.

---

## 1. Requisitos e Sincronização via `uv`

> **Importante:** O uso de `pip` é estritamente proibido neste projeto. Utilize exclusivamente o gerenciador **`uv`**.

```bash
# Clonar o repositório e acessar o diretório
git clone https://github.com/klebermelo/v-max.git
cd v-max
git checkout dev

# Sincronizar ambiente virtual e instalar dependências exatas do uv.lock
uv sync
```

---

## 2. Execução Sequencial da Pipeline Medalhão

1. **Ingestão Camada Bronze (`data/bronze/bronze.db`):**
   ```bash
   uv run python -m src.ingestion.bronze_ingestion
   ```
2. **Processamento e Sanitização Camada Silver (`data/silver/silver.db`):**
   ```bash
   uv run python -m src.processing.silver_processing
   ```
3. **Criação da Camada Semântica de Views em Português:**
   ```bash
   uv run python -m src.processing.semantic_views
   ```
4. **Modelagem Dimensional e Validação Camada Gold (`data/gold/gold.db`):**
   ```bash
   uv run python -m src.processing.gold_processing
   ```
5. **Indexação B-Tree e Estatísticas CBO (`ANALYZE`):**
   ```bash
   uv run python -m src.processing.gold_optimization
   ```

---

## 3. Servidor MCP Nativo

Para iniciar o servidor Model Context Protocol em modo `stdio`:

```bash
uv run python -m src.mcp.server
```

---

## 4. Dashboard Executivo FastAPI + Google Charts

Para subir a aplicação web interativa:

```bash
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

- **Dashboard Executivo:** `http://localhost:8000`
- **Documentação OpenAPI / Swagger:** `http://localhost:8000/docs`

---

## 5. Qualidade de Código e Suíte de Testes

```bash
# Formatação e Linting com Ruff
uv run ruff format .
uv run ruff check --select I --fix .
uv run ruff check .

# Testes Unitários com Cobertura Mínima Obrigatória de 90%
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

---

## 6. Visualizar esta Documentação (MkDocs Material)

```bash
uv run mkdocs serve
```
Acesse em `http://127.0.0.1:8000` (ou especifique outra porta com `-a 127.0.0.1:8001`).
