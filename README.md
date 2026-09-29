# Chat SQL

Perguntas em linguagem natural viram **Consultas SQL somente leitura**, validadas e executadas na hora — **funciona offline, sem chave de API**.

> "os 10 maiores clientes por faturamento no mes passado" → SQL valido, executado, resultado na tela.

O diferencial nao e gerar SQL — e gerar SQL **confiavel**. Toda Consulta passa por uma Trava que bloqueia escrita, DDL e colunas que nao existem, e nada executa sem o usuario ver o SQL antes.

## Modos de geracao

- **Motor Offline (padrao)** — regras deterministicas em PT-BR, sem modelo de linguagem, sem rede, sem chave. Ideal para uso corporativo onde IA e proibida ou para nao gastar com tokens.
- **Provedor de IA (opcional)** — qualquer API OpenAI-compatible (DeepSeek, OpenAI, Groq, OpenRouter, Ollama local...). Usa uma chave fornecida na sessao. Gera um Par de Exemplos por schema e tem loop de Correcao.

## Fontes de dados

- **Planilhas** — envie CSV, XLSX ou XLS (uma tabela por aba/arquivo). O schema e os tipos sao inferidos, com limpeza de formatos BR (`R$ 1.234,50`, datas `dd/mm/aaaa`, delimitador `;`) e inferencia de chaves estrangeiras por colunas `algo_id`.
- **DDL + Dados de Exemplo** — cole seus `CREATE TABLE` e o app gera dados sinteticos deterministicos para testar na hora.

## Como funciona

1. **Schema da Sessao** — colado (DDL) ou inferido da Planilha.
2. **Trava** — valida com [sqlglot](https://github.com/tobymao/sqlglot): uma unica instrucao, apenas `SELECT`, sem funcoes perigosas e **somente tabelas/colunas que existem**.
3. **Confirmacao** — o SQL aparece na tela; so executa quando voce clica em **Executar**.
4. **Correcao (so no modo IA)** — se a execucao falhar, o erro volta ao modelo e uma nova Consulta e proposta (1 geracao + 2 correcoes). A Consulta corrigida **nunca** executa sozinha.
5. **Execucao isolada** — SQLite em memoria. `PRAGMA query_only`, timeout de 5s e limite de linhas.

## O que o Motor Offline entende

- **Intencoes**: listagem, contagem, contagem distinta, soma, media, maior, menor, top-N.
- **Agrupamento**: "por categoria", "para cada departamento", com `HAVING` ("com mais de 10").
- **Filtros numericos**: `>`, `<`, `=`, `!=`, `entre X e Y`.
- **Filtros de texto**: igualdade ("status ativo"), `LIKE` ("que contem premium", "comeca com Ana"), nulo/nao nulo ("sem email", "com email preenchido").
- **Booleanos**: "ativos", "inativos".
- **Datas**: "mes passado", "este mes", "ano passado", "hoje", "ontem", "ultimos N dias/meses/anos", mes por nome ("janeiro de 2025"), trimestre e ano.
- **Ordenacao e limite**: "ordenado por nome crescente", "os 5 mais caros", "top 10", "os 3 mais recentes".
- **Juncao** automatica por chave estrangeira, inclusive em multiplos saltos (BFS no grafo de FKs).

Quando nao entende, **nao chuta**: devolve um Diagnostico com o motivo, eventuais tabelas ambiguas e sugestoes de Perguntas (ver [ADR 0006](docs/adr/0006-motor-offline-nunca-falha-em-silencio.md)).

## Interface

- **Persistencia**: fontes, **historico de perguntas** e resultados ficam salvos em disco (`~/.chat_sql_sources`) e a fonte ativa e lembrada na URL, entao **recarregar a pagina nao perde nada**. Configuracoes lista as fontes salvas (reabrir/limpar).
- **Historico em turnos** e **perguntas recentes** clicaveis.
- **Explicacao em linguagem natural** de cada Consulta ("Contei os registros de pedidos, agrupando por status...").
- **Baixar SQL** e **baixar CSV**; **grafico** (barra/linha/area) para resultados agregados.
- **Sidebar** com a Fonte ativa, contagem de linhas por tabela e Provedor.
- **Chat em turnos**: cada Pergunta vira uma bolha; o SQL aparece em cartao e so executa no clique.
- **Sugestoes clicaveis** geradas do seu schema (contagem, listagem, total, agrupamento, top-5, ultimo).
- **Desambiguacao clicavel** quando a Pergunta serve para mais de uma tabela.
- **"Entendi → ..."**: resumo do que o Motor Offline interpretou.
- **Metricas e grafico** automaticos para resultados agregados (2 colunas).
- Tema escuro proprio em `.streamlit/config.toml`.

## Stack

Python 3.11+ · Streamlit · sqlglot · SQLite3 · pandas · Faker · openpyxl · openai

## Rodar localmente

```bash
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O app abre no **Modo offline** — nenhuma configuracao necessaria. Para usar IA, escolha um Provedor na aba **Configuracoes** e cole a chave (fica apenas na sessao). Opcionalmente, crie um `.env`:

```dotenv
CHATSQL_API_KEY=sk-...
```

## Schemas prontos

`schemas/e-commerce.sql`, `schemas/rh.sql`, `schemas/vendas.sql`. Na aba **Dados**, escolha "Schema de exemplo" e clique em **Carregar exemplo**.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Inclui a matriz de bloqueio da Trava, o loop de Correcao, integridade de FK, leitura de planilhas e o placar do **Motor Offline** contra `tests/eval/cases.json`.

### Avaliacao com IA (opcional)

```bash
# PowerShell
$env:CHATSQL_EVAL_API_KEY = "sk-..."
pytest tests/eval -s
```

O placar aparece no terminal (ex.: `Acuracia: 11/13 = 85%`).

## Deploy (Streamlit Community Cloud)

1. Suba o repositorio no GitHub.
2. Em [share.streamlit.io](https://share.streamlit.io), aponte para `app.py`.
3. Nenhuma chave e obrigatoria — o app funciona no Modo offline.

## Estrutura

```
app.py                    Interface Streamlit (Chat, Dados, Configuracoes)
.streamlit/config.toml    Tema e configuracao
chat_sql/
  nl/                     Motor Offline
    text.py               Normalizacao PT-BR
    lexicon.py            Vocabulario (meses, unidades, operadores)
    builder.py            Montagem de SQL + juncoes multi-hop (BFS)
    engine.py             Analise, intencoes, filtros, Diagnostico, explicacao
  offline.py              Reexporta o Motor Offline
  spreadsheet.py          Leitura de planilhas + inferencia de schema/FK
  store.py                Persistencia de fontes, historico e recentes
  provider.py             Cliente OpenAI-compatible
  schema.py               Parse/normalizacao do DDL (sqlglot)
  sample_data.py          Gerador deterministico de Dados de Exemplo
  guard.py                A Trava
  engine.py               SQLite em memoria
  prompt.py               Instrucoes + Pares de Exemplos
  pipeline.py             Fluxo gerar -> validar -> executar -> Correcao
schemas/                  Schemas prontos
exemplos/                 Planilhas de exemplo
tests/                    Testes unitarios + UI + offline + store
tests/eval/               Harness de acuracia (IA)
```

## Documentacao de design

- [`CONTEXT.md`](CONTEXT.md) — glossario do dominio.
- [`docs/adr/`](docs/adr/) — decisoes arquiteturais.

## Privacidade

No Modo offline, nada sai da sua maquina. As fontes e o historico ficam salvos localmente em `~/.chat_sql_sources` (apenas no seu computador) e podem ser apagados em Configuracoes. So no modo com IA os dados do schema/prompt vao para o Provedor escolhido.

## Nao-objetivos

Banco real, escrita/DDL/DML, autenticacao, persistencia, Docker e graficos. O foco e a confiabilidade da Consulta gerada.
