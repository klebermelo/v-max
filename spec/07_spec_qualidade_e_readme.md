# Spec 07: Testes, Linting e Documentação Final

Finalize o projeto focando na garantia de qualidade exigida para a pós-graduação.

## Tarefas
1. **Ferramentas de Qualidade:**
   - Garanta que `pytest`, `pytest-cov` e o linter `ruff` estão instalados via `uv`.
2. **Suíte de Testes (TDD/Garantia de Qualidade):**
   - Crie no mínimo 42 testes unitários na pasta `tests/`.
   - Teste as funções modulares da camada Silver (ex: testar se `limpar_telefones` remove letras, testar se `padronizar_moedas` retorna decimal).
   - Teste as chaves de integridade referencial da camada Gold.
   - Assegure que a execução de `pytest --cov=src` atinja **cobertura mínima de 90%**.
3. **Atualização do README:**
   - Documente o passo a passo de execução (como instalar via `uv`, como rodar a pipeline Bronze->Silver->Gold, como iniciar o servidor MCP e acessar o Dashboard FastAPI).
   - **Seção Crítica (Feedback):** Adicione uma seção literal chamada `## Onde a IA Errou`, com um texto descrevendo as falhas de contexto, correções manuais de queries ou dificuldades da IA durante as gerações anteriores deste projeto.
4. **Linting Estrito:**
   - Rode o `ruff` em todo o diretório `src/` e corrija os apontamentos de formatação e imports.
5. **Commit e Orientação Final:**
   - Adicione os arquivos gerados.
   - Faça o commit com a mensagem exata: `feat: 42 testes com pytest-cov, ruff linting e docs atualizados`.
   - No terminal, exiba os comandos para o usuário realizar o merge/Pull Request da branch `dev` para a `main`.