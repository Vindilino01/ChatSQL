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
| `schemas/biblioteca.sql` | **A criar**: o banco da biblioteca (livros, autores, exemplares, usuários, empréstimos). |
| `schemas/biblioteca-postgres.sql` | **Pronto**: o DDL revisado, para Postgres/Neon. |
| `docs/BANCO.md` | **Pronto**: por que cada restrição e índice existe. |
| `scripts/apply_ddl.py` | **Pronto**: aplica o DDL no banco do `.env`. |
| `chat_sql/sample_data.py` | Cria dados de exemplo automaticamente (a função `generate_sample_data`). |
| `chat_sql/spreadsheet.py` | Lê planilhas CSV, XLSX e XLS. |
| `chat_sql/sheets.py` | Lê planilha pública do Google Sheets (link → CSV). |
| `chat_sql/sql_dump.py` | Importa arquivo `.sql` (dump com ou sem dados). |
| `tests/test_sample_data.py` | Testes dos dados de exemplo. |
| `tests/test_spreadsheet.py` | Testes de planilhas. |
| `tests/test_sheets.py` e `tests/test_sql_dump.py` | Testes das duas fontes novas (14 casos). |

## Primeira tarefa (passo a passo): criar o banco da biblioteca

1. Crie o arquivo `schemas/biblioteca.sql`.
2. Escreva as tabelas assim (modelo):
   ```sql
   CREATE TABLE autores (
       id INTEGER PRIMARY KEY,
       nome TEXT NOT NULL
   );

   CREATE TABLE livros (
       id INTEGER PRIMARY KEY,
       titulo TEXT NOT NULL,
       autor_id INTEGER,
       ano INTEGER,
       FOREIGN KEY (autor_id) REFERENCES autores(id)
   );

   CREATE TABLE usuarios (
       id INTEGER PRIMARY KEY,
       nome TEXT NOT NULL,
       email TEXT
   );

   CREATE TABLE emprestimos (
       id INTEGER PRIMARY KEY,
       livro_id INTEGER NOT NULL,
       usuario_id INTEGER NOT NULL,
       data_emprestimo DATE,
       data_devolucao DATE,
       FOREIGN KEY (livro_id) REFERENCES livros(id),
       FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
   );
   ```
3. Teste no app: aba **Dados** -> **Script SQL** -> cole o conteúdo -> **Carregar script**.

## Segunda tarefa: gerar 10 mil registros

O projeto já cria dados de exemplo automaticamente. Para aumentar a quantidade:
- Na aba **Dados** -> **Schema de exemplo**, o controle "Linhas por tabela" vai até 500.
- Para 10 mil, use o código:
  ```python
  from chat_sql.schema import parse_schema
  from chat_sql.sample_data import generate_sample_data

  schema = parse_schema(open("schemas/biblioteca.sql", encoding="utf-8").read())
  dados = generate_sample_data(schema, 10000)
  ```
- O gerador respeita as relações (um empréstimo só aponta para livro/usuário que existem).

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
