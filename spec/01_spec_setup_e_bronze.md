# Spec 01: Setup do Projeto e Camada Bronze

Você é o assistente de IA desenvolvendo o projeto V-MAX. 
**AÇÃO OBRIGATÓRIA INICIAL:** Antes de executar qualquer passo abaixo, leia o arquivo `skill.md` na raiz do projeto e aplique rigorosamente todas as suas diretrizes ao longo desta e das próximas execuções.

## Tarefas
1. **Inicialização do Ambiente (Padrão uv):**
   - Utilize a ferramenta `uv` no terminal para inicializar o projeto Python (`uv init`). Lembre-se: o uso do `pip` é expressamente proibido, conforme a `skill.md`.
   - Crie o ambiente virtual com `uv venv` e ative-o.
   - Adicione o duckdb como dependência do projeto (`uv add duckdb`).
2. **Versionamento Git:**
   - Execute `git init`.
   - Crie a branch `dev` e mude para ela (`git checkout -b dev`).
3. **Estrutura de Diretórios:**
   - Crie a estrutura de pastas modular (conforme `skill.md`): `data/raw/`, `data/bronze/`, `data/silver/`, `data/gold/`, `src/`, `src/ingestion/`, `tests/` e `docs/`.
4. **Camada Bronze (Ingestão Fiel):**
   - Crie o script `src/ingestion/bronze_ingestion.py`.
   - Implemente o script para ler todos os arquivos CSV do dataset Olist (localizados em `data/raw/`) e salvá-los no banco DuckDB `data/bronze/bronze.db`.
   - Utilize Context Managers para a conexão do DuckDB (`with duckdb.connect...`).
   - **Regra de Ouro:** Não faça nenhuma alteração, tipagem ou limpeza nos dados nesta etapa.
   - Adicione um carimbo de auditoria temporal (`_loaded_at`).
   - Calcule o hash SHA-256 dos arquivos lidos para rastreabilidade.
   - Utilize a biblioteca `logging` para os registros (proibido `print()`).
5. **Documentação Inicial:**
   - Crie o `README.md` na raiz.
   - Adicione a seção "Fonte de Dados", informando que a base é o Brazilian E-Commerce Public Dataset by Olist (Kaggle).
   - Inclua explicitamente a **Licença** dos dados no README para garantir permissão de uso público.
6. **Controle de Qualidade e Commit:**
   - Rode o formatador e o linter (`uv run ruff format .` e `uv run ruff check --select I --fix .`).
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: setup inicial, uv e ingestao fiel na camada bronze`.