# ROADMAP — Chat SQL

O núcleo está pronto e verificado (347 testes coletados). O que resta está
dividido em 5 frentes — e a coluna **Estado** diz o que de fato falta.

**Para entender cada frente em detalhe, abra o guia dela (link em cada título).**

[Início](README.md) · [Índice da documentação](docs/README.md) · [Mapa: onde fica o quê](docs/ONDE-FICA-O-QUE.md)

---

## Frentes

| Frente | Pessoas | Entrega | Estado |
|--------|---------|---------|--------|
| A. Banco de dados | 2 | Conectar a um banco real (somente leitura) | ✅ pronto (falta MySQL) |
| B. Motor Offline | 2 | Entender perguntas em PT-BR com precisão | ✅ 95/95 — falta bateria do grupo |
| C. Interface | 1 | Tela da Conexão e ajustes | ✅ pronto — faltam prints |
| D. Dados | 1 | Biblioteca, Google Sheets e dump `.sql` | ✅ pronto |
| E. Entrega | 1 | Docker, CI, PRD e apresentação | 🟡 CI pronto — faltam slides e ensaio |

## Tarefas

**A — Banco de dados** — [guia completo](docs/frentes/A-banco-de-dados.md)
- ✅ Conector SQLite/Postgres somente leitura, com introspecção do schema.
- ✅ Usuário `chatsql_ro` read-only no Neon; a Trava bloqueia escrita.
- ⬜ MySQL — evolução, não bloqueia a entrega.

**B — Motor Offline** — [guia completo](docs/frentes/B-motor-offline.md)
- ✅ 95 perguntas em quatro conjuntos, 100% de acerto; recusa 6/6 fora do domínio.
- ✅ Filtro por nacionalidade (país e gentílico): "autores brasileiros".
- ⬜ **Bateria cega do grupo**: cada pessoa escreve 8 perguntas sem olhar o
  código. Cole em `tests/eval/bateria_cega.txt` e rode
  `.\venv\Scripts\python scripts\medir_bateria_cega.py`.
  Instruções: [`docs/AVALIACAO-MOTOR.md`](docs/AVALIACAO-MOTOR.md).

**C — Interface e Design** — [guia completo](docs/frentes/C-interface-e-design.md)
- ✅ Conexão com campos separados ou URL, lembrada sem a senha.
- ✅ Seletor visual de tabelas.
- ✅ CSS ajustado para projetor 1366×768.
- ⬜ **Prints das telas** em `docs/imagens/` (instruções prontas no
  [`README` da pasta](docs/imagens/README.md)).

**D — Dados e biblioteca** — [guia completo](docs/frentes/D-dados-e-biblioteca.md)
- ✅ Biblioteca no Neon: 456 obras reais, 277 autores, 40 editoras.
- ✅ Nacionalidade real de cada autor (não é mais sorteada).
- ✅ MER completo gerado do schema (`docs/mer/`).
- ✅ Google Sheets por link público e upload de `.sql`, com conversão de MySQL.
- ✅ Diagrama pronto para o draw.io (`docs/mer/biblioteca.drawio`).
- ⬜ Revisar o texto do relatório ([`RELATORIO.md`](RELATORIO.md)).

**E — Entrega e apresentação** — [guia completo](docs/frentes/E-entrega-e-apresentacao.md)
- ✅ CI no GitHub Actions: lint + testes em Python 3.11, 3.12 e 3.13.
- ✅ Licença MIT.
- ⬜ **Slides** e **ensaio cronometrado** — roteiro em
  [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md).
- ⬜ Docker (opcional; o app roda com 3 comandos).

## Cronograma

| Semana | Meta | Estado |
|--------|------|--------|
| 1 | Fundação | ✅ |
| 2–3 | Banco + dados | ✅ |
| 4–5 | Motor + acurácia | ✅ |
| 6 | Serviço + PRD | ✅ |
| 7 | Apresentação | ⬜ slides e ensaio |

## Definido

- SGBD da demo: **Postgres** no Neon (SQLite roda nos testes e em memória).
- Instituição da demo: **Biblioteca Universitária**, com acervo real.

---

[Início](README.md) · [Índice da documentação](docs/README.md) · [Mapa: onde fica o quê](docs/ONDE-FICA-O-QUE.md)
