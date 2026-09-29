# ROADMAP — Chat SQL

A base está pronta (125 testes). Falta isto, dividido em 5 frentes:

## Frentes

| Frente | Pessoas | Entrega |
|--------|---------|---------|
| A. Banco de dados | 2 | Conectar a um banco real (somente leitura) |
| B. Motor Offline | 2 | Mais sinônimos e acurácia ≥ 70% |
| C. Interface | 1 | Tela da Conexão e ajustes |
| D. Dados | 1 | Biblioteca 10k+, Google Sheets e dump `.sql` |
| E. Entrega | 1 | Docker, CI, PRD e apresentação |

## Tarefas

**A — Banco de dados** (Fase 1)
- Implementar `chat_sql/db.py` (comece por SQLite, depois Postgres).
- Ativar `tests/test_db_connector.py` (remover o `skip`).
- Garantir usuário **somente-leitura** e timeout.

**B — Motor Offline**
- Sinônimos por schema (`schemas/<nome>.synonyms.json`).
- Preencher o placar em `tests/eval/cases.json` e registrar a acurácia no `PRD.md`.

**C — Interface**
- Nova opção "Banco de dados" na aba Dados (testar conexão + escolher tabelas).

**D — Dados**
- Biblioteca: `schemas/biblioteca.sql` + gerador de 10k registros.
- Google Sheets por link público (D1) e upload de `.sql` (D2).

**E — Entrega**
- `Dockerfile` + `docker compose up`.
- CI (GitHub Actions), slides e ensaio da demo.

## Cronograma

| Semana | Meta |
|--------|------|
| 1 | Fundação (pronta) |
| 2–3 | Banco + dados |
| 4–5 | Motor + acurácia |
| 6 | Serviço + PRD |
| 7 | Apresentação |

## Precisamos definir
- SGBD da demo (sugestão: **Postgres**).
- Instituição simulada (biblioteca, clínica, escola...).
