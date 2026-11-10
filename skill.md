# 🛠️ Skill de Engenharia de Dados: Python & DuckDB

Este documento define as regras, padrões arquiteturais e boas práticas que devem ser rigorosamente seguidos no desenvolvimento do projeto V-MAX e demais pipelines de dados da equipe.

---

## 1. Gerenciamento de Ambiente e Pacotes (`uv`)
Utilizamos o **`uv`** como nosso gerenciador de pacotes e ambientes virtuais, devido à sua extrema velocidade e confiabilidade. 
* 🚫 **REGRA DE OURO:** O uso do `pip` é expressamente **PROIBIDO** neste projeto.
* **Inicialização:** Sempre inicie projetos usando `uv init`.
* **Adição de pacotes:** Utilize `uv add <pacote>` e `uv add --dev <pacote>` para dependências de desenvolvimento.
* **Execução:** Execute scripts sempre pelo contexto do uv, ex: `uv run python src/main.py`.

---

## 2. Estrutura Modular
O projeto deve ser altamente coeso e com baixo acoplamento (Single Responsibility Principle). O código funcional deve ser separado de testes, documentação e dados.

**Padrão de Diretórios:**

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


---

## 3. Linting e Formatação de Código (`ruff`)
O código deve ser legível, limpo e padronizado. Usamos exclusivamente o **`ruff`** para substituir o `flake8`, `black` e `isort`.
* **Formatação:** `uv run ruff format .` (Aplica a formatação de código).
* **Lint e Imports:** `uv run ruff check --select I --fix .` (Organiza imports e corrige problemas de sintaxe de forma automática).
* Todos os scripts Python devem passar pelo `ruff` antes de qualquer commit.

---

## 4. Testes Automatizados e Cobertura (`pytest`)
A garantia de qualidade é inegociável. Todo código novo deve ser testado.
* **Ferramentas:** `pytest` e `pytest-cov`.
* **Cobertura Mínima:** É **obrigatório** ter no mínimo **90%** de cobertura de testes.
* **Validação:** A pipeline falhará caso a cobertura não seja atingida. O comando padrão de execução será:
  `uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90`
* **Padrão de Teste:** Concentre-se em testar comportamentos (transformações de dados, higienização) e não apenas detalhes de implementação (mocking excessivo).

---

## 5. Documentação (`mkdocs-material`)
A documentação do projeto, incluindo arquitetura de dados e dicionário de dados, deve viver junto com o código.
* **Framework:** `mkdocs` utilizando o tema `mkdocs-material`.
* A documentação deve ser estruturada na pasta `docs/` e gerenciada pelo `mkdocs.yml` na raiz.
* As docs devem conter: arquitetura em medalhão, dependências, instruções de deploy e modelo dimensional da camada Gold.

---

## 6. Boas Práticas Python 
* **Type Hinting:** O uso de *Type Hints* (dicas de tipagem) é obrigatório em todas as assinaturas de funções e métodos.
* **Docstrings:** Utilize docstrings em formato padrão (ex: Google Style) para descrever o que a função faz, seus argumentos e retornos.
* **Logging vs Print:** **NUNCA** use `print()` em produção. Utilize a biblioteca padrão `logging` para registrar os passos da pipeline, facilitando a observabilidade (INFO, WARNING, ERROR).

---

## 7. Boas Práticas DuckDB
* **Conexões Gerenciadas:** Use o DuckDB preferencialmente através de Context Managers (`with duckdb.connect() as con:`) para garantir o fechamento seguro de conexões em arquivos estáticos (bancos `.db`).
* **Segurança SQL:** Nunca concatene strings diretamente em consultas SQL. Utilize parâmetros/prepared statements para evitar *SQL Injection* ou quebras de sintaxe (ex: `con.execute("SELECT * FROM table WHERE id = ?", [id_var])`).
* **Memória e I/O:** Para grandes volumes de dados, delegue as transformações ao motor do DuckDB (utilizando SQL) em vez de trazer os dados para a memória via Pandas/DataFrames sempre que possível.
* **Modularidade SQL:** Mantenha lógicas analíticas complexas, como CTEs e Window Functions, em arquivos `.sql` puros na pasta `src/sql/`, lendo-os no Python, para que o código Python atue apenas como orquestrador.