# ROADMAP — Chat SQL

Este e o plano de trabalho do grupo (7 pessoas). Cada tarefa tem **objetivo**, **o que
estudar**, **arquivos** e **criterio de aceite**. Comece pelas tarefas marcadas como
`[facil]` se estiver aprendendo.

> A base ja esta pronta e com 124 testes passando. O que falta esta aqui.

## Como usar

1. Escolha uma frente (tabela abaixo) e combine na reuniao semanal.
2. Leia o `docs/ARQUITETURA.md` antes de mexer no codigo.
3. Rode `pytest` antes e depois de cada tarefa.
4. Ao terminar, atualize este arquivo (marque a caixa) e o `PRD.md` (resultados).

## Frentes

| Frente | Pessoas | Foco |
|--------|---------|------|
| A. Conexoes a banco | 2 | SQLAlchemy, introspeccao, read-only |
| B. Motor Offline e vocabulario | 2 | Regras, sinonimos, acuracia |
| C. UI / UX | 1 | Streamlit, fluxos, tema |
| D. Dados e demo | 1 | Biblioteca 10k+, dumps, Sheets |
| E. Qualidade, infra e docs | 1 | Testes, Docker, PRD, pitch |

---

## Fase 1 — Conexoes a banco real (Frente A)

- [ ] **A1 `[facil]` Ler a interface `DataSource`**
  - Objetivo: entender o contrato que qualquer Fonte de Dados deve cumprir.
  - Estudar: `chat_sql/datasource.py` e o uso em `chat_sql/pipeline.py`.
  - Aceite: explicar em uma frase o que `schema()` e `execute()` fazem.

- [ ] **A2 `[medio]` Conectar via SQLAlchemy (SQLite primeiro)**
  - Objetivo: abrir uma conexao e rodar `SELECT 1`.
  - Estudar: `create_engine`, `text()`.
  - Arquivos: `chat_sql/db.py`, `tests/test_db_connector.py` (teste-guia).
  - Aceite: teste `test_database_source_reads_sqlite` passa (remova o `skip`).

- [ ] **A3 `[medio]` Introspectar o schema**
  - Objetivo: montar um `Schema` (tabelas, colunas, tipos, FKs) a partir do banco.
  - Estudar: `sqlalchemy.inspect`, `get_columns`, `get_foreign_keys`.
  - Aceite: o schema gerado tem as mesmas tabelas/colunas do banco.

- [ ] **A4 `[medio]` Executar com a Trava**
  - Objetivo: reaproveitar `guard.validate()` e os limites de `engine.py`.
  - Aceite: `INSERT`/`DROP` sao bloqueados; `SELECT` executa com timeout e limite de linhas.

- [ ] **A5 `[dificil]` Modo somente-leitura e seguranca**
  - Objetivo: exigir usuario read-only e abrir a sessao em modo leitura por dialeto.
  - Estudar: `SET TRANSACTION READ ONLY` (Postgres/MySQL), permissoes.
  - Aceite: documentar no `PRD.md` e testar em Postgres local.

- [ ] **A6 `[medio]` Subir a Conexao na UI**
  - Objetivo: nova Fonte "Banco de dados" na aba Dados (URL, testar conexao, escolher tabelas).
  - Arquivos: `app.py`.
  - Aceite: da para conectar, ver a previa e perguntar.

## Fase 2 — Sheets, dump e biblioteca (Frente D)

- [ ] **D1 `[facil]` Google Sheets por link publico**
  - Objetivo: baixar uma planilha publica como CSV e transformar em Fonte de Dados.
  - Estudar: URL de export `https://docs.google.com/spreadsheets/d/<id>/export?format=csv`.
  - Arquivos: `chat_sql/sheets.py`, `tests/test_sheets.py` (teste-guia).
  - Aceite: upload por link funciona com uma planilha publica de teste.

- [ ] **D2 `[facil]` Importar arquivo `.sql`**
  - Objetivo: ler um dump `.sql` (CREATE + INSERT) e carregar como Script SQL.
  - Arquivos: `chat_sql/sql_dump.py`, `tests/test_sql_dump.py` (teste-guia).
  - Aceite: dump de exemplo carrega e responde perguntas.

- [ ] **D3 `[medio]` Schema e dados da biblioteca (10k+)**
  - Objetivo: `schemas/biblioteca.sql` + gerador deterministico de 10k+ registros
    (livros, autores, exemplares, usuarios, emprestimos).
  - Arquivos: `schemas/biblioteca.sql`, `chat_sql/sample_data.py` (extensao).
  - Aceite: `pytest` gera 10k+ linhas sem erro e o app responde perguntas da biblioteca.

- [ ] **D4 `[facil]` Roteiro de demo**
  - Objetivo: lista de ~15 perguntas que a demo vai mostrar.
  - Aceite: todas respondem com SQL valido e resultado na tela.

## Fase 3 — Vocabulario e acuracia (Frente B)

- [ ] **B1 `[facil]` Entender o motor**
  - Estudar: `chat_sql/nl/lexicon.py` e `chat_sql/nl/engine.py`.
  - Aceite: adicionar um sinonimo simples e ver o efeito.

- [ ] **B2 `[medio]` Sinonimos por schema**
  - Objetivo: arquivo `schemas/<nome>.synonyms.json` lido pelo motor.
  - Aceite: "anos" -> `Age`, "tarifa" -> `Fare` configuravel por schema.

- [ ] **B3 `[medio]` Mais padroes de pergunta**
  - Ideias: "entre X e Y", "nulos/nao nulos", "contem", "ultimos N meses",
    "ordenado por", comparacoes de data.
  - Aceite: cada padrao com pelo menos 1 teste.

- [ ] **B4 `[medio]` Avaliacao da biblioteca**
  - Objetivo: `tests/eval/cases.json` com 15-20 perguntas da biblioteca.
  - Aceite: rodar `pytest tests/eval -s` (offline) e registrar a acuracia no `PRD.md`.

- [ ] **B5 `[dificil]` Bater a meta de 70%**
  - Objetivo: iterar o vocabulario ate a meta.
  - Aceite: `PRD.md` com a tabela de resultados preenchida.

## Fase 4 — Servico e entrega (Frente E)

- [ ] **E1 `[medio]` Dockerfile + docker-compose**
  - Objetivo: subir o app em um comando, com Postgres de demonstracao opcional.
  - Aceite: `docker compose up` funciona a partir de um clone limpo.

- [ ] **E2 `[facil]` CI no GitHub Actions**
  - Objetivo: rodar `pytest` a cada push.
  - Aceite: badge verde no README.

- [ ] **E3 `[facil]` Atualizar PRD/README com resultados e prints**
  - Aceite: PRD com acuracia, prints das telas, secoes completas.

- [ ] **E4 `[medio]` Slides e ensaio**
  - Roqueiro de apresentacao (problema, solucao, arquitetura, seguranca, resultados, demo).
  - Aceite: demo cronometrado em <= 10 min, com video de backup.

---

## Fase 5 — "Do nosso jeito" (extras, se sobrar tempo)

- [ ] Ajuste de tipos das colunas da planilha (`st.data_editor`).
- [ ] Joins manuais entre multiplos arquivos.
- [ ] Multiusuario / multi-tenant (trabalhos futuros).
- [ ] Suporte a SQL Server / Oracle.
- [ ] Exportar a sessao (perguntas + SQL + resultados).

---

## Cronograma (29/set -> meados/nov)

| Semana | Meta |
|--------|------|
| 1 | Fundacao entregue; reuniao de alinhamento; frentes definidas |
| 2-3 | Fase 1 (conexoes) + Fase 2 (Sheets/dump) |
| 4-5 | Fase 2 (biblioteca) + Fase 3 (vocabulario/acuracia) |
| 6 | Fase 4 (Docker, CI, PRD) |
| 7 | Ensaio, slides e apresentacao |

## Definicao de pronto (DoD)

Uma tarefa esta pronta quando: codigo revisado por outra pessoa, `pytest` verde,
teste-guia ativado (ou teste novo) e documentacao/roadmap atualizados.

## Precisamos definir

- Qual SGBD a demo da biblioteca vai usar (sugestao: **Postgres**, com SQLite de reserva).
- Qual instituicao sera simulada (biblioteca, clinica, escola...).
