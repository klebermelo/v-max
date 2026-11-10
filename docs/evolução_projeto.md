# Histórico da Evolução do Projeto V-MAX

Este documento registra o histórico sequencial das entregas, respostas e marcos fornecidos pela IA durante o desenvolvimento do projeto **V-MAX**.

---

## 1. Conclusão da Spec 01 (Setup do Projeto e Camada Bronze)

**Data/Hora:** 10/11/2026 - 13:28  
**Branch:** `dev`  
**Commit:** `65d7122` (`feat: setup inicial, uv e ingestao fiel na camada bronze`)

### Resumo das Ações Realizadas:
1. **Ambiente (`uv`) e Versionamento (`git`)**:
   - Configuração do projeto via `pyproject.toml` contendo dependências do DuckDB, Pandas, Streamlit e grupo de desenvolvimento (`pytest`, `ruff`).
   - Branch `dev` configurada.
2. **Estrutura Modular de Diretórios**:
   - Criação da estrutura completa conforme a `skill.md`: `data/raw/`, `data/bronze/`, `data/silver/`, `data/gold/`, `src/ingestion/`, `src/processing/`, `src/sql/`, `src/mcp/`, `src/api/`, `tests/` e `docs/`.
3. **Camada Bronze (`src/ingestion/bronze_ingestion.py`)**:
   - Implementação modular com Type Hints, Google Style Docstrings e biblioteca `logging`.
   - Funções: `calculate_sha256`, `extract_table_name`, `list_raw_csv_files`, `ingest_csv_to_bronze` e `run_bronze_ingestion`.
   - Conexão gerenciada via Context Manager (`with duckdb.connect(...) as con:`) e Prepared Statements (`?`).
   - Ingestão fiel (`all_varchar = true`) das 9 tabelas do dataset Olist para `data/bronze/bronze.db`.
   - Inclusão dos campos de auditoria temporal `_loaded_at` e rastreabilidade `_file_sha256`.
4. **Documentação Inicial (`README.md`)**:
   - Seção "Fonte de Dados" especificando a base *Brazilian E-Commerce Public Dataset by Olist (Kaggle)*.
   - Indicação explícita da licença de uso dos dados (**CC BY-NC-SA 4.0**).
5. **Qualidade e Testes**:
   - Criados testes unitários em `tests/test_bronze_ingestion.py` (6/6 testes passando).
   - Formatação e linting aplicados com `ruff`.

---

## 2. Conclusão da Spec 02 (Sanitização e Higienização — Camada Silver)

**Data/Hora:** 10/11/2026 - 13:54  
**Branch:** `dev`  
**Commit:** `40a05bc` (`feat: sanitizacao silver com funcoes modulares e logging`)

### Resumo das Ações Realizadas:
1. **Processamento Silver e Funções Modulares (`src/processing/silver_processing.py`)**:
   - Aplicação do princípio de responsabilidade única (Single Responsibility Principle) com limite rigoroso de $\le 40$ linhas por função.
   - Implementação das funções utilitárias puras: `limpar_telefones`, `padronizar_moedas` e `padronizar_texto`.
2. **Transformações em Banco DuckDB**:
   - Conversão de moedas e fretes para `DECIMAL(10,2)`.
   - Padronização de datas para `DATE` e carimbos de data/hora para `TIMESTAMP`.
   - Higienização e remoção de espaços em branco e padronização em minúsculas para categorias e status.
   - Sanitização de CEPs/identificadores mantendo padrão puramente numérico.
3. **Observabilidade e Armazenamento**:
   - Logging estruturado registrando o início, progresso e fim do processamento de cada uma das 9 tabelas.
   - Persistência dos dados higienizados no banco DuckDB `data/silver/silver.db`.
4. **Testes Unitários**:
   - Testes criados em `tests/test_silver_processing.py` validando limpeza de telefones, moedas, textos e integridade das tabelas temporárias (13/13 testes passando).

---

## 3. Conclusão da Spec 03 (Modelagem Dimensional e Analítica — Camada Gold)

**Data/Hora:** 10/11/2026 - 14:07  
**Branch:** `dev`  
**Commit:** `1b9abd3` (`feat: modelagem dimensional gold e calculo de lead time`)

### Resumo das Ações Realizadas:
1. **Separação Arquitetural SQL Puro / Orquestrador Python**:
   - Queries dimensionais isoladas na pasta `src/sql/gold/`:
     - `dim_clientes.sql`: Grão por cliente (`customer_id`, `customer_unique_id`, cidade, UF).
     - `dim_produtos.sql`: Grão por produto com categoria traduzida em inglês.
     - `dim_vendedores.sql`: Grão por vendedor com localização.
     - `dim_tempo.sql`: Calendário diário contínuo de 04/09/2016 a 17/10/2018 (774 dias).
     - `fato_vendas.sql`: Grão por item de pedido, com cálculo de `lead_time_dias`, `atraso_entrega_dias` e `nota_avaliacao`.
     - `kpi_sumario_mensal.sql`: Agregações mensais de receita total, volume de pedidos e ticket médio (excluindo pedidos cancelados/indisponíveis).
2. **Orquestrador Python (`src/processing/gold_processing.py`)**:
   - Todas as funções com $\le 40$ linhas, Google Style Docstrings, Type Hints e observabilidade via `logging`.
   - Prepared statements com `con.execute("ATTACH ? AS silver (READ_ONLY)", [str(silver_db_path)])`.
   - Execução transacional com `BEGIN TRANSACTION`, `COMMIT` e `ROLLBACK` em caso de falha.
3. **Validação Estrita de Integridade Referencial**:
   - Verificação automática de chaves estrangeiras (`customer_id`, `product_id`, `seller_id`, `data_pedido`).
   - Disparo da exceção `IntegridadeReferencialError` e registro em log de nível `ERROR` caso haja órfãos.
   - Validação confirmou 0 órfãos em todas as dimensões.
4. **Testes Unitários**:
   - 10 novos testes adicionados em `tests/test_gold_processing.py` totalizando 23 testes na suíte.

---

## 4. Correção de Vulnerabilidade SQL e Cobertura de Testes (Fix Pós-Spec 03)

**Data/Hora:** 10/11/2026 - 14:37  
**Branch:** `dev`  
**Commit:** `7cccb64` (`fix: corrige vulnerabilidade sql attach e atinge cobertura silver > 90%`)

### Resumo das Ações Realizadas:
1. **Segurança SQL no `ATTACH`**:
   - Refatoração do script `src/processing/silver_processing.py` para eliminar a f-string e adotar prepared statement parametrizado: `con_silver.execute("ATTACH ? AS con_bronze (READ_ONLY)", [str(bronze_db_path)])`.
2. **Cobertura de Testes**:
   - Reestruturação do arquivo `tests/test_silver_processing.py` para cobrir todas as funções de transformação das tabelas e a rotina principal do pipeline `executar_pipeline_silver`.
   - Execução via `uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90`.
   - **Resultado alcançado:**
     - `bronze_ingestion.py`: 98%
     - `gold_processing.py`: 99%
     - `silver_processing.py`: 99% (subiu de 69% para 99%)
     - **Total Geral:** **98.76%** de cobertura (24/24 testes passando).

---

## 5. Validação das Consultas SQL da Spec 04 (Em andamento)

**Data/Hora:** 10/11/2026 - 14:41  
**Status:** Scripts SQL criados e validados com sucesso no banco `data/gold/gold.db`:
- `src/sql/gmv_por_categoria.sql`: Retornou 74 categorias com GMV, volume de itens, preço médio e percentual de participação.
- `src/sql/scorecard_vendedores.sql`: Retornou 3.053 vendedores ranqueados com Window Functions (`RANK()` e `DENSE_RANK()`).
- `src/sql/risco_churn.sql`: Retornou 14.557 clientes pós-incidente analisados no grão de `customer_unique_id`.
