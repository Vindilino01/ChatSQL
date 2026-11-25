# Banco de dados — Biblioteca Universitária

Documento de apoio ao schema `schemas/biblioteca-postgres.sql`, explicando
**por que** cada decisão foi tomada. Serve para a defesa do projeto.

[Início](../README.md) · [Índice](README.md) · [Guia da Frente D](frentes/D-dados-e-biblioteca.md)

---

## Visão geral

Sete tabelas, modeladas em 3ª forma normal:

```
editora ──< livro ──< exemplar ──< emprestimo >── usuario
                │
                └──< livro_autor >── autor
```

- `livro_autor` resolve o N:N entre livro e autor (PK composta).
- `exemplar` é a cópia física; um livro tem várias.
- `emprestimo` liga um exemplar a um usuário.

## Tabelas

| Tabela | Função | Chave |
|---|---|---|
| `usuario` | quem pega livros emprestados | `id_usuario` |
| `editora` | quem publica | `id_editora` |
| `autor` | quem escreve | `id_autor` |
| `livro` | a obra (título, ISBN, ano) | `id_livro` |
| `exemplar` | a cópia física (patrimônio, estado) | `id_exemplar` |
| `livro_autor` | ligação N:N | (`id_livro`, `id_autor`) |
| `emprestimo` | retirada e devolução | `id_emprestimo` |

## Por que cada restrição existe

**PRIMARY KEY** — identifica cada registro. Em `livro_autor` é composta porque
o mesmo par livro+autor não pode se repetir.

**FOREIGN KEY** — garante integridade referencial. Sem elas, um empréstimo
poderia apontar para um exemplar que não existe.

**`ON DELETE` explícito** — o padrão do Postgres é `NO ACTION`, mas declarar a
intenção evita surpresa:
- `RESTRICT` nas relações com histórico (não apagar uma editora que tem livros);
- `CASCADE` apenas em `livro_autor`, onde a ligação não faz sentido sozinha.

**NOT NULL** — campos obrigatórios do domínio.

**UNIQUE** — `documento`, `email`, `isbn` e `codigo_patrimonio` não podem repetir.

**CHECK de CPF e ISBN** — este é o ponto mais importante de defesa:
guardamos **apenas dígitos** (11 para CPF, 13 para ISBN) e validamos o formato.
Se armazenássemos formatado, `123.456.789-01` e `12345678901` seriam strings
diferentes e o `UNIQUE` deixaria passar a mesma pessoa duas vezes. A formatação
(máscara) é responsabilidade da interface.

**CHECK de ano** — `> 0` aceitaria o ano 30000; a faixa 1400–2100 mantém os
dados plausíveis.

**CHECK de estado/tipo** — `tipo_usuario` e `estado_conservacao` só aceitam os
valores previstos. Isso também impede que o gerador de dados fictícios invente
valores inválidos.

**CHECK de datas** — a devolução prevista precisa ser **posterior** ao
empréstimo (mesmo dia não faz sentido) e a devolução real não pode ser anterior
à retirada.

**Índice único parcial** — `idx_exemplar_emprestimo_ativo` garante no banco que
um exemplar não tenha dois empréstimos abertos. É uma regra de negócio
implementada onde ela não pode ser burlada: no próprio banco.

## Por que cada índice existe

| Índice | Motivo |
|---|---|
| `idx_livro_editora` | toda FK usada em JOIN deve ter índice |
| `idx_exemplar_livro` | idem |
| `idx_emprestimo_usuario` / `idx_emprestimo_exemplar` | histórico por pessoa/exemplar |
| `idx_emprestimo_data` | as perguntas do Chat SQL filtram por data |
| `idx_livro_autor_autor` | busca "livros de um autor" |
| `idx_livro_titulo_trgm` | **GIN + pg_trgm**: busca por trecho (`LIKE '%dom%'`) |

Sobre o último: um índice btree comum **não** atende `LIKE '%texto%'` — o banco
ainda varre a tabela inteira. O índice GIN com `pg_trgm` atende justamente esse
tipo de busca, que é o que o Chat SQL gera quando você pergunta "livros que
contêm Dom".

## Como aplicar

**Neon (ou qualquer Postgres gerenciado):**
```powershell
.\venv\Scripts\python scripts\apply_ddl.py
.\venv\Scripts\python scripts\seed_biblioteca.py     # dados de exemplo
```
O script lê `CHATSQL_SEED_URL` do `.env`, recria as tabelas e imprime um resumo
(tabelas, índices, restrições, extensões). Nunca imprime a senha.

O seed usa um **acervo real** definido em `scripts/acervo_biblioteca.py` (456
obras e 40 editoras), com a nacionalidade dos 277 autores em
`scripts/acervo_nacionalidades.py` e a editora de cada obra em
`scripts/acervo_editoras.py`.

| Dado | Origem |
|---|---|
| Título, ano da 1ª publicação, autor | Reais |
| Nacionalidade do autor | Real, autor por autor |
| Nome e país da editora | Reais |
| Editora de cada obra | Atribuída por área (plausível, não é a edição real) |
| ISBN | Sintético (dígito verificador válido) |
| Exemplares, usuários, empréstimos | Gerados |

> **Atenção:** o script **remove** as tabelas antes de recriar. É intencional
> durante o desenvolvimento; não rode em produção.

## Conectar no app

Aba **Dados** → **Banco de dados (Postgres/SQLite)**:
```
postgresql+psycopg://USUARIO:SENHA@HOST/BANCO?sslmode=require
```
Use um usuário **somente leitura**. O app aplica `SET TRANSACTION READ ONLY`,
limita o tempo e bloqueia qualquer coisa que não seja `SELECT` pela Trava — mas
o usuário read-only é a última linha de defesa.

### Criar o usuário somente leitura

```sql
CREATE ROLE chatsql_ro LOGIN PASSWORD 'uma_senha_forte';
GRANT CONNECT ON DATABASE neondb TO chatsql_ro;
GRANT USAGE ON SCHEMA public TO chatsql_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatsql_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO chatsql_ro;
```

## Dialeto

O Motor Offline precisa falar o SQL do banco conectado. Isso é resolvido por
`chat_sql/nl/dialect.py`:

| Intenção | SQLite | Postgres |
|---|---|---|
| mês passado | `date('now','-1 month')` | `CURRENT_DATE - INTERVAL '1 months'` |
| este mês | `date('now','start of month')` | `date_trunc('month', CURRENT_DATE)::date` |
| mês da coluna | `strftime('%m', col)` | `to_char(col, 'MM')` |
| busca sem caixa | `LIKE` | `ILIKE` |
| booleano | `1` / `0` | `true` / `false` |

Coberto por `tests/test_dialect.py` (20 testes).

## Divergências conhecidas do material original

- O MER mostra `email VARCHAR(20)` e `pais VARCHAR(40)`; o DDL usa 150 e 60.
  **O DDL é a fonte da verdade** — vale corrigir o documento do grupo.
- Nomes de tabela: o MER usa plural (`LIVROS`), o DDL usa singular (`livro`).
  Padronizamos **singular sem acento**.
- O MER escreve `ano_publicação` (com cedilha); a coluna é `ano_publicacao`.

---

[Início](../README.md) · [Índice](README.md) · [Guia da Frente D](frentes/D-dados-e-biblioteca.md)
