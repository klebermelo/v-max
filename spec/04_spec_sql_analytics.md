# Spec 04: Repositório de Consultas Analíticas Avançadas e Otimização DuckDB


Você é o assistente de IA atuando como Engenheiro de Dados Sênior no projeto V-MAX.
**AÇÃO OBRIGATÓRIA:** Siga rigorosamente a `skill.md` (formatação e lint com `ruff`, single responsibility, queries desacopladas em arquivos `.sql`).

---

## Contexto de Negócio e Desafios da Base Olist
Com base no alinhamento executivo e na inspeção real das tabelas da camada Silver/Gold:
- **Ausência de Dados Demográficos Pessoais:** A base Olist não possui campos de gênero ou nomes de clientes. Perguntas como "quem comprou mais, homem ou mulher" devem ser mapeadas analiticamente para segmentação demográfica/geográfica viável (`customer_state`, `customer_city`).
- **Inexistência de Tabela de Inventário/Estoque Físico:** O dataset é transacional. Questões sobre "estoque parado" devem ser mapeadas como análise de giro/recência de venda por produto (`dias_sem_vender` em relação à última data do histórico).
- **Preparação para o MCP (Spec 05):** Como assistentes de IA executarão queries ad-hoc dinâmicas via MCP na Spec 05, a camada Gold no DuckDB deve estar pré-indexada e otimizada estruturalmente para suportar múltiplos joins e agregações complexas.

---

## Tarefas

### 1. Criação do Repositório de Consultas (`src/sql/`)
Crie o diretório `src/sql/` e salve os seguintes arquivos `.sql` independentes, com sintaxe 100% compatível com DuckDB:

1. **`src/sql/gmv_por_categoria.sql`**
   - **Pergunta de Negócio:** *Quais categorias de produtos geram maior faturamento (GMV), qual o ticket médio por item e a participação percentual de cada categoria no faturamento global?*
   - **Técnicas Exigidas:** CTE (`WITH`), agregações (`SUM`, `AVG`, `COUNT`), `ROUND(..., 2)` e cálculo de share percentual com `CROSS JOIN`.

2. **`src/sql/scorecard_vendedores.sql`**
   - **Pergunta de Negócio:** *Quem são os melhores vendedores combinando faturamento, volume de pedidos entregues e qualidade do serviço (avaliação média dos clientes)?*
   - **Técnicas Exigidas:** CTE, Window Functions (`DENSE_RANK() OVER (...)` para ranking financeiro e ranking de qualidade de reviews).

3. **`src/sql/risco_churn.sql`**
   - **Pergunta de Negócio:** *Quais clientes foram severamente impactados por atrasos na entrega logística em relação ao prazo prometido e deram notas críticas ($\le 2$), configurando risco imediato de churn no marketplace?*
   - **Técnicas Exigidas:** Cálculo de diferença de datas (`DATEDIFF('day', ...)`), joins entre pedidos, clientes e reviews, e classificação condicional com `CASE WHEN` ('Risco Crítico', 'Risco Alto', 'Alerta Operacional').

4. **`src/sql/produtos_sem_saida.sql`**
   - **Pergunta de Negócio:** *Quais produtos cadastrados no catálogo estão há mais tempo sem registrar saída ou nunca registraram venda (baixa rotação/estoque parado virtual)?*
   - **Técnicas Exigidas:** Recência de compra (`DATEDIFF` em relação ao `MAX(order_purchase_timestamp)` da base), tratamento com `LEFT JOIN` e `NULLS FIRST`.

5. **`src/sql/performance_geografica.sql`**
   - **Pergunta de Negócio:** *Como se distribui a receita, o ticket médio e os prazos médios de entrega por estado e região dos clientes?*
   - **Técnicas Exigidas:** Agrupamento por `customer_state`, cálculo de frete médio versus valor dos produtos.

---

### 2. Otimização e Indexação para o Servidor MCP
Crie o script `src/processing/gold_optimization.py`:
- Conecte-se ao banco `data/gold/gold.db`.
- **Criação de Índices:** Crie índices em chaves primárias e estrangeiras frequentemente consultadas por IA e analistas:
  - `idx_fato_vendas_pedido` em `fato_vendas(order_id)`
  - `idx_fato_vendas_cliente` em `fato_vendas(customer_id)`
  - `idx_fato_vendas_produto` em `fato_vendas(product_id)`
  - `idx_fato_vendas_vendedor` em `fato_vendas(seller_id)`
- **Estatísticas de Otimização:** Execute o comando `ANALYZE;` do DuckDB para atualizar os metadados do otimizador de custos de consultas (CBO).
- Garanta limites estritos: nenhuma função com mais de 40 linhas, `logging` obrigatório (sem `print`), e uso de contexto `with duckdb.connect...`.

---

### 3. Testes Unitários de Otimização e Analytics
No diretório `tests/test_sql_analytics.py`:
- Adicione testes automatizados que executem cada uma das 5 queries SQL salvas em `src/sql/` contra um banco DuckDB em memória com amostra dos dados.
- Valide se o resultado não retorna erros de sintaxe e se as colunas esperadas estão presentes.
- Assegure que a cobertura de testes do projeto continue superior a 90%.

---

### 4. Formatação e Commit
1. Execute:
   ```bash
   uv run ruff format .
   uv run ruff check --select I --fix .
   uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
   ```
2. Realize o commit na branch `dev`:
   ```bash
   git add src/sql/ src/processing/gold_optimization.py tests/test_sql_analytics.py
   git commit -m "feat: consultas sql avancadas, otimizacao duckdb e indices para mcp"
   ```