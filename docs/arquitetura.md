# Documentação Arquitetural e Camada Semântica — Projeto V-MAX

O projeto **V-MAX** adota a **Arquitetura em Medalhão (Bronze $\rightarrow$ Silver $\rightarrow$ Gold)** implementada no motor colunar de alta performance **DuckDB**, complementada por uma **Camada Semântica de Views em Português** e um servidor **Model Context Protocol (MCP)** nativo para agentes de inteligência artificial.

---

## 1. Fluxo de Dados Medalhão

```text
       data/raw/ (.csv.gz)
              │
              ▼ (Ingestão Fiel, all_varchar=True, SHA-256)
      data/bronze/bronze.db
              │
              ▼ (Sanitização, DECIMAL, TIMESTAMP, Limpeza)
      data/silver/silver.db
              │  ├── Tabelas Físicas Originais (olist_*_dataset)
              │  └── Views Semânticas em Português (pedidos, clientes, ...)
              ▼ (Modelagem Dimensional, Integridade Referencial, Lead Time)
       data/gold/gold.db
                 ├── fato_vendas (com índices B-Tree)
                 ├── dim_clientes, dim_produtos, dim_vendedores, dim_tempo
                 ├── kpi_sumario_mensal
                 └── Espelho das Views Semânticas (para exploração MCP)
```

---

## 2. Decisão Arquitetural: Camada Semântica por Views (Zero Storage Overhead)

### Por que não renomeamos os arquivos ou tabelas físicas da fonte bruta?
1. **Preservação da Fonte da Verdade e Rastreabilidade:** Os datasets do Kaggle (Olist) possuem convenção de nomes estabelecida (`olist_orders_dataset`, etc.). Preservar esses identificadores garante conformidade com a auditoria criptográfica SHA-256 e simplifica atualizações com novas extrações de dados.
2. **Abstração Amigável para LLMs e Analistas:** Assistentes de inteligência artificial e analistas de negócio operam com maior assertividade ao consultar entidades como `pedidos`, `clientes` ou `itens_pedido`.
3. **Custo Zero de Armazenamento:** As views do DuckDB (`CREATE OR REPLACE VIEW ... AS SELECT * FROM ...`) não duplicam registros em disco, atuando como ponte direta de consulta com custo zero de I/O adicional.

---

## 3. Dicionário das Views Semânticas em Português

| View Semântica | Tabela Física Subjacente | Descrição Funcional |
|---|---|---|
| `pedidos` | `olist_orders_dataset` | Dados cadastrais e status dos pedidos, datas de compra, aprovação e entrega. |
| `itens_pedido` | `olist_order_items_dataset` | Itens transacionados, preços de produtos e valores de frete em `DECIMAL(10,2)`. |
| `pagamentos` | `olist_order_payments_dataset` | Meios de pagamento (cartão, boleto, voucher), parcelas e valores. |
| `avaliacoes` | `olist_order_reviews_dataset` | Notas de satisfação do cliente (1 a 5) e comentários de feedback. |
| `clientes` | `olist_customers_dataset` | Localização do cliente (cidade e UF) e chaves identificadoras. |
| `vendedores` | `olist_sellers_dataset` | Localização do lojista parceiro (cidade e UF). |
| `produtos` | `olist_products_dataset` | Atributos físicos (peso, dimensões) e categoria do item. |
| `traducao_categorias` | `product_category_name_translation` | Mapeamento bilíngue (Português $\leftrightarrow$ Inglês) das categorias. |
| `geolocalizacao` | `olist_geolocation_dataset` | Coordenadas de latitude/longitude e prefixos de CEP. |

---

## 4. Integração com Servidor MCP e IA

O servidor nativo `src/mcp/server.py` permite que agentes de IA inspecionem tanto as tabelas analíticas (`fato_vendas`, `kpi_sumario_mensal`) quanto as 9 views semânticas, viabilizando consultas dinâmicas de negócio em português com resposta em JSON e validação estrita *Read-Only*.
