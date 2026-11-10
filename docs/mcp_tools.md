# Documentação das Tools do Servidor MCP (`src/mcp/server.py`)

O servidor **Model Context Protocol (MCP)** do projeto **V-MAX** utiliza o SDK oficial `mcp` para conectar modelos de linguagem (LLMs) diretamente ao motor colunar **DuckDB** da camada Gold (`data/gold/gold.db`) e às Views Semânticas em Português (`data/silver/silver.db`).

---

## 1. Arquitetura de Segurança (Read-Only Enforced)

Para impedir qualquer mutação ou destruição de dados por prompts maliciosos (Prompt Injection / SQL Injection), o servidor aplica **dupla camada de proteção**:

1. **Conexão Física Somente Leitura:** O banco `gold.db` e o anexo `silver.db` são abertos com `read_only=True` no driver nativo do DuckDB.
2. **Validação Léxica Estrita (`validar_apenas_select`):**
   - A query deve obrigatoriamente iniciar com `SELECT` ou `WITH`.
   - Múltiplos comandos separados por ponto e vírgula (`;`) são bloqueados.
   - Palavras-chave proibidas (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `CREATE`, `REPLACE`, `GRANT`, `REVOKE`, `ATTACH`, `DETACH`, `COPY`, `EXPORT`, `PRAGMA`, `CALL`) disparam imediatamente a exceção `SQLSecurityError`.

---

## 2. Ferramentas (Tools) Expostas ao LLM

### 2.1 `get_schema(db_path: Path | None = None) -> str`
Retorna um objeto JSON estruturado descrevendo todas as tabelas da camada Gold e as 9 views semânticas em português, com o nome e o tipo de dado de cada coluna.

**Exemplo de Retorno:**
```json
{
  "fato_vendas": [
    {"coluna": "order_id", "tipo": "VARCHAR"},
    {"coluna": "valor_total", "tipo": "DECIMAL(10,2)"},
    {"coluna": "lead_time_dias", "tipo": "INTEGER"}
  ],
  "pedidos": [
    {"coluna": "order_id", "tipo": "VARCHAR"},
    {"coluna": "order_status", "tipo": "VARCHAR"}
  ]
}
```

### 2.2 `run_query(query: str, db_path: Path | None = None) -> str`
Executa uma consulta analítica SQL em modo somente leitura no DuckDB e retorna o resultado serializado em JSON (convertendo automaticamente objetos `Decimal`, `date` e `datetime`).

**Exemplo de Retorno (Sucesso):**
```json
{
  "status": "success",
  "total_linhas": 5,
  "dados": [
    {"regiao": "Sudeste", "qtd_pedidos": 67336, "faturamento": 10159955.08}
  ]
}
```

**Exemplo de Retorno (Bloqueio de Segurança):**
```json
{
  "status": "error",
  "mensagem": "Operação bloqueada: palavra-chave proibida 'DROP' detectada."
}
```

---

## 3. Roteador de Intenções Semânticas (`src/api/intent_router.py`)

Integrado ao endpoint `/api/chat` e `/api/ask` da API FastAPI, o roteador semântico consome a tool `run_query` do MCP diferenciando:

- **Métrica Solicitada:**
  - *Volume de Pedidos* (`pedidos`, `quantidade`, `volume`) $\rightarrow$ `COUNT(DISTINCT order_id)`
  - *Faturamento Financeiro* (`faturamento`, `receita`, `gmv`, `valor`) $\rightarrow$ `ROUND(SUM(valor_total), 2)`
- **Recorte Geográfico:**
  - *Macrorregião* (`região`, `macrorregião`) $\rightarrow$ Agrupamento via `CASE` nas 5 regiões oficiais do Brasil (`Sudeste`, `Sul`, `Nordeste`, `Centro-Oeste`, `Norte`).
  - *Unidade Federativa* (`estado`, `UF`) $\rightarrow$ Agrupamento direto por `customer_state`.
- **Outras Dimensões:** Categorias de Produto, Scorecard de Vendedores, Monitoramento de Churn Logístico e Evolução Mensal.
