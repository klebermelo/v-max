# Spec 05: Servidor MCP Nativo (Model Context Protocol)

Construa a ponte para a IA analisar os dados via Model Context Protocol.

## Tarefas
1. **Dependências:**
   - Atualize os pacotes do `uv` incluindo bibliotecas necessárias para rodar um servidor MCP em Python (ex: `mcp` sdk oficial).
2. **Implementação do Servidor:**
   - Crie `src/mcp/server.py`.
   - Implemente um servidor MCP que se conecte estritamente ao banco `data/gold/gold.db`.
3. **Criação de Tools (Ferramentas):**
   - Exponha ferramentas para que o assistente LLM possa inspecionar os dados:
     - `get_schema`: Retorna o DDL das tabelas da camada Gold.
     - `run_query`: Recebe uma query SQL e retorna os resultados em JSON.
4. **Segurança e Tratamento de Erros:**
   - Implemente proteções na tool `run_query` para aceitar **apenas** comandos `SELECT`. Rejeite qualquer instrução `DROP`, `INSERT`, `UPDATE` ou `DELETE`.
   - O servidor deve rodar via requisição padrão e estar modularizado para iniciar via terminal.
5. **Commit:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: implementacao do servidor mcp duckdb com tools read-only`.