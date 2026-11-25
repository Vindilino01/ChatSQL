# ROADMAP — Chat SQL

O núcleo está pronto e verificado (240 testes). O que resta está dividido em 5 frentes.
**Para entender cada frente em detalhe, abra o guia dela (link em cada título).**

[Início](README.md) · [Índice da documentação](docs/README.md) · [Mapa: onde fica o quê](docs/ONDE-FICA-O-QUE.md)

---

## Frentes

| Frente | Pessoas | Entrega |
|--------|---------|---------|
| A. Banco de dados | 2 | Conectar a um banco real (somente leitura) |
| B. Motor Offline | 2 | Mais sinônimos e acurácia ≥ 70% |
| C. Interface | 1 | Tela da Conexão e ajustes |
| D. Dados | 1 | Biblioteca 10k+, Google Sheets e dump `.sql` |
| E. Entrega | 1 | Docker, CI, PRD e apresentação |

## Tarefas

**A — Banco de dados** (Fase 1 — conector de referência pronto) — [guia completo](docs/frentes/A-banco-de-dados.md)
- Ler e entender `chat_sql/db.py` (SQLite e Postgres já funcionam).
- Evoluir: MySQL e teste real em Postgres (`CHATSQL_POSTGRES_URL`).
- Garantir usuário **somente leitura** no banco da instituição.

**B — Motor Offline** — [guia completo](docs/frentes/B-motor-offline.md)
- Sinônimos por schema (`schemas/<nome>.synonyms.json`).
- Preencher o placar em `tests/eval/cases.json` e registrar a acurácia no `PRD.md`.

**C — Interface e Design** — [guia completo](docs/frentes/C-interface-e-design.md)
- Feito: conexão na aba Dados com campos separados ou URL, conexão lembrada
  (sem a senha) e seletor visual de tabelas.
- Falta: capturas de tela em `docs/imagens/` e conferência em 1366×768.

**D — Dados e biblioteca** — [guia completo](docs/frentes/D-dados-e-biblioteca.md)
- Feito: biblioteca no Neon (456 obras reais, ~5.300 registros) e MER completo.
- Feito: Google Sheets por link público (D1) e upload de `.sql` (D2), com testes.
- Falta: revisão do texto do relatório (`RELATORIO.md`).

**E — Entrega e apresentação** — [guia completo](docs/frentes/E-entrega-e-apresentacao.md)
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

---

[Início](README.md) · [Índice da documentação](docs/README.md) · [Mapa: onde fica o quê](docs/ONDE-FICA-O-QUE.md)
