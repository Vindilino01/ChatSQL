# ROADMAP — Chat SQL

A base está pronta (133 testes). Falta isto, dividido em 5 frentes:

## Frentes

| Frente | Pessoas | Entrega |
|--------|---------|---------|
| A. Banco de dados | 2 | Conectar a um banco real (somente leitura) |
| B. Motor Offline | 2 | Mais sinônimos e acurácia ≥ 70% |
| C. Interface | 1 | Tela da Conexão e ajustes |
| D. Dados | 1 | Biblioteca 10k+, Google Sheets e dump `.sql` |
| E. Entrega | 1 | Docker, CI, PRD e apresentação |

## Tarefas

**A — Banco de dados** (Fase 1 — conector de referência pronto)
- Ler e entender `chat_sql/db.py` (SQLite e Postgres já funcionam).
- Evoluir: MySQL e teste real em Postgres (`CHATSQL_POSTGRES_URL`).
- Garantir usuário **somente-leitura** no banco da instituição.

**B — Motor Offline**
- Sinônimos por schema (`schemas/<nome>.synonyms.json`).
- Preencher o placar em `tests/eval/cases.json` e registrar a acurácia no `PRD.md`.

**C — Interface**
- Conexão já ligada na aba Dados (URL + conectar). Evoluir: botão "Testar
  conexão", seletor visual de tabelas e salvar a conexão (sem a senha).

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

## Definido
- SGBD da demo: **Postgres** (SQLite roda nos testes).
- Instituição simulada: a definir (biblioteca, clínica, escola...).
