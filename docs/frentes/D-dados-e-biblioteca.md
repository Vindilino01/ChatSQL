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
| `chat_sql/sample_data.py` | Cria dados de exemplo automaticamente (a função `generate_sample_data`). |
| `chat_sql/spreadsheet.py` | Lê planilhas CSV, XLSX e XLS. |
| `chat_sql/sheets.py` | **A implementar**: ler planilha pública do Google Sheets. |
| `chat_sql/sql_dump.py` | **A implementar**: importar arquivo `.sql`. |
| `tests/test_sample_data.py` | Testes dos dados de exemplo. |
| `tests/test_spreadsheet.py` | Testes de planilhas. |
| `tests/test_sheets.py` e `tests/test_sql_dump.py` | **Testes-guia** (estão com `skip`; remova o `skip` ao implementar). |

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

Os arquivos já existem como esqueleto, com comentários explicando o que fazer:
- `chat_sql/sheets.py`: transformar o link de edição na URL de export CSV e baixar.
- `chat_sql/sql_dump.py`: ler o arquivo e detectar se tem `CREATE TABLE` + `INSERT`.

Para cada um, existe um teste-guia pronto. **Remova o `skip`** e faça passar:
```powershell
.\venv\Scripts\python -m pytest tests/test_sheets.py -v
.\venv\Scripts\python -m pytest tests/test_sql_dump.py -v
```

## Como testar

```powershell
.\venv\Scripts\python -m pytest tests/test_sample_data.py tests/test_spreadsheet.py -v
```

## Pronto quando

- [ ] `schemas/biblioteca.sql` existe e carrega no app.
- [ ] Dá para gerar 10 mil registros sem erro.
- [ ] `tests/test_sheets.py` e `tests/test_sql_dump.py` passam (sem `skip`).
- [ ] A demo responde pelo menos 15 perguntas sobre a biblioteca.

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| Schema | A estrutura do banco (as tabelas e colunas) |
| Seed / semente | O ponto de partida para gerar dados de exemplo |
| Dump | Um arquivo `.sql` com o banco inteiro para importar |
| CSV | Um arquivo de planilha simples, separado por vírgulas ou ponto e vírgula |

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
