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

---

## 6. Conclusão da Spec 04 (Repositório de Consultas Analíticas Avançadas)

**Data/Hora:** 10/11/2026 - 15:50  
**Branch:** `dev`  
**Commit:** `b23715d` (`feat: consultas sql avancadas com window functions e ctes`)

### Resumo das Ações Realizadas:
1. **Estrutura de Queries (`src/sql/`)**:
   - Criação de arquivos SQL independentes e puros para atender às análises de negócio solicitadas, respeitando a separação entre Python (orquestrador) e SQL puro (`skill.md`).
2. **Consultas Implementadas e Validadas Diretamente no DuckDB (`gold.db`)**:
   - `src/sql/gmv_por_categoria.sql`:
     - Utiliza Common Table Expressions (CTEs) encadeadas (`vendas_validas`, `gmv_categoria`, `gmv_total`).
     - Calcula Gross Merchandise Volume (GMV), quantidade de pedidos distintos, quantidade de itens, preço médio e percentual de participação de cada categoria sobre o faturamento total.
     - Retornou 74 categorias com faturamento consolidado.
   - `src/sql/scorecard_vendedores.sql`:
     - Utiliza Window Functions (`RANK()`, `DENSE_RANK()`) com partição e ordenação.
     - Avalia 3.053 vendedores em faturamento, volume de pedidos e nota média de avaliação, gerando ranking nacional, ranking estadual (`rank_faturamento_uf`) e índice unificado de scorecard.
   - `src/sql/risco_churn.sql`:
     - Analisa o comportamento dos clientes no nível de pessoa física (`customer_unique_id`).
     - Filtra compras pós-incidente com atraso na entrega superior a 5 dias (`atraso_entrega_dias > 5`) OU nota de avaliação baixa ($\le 2$).
     - Identificou 14.557 clientes em risco de evasão, quantificando o valor financeiro em risco e sinalizando se o cliente voltou a comprar após o incidente.
3. **Qualidade e Versionamento**:
   - Compatibilidade de sintaxe 100% validada no DuckDB.
   - Verificação com `ruff` aprovada sem apontamentos.
   - Commit realizado na branch `dev` com a mensagem exata solicitada.

---

## 7. Visualização das Tabelas da Camada Silver (Amostragem de 5 Linhas)

**Data/Hora:** 10/11/2026 - 15:51  
**Origem:** `data/silver/silver.db`

### 1. `olist_customers_dataset`
- **Colunas:** `customer_id`, `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('06b8999e2fba1a1fbc88172c00ba8bc7', '861eff4711a542e4b93843c6dd7febb0', '14409', 'franca', 'SP', '2026-11-10T16:52:37.676918+00:00')`
  2. `('18955e83d337fd6b2def6b18a428ac77', '290c77bc529b7ac935b93aa66c333dc3', '09790', 'sao bernardo do campo', 'SP', '2026-11-10T16:52:37.676918+00:00')`
  3. `('4e7b3e00288586ebd08712fdd0374a03', '060e732b5b29e8181a18229c7b0b2b5e', '01151', 'sao paulo', 'SP', '2026-11-10T16:52:37.676918+00:00')`
  4. `('b2b6027bc5c5109e529d4dc6358b12c3', '259dac757896d24d7702b9acbbff3f3c', '08775', 'mogi das cruzes', 'SP', '2026-11-10T16:52:37.676918+00:00')`
  5. `('4f2d8ab171c80ec8364f7c12e35b23ad', '345ecd01c38d18a9036ed96c73b8d066', '13056', 'campinas', 'SP', '2026-11-10T16:52:37.676918+00:00')`

### 2. `olist_geolocation_dataset`
- **Colunas:** `geolocation_zip_code_prefix`, `geolocation_lat`, `geolocation_lng`, `geolocation_city`, `geolocation_state`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('01037', -23.54562128115268, -46.63929204800168, 'sao paulo', 'SP', '2026-11-10T16:52:38.613378+00:00')`
  2. `('01046', -23.546081127035535, -46.64482029837157, 'sao paulo', 'SP', '2026-11-10T16:52:38.613378+00:00')`
  3. `('01046', -23.54612896641469, -46.64295148361138, 'sao paulo', 'SP', '2026-11-10T16:52:38.613378+00:00')`
  4. `('01041', -23.5443921648681, -46.63949930627844, 'sao paulo', 'SP', '2026-11-10T16:52:38.613378+00:00')`
  5. `('01035', -23.541577961711493, -46.64160722329613, 'sao paulo', 'SP', '2026-11-10T16:52:38.613378+00:00')`

### 3. `olist_order_items_dataset`
- **Colunas:** `order_id`, `order_item_id`, `product_id`, `seller_id`, `shipping_limit_date`, `price`, `freight_value`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('00010242fe8c5a6d1ba2dd792cb16214', 1, '4244733e06e7ecb4970a6e2683c13e61', '48436dade18ac8b2bce089ec2a041202', '2017-09-19 09:45:35', Decimal('58.90'), Decimal('13.29'), '2026-11-10T16:52:35.293772+00:00')`
  2. `('00018f77f2f0320c557190d7a144bdd3', 1, 'e5f2d52b802189ee658865ca93d83a8f', 'dd7ddc04e1b6c2c614352b383efe2d36', '2017-05-03 11:05:13', Decimal('239.90'), Decimal('19.93'), '2026-11-10T16:52:35.293772+00:00')`
  3. `('000229ec398224ef6ca0657da4fc703e', 1, 'c777355d18b72b67abbeef9df44fd0fd', '5b51032eddd242adc84c38acab88f23d', '2018-01-18 14:48:30', Decimal('199.00'), Decimal('17.87'), '2026-11-10T16:52:35.293772+00:00')`
  4. `('00024acbcdf0a6daa1e931b038114c75', 1, '7634da152a4610f1595efa32f14722fc', '9d7a1d34a5052409006425275ba1c2b4', '2018-08-15 10:10:18', Decimal('12.99'), Decimal('12.79'), '2026-11-10T16:52:35.293772+00:00')`
  5. `('00042b26cf59d7ce69dfabb4e55b4fd9', 1, 'ac6c3623068f30de03045865e4e10089', 'df560393f3a51e74553ab94004ba5c87', '2017-02-13 13:57:51', Decimal('199.90'), Decimal('18.14'), '2026-11-10T16:52:35.293772+00:00')`

### 4. `olist_order_payments_dataset`
- **Colunas:** `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('b81ef226f3fe1789b1e8b2acac839d17', 1, 'credit_card', 8, Decimal('99.33'), '2026-11-10T16:52:36.528865+00:00')`
  2. `('a9810da82917af2d9aefd1278f1dcfa0', 1, 'credit_card', 1, Decimal('24.39'), '2026-11-10T16:52:36.528865+00:00')`
  3. `('25e8ea4e93396b6fa0d3dd708e76c1bd', 1, 'credit_card', 1, Decimal('65.71'), '2026-11-10T16:52:36.528865+00:00')`
  4. `('ba78997921bbcdc1373bb41e913ab953', 1, 'credit_card', 8, Decimal('107.78'), '2026-11-10T16:52:36.528865+00:00')`
  5. `('42fdf880ba16b47b59251dd489d4441a', 1, 'credit_card', 2, Decimal('128.45'), '2026-11-10T16:52:36.528865+00:00')`

### 5. `olist_order_reviews_dataset`
- **Colunas:** `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('7bc2406110b926393aa56f80a40eba40', '73fc7af87114b39712e6da79b0a377eb', 4, None, None, 2018-01-18, '2018-01-18 21:46:59', '2026-11-10T16:52:36.731970+00:00')`
  2. `('80e641a11e56f04c1ad469d5645fdfde', 'a548910a1c6147796b98fdf73dbeba33', 5, None, None, 2018-03-10, '2018-03-11 03:05:13', '2026-11-10T16:52:36.731970+00:00')`
  3. `('228ce5500dc1d8e020d8d1322874b6f0', 'f9e4b658b201a9f2ecdecbb34bed034b', 5, None, None, 2018-02-17, '2018-02-18 14:36:24', '2026-11-10T16:52:36.731970+00:00')`
  4. `('e64fb393e7b32834bb789ff8bb30750e', '658677c97b385a9be170737859d3511b', 5, None, 'Recebi bem antes do prazo estipulado.', 2017-04-21, '2017-04-21 22:02:06', '2026-11-10T16:52:36.731970+00:00')`
  5. `('f7c4243c7fe1938f181bec41a392bdeb', '8e6bfb81e283fa7e4f11123a3fb894f1', 5, None, 'Parabéns lojas lannister...', 2018-03-01, '2018-03-02 10:26:53', '2026-11-10T16:52:36.731970+00:00')`

### 6. `olist_orders_dataset`
- **Colunas:** `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp`, `order_approved_at`, `order_delivered_carrier_date`, `order_delivered_customer_date`, `order_estimated_delivery_date`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('e481f51cbdc54678b7cc49136f2d6af7', '9ef432eb6251297304e76186b10a928d', 'delivered', '2017-10-02 10:56:33', '2017-10-02 11:07:15', '2017-10-04 19:55:00', '2017-10-10 21:25:13', '2017-10-18 00:00:00', '2026-11-10T16:52:34.988306+00:00')`
  2. `('53cdb2fc8bc7dce0b6741e2150273451', 'b0830fb4747a6c6d20dea0b8c802d7ef', 'delivered', '2018-07-24 20:41:37', '2018-07-26 03:24:27', '2018-07-26 14:31:00', '2018-08-07 15:27:45', '2018-08-13 00:00:00', '2026-11-10T16:52:34.988306+00:00')`
  3. `('47770eb9100c2d0c44946d9cf07ec65d', '41ce2a54c0b03bf3443c3d931a367089', 'delivered', '2018-08-08 08:38:49', '2018-08-08 08:55:23', '2018-08-08 13:50:00', '2018-08-17 18:06:29', '2018-09-04 00:00:00', '2026-11-10T16:52:34.988306+00:00')`
  4. `('949d5b44dbf5de918fe9c16f97b45f8a', 'f88197465ea7920adcdbec7375364d82', 'delivered', '2017-11-18 19:28:06', '2017-11-18 19:45:59', '2017-11-22 13:39:59', '2017-12-02 00:28:42', '2017-12-15 00:00:00', '2026-11-10T16:52:34.988306+00:00')`
  5. `('ad21c59c0840e6cb83a9ceb5573f8159', '8ab97904e6daea8866dbdbc4fb7aad2c', 'delivered', '2018-02-13 21:18:39', '2018-02-13 22:20:29', '2018-02-14 19:46:34', '2018-02-16 18:17:02', '2018-02-26 00:00:00', '2026-11-10T16:52:34.988306+00:00')`

### 7. `olist_products_dataset`
- **Colunas:** `product_id`, `product_category_name`, `product_name_lenght`, `product_description_lenght`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('1e9e8ef04dbcff4541ed26657ea517e5', 'perfumaria', 40, 287, 1, 225, 16, 10, 14, '2026-11-10T16:52:38.091230+00:00')`
  2. `('3aa071139cb16b67ca9e5dea641aaa2f', 'artes', 44, 276, 1, 1000, 30, 18, 20, '2026-11-10T16:52:38.091230+00:00')`
  3. `('96bd76ec8810374ed1b65e291975717f', 'esporte_lazer', 46, 250, 1, 154, 18, 9, 15, '2026-11-10T16:52:38.091230+00:00')`
  4. `('cef67bcfe19066a932b7673e239eb23d', 'bebes', 27, 261, 1, 371, 26, 4, 26, '2026-11-10T16:52:38.091230+00:00')`
  5. `('9dc1a7de274444849c219cff195d0b71', 'utilidades_domesticas', 37, 402, 4, 625, 20, 17, 13, '2026-11-10T16:52:38.091230+00:00')`

### 8. `olist_sellers_dataset`
- **Colunas:** `seller_id`, `seller_zip_code_prefix`, `seller_city`, `seller_state`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('3442f8959a84dea7ee197c632cb2df15', '13023', 'campinas', 'SP', '2026-11-10T16:52:38.203831+00:00')`
  2. `('d1b65fc7debc3361ea86b5f14c68d2e2', '13844', 'mogi guacu', 'SP', '2026-11-10T16:52:38.203831+00:00')`
  3. `('ce3ad9de960102d0677a81f5d0bb7b2d', '20031', 'rio de janeiro', 'RJ', '2026-11-10T16:52:38.203831+00:00')`
  4. `('c0f3eea2e14555b6faeea3dd58c1b1c3', '04195', 'sao paulo', 'SP', '2026-11-10T16:52:38.203831+00:00')`
  5. `('51a04a8a6bdcb23deccc82b0b80742cf', '12914', 'braganca paulista', 'SP', '2026-11-10T16:52:38.203831+00:00')`

### 9. `product_category_name_translation`
- **Colunas:** `product_category_name`, `product_category_name_english`, `_processed_at`
- **Amostra (5 linhas):**
  1. `('beleza_saude', 'health_beauty', '2026-11-10T16:52:39.468490+00:00')`
  2. `('informatica_acessorios', 'computers_accessories', '2026-11-10T16:52:39.468490+00:00')`
  3. `('automotivo', 'auto', '2026-11-10T16:52:39.468490+00:00')`
  4. `('cama_mesa_banho', 'bed_bath_table', '2026-11-10T16:52:39.468490+00:00')`
  5. `('moveis_decoracao', 'furniture_decor', '2026-11-10T16:52:39.468490+00:00')`
