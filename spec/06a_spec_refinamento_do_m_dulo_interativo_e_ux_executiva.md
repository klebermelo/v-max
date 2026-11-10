# Spec 06-A: Refinamento do Módulo Interativo, Roteamento Semântico e UX Executiva

Você é o assistente de IA atuando como Engenheiro de Dados Sênior no projeto V-MAX.
**AÇÃO OBRIGATÓRIA:** Siga rigorosamente as diretrizes do `skill.md` (limite de 40 linhas por função, sem `print()`, uso de `logging`, formatação com `ruff` e tipagem estrita).

---

## 1. Contexto e Motivação do Refinamento
Durante a validação funcional da Spec 06, identificou-se um comportamento inadequado na experiência do usuário de negócios:
1. **Fallback Estático / Falha de Interpretação:** Ao submeter perguntas em linguagem natural (ex: *"Qual a UF que mais vendeu?"*), o assistente caía em um fallback genérico executando `SELECT * FROM kpi_sumario_mensal`, gerando um gráfico de evolução temporal em vez de uma distribuição geográfica.
2. **Vazamento de Detalhes Técnicos (Data Leaks de Arquitetura):** O frontend exibia o bloco de código SQL bruto executado e jargões internos da engenharia (*"camada Gold"*, nomes de views). Um painel executivo deve ocultar complexidades de infraestrutura e focar na resposta de negócio.

---

## 2. Tarefas e Requisitos Técnicos

### 2.1 Refatoração do Backend FastAPI (`src/api/app.py` ou módulo de serviço)
Implemente um roteador semântico de intenções (*Intent Router / Text-to-SQL Seguro*):
* Mapeie expressões e termos-chave enviados pelo usuário para queries parametrizadas executadas via ferramenta `run_query` do servidor MCP:
  * **Intenção Geográfica (UF/Estados):** Se a pergunta contiver termos como `UF`, `estado`, `onde mais vendeu` ou `região`:
    - Executar agregação de `ROUND(SUM(f.valor_total), 2)` e contagem de pedidos agrupados por `c.customer_state`, com `INNER JOIN dim_clientes c ON f.customer_id = c.customer_id`, ordenado por faturamento decrescente (Top 10 ou todos os estados).
  * **Intenção de Categorias/Produtos:** Se contiver `categoria`, `produto` ou `mais vendido`:
    - Executar agregação por `p.product_category_name` via `INNER JOIN dim_produtos`.
  * **Intenção de Vendedores:** Se contiver `vendedor`, `seller` ou `scorecard`:
    - Executar agregação de faturamento e média de avaliação via `dim_vendedores`.
  * **Intenção de Logística e Churn:** Se contiver `atraso`, `entrega`, `churn` ou `insatisfação`:
    - Consultar clientes com atraso positivo e notas $\le 2$.
  * **Intenção Temporal/Mensal:** Se contiver `mês`, `ano`, `evolução` ou `histórico`:
    - Consultar a view `kpi_sumario_mensal`.
* **Sanitização do Payload de Resposta:**
  - O JSON retornado pela API **não deve** conter código SQL exposto nem menções a camadas do banco.
  - Formato padronizado de resposta:
    ```json
    {
      "sucesso": true,
      "resumo_executivo": "São Paulo (SP) lidera o volume de compras com R$ X faturados...",
      "tipo_grafico": "bar|column|line|table",
      "titulo_visualizacao": "Distribuição de Vendas por Estado (UF)",
      "colunas": ["Estado", "Faturamento (R$)", "Qtd Pedidos"],
      "dados": [
        ["SP", 5214820.50, 41746],
        ["RJ", 1823940.10, 12853]
      ]
    }
    ```

### 2.2 Refatoração da Interface Frontend (`src/frontend/index.html` e `src/frontend/app.js`)
* **Remoção de Elementos Técnicos:**
  - Excluir do DOM da página os elementos que exibem `SQL Executado: ...` e referências a tabelas técnicas.
* **Componente de Sugestões de Perguntas (Chips/Pills):**
  - Adicionar abaixo da caixa de pesquisa botões clicáveis com perguntas frequentes de negócio pré-mapeadas:
    1. 📍 *"Qual estado (UF) mais comprou?"*
    2. 🏷️ *"Top 5 categorias com maior faturamento"*
    3. ⭐ *"Quais vendedores têm maior nota e volume?"*
    4. 🚚 *"Clientes com entregas críticas e atraso"*
  - Ao clicar em um chip, preencher automaticamente o input e disparar a consulta.
* **Renderização Dinâmica do Google Charts:**
  - Adaptar a função de desenho para renderizar o gráfico adequado conforme o `tipo_grafico` informado pela API (barras horizontais para ranking de estados e categorias, linhas/área para séries temporais, ou tabela estruturada com alertas de cor).

---

## 3. Padrões de Engenharia e Verificação

1. **Modularidade e SRP:** Cada função de interpretação de intenção deve ter responsabilidade única e menos de 40 linhas.
2. **Observabilidade:** Utilizar `logging.info` para registrar a intenção identificada e o tempo de execução (proibido `print`).
3. **Qualidade e Estilo:**
   ```bash
   uv run ruff format .
   uv run ruff check --select I --fix .
   uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
   ```

---

## 4. Controle de Versão (Git Commit)

Adicione os arquivos alterados e realize o commit na branch `dev`:
```bash
git add src/api/ src/frontend/ tests/
git commit -m "feat: refinamento do modulo interativo com roteador semantico e ux executiva"
```