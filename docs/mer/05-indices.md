# Índices

[Início](../../README.md) · [Índice](README.md)

Índices aceleram a busca ao custo de espaço e de escrita mais lenta.
Como este banco é somente leitura para o app, criamos os que ajudam as consultas.

| Tabela | Índice | Serve para |
|---|---|---|
| `emprestimo` | `idx_emprestimo_data` | filtrar por data (mês passado, este ano) |
| `emprestimo` | `idx_emprestimo_exemplar` | histórico de um exemplar |
| `emprestimo` | `idx_emprestimo_usuario` | histórico de um usuário |
| `emprestimo` | `idx_exemplar_emprestimo_ativo` | impedir dois empréstimos abertos no mesmo exemplar |
| `exemplar` | `idx_exemplar_livro` | juntar exemplar com livro |
| `livro` | `idx_livro_editora` | juntar livro com editora |
| `livro` | `idx_livro_titulo_trgm` | buscar por trecho no título (`ILIKE '%dom%'`) |
| `livro_autor` | `idx_livro_autor_autor` | buscar livros de um autor |

## O índice único parcial

```sql
CREATE UNIQUE INDEX idx_exemplar_emprestimo_ativo ON public.emprestimo USING btree (id_exemplar) WHERE (data_devolucao IS NULL);
```

Este é o índice mais importante do projeto. Ele implementa **no banco** a regra:
"um exemplar não pode ter dois empréstimos abertos ao mesmo tempo".
A maioria dos sistemas resolve isso no código da aplicação — onde pode ser burlado.
Aqui, nem um `INSERT` manual consegue violar a regra.
