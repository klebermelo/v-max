# Spec 06-C: Filtros Temporais, Análises Comparativas por UF e Correção Semântica no MCP

Você é o assistente de IA atuando como Engenheiro de Dados Especialista no projeto V-MAX.
**DIRETRIZ OBRIGATÓRIA:** Siga rigorosamente o `skill.md` (funções com $\le 40$ linhas, uso de `logging` sem `print()`, formatação com `ruff` e cobertura de testes $\ge 90\%$).

---

## 1. Diagnóstico e Correções Críticas Imediatas

### 1.1 Correção de Tipagem no Google Charts (Frontend `src/frontend/app.js`)
* **Problema:** Erro `Type mismatch. Value guariba (SP) does not match type number in column index 1` e `Value RJ does not match type number in column index 1`.
* **Causa:** O script define colunas como `'number'` para desenhar gráficos de barras, mas as consultas de *Scorecard de Vendedores* e *Entregas Críticas* retornam dados textuais (cidade, UF, status).
* **Solução:**
  - Separar as consultas tabulares das consultas gráficas.
  - Para respostas do tipo *scorecard*, *ranking detalhado* ou *churn*, renderizar o componente `google.visualization.Table` com colunas tipadas dinamicamente (`string` para textos, `number` para métricas).
  - Para gráficos de barras/colunas/linhas (`google.visualization.ColumnChart`, `BarChart`, `LineChart`), assegurar estritamente que a coluna 0 seja `string` (rótulo) e a coluna 1 em diante sejam `number` (valores métricos).

### 1.2 Ajuste Semântico no Roteador MCP (`src/api/app.py` / `src/mcp/server.py`)
* **Problema:** Pergunta *"Total de pedidos por região"* retornou *"O estado de SP lidera o ranking com R$ 5,878,132.06 faturados"* (faturamento em vez de volume de pedidos, e UF em vez de macrorregião).
* **Solução:**
  - Diferenciar no roteador a intenção de métrica:
    - Termos como `pedidos`, `volume`, `quantidade`: usar `COUNT(DISTINCT order_id)`.
    - Termos como `faturamento`, `receita`, `gmv`, `vendeu`: usar `ROUND(SUM(valor_total), 2)`.
  - Diferenciar intenção de agrupamento geográfico:
    - Se o usuário pedir `região`: mapear as UFs para as 5 macrorregiões oficiais do Brasil via expressão SQL:
      ```sql
      CASE 
          WHEN c.customer_state IN ('SP', 'RJ', 'MG', 'ES') THEN 'Sudeste'
          WHEN c.customer_state IN ('PR', 'SC', 'RS') THEN 'Sul'
          WHEN c.customer_state IN ('BA', 'PE', 'CE', 'MA', 'PB', 'RN', 'AL', 'SE', 'PI') THEN 'Nordeste'
          WHEN c.customer_state IN ('GO', 'MT', 'MS', 'DF') THEN 'Centro-Oeste'
          ELSE 'Norte'
      END AS regiao
      ```
    - Se pedir `estado` ou `UF`: agrupar diretamente por `c.customer_state`.

---

## 2. Novos Requisitos de Negócio e Funcionalidades

### 2.1 Componente Global de Filtro por Período
Adicionar no topo do painel (`src/frontend/index.html`) seletores drop-down para filtragem temporal:
* **Filtro de Ano:** Opções `Todos`, `2016`, `2017`, `2018`.
* **Filtro de Mês:** Opções `Todos`, `Janeiro (01)` a `Dezembro (12)`.
* **Comportamento Reativo:** A alteração do drop-down deve disparar chamadas assíncronas atualizando automaticamente:
  1. **GMV Total Faturado**
  2. **Volume de Pedidos**
  3. **Ticket Médio Global**
  4. **Tempo Médio de Entrega (Lead Time)**
  5. Gráficos analíticos e comparativos da tela.

### 2.2 Gráficos Analíticos e Comparativos Anuais
Implementar endpoints no backend e visualizações no frontend para responder:

1. **Comparativo Global entre Anos:**
   - Comparação temporal mensal entre anos selecionados (ex: 2016 vs 2017 ou 2016 a 2018).
   - Renderização via `LineChart` ou `ColumnChart` com séries múltiplas de receita e pedidos.

2. **Comparativo por Estado (UF) Multi-ano:**
   - Permite comparar o faturamento/pedidos dos principais estados entre 2 ou 3 anos selecionados.

3. **Painel de Métricas Especializadas por UF:**
   - **Pedidos por UF + Ticket Médio:** Gráfico de eixo duplo ou barras combinadas.
   - **Top Categorias por Estado:** Permite selecionar um estado e ver as categorias líderes.
   - **Frete Médio por Estado:** Identificar os estados com maior custo logístico percentual.

---

## 3. Repositório SQL Atualizado (`src/sql/`)

Criar e versionar as queries parametrizadas com suporte a filtro de ano (`ano_filtro`):

### 3.1 `src/sql/comparativo_anual_mensal.sql`
```sql
SELECT 
    STRFTIME(TRY_CAST(t.data AS DATE), '%m') AS mes,
    STRFTIME(TRY_CAST(t.data AS DATE), '%Y') AS ano,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio
FROM fato_vendas f
INNER JOIN dim_tempo t ON f.data_compra_id = t.tempo_id
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 3.2 `src/sql/metricas_por_estado.sql`
```sql
SELECT 
    c.customer_state AS uf,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio,
    ROUND(AVG(f.tempo_entrega_dias), 1) AS lead_time_medio
FROM fato_vendas f
INNER JOIN dim_clientes c ON f.customer_id = c.customer_id
INNER JOIN dim_tempo t ON f.data_compra_id = t.tempo_id
WHERE (? IS NULL OR STRFTIME(TRY_CAST(t.data AS DATE), '%Y') = ?)
GROUP BY c.customer_state
ORDER BY gmv_total DESC;
```

### 3.3 `src/sql/pedidos_por_regiao.sql`
```sql
SELECT 
    CASE 
        WHEN c.customer_state IN ('SP', 'RJ', 'MG', 'ES') THEN 'Sudeste'
        WHEN c.customer_state IN ('PR', 'SC', 'RS') THEN 'Sul'
        WHEN c.customer_state IN ('BA', 'PE', 'CE', 'MA', 'PB', 'RN', 'AL', 'SE', 'PI') THEN 'Nordeste'
        WHEN c.customer_state IN ('GO', 'MT', 'MS', 'DF') THEN 'Centro-Oeste'
        ELSE 'Norte'
    END AS regiao,
    COUNT(DISTINCT f.order_id) AS total_pedidos,
    ROUND(SUM(f.valor_total), 2) AS gmv_total,
    ROUND(AVG(f.valor_total), 2) AS ticket_medio
FROM fato_vendas f
INNER JOIN dim_clientes c ON f.customer_id = c.customer_id
INNER JOIN dim_tempo t ON f.data_compra_id = t.tempo_id
WHERE (? IS NULL OR STRFTIME(TRY_CAST(t.data AS DATE), '%Y') = ?)
GROUP BY 1
ORDER BY total_pedidos DESC;
```

---

## 4. Endpoints da API FastAPI (`src/api/app.py`)

Atualizar os endpoints para aceitar parâmetros de consulta opcionais (`ano: Optional[str] = None`, `mes: Optional[str] = None`):

* `GET /api/kpis?ano={ano}&mes={mes}`: Retorna GMV, pedidos, ticket médio e lead time filtrados.
* `GET /api/comparativo/anual`: Retorna matriz consolidada para o gráfico multi-ano.
* `GET /api/metricas/uf?ano={ano}`: Retorna métricas completas agregadas por estado.
* `POST /api/chat`: Processa a linguagem natural diferenciando metricas (`pedidos` vs `faturamento`) e dimensões (`região` vs `estado`).

---

## 5. Padrões de Verificação e Git Commit

1. **Linting e Formatação:**
   ```bash
   uv run ruff format .
   uv run ruff check --select I --fix .
   ```

2. **Garantia de Qualidade de Testes:**
   Atualizar `tests/test_api.py` e `tests/test_sql_analytics.py` validando os parâmetros de ano e as queries de região.
   ```bash
   uv run pytest tests/ --cov=src --cov-fail-under=90
   ```

3. **Commit no Repositório (Branch `dev`):**
   ```bash
   git add src/api/ src/frontend/ src/sql/ tests/ 06c_spec_filtros_temporais_comparativos_e_mcp_fix.md
   git commit -m "fix: correcao datatable google charts, filtros temporais e refinamento semantico mcp"
   ```