# V-MAX — Pipeline Analítico de E-Commerce (Arquitetura em Medalhão com DuckDB)

O projeto **V-MAX** implementa uma plataforma moderna de Engenharia de Dados em Python e **DuckDB**, estruturada sob a **Arquitetura em Medalhão (Bronze, Silver e Gold)** para ingestão, higienização, modelagem dimensional e análise de dados de e-commerce.

---

## Arquitetura e Estrutura do Projeto

```text
v-max/
├── data/               # Diretórios de dados particionados (raw, bronze, silver, gold)
├── docs/               # Documentação do projeto (MkDocs)
├── src/                # Código fonte modular
│   ├── ingestion/      # Scripts de extração/ingestão (Raw -> Bronze)
│   ├── processing/     # Scripts de transformação (Silver, Gold)
│   ├── sql/            # Repositório de queries analíticas (.sql)
│   ├── mcp/            # Servidor Model Context Protocol
│   └── api/            # Backend do Dashboard
├── tests/              # Testes unitários e de integração
├── pyproject.toml      # Configurações do projeto, uv, ruff e pytest
└── README.md
```

### Camada Bronze (Ingestão Fiel)
- Leitura direta dos arquivos CSV brutos em `data/raw/` para o banco colunar `data/bronze/bronze.db`.
- Preservação integral dos dados originais (`all_varchar=True`), sem tipagem ou limpeza prévia.
- Rastreabilidade e auditoria garantidas via cálculo de hash **SHA-256** (`_file_sha256`) de cada arquivo ingerido e carimbo temporal UTC (`_loaded_at`).

---

## Fonte de Dados

Os dados utilizados neste projeto provêm do conjunto de dados público **Brazilian E-Commerce Public Dataset by Olist**, disponibilizado originalmente na plataforma **Kaggle** ([Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)).

A base reúne informações reais (anonimizadas) de cerca de 100 mil pedidos realizados entre 2016 e 2018 em múltiplos marketplaces no Brasil, abrangendo pedidos, itens, pagamentos, avaliações de clientes, produtos, vendedores e geolocalização.

### Licença de Uso dos Dados
- **Licença:** **CC BY-NC-SA 4.0** (*Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International*).
- **Permissão de Uso Público:** Esta licença permite copiar, redistribuir, remixar, transformar e criar a partir do material para fins públicos, acadêmicos e não comerciais, desde que seja atribuído o devido crédito ao autor original (**Olist**) e que eventuais obras derivadas sejam compartilhadas sob a mesma licença.

---

## Como Executar (Gerenciamento via `uv`)

1. **Sincronizar o ambiente virtual e dependências:**
   ```bash
   uv sync
   ```
2. **Executar a ingestão da Camada Bronze:**
   ```bash
   uv run python -m src.ingestion.bronze_ingestion
   ```
3. **Formatação e Linting (`ruff`):**
   ```bash
   uv run ruff format .
   uv run ruff check --select I --fix .
   ```
4. **Testes Automatizados (`pytest`):**
   ```bash
   uv run pytest tests/
   ```
