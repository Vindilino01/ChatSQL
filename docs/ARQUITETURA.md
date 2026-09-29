# Arquitetura — tour guiado

Este documento explica **como o Chat SQL funciona por dentro**, modulo por modulo.
A ideia e que qualquer integrante consiga ler e entender em ~20 minutos.

## 1. Visao em uma imagem

```
 Usuario escreve: "quantos clientes por estado"
        |
        v
 +----------------+     (1) gera o SQL
 |  Motor Offline |  ou Provedor de IA (opcional)
 +--------+-------+
          |
          v
 +----------------+     (2) valida: so SELECT, 1 instrucao,
 |     Trava      |         colunas/tabelas existem
 +--------+-------+
          |  rejeitou? ----> Diagnostico (motivo + sugestoes)
          v aprovou
 +----------------+
 |  Fonte de Dados|     (3) executa
 |  (memoria/DB)  |
 +--------+-------+
          v
    Resultado na tela
```

## 2. O fluxo de uma pergunta

1. O usuario digita a **Pergunta** na aba Chat.
2. O `ChatSession` (`chat_sql/pipeline.py`) chama o gerador:
   - sem chave -> `OfflineEngine` (`chat_sql/nl/engine.py`), por regras;
   - com chave -> `OpenAICompatibleProvider` (`chat_sql/provider.py`).
3. O SQL gerado passa pela **Trava** (`chat_sql/guard.py`).
4. O SQL aparece na tela; o usuario clica em **Executar**.
5. A **Fonte de Dados** executa (`chat_sql/engine.py` hoje; `chat_sql/db.py` no futuro).
6. O resultado vira tabela (`pandas`), com grafico quando faz sentido.

## 3. Modulos do produto (`chat_sql/`)

| Modulo | O que faz | Por que existe |
|--------|-----------|----------------|
| `config.py` | Constantes e presets de provedor | Um so lugar para limites e padroes |
| `nl/text.py` | Normalizacao de PT-BR (acentos, plural) | Regras com poucas linhas |
| `nl/lexicon.py` | Vocabulario (meses, unidades, medidas) | Dados separados da logica |
| `nl/builder.py` | Monta SQL e juncoes (BFS no grafo de FKs) | Descobrir como ligar tabelas |
| `nl/engine.py` | Interpreta a pergunta e decide o SQL | O "cerebro" offline |
| `guard.py` | A Trava: valida antes de executar | Seguranca |
| `engine.py` | SQLite em memoria | Execucao isolada e rapida |
| `datasource.py` | Interface de Fonte de Dados | Permite trocar memoria por banco real |
| `schema.py` | Le `CREATE TABLE` e extrai tabelas/colunas/FKs | Entender o schema do usuario |
| `spreadsheet.py` | Le CSV/XLSX/XLS e limpa formatos BR | Entrada sem banco |
| `sample_data.py` | Gera dados de exemplo deterministicos | Testar sem dados reais |
| `store.py` | Salva fontes e historico em disco | Nao perder no reload |
| `prompt.py` | Monta prompts (modo IA) | Separar texto de logica |
| `provider.py` | Cliente OpenAI-compatible | Multi-provedor |
| `pipeline.py` | Orquestra gerar -> validar -> executar | Um lugar para o fluxo |
| `db.py` | Conexao somente-leitura (SQLite/Postgres) | Consultar bancos reais |
| `sheets.py` / `sql_dump.py` | **A IMPLEMENTAR** | Ver `ROADMAP.md` |

### Conexao a banco real (`db.py`)

`DatabaseSource` usa SQLAlchemy para: abrir a conexao, **introspectar** o schema
(tabelas, colunas, tipos e FKs) e executar passando pela Trava no dialeto da fonte.
Suporta SQLite (testes) e Postgres (demo). A seguranca e em camadas: usuario
somente-leitura, sessao em modo leitura quando possivel, timeout por dialeto e a
Trava bloqueando qualquer coisa que nao seja `SELECT`. A ligacao na tela ja existe
na aba Dados (frente C evolui: MySQL, testar conexao e seletor de tabelas).

## 4. A Trava (seguranca)

`chat_sql/guard.py` valida em camadas:

1. Uma unica instrucao.
2. A raiz precisa ser `SELECT` (inclui `WITH` e `UNION`).
3. Funcoes perigosas bloqueadas (`load_extension`, `writefile`...).
4. Tabelas e colunas precisam existir no schema (pega "alucinacao").

Se reprovar, devolve um `GuardResult` com o motivo — que vira o **Diagnostico** mostrado
ao usuario e, no modo IA, volta para o modelo corrigir.

## 5. O Motor Offline

- `_find_subject`: descobre a tabela principal (nome completo vence parte).
- `_detect_aggregation`: conta, soma, media, maior/menor, top-N.
- `_resolve_measure` / `_resolve_group`: qual numero e qual agrupamento.
- `_extract_*`: filtros (numero, data, texto, nulo, booleano).
- `_explain_plan`: gera a frase "Contei os registros de ...".

Tudo termina em `Plan` -> `_build()` -> SQL. Se nao entender, retorna `OfflineResult`
com motivo e sugestoes (nunca "chuta").

## 6. Onde mexer para cada feature

| Quero... | Mexo em... |
|----------|------------|
| Ensinar um sinonimo | `nl/lexicon.py` |
| Entender um novo padrao | `nl/engine.py` + teste |
| Nova Fonte de Dados | `datasource.py` + `db.py`/`sheets.py` |
| Mudar a tela | `app.py` |
| Novo schema de exemplo | `schemas/` |
| Mais dados de demo | `sample_data.py` |

## 7. Como rodar e testar

```bash
pytest                  # suite completa
pytest tests/test_guard.py -v
streamlit run app.py    # sobe a interface
```

## 8. Glossario

Os termos do dominio (Pergunta, Consulta, Trava, Fonte de Dados, Instituicao...) estao
em [`CONTEXT.md`](../CONTEXT.md). As decisoes de arquitetura estao em
[`docs/adr/`](./adr/).
