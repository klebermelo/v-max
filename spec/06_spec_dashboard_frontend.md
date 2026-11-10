# Spec 06: Dashboard Interativo (IA + MCP)

Construa a interface visual interativa para o gerente de negócios.

## Tarefas
1. **API Backend:**
   - Crie `src/api/app.py` utilizando FastAPI.
   - Crie rotas que conectem o frontend ao servidor MCP criado no passo anterior, permitindo que perguntas em linguagem natural sejam processadas pela IA usando as tools do MCP e convertidas em SQL dinâmico.
2. **Interface Frontend (HTML/JS):**
   - Crie uma pasta `src/frontend/` com `index.html` e `app.js`.
   - Crie uma barra de busca onde o "gerente" digita a pergunta de negócio (ex: "Quem comprou mais, homem ou mulher?").
   - Integre gráficos gratuitos do **Google Charts** para renderizar visualmente a resposta enviada pelo backend.
3. **Gestão de Expectativas (Feedback):**
   - Adicione no HTML do painel inicial um banner explícito e visível de ressalva: *Disclaimer: Os dados representados neste painel são referentes a uma amostra extraída do dataset público Olist e não representam todo o ecossistema de e-commerce brasileiro.*
4. **Regras de Negócio:**
   - O HTML/JS não deve realizar nenhum cálculo de agregação. Toda inteligência vem das queries SQL dinâmicas rodando no DuckDB da camada Gold via backend/MCP.
5. **Commit:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: dashboard fastapi e google charts integrado ao mcp para ia`.