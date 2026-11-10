# Dicionário de Dados e Modelo Dimensional — Camada Gold

A camada **Gold** (`data/gold/gold.db`) materializa o esquema dimensional em estrela (*Star Schema*) projetado para consultas OLAP de alta performance, relatórios executivos e consumo pelo servidor MCP.

---

## 1. Diagrama do Modelo Dimensional (Star Schema)

```text
                  ┌───────────────────────┐
                  │      dim_tempo        │
                  │ PK: data (DATE)       │
                  │ ano, mes, trimestre   │
                  └───────────┬───────────┘
                              │
┌───────────────────────┐     │     ┌───────────────────────┐
│     dim_clientes      │     │     │     dim_produtos      │
│ PK: customer_id       ├─────┼─────┤ PK: product_id        │
│ customer_unique_id    │     │     │ product_category_name │
│ customer_city, state  │     │     │ weight_g, dimensions  │
└───────────────────────┘     │     └───────────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │      fato_vendas      │
                  │ PK: (order_id, item)  │
                  │ FK: customer_id       │
                  │ FK: product_id        │
                  │ FK: seller_id         │
                  │ FK: data_pedido       │
                  │ valor_produto, frete  │
                  │ lead_time_dias        │
                  │ atraso_entrega_dias   │
                  │ nota_avaliacao        │
                  └───────────▲───────────┘
                              │
                  ┌───────────┴───────────┐
                  │    dim_vendedores     │
                  │ PK: seller_id         │
                  │ seller_city, state    │
                  └───────────────────────┘
```

---

## 2. Tabelas Dimensionais e Fato

### 2.1 `fato_vendas`
Tabela fato central no grão de **item de pedido**, com integridade referencial estrita garantida por transação ACID e índices B-Tree nas chaves estrangeiras.

| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `order_id` | `VARCHAR` | Identificador único do pedido. |
| `order_item_id` | `INTEGER` | Sequencial do item dentro do pedido. |
| `customer_id` | `VARCHAR` | Chave estrangeira para `dim_clientes`. |
| `product_id` | `VARCHAR` | Chave estrangeira para `dim_produtos`. |
| `seller_id` | `VARCHAR` | Chave estrangeira para `dim_vendedores`. |
| `data_pedido` | `DATE` | Chave estrangeira para `dim_tempo`. |
| `order_status` | `VARCHAR` | Status do pedido (`delivered`, `shipped`, `canceled`, etc.). |
| `valor_produto` | `DECIMAL(10,2)` | Preço unitário do item. |
| `valor_frete` | `DECIMAL(10,2)` | Valor do frete alocado ao item. |
| `valor_total` | `DECIMAL(10,2)` | Soma de `valor_produto + valor_frete`. |
| `order_purchase_timestamp` | `TIMESTAMP` | Data/hora exata da compra. |
| `order_delivered_customer_date` | `TIMESTAMP` | Data/hora real de entrega ao cliente. |
| `order_estimated_delivery_date` | `TIMESTAMP` | Data estimada de entrega no momento da compra. |
| `lead_time_dias` | `INTEGER` | Dias corridos entre a compra e a entrega efetiva. |
| `atraso_entrega_dias` | `INTEGER` | Diferença em dias entre a entrega real e a estimada (positivo = atraso). |
| `nota_avaliacao` | `DECIMAL(3,2)` | Nota média de avaliação (1 a 5) atribuída ao pedido. |

### 2.2 `dim_clientes`
| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `customer_id` | `VARCHAR` | Chave primária do cliente por pedido. |
| `customer_unique_id` | `VARCHAR` | Identificador canônico do cliente para análise de recorrência e churn. |
| `customer_zip_code_prefix` | `VARCHAR` | Prefixo de 5 dígitos do CEP. |
| `customer_city` | `VARCHAR` | Nome da cidade higienizado. |
| `customer_state` | `VARCHAR` | Sigla da Unidade Federativa (UF) em maiúsculas (2 caracteres). |

### 2.3 `dim_produtos`
| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `product_id` | `VARCHAR` | Chave primária do produto. |
| `product_category_name` | `VARCHAR` | Categoria em português (tratada com `nao_informado` se nula). |
| `product_category_name_english` | `VARCHAR` | Tradução da categoria para inglês. |
| `product_photos_qty` | `INTEGER` | Quantidade de fotos publicadas no anúncio. |
| `product_weight_g` | `INTEGER` | Peso do produto em gramas. |
| `product_length_cm` | `INTEGER` | Comprimento em centímetros. |
| `product_height_cm` | `INTEGER` | Altura em centímetros. |
| `product_width_cm` | `INTEGER` | Largura em centímetros. |

### 2.4 `dim_vendedores`
| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `seller_id` | `VARCHAR` | Chave primária do vendedor (lojista). |
| `seller_zip_code_prefix` | `VARCHAR` | Prefixo de CEP do lojista. |
| `seller_city` | `VARCHAR` | Cidade de origem do lojista. |
| `seller_state` | `VARCHAR` | Sigla da UF do lojista. |

### 2.5 `dim_tempo`
| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `data` | `DATE` | Chave primária da data civil (`YYYY-MM-DD`). |
| `ano` | `INTEGER` | Ano civil (ex: 2016, 2017, 2018). |
| `trimestre` | `INTEGER` | Trimestre do ano (1 a 4). |
| `mes` | `INTEGER` | Mês do ano (1 a 12). |
| `dia` | `INTEGER` | Dia do mês (1 a 31). |
| `dia_semana_iso` | `INTEGER` | Dia da semana ISO (1 = Segunda a 7 = Domingo). |
| `ano_mes` | `VARCHAR` | Representação `YYYY-MM` para agrupamentos temporais. |
| `fim_de_semana` | `BOOLEAN` | Indicador booleano de sábado ou domingo. |

### 2.6 `kpi_sumario_mensal`
Tabela agregada de indicadores executivos mensais:

| Coluna | Tipo DuckDB | Descrição |
|---|---|---|
| `ano_mes` | `VARCHAR` | Período de referência (`YYYY-MM`). |
| `volume_pedidos` | `BIGINT` | Total de pedidos distintos válidos no mês. |
| `itens_vendidos` | `BIGINT` | Total de itens comercializados no mês. |
| `receita_produtos` | `DECIMAL(14,2)` | Soma do valor de face dos produtos. |
| `receita_frete` | `DECIMAL(14,2)` | Soma dos valores de frete. |
| `receita_total` | `DECIMAL(14,2)` | GMV Total faturado no mês. |
| `ticket_medio` | `DECIMAL(10,2)` | Receita total dividida pelo volume de pedidos. |
| `lead_time_medio_dias` | `DOUBLE` | Média de dias de entrega no mês. |
| `avaliacao_media` | `DOUBLE` | Nota média das avaliações do mês. |
