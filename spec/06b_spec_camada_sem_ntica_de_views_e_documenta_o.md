# Spec 06-B: Camada Semântica de Views em Português e Documentação Arquitetural

Você é o assistente de IA atuando como Engenheiro de Dados Sênior no projeto V-MAX.
**AÇÃO OBRIGATÓRIA:** Siga rigorosamente o `skill.md` (Single Responsibility, limite de 40 linhas por função, sem `print()`, uso de `logging`, formatação com `ruff` e tipagem estrita).

---

## 1. Contexto e Motivação Arquitetural (Decisão de Engenharia)

Para facilitar a exploração analítica ad-hoc, consultas de memória e simplificar prompts para LLMs e MCP, optou-se por disponibilizar um vocabulário completamente em português para as entidades de negócio.

Em consonância com as melhores práticas de Engenharia de Dados:
* **Preservação da Fonte da Verdade:** As tabelas físicas originais em `data/silver/silver.db` e `data/bronze/bronze.db` são preservadas em seus nomes originais (`olist_*_dataset`), garantindo rastreabilidade, compliance com auditoria SHA-256 e compatibilidade com novos dumps do Kaggle.
* **Camada Semântica por Views (Zero Storage Overhead):** Criamos uma camada de abstração semântica com `CREATE OR REPLACE VIEW` no DuckDB, mapeando os nomes em inglês/técnicos para entidades intuitivas em português.

---

## 2. Mapa Semântico (Entidade Física -> View Semântica)

| Tabela Física Silver | View Semântica (Português) |
|---|---|
| `olist_orders_dataset` | `pedidos` |
| `olist_order_items_dataset` | `itens_pedido` |
| `olist_order_payments_dataset` | `pagamentos` |
| `olist_order_reviews_dataset` | `avaliacoes` |
| `olist_customers_dataset` | `clientes` |
| `olist_sellers_dataset` | `vendedores` |
| `olist_products_dataset` | `produtos` |
| `product_category_name_translation` | `traducao_categorias` |
| `olist_geolocation_dataset` | `geolocalizacao` |

---

## 3. Tarefas Técnicas

### 3.1 Módulo de Criação de Views (`src/processing/semantic_views.py`)
1. Crie o script `src/processing/semantic_views.py`.
2. O script deve conectar-se ao banco `data/silver/silver.db` (e opcionalmente replicar no `data/gold/gold.db` caso necessário para consultas cross-table) usando contexto `with duckdb.connect...`.
3. Executar em transação segura a criação das 9 views listadas no mapa semântico.
4. **Regras de Qualidade:**
   - Funções com menos de 40 linhas.
   - Logs de execução detalhados utilizando a biblioteca `logging` (proibido `print()`).
   - Type hints e docstrings explicativas.

### 3.2 Atualização do Servidor MCP (`src/mcp/server.py`)
1. Atualize a tool `get_schema()` para incluir na listagem as views em português recém-criadas.
2. Adicione na docstring da tool `run_query()` a informação explícita para o LLM de que ele pode consultar tanto os nomes das dimensões da Gold quanto as views em português (`pedidos`, `clientes`, `itens_pedido`, `produtos`, etc.).

### 3.3 Testes Automatizados (`tests/test_semantic_views.py`)
1. Crie o arquivo `tests/test_semantic_views.py`.
2. Implemente testes unitários que:
   - Validem a criação das 9 views em um banco DuckDB em memória.
   - Executem um `JOIN` simples de teste entre `pedidos` e `clientes` usando exclusivamente os aliases em português.
   - Garantam que o coverage geral do projeto se mantenha **$\ge$ 90%**.

### 3.4 Documentação Arquitetural (`docs/arquitetura.md` e `README.md`)
1. Crie ou atualize o arquivo `docs/arquitetura.md` detalhando:
   - O fluxo Medalhão (Bronze -> Silver -> Gold).
   - A decisão de design: por que utilizar Views Semânticas em vez de renomear os arquivos da fonte bruta.
   - Dicionário das 9 views disponíveis para os analistas e gerentes.
2. Adicione uma nota explicativa no `README.md` destacando a camada semântica em português pronta para consultas MCP.

---

## 4. Padrões de Verificação e Git Commit

1. Execute a suíte de qualidade:
   ```bash
   uv run ruff format .
   uv run ruff check --select I --fix .
   uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
   ```

2. Realize o commit na branch `dev`:
   ```bash
   git add src/processing/semantic_views.py src/mcp/server.py tests/test_semantic_views.py docs/ README.md
   git commit -m "feat: camada semantica de views em portugues e documentacao arquitetural"
   ```