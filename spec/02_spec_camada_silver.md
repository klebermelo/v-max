# Spec 02: Sanitização e Higienização (Camada Silver)

Avance para a construção da camada intermediária do projeto V-MAX.

## Tarefas
1. **Processamento Silver:**
   - Crie o script `src/processing/silver_processing.py`.
   - Leia as tabelas do banco `data/bronze/bronze.db`.
2. **Transformações Exigidas:**
   - Converta todas as moedas e valores financeiros para `DECIMAL(10,2)`.
   - Padronize todas as strings de datas para o formato `DATE (YYYY-MM-DD)` ou `TIMESTAMP`.
   - Limpe strings (remova espaços extras e padronize minúsculas para categorias).
   - Limpe dados de telefone, deixando o formato puramente numérico.
3. **Padrões de Engenharia (Single Responsibility):**
   - Nenhuma função no script pode ultrapassar 40 linhas.
   - Quebre as transformações em funções menores e testáveis (ex: `def limpar_telefones(df):`, `def padronizar_moedas(df):`).
4. **Observabilidade:**
   - **Proibido usar `print()`**. Utilize a biblioteca padrão `logging` do Python para registrar o início, progresso e fim do processamento de cada tabela.
5. **Armazenamento:**
   - Salve as tabelas higienizadas no banco DuckDB `data/silver/silver.db`.
6. **Commit:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: sanitizacao silver com funcoes modulares e logging`.