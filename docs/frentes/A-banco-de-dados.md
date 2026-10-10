# Frente A - Banco de dados

**Responsáveis:** (preencher)

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)

---

## Em uma frase

Conectar o Chat SQL a um banco de dados de verdade, permitindo **apenas leitura**
(nunca apaga ou altera nada).

## Onde fica no projeto

| Arquivo | O que é |
|---|---|
| `chat_sql/db.py` | **O coração desta frente**: faz a conexão e lê o banco. |
| `tests/test_db_connector.py` | Os testes que provam que funciona (e que escrita é bloqueada). |
| `app.py` (função `_connect_database`) | A tela onde o usuário digita a conexão. |
| `docs/adr/0008-conexao-somente-leitura.md` | A decisão de permitir conexão, mas só leitura. |

O que já está pronto: conexão e leitura de **SQLite** e **Postgres**, com
introspecção do banco (descobrir tabelas, colunas e relações) e bloqueio de escrita.

## Primeira tarefa (passo a passo)

1. Abra `chat_sql/db.py` e leia os comentários do topo.
2. Rode os testes desta frente:
   ```powershell
   .\venv\Scripts\python -m pytest tests/test_db_connector.py -v
   ```
3. Entenda o fluxo: `DatabaseSource` conecta, `_introspect` lê o banco e
   `execute` passa pela Trava antes de rodar.
4. Depois, teste com um Postgres de verdade (próximo tópico).

## O que mexer para...

**Testar num Postgres real**
```powershell
$env:CHATSQL_POSTGRES_URL="postgresql+psycopg://usuario_readonly:senha@localhost:5432/biblioteca"
.\venv\Scripts\python -m pytest tests/test_db_connector.py -v
```
Use sempre um usuário **somente leitura** no banco.

**Adicionar suporte a MySQL**
- No arquivo `chat_sql/db.py`, procure por `_apply_read_only`; já existe um trecho para MySQL.
- Instale o driver: `.\venv\Scripts\python -m pip install pymysql`.
- Adicione um teste em `tests/test_db_connector.py`.

**Melhorar a tela da conexão**
- No arquivo `app.py`, procure por `_connect_database` e por `_render_data_tab`.
- Ideias: botão "Testar conexão", seletor visual de tabelas, salvar a conexão
  (sem a senha).

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Aba **Dados** -> marque **Banco de dados (Postgres/SQLite)** -> cole a URL ->
**Conectar e usar** -> vá para a aba **Chat** e pergunte.

## Pronto quando

- [ ] `pytest tests/test_db_connector.py -v` passa.
- [ ] Um teste real em Postgres foi feito (com usuário read-only).
- [ ] Se mexeu em algo novo, criou o teste correspondente.
- [ ] Atualizou este guia ou o `ROADMAP.md` se mudou o combinado.

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| SQLAlchemy | Programa que fala com vários bancos diferentes |
| Introspecção | O robô "olhar" o banco e descobrir as tabelas e colunas |
| Read-only | Somente leitura (não apaga, não altera) |
| URL de conexão | O endereço com usuário, senha e nome do banco |

## Não confunda

- `chat_sql/db.py` = banco **de verdade**.
- `chat_sql/engine.py` = banco **na memória** (usado por planilhas e exemplos).

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
