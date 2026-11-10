# V-MAX — Plataforma Analítica de E-Commerce (Medalhão + DuckDB + MCP)

Bem-vindo à documentação técnica oficial do projeto **V-MAX**, uma arquitetura completa de Engenharia de Dados em Python e **DuckDB** implementando o padrão **Medalhão (Bronze, Silver e Gold)**, **Camada Semântica em Português**, **Servidor MCP Nativo** e **Dashboard Executivo em FastAPI + Google Charts**.

---

## ⚠️ Ressalva Amostral e Licenciamento

> **Aviso Importante:** Os dados apresentados neste projeto referem-se a uma amostra extraída do dataset público *Brazilian E-Commerce Public Dataset by Olist* (~100 mil pedidos realizados entre 2016 e 2018 em múltiplos marketplaces no Brasil) e possuem finalidade estritamente analítica e educacional.
>
> **Licença:** Disponibilizado sob a licença **CC BY-NC-SA 4.0** (*Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International*).

---

## 🧭 Navegação da Documentação

- **[Arquitetura Medalhão e Views Semânticas](arquitetura.md):** Fluxo completo de ingestão, sanitização, abstração semântica e modelagem dimensional.
- **[Dicionário de Dados e Modelo Dimensional Gold](dicionario_gold.md):** Especificação detalhada das tabelas Fato, Dimensões e KPIs consolidados.
- **[Guia de Execução e Operação](guia_execucao.md):** Passo a passo com `uv` para rodar pipelines, testes automatizados e o Dashboard Executivo.
- **[Servidor MCP e Tools para IA](mcp_tools.md):** Documentação técnica do servidor Model Context Protocol, segurança Read-Only e roteador semântico.
- **[Onde a IA Errou (Registro Técnico)](erros_ia.md):** Relatório transparente de falhas, causas-raiz e soluções de engenharia aplicadas.
- **[Histórico de Evolução do Projeto](evolução_projeto.md):** Registro cronológico de todas as entregas (Specs 01 a 07).
