# Arquitetura — tour guiado

Este documento explica **como o Chat SQL funciona por dentro**, módulo por módulo.
A ideia é que qualquer integrante consiga ler e entender em ~20 minutos.

> Trabalhando em uma frente específica? O guia dela fica em [`frentes/`](frentes/).
> Aqui é a visão geral do código.

[Início](../README.md) · [Índice](README.md) · [Mapa: onde fica o quê](ONDE-FICA-O-QUE.md)

---

## Sumário

1. [Visão em uma imagem](#1-visão-em-uma-imagem)
2. [O fluxo de uma pergunta](#2-o-fluxo-de-uma-pergunta)
3. [Módulos do produto](#3-módulos-do-produto)
4. [A Trava (segurança)](#4-a-trava-segurança)
5. [O Motor Offline](#5-o-motor-offline)
6. [Onde mexer para cada feature](#6-onde-mexer-para-cada-feature)
7. [Como rodar e testar](#7-como-rodar-e-testar)
8. [Glossário](#8-glossário)

---

## 1. Visão em uma imagem

```
 Usuário escreve: "quantos clientes por estado"
        |
        v
 +----------------+     (1) gera o SQL
 |  Motor Offline |  ou Provedor de IA (opcional)
 +--------+-------+
          |
          v
 +----------------+     (2) valida: só SELECT, 1 instrução,
 |     Trava      |         colunas/tabelas existem
 +--------+-------+
          |  rejeitou? ----> Diagnóstico (motivo + sugestões)
          v aprovou
 +----------------+
 |  Fonte de Dados|     (3) executa
 |  (memória/DB)  |
 +--------+-------+
          v
    Resultado na tela
```

## 2. O fluxo de uma pergunta

1. O usuário digita a **Pergunta** na aba Chat.
2. O `ChatSession` (`chat_sql/pipeline.py`) chama o gerador:
   - sem chave -> `OfflineEngine` (`chat_sql/nl/engine.py`), por regras;
   - com chave -> `OpenAICompatibleProvider` (`chat_sql/provider.py`).
3. O SQL gerado passa pela **Trava** (`chat_sql/guard.py`).
4. O SQL aparece na tela; o usuário clica em **Executar**.
5. A **Fonte de Dados** executa (`chat_sql/engine.py` hoje; `chat_sql/db.py` para banco real).
6. O resultado vira tabela (`pandas`), com gráfico quando faz sentido.

## 3. Módulos do produto

| Módulo | O que faz | Por que existe |
|--------|-----------|----------------|
| `config.py` | Constantes e presets de provedor | Um só lugar para limites e padrões |
| `nl/text.py` | Normalização de PT-BR (acentos, plural) | Regras com poucas linhas |
| `nl/lexicon.py` | Vocabulário (meses, unidades, medidas) | Dados separados da lógica |
| `nl/builder.py` | Monta SQL e junções (BFS no grafo de FKs) | Descobrir como ligar tabelas |
| `nl/engine.py` | Interpreta a pergunta e decide o SQL | O "cérebro" offline |
| `guard.py` | A Trava: valida antes de executar | Segurança |
| `engine.py` | SQLite na memória | Execução isolada e rápida |
| `datasource.py` | Interface de Fonte de Dados | Permite trocar memória por banco real |
| `schema.py` | Lê `CREATE TABLE` e extrai tabelas/colunas/FKs | Entender o schema do usuário |
| `spreadsheet.py` | Lê CSV/XLSX/XLS e limpa formatos BR | Entrada sem banco |
| `sample_data.py` | Gera dados de exemplo determinísticos | Testar sem dados reais |
| `store.py` | Salva fontes e histórico em disco | Não perder no reload |
| `prompt.py` | Monta prompts (modo IA) | Separar texto de lógica |
| `provider.py` | Cliente OpenAI-compatible | Multi-provedor |
| `pipeline.py` | Orquestra gerar -> validar -> executar | Um lugar para o fluxo |
| `db.py` | Conexão somente leitura (SQLite/Postgres) | Consultar bancos reais |
| `sheets.py` / `sql_dump.py` | **A IMPLEMENTAR** | Ver `ROADMAP.md` |

### Conexão a banco real (`db.py`)

`DatabaseSource` usa SQLAlchemy para: abrir a conexão, **introspectar** o schema
(tabelas, colunas, tipos e FKs) e executar passando pela Trava no dialeto da fonte.
Suporta SQLite (testes) e Postgres (demo). A segurança é em camadas: usuário
somente leitura, sessão em modo leitura quando possível, timeout por dialeto e a
Trava bloqueando qualquer coisa que não seja `SELECT`. A ligação na tela já existe
na aba Dados (frente C evolui: MySQL, testar conexão e seletor de tabelas).

## 4. A Trava (segurança)

`chat_sql/guard.py` valida em camadas:

1. Uma única instrução.
2. A raiz precisa ser `SELECT` (inclui `WITH` e `UNION`).
3. Funções perigosas bloqueadas (`load_extension`, `writefile`...).
4. Tabelas e colunas precisam existir no schema (pega "alucinação").

Se reprovar, devolve um `GuardResult` com o motivo — que vira o **Diagnóstico** mostrado
ao usuário e, no modo IA, volta para o modelo corrigir.

## 5. O Motor Offline

- `_find_subject`: descobre a tabela principal (nome completo vence parte).
- `_detect_aggregation`: conta, soma, média, maior/menor, top-N.
- `_resolve_measure` / `_resolve_group`: qual número e qual agrupamento.
- `_extract_*`: filtros (número, data, texto, nulo, booleano).
- `_explain_plan`: gera a frase "Contei os registros de ...".

Tudo termina em `Plan` -> `_build()` -> SQL. Se não entender, retorna `OfflineResult`
com motivo e sugestões (nunca "chuta").

## 6. Onde mexer para cada feature

| Quero... | Mexo em... |
|----------|------------|
| Ensinar um sinônimo | `nl/lexicon.py` |
| Entender um novo padrão | `nl/engine.py` + teste |
| Nova Fonte de Dados | `datasource.py` + `db.py`/`sheets.py` |
| Mudar a tela | `app.py` |
| Novo schema de exemplo | `schemas/` |
| Mais dados de demo | `sample_data.py` |

## 7. Como rodar e testar

```bash
pytest                  # suíte completa
pytest tests/test_guard.py -v
streamlit run app.py    # sobe a interface
```

## 8. Glossário

Os termos do domínio (Pergunta, Consulta, Trava, Fonte de Dados, Instituição...) estão
em [`CONTEXT.md`](../CONTEXT.md). As decisões de arquitetura estão em
[`adr/`](adr/).

---

[Início](../README.md) · [Índice](README.md) · [Mapa: onde fica o quê](ONDE-FICA-O-QUE.md)
