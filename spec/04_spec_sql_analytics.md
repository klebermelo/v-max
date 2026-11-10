# Spec 04: Repositório de Consultas Analíticas Avançadas

Crie o repositório de queries complexas que extraem valor da camada Gold.

## Tarefas
1. **Estrutura:**
   - Crie a pasta `src/sql/`.
2. **Desenvolvimento SQL:**
   - Crie arquivos `.sql` independentes para cada análise de negócio, que serão lidos posteriormente pelo MCP ou pelas rotinas do app.
   - `gmv_por_categoria.sql`: Use CTEs para calcular o Gross Merchandise Volume por categoria de produto.
   - `scorecard_vendedores.sql`: Use Window Functions (`RANK()`, `DENSE_RANK()`) para criar um ranking de vendedores baseado em faturamento e notas de avaliação.
   - `risco_churn.sql`: Identifique clientes com risco de evasão (churn) pós-incidente, filtrando compras que tiveram atraso superior a 5 dias na entrega ou avaliação menor ou igual a 2.
3. **Compatibilidade:**
   - Garanta que a sintaxe SQL seja 100% compatível com o DuckDB.
4. **Commit:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: consultas sql avancadas com window functions e ctes`.