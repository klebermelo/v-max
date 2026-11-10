# Spec 03: Modelagem Dimensional e Analítica (Camada Gold)

Construa a camada de indicadores de negócio do V-MAX.

## Tarefas
1. **Processamento Gold:**
   - Crie o script `src/processing/gold_processing.py`.
   - Leia os dados transformados de `data/silver/silver.db`.
2. **Modelagem Dimensional:**
   - Estruture o banco em tabelas de Fatos e Dimensões (ex: `fato_vendas`, `dim_clientes`, `dim_produtos`, `dim_tempo`).
3. **Enriquecimento e Regras de Negócio:**
   - Calcule e adicione o Lead Time de entrega (tempo entre pedido e entrega).
   - Crie uma tabela ou view materializada `kpi_sumario_mensal` contendo agregações prévias de receita, volume de pedidos e ticket médio.
4. **Validação de Integridade:**
   - Aplique validações de integridade referencial estrita via código (verifique se todos os IDs da Fato existem nas Dimensões). Se falhar, o script deve disparar uma exceção e logar o erro.
5. **Armazenamento:**
   - Salve a modelagem final no banco DuckDB `data/gold/gold.db`.
6. **Commit:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: modelagem dimensional gold e calculo de lead time`.