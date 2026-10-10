# Frente A - Banco de dados

**Responsaveis:** (preencher)

## Em uma frase

Conectar o Chat SQL a um banco de dados de verdade, permitindo **apenas leitura**
(nunca apaga ou altera nada).

## Onde fica no projeto

| Arquivo | O que e |
|---|---|
| `chat_sql/db.py` | **O coracao desta frente**: faz a conexao e le o banco. |
| `tests/test_db_connector.py` | Os testes que provam que funciona (e que escrita e bloqueada). |
| `app.py` (funcao `_connect_database`) | A tela onde o usuario digita a conexao. |
| `docs/adr/0008-conexao-somente-leitura.md` | A decisao de permitir conexao, mas so leitura. |

O que ja esta pronto: conexao e leitura de **SQLite** e **Postgres**, com
introspeccao do banco (descobrir tabelas, colunas e relacoes) e bloqueio de escrita.

## Primeira tarefa (passo a passo)

1. Abra `chat_sql/db.py` e leia os comentarios do topo.
2. Rode os testes desta frente:
   ```powershell
   .\venv\Scripts\python -m pytest tests/test_db_connector.py -v
   ```
3. Entenda o fluxo: `DatabaseSource` conecta, `_introspect` le o banco e
   `execute` passa pela Trava antes de rodar.
4. Depois, teste com um Postgres de verdade (proximo topico).

## O que mexer para...

**Testar num Postgres real**
```powershell
$env:CHATSQL_POSTGRES_URL="postgresql+psycopg://usuario_readonly:senha@localhost:5432/biblioteca"
.\venv\Scripts\python -m pytest tests/test_db_connector.py -v
```
Use sempre um usuario **somente-leitura** no banco.

**Adicionar suporte a MySQL**
- Em `chat_sql/db.py`, no metodo `_apply_read_only`, ja existe um trecho para MySQL.
- Instale o driver: `.\venv\Scripts\python -m pip install pymysql`.
- Adicione um teste em `tests/test_db_connector.py`.

**Melhorar a tela da conexao**
- O formulario esta em `app.py`, na funcao `_connect_database` e na parte do
  radio "Banco de dados" da funcao `_render_data_tab`.
- Ideias: botao "Testar conexao", seletor visual de tabelas, salvar a conexao
  (sem a senha).

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Aba **Dados** -> marque **Banco de dados (Postgres/SQLite)** -> cole a URL ->
**Conectar e usar** -> va para a aba **Chat** e pergunte.

## Pronto quando

- [ ] `pytest tests/test_db_connector.py -v` passa.
- [ ] Um teste real em Postgres foi feito (com usuario read-only).
- [ ] Se mexeu em algo novo, criou o teste correspondente.
- [ ] Atualizou este guia ou o `ROADMAP.md` se mudou o combinado.

## Nao confunda

- `chat_sql/db.py` = banco **de verdade**.
- `chat_sql/engine.py` = banco **na memoria** (usado por planilhas e exemplos).
