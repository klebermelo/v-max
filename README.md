# V-MAX — Plataforma Analítica de E-Commerce (Arquitetura em Medalhão com DuckDB & MCP)

O projeto **V-MAX** implementa uma plataforma moderna de Engenharia de Dados e Inteligência Analítica em Python e **DuckDB**, estruturada sob a **Arquitetura em Medalhão (Bronze, Silver e Gold)** e complementada por uma **Camada Semântica de Views em Português**. O ecossistema contempla desde a ingestão fiel e higienização estrita de dados públicos de e-commerce até a modelagem dimensional em estrela (*Star Schema*), um servidor **Model Context Protocol (MCP)** nativo para exploração via Inteligência Artificial e um **Dashboard Executivo interativo em FastAPI com Google Charts**.

---

## ⚠️ Ressalva Amostral e Escopo dos Dados

> **Aviso Executivo e Educacional:** Os dados apresentados neste projeto referem-se a uma **amostra histórica de marketplace brasileiro extraída entre 2016 e 2018** a partir do dataset público da **Olist**. Todas as análises, KPIs de faturamento (GMV), indicadores de *Lead Time* logístico e classificações de risco de *Churn* possuem **finalidade estritamente analítica, acadêmica e educacional**, não representando a totalidade das operações atuais da empresa nem contendo dados pessoais identificáveis (PII).

---

## 📊 Fonte de Dados e Licença Pública

- **Conjunto de Dados:** *Brazilian E-Commerce Public Dataset by Olist*, disponibilizado publicamente na plataforma **Kaggle** ([https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)).
- **Escopo e Volume:** Aproximadamente 100 mil pedidos comerciais distribuídos em 9 tabelas relacionais (pedidos, itens, pagamentos, avaliações, clientes, vendedores, produtos, categorias e geolocalização por prefixo de CEP).
- **Licença de Uso:** Licenciado sob **CC BY-NC-SA 4.0** (*Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International*), que autoriza o compartilhamento, redistribuição e adaptação do material para fins educacionais e não comerciais, desde que atribuído o devido crédito à fonte original.

---

## 🏛️ Arquitetura Implementada

```text
v-max/
├── data/
│   ├── raw/                # Arquivos CSV brutos compactados (.csv.gz) do dataset Olist
│   ├── bronze/             # Banco DuckDB bronze.db (Ingestão fiel, all_varchar=True, auditoria SHA-256)
│   ├── silver/             # Banco DuckDB silver.db (Sanitização, DECIMAL(10,2), TIMESTAMP e 9 Views Semânticas PT-BR)
│   └── gold/               # Banco DuckDB gold.db (Star Schema, Fato, 4 Dimensões, KPIs e índices B-Tree)
├── docs/
│   ├── index.md            # Página inicial da documentação técnica MkDocs Material
│   ├── arquitetura.md      # Detalhamento da Arquitetura em Medalhão e Views Semânticas
│   ├── dicionario_gold.md  # Dicionário de Dados e Modelo Dimensional da Camada Gold
│   ├── guia_execucao.md    # Manual completo de operação via uv
│   ├── mcp_tools.md        # Especificação das Tools do Servidor MCP e segurança Read-Only
│   ├── erros_ia.md         # Registro minucioso de falhas da IA, causas-raiz e soluções aplicadas
│   ├── evolução_projeto.md # Histórico cronológico de todas as entregas (Specs 01 a 07)
│   └── conteúdo_tabelas.md # Amostras e estrutura das tabelas da camada Silver
├── src/
│   ├── ingestion/          # Pipeline Bronze (bronze_ingestion.py com hash SHA-256 e _loaded_at)
│   ├── processing/         # Pipelines Silver, Views Semânticas, Gold e Otimizações CBO (gold_optimization.py)
│   ├── sql/                # Repositório de queries SQL analíticas desacopladas (.sql)
│   │   ├── gold/           # DDLs dimensionais (dim_clientes, dim_produtos, dim_vendedores, dim_tempo, fato_vendas, kpi_sumario_mensal)
│   │   └── *.sql           # Consultas analíticas (GMV, Scorecard, Risco Churn, Comparativo Anual, Regiões e UF)
│   ├── mcp/                # Servidor MCP nativo (server.py com tools get_schema e run_query read-only)
│   ├── api/                # Backend FastAPI (app.py e roteador semântico intent_router.py)
│   └── frontend/           # Interface executiva (index.html e app.js com Google Charts e filtros temporais)
├── tests/                  # Suíte com 58 testes automatizados (> 95% de cobertura de código)
├── mkdocs.yml              # Configuração da documentação técnica MkDocs Material
├── pyproject.toml          # Gerenciamento estrito via uv, ruff e pytest-cov
└── README.md
```

---

## 🚀 Guia Rápido de Execução (Padrão `uv`)

> ⚠️ **Diretriz Inegociável:** O uso de `pip` é proibido neste projeto. Utilize exclusivamente o gerenciador **`uv`** para instalação de pacotes, sincronização de dependências e execução de scripts.

### 1. Configurar e Sincronizar o Ambiente
```bash
git clone https://github.com/klebermelo/v-max.git
cd v-max
git checkout dev

# Sincronizar ambiente virtual (.venv) e dependências via uv
uv sync
```

### 2. Executar a Pipeline Medalhão Completa (Bronze $\rightarrow$ Silver $\rightarrow$ Gold)
```bash
# 1. Camada Bronze: Ingestão bruta fiel com hash SHA-256 e carimbo temporal
uv run python -m src.ingestion.bronze_ingestion

# 2. Camada Silver: Limpeza de strings, tipagem DECIMAL/TIMESTAMP e deduplicação
uv run python -m src.processing.silver_processing

# 3. Camada Semântica: Criação das 9 views em português (zero storage overhead)
uv run python -m src.processing.semantic_views

# 4. Camada Gold: Modelagem Star Schema, cálculo de Lead Time e validação transacional
uv run python -m src.processing.gold_processing

# 5. Otimização Gold: Criação de índices B-Tree nas FKs e atualização de estatísticas (ANALYZE)
uv run python -m src.processing.gold_optimization
```

### 3. Iniciar o Servidor MCP Nativo (Model Context Protocol)
```bash
uv run python -m src.mcp.server
```

### 4. Subir o Dashboard Executivo (FastAPI + Google Charts)
```bash
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
- **Painel Executivo no Navegador:** [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa da API (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Executar Linting, Formatação e Testes Unitários (Cobertura $\ge 90\%$)
```bash
# Formatação e Linting estrito com Ruff
uv run ruff format .
uv run ruff check --select I --fix .
uv run ruff check .

# Suíte de Testes com verificação de cobertura mínima obrigatória de 90%
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```
- **Total de Testes Atuais:** **58 testes unitários aprovados** (superando a meta mínima de 42 testes).
- **Cobertura Total Atingida:** **95.48%** (superando o requisito mínimo de 90%).

### 6. Visualizar a Documentação Técnica (MkDocs Material)
```bash
uv run mkdocs serve -a 127.0.0.1:8001
```

---

## Onde a IA Errou

Em cumprimento aos critérios de transparência e rigor de engenharia, esta seção sintetiza todas as falhas técnicas, desvios de premissa e problemas de contexto cometidos pela Inteligência Artificial ao longo do ciclo de desenvolvimento do projeto V-MAX, bem como as respectivas correções implementadas (o relatório integral encontra-se em [`docs/erros_ia.md`](docs/erros_ia.md)):

1. **Ausência do Binário `uv` no Sandbox e Ausência Inicial do Plugin `pytest-cov`:**
   - **O que ocorreu:** Nas primeiras specs, o ambiente de sandbox da IA não continha o binário `uv` no `PATH` padrão e o pacote `pytest-cov` não estava instalado localmente. A IA chegou a criar temporariamente um script shell (*shim*) para simular o `uv` e executou o `pytest` puro sem aferir formalmente a meta de 90% de cobertura. Na primeira verificação formal com `pytest-cov`, constatou-se que a cobertura real estava em **85.06%** (abaixo dos 90%), pois o módulo `silver_processing.py` possuía apenas **69%** de cobertura (apenas funções auxiliares haviam sido testadas).
   - **Correção aplicada:** O *shim* foi removido imediatamente sem deixar rastros no Git, o `pytest-cov` foi instalado via `uv add --dev pytest-cov` e a suíte `tests/test_silver_processing.py` foi expandida com fixtures completas em memória cobrindo todas as transformações de tabelas e o orquestrador, elevando a cobertura da Silver para **99%** e a cobertura global do projeto para **95.48%**.

2. **Vulnerabilidade de Interpolação de String na Instrução `ATTACH` do DuckDB:**
   - **O que ocorreu:** No módulo `src/processing/silver_processing.py`, a IA montou a instrução de conexão ao banco Bronze concatenando caminhos via f-string (`f"ATTACH '{bronze_db_path}' AS con_bronze (READ_ONLY)"`), violando a regra de segurança da `skill.md` que exige *prepared statements* para parâmetros dinâmicos.
   - **Correção aplicada:** O comando foi refatorado na camada Silver e padronizado na camada Gold e no servidor MCP para utilizar parâmetros posicionais seguros: `con.execute("ATTACH ? AS con_bronze (READ_ONLY)", [str(bronze_db_path)])`.

3. **Tentativa de Sanitizar Coluna Inexistente de Telefone no Dataset Olist:**
   - **O que ocorreu:** A Spec 02 previa uma função de limpeza de números de telefone. A IA implementou a função `limpar_telefones` e seus testes unitários sem antes inspecionar e reportar ao usuário que nenhuma das 9 tabelas do dataset público Olist possui coluna de telefone (existem apenas prefixos de CEP, cidade e UF), nem dados demográficos de gênero.
   - **Correção aplicada:** A função `limpar_telefones` foi mantida como utilitário validado de higienização textual para demonstrar conformidade com os testes da spec, e a ausência da coluna na base real do Olist foi formalmente documentada no dicionário de dados e na arquitetura.

4. **Integridade Referencial em Pedidos sem Itens e Tentativa de `CREATE VIEW` em Conexão `read_only=True`:**
   - **O que ocorreu:**
     - Na modelagem da camada Gold, 775 pedidos da tabela `olist_orders_dataset` (majoritariamente com status `canceled` ou `unavailable`) não possuíam registros correspondentes em `olist_order_items_dataset`. Um `LEFT JOIN` a partir de pedidos geraria chaves estrangeiras nulas (`product_id` e `seller_id` nulos) na `fato_vendas`.
     - Posteriormente, na Spec 06-B, ao expor as views semânticas no servidor MCP (`src/mcp/server.py`), a IA tentou executar `CREATE OR REPLACE VIEW` dentro de uma conexão DuckDB aberta com `read_only=True`, disparando `InvalidInputException: Cannot execute statement of type "CREATE" on database "gold" which is attached in read-only mode!`.
     - Na Spec 06-C, os templates SQL iniciais referenciaram `f.data_compra_id = t.tempo_id` em vez das chaves físicas reais `f.data_pedido = t.data`.
   - **Correção aplicada:** A `fato_vendas` foi modelada no grão estrito de item de pedido via `INNER JOIN` protegido por bloco transacional (`BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`) com verificação de zero órfãos; no servidor MCP, substituiu-se a criação persistente por `CREATE OR REPLACE TEMP VIEW` (registrada na memória temporária da sessão sem violar o modo somente leitura); e os scripts SQL foram alinhados às chaves canônicas do esquema Gold.

5. **Erros de Tipagem no Google Charts (`Type mismatch. Value does not match type number`) e Interpretação Semântica:**
   - **O que ocorreu:** No frontend (`src/frontend/app.js`), a função `renderizarVisualizacaoDinamica` definia rigidamente todas as colunas a partir do índice 1 como `'number'`. Quando o usuário clicava em *"Melhores vendedores"* ou *"Entregas críticas"*, colunas textuais como `Localização` (`guariba (SP)`) ou `UF` (`RJ`) na posição 1 causavam falha de renderização no `google.visualization.DataTable`. Além disso, perguntas sobre *"Total de pedidos por região"* no roteador semântico retornavam faturamento por UF em vez de contagem de pedidos por macrorregião brasileira.
   - **Correção aplicada:** A renderização de dados tabulares/scorecards foi isolada utilizando `google.visualization.Table` com inferência dinâmica de tipos coluna a coluna (`typeof val === 'number' ? 'number' : 'string'`), enquanto o roteador semântico (`src/api/intent_router.py`) passou a distinguir explicitamente métricas de volume (`COUNT(DISTINCT order_id)`) de faturamento (`SUM(valor_total)`) e a mapear as 5 macrorregiões oficiais do Brasil via expressão `CASE` sobre a UF.

6. **Violações Pontuais do Limite de 40 Linhas por Função e Mensagem de Commit:**
   - **O que ocorreu:** Algumas funções de orquestração e roteamento ultrapassaram em 1 a 3 linhas o teto de 40 linhas após a quebra automática do formatador `ruff`, e na Spec 02 um commit foi registrado com a palavra `funcoes` sem acentuação (`funções`).
   - **Correção aplicada:** Todas as funções foram modularizadas em sub-rotinas coesas e auditadas via árvore sintática abstrata (`ast` do Python) para garantir que 100% das funções em `src/` possuam estritamente $\le 40$ linhas.
