# Frente D - Dados e Biblioteca

**Responsáveis:** (preencher)

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)

---

## Em uma frase

Criar os **dados da demonstração** (uma biblioteca com mais de 10 mil registros) e
as formas de entrar com dados: planilhas, Google Sheets e dump `.sql`.

## Onde fica no projeto

| Arquivo | O que é |
|---|---|
| `schemas/biblioteca-postgres.sql` | **Pronto**: o DDL revisado, para Postgres/Neon. É o schema real, extraído do banco em uso. |
| `docs/BANCO.md` | **Pronto**: por que cada restrição e índice existe. |
| `scripts/apply_ddl.py` | **Pronto**: aplica o DDL no banco do `.env`. |
| `chat_sql/sample_data.py` | Cria dados de exemplo automaticamente (a função `generate_sample_data`). |
| `chat_sql/spreadsheet.py` | Lê planilhas CSV, XLSX e XLS. |
| `chat_sql/sheets.py` | Lê planilha pública do Google Sheets (link → CSV). |
| `chat_sql/sql_dump.py` | Importa arquivo `.sql` (dump com ou sem dados). |
| `tests/test_sample_data.py` | Testes dos dados de exemplo. |
| `tests/test_spreadsheet.py` | Testes de planilhas. |
| `tests/test_sheets.py` e `tests/test_sql_dump.py` | Testes das duas fontes novas (14 casos). |

## Primeira tarefa: o banco da biblioteca (já pronto)

**Não é preciso criar nada.** O schema real está em
`schemas/biblioteca-postgres.sql`, foi aplicado no Neon e é de onde saem os
diagramas de `docs/mer/`.

Para conferir o que existe:

```powershell
.\venv\Scripts\python -m pytest tests/test_schema.py -v
```

Se um dia precisar replicar em outro banco:

```powershell
.\venv\Scripts\python scripts\apply_ddl.py
```

O passo a passo de conexão está em [`../COMO-CONECTAR.md`](../COMO-CONECTAR.md).

## Segunda tarefa: dados da demonstração (já pronto)

O banco tem 456 obras reais, 277 autores e 40 editoras, com a contagem
conferida por teste (`tests/test_documentacao.py`). Para ver os números:

```powershell
.\venv\Scripts\python -m scripts.contagens
```

Para recarregar do zero — ou aumentar o volume:

```powershell
.\venv\Scripts\python scripts\seed_biblioteca.py --usuarios 2000 --emprestimos 8000
```

O gerador respeita as relações: um empréstimo só aponta para livro e usuário
que existem, e o banco recusa dois empréstimos abertos do mesmo exemplar.

## Terceira tarefa: Google Sheets (D1) e dump `.sql` (D2)

**Já estão implementados.** O que existe:

- `chat_sql/sheets.py`: converte o link de edição do Google na URL de export CSV,
  baixa e devolve o conteúdo. Trata planilha privada (403), link inválido, página
  de login e resposta vazia — cada caso com mensagem própria em português.
- `chat_sql/sql_dump.py`: detecta a codificação (UTF-8, latin-1, cp1252), confere
  se há `CREATE TABLE` e classifica o arquivo em "dump com dados" ou "só
  estrutura". Dump MySQL é convertido para SQLite antes de executar (o banco de
  execução é SQLite em memória): `int(11)` → `INTEGER`, `VARCHAR(120)` → `TEXT`,
  índices `KEY nome (col)` descartados, `INSERT`s preservados. Sem `CREATE TABLE`,
  recusa com explicação.

Na tela, os dois aparecem como opções próprias em **Dados**:
**Google Sheets (link público)** e **Arquivo .sql (dump)**.

Para conferir:
```powershell
.\venv\Scripts\python -m pytest tests/test_sheets.py tests/test_sql_dump.py -v
.\venv\Scripts\python -m pytest tests/test_fontes_novas.py -v
```

O que **não** é suportado: planilha privada (exigiria login Google/OAuth) e dump
maior que a memória da máquina. Se precisar de um desses, é trabalho novo, não um
bug.

## Como testar

```powershell
.\venv\Scripts\python -m pytest tests/test_sample_data.py tests/test_spreadsheet.py -v
```

## Pronto quando

- [x] `schemas/biblioteca-postgres.sql` existe, foi aplicado no Neon e o app conecta.
- [x] Dá para gerar milhares de registros sem erro (o seed real tem ~5.300).
- [x] `tests/test_sheets.py` e `tests/test_sql_dump.py` passam (sem `skip`).
- [x] A demo responde pelo menos 15 perguntas sobre a biblioteca (91 no total).

## Seed pronto (acervo real)

O script `scripts/seed_biblioteca.py` já popula o banco com **obras, autores e
editoras reais** (456 obras, 277 autores, 40 editoras) e ~5.300 registros no
total. Uso:

```powershell
.\venv\Scripts\python scripts\seed_biblioteca.py
```

Para medir a acurácia do motor sem IA nesse banco:

```powershell
.\venv\Scripts\python -m pytest tests/eval/test_biblioteca.py -s
```

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| Schema | A estrutura do banco (as tabelas e colunas) |
| Seed / semente | O ponto de partida para gerar dados de exemplo |
| Dump | Um arquivo `.sql` com o banco inteiro para importar |
| CSV | Um arquivo de planilha simples, separado por vírgulas ou ponto e vírgula |

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
