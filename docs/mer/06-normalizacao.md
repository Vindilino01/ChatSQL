# Normalização

[Início](../../README.md) · [Índice](README.md) · [MER conceitual](01-conceitual.md)

O banco está na **Terceira Forma Normal (3FN)**. Abaixo, a prova por tabela.

---

## O que cada forma exige

| Forma | Exige | Violação típica |
|---|---|---|
| **1FN** | todo valor é atômico; sem grupos repetidos | coluna `telefones` com "11-9999, 11-8888" |
| **2FN** | 1FN + nenhum atributo depende de **parte** da chave | com PK (livro, autor), guardar `titulo` do livro na ligação |
| **3FN** | 2FN + nenhum atributo depende de **outro não-chave** | guardar `nome_editora` dentro de `livro` |

## Prova por tabela

### `usuario`
- **1FN:** cada coluna é atômica (nome, documento, e-mail). ✔
- **2FN:** PK simples (`id_usuario`); não há chave composta para violar. ✔
- **3FN:** `tipo_usuario` depende só do usuário; não há coluna que dependa de
  outra não-chave. ✔

### `editora`
- Colunas: `id_editora`, `nome`, `pais`. Todos dependem só da chave. ✔

### `autor`
- Colunas: `id_autor`, `nome`, `nacionalidade`. ✔

### `livro`
- **3FN:** **não** guardamos `nome_editora`. Guardamos `id_editora` (FK). Se
  guardássemos o nome, haveria dependência transitiva
  (`id_livro → id_editora → nome_editora`) e mudar o nome da editora exigiria
  atualizar todos os livros. ✔

### `exemplar`
- **3FN:** **não** guardamos `titulo` do livro. Guardamos `id_livro`. ✔
- `codigo_patrimonio` é atributo da cópia física, não do livro — por isso fica
  aqui e não em `livro`.

### `livro_autor`
- **1FN:** duas colunas atômicas.
- **2FN:** PK composta (`id_livro`, `id_autor`) e **nenhum atributo extra**. Se
  tivéssemos `nome_autor` aqui, ele dependeria só de `id_autor` — violação de
  2FN. Por isso a tabela tem apenas as duas chaves. ✔
- Esta é a forma correta de resolver um relacionamento **N : N**.

### `emprestimo`
- **3FN:** guardamos `id_usuario` e `id_exemplar`, não o nome nem o título.
  Nome do usuário muda; o empréstimo não deve ser reescrito por isso. ✔
- `data_prevista_devolucao` é atributo **do empréstimo** (o prazo combinado
  naquele caso), não do exemplar. Por isso não está em `exemplar`.

## Uma dependência que aceitamos

`data_prevista_devolucao` poderia ser calculada (`data_emprestimo + 14 dias`),
o que seria tecnicamente redundante. Mantivemos como coluna porque:

- o prazo **varia** (aluno 14 dias, professor 30 dias) e é histórico;
- guardar o valor combinado preserva o que foi acordado, mesmo se a regra mudar
  depois.

Isso é uma **desnormalização intencional**, documentada — não um descuido.

## O que ficaria pior se voltássemos ao modelo antigo

O MER original tinha `ALUNO` e `FUNCIONARIO` separados. Isso obrigaria
`emprestimo` a ter duas FKs (`matricula` e `codigo_funcionario`), com **apenas
uma preenchida** por linha — um relacionamento polimórfico, que:

- impede `NOT NULL` nas duas colunas;
- exige `CHECK` do tipo "exatamente uma preenchida";
- torna "quem mais pegou livro" uma consulta com `UNION`.

A tabela única `usuario` resolve os três problemas de uma vez.

---

[Início](../../README.md) · [Índice](README.md) · [MER conceitual](01-conceitual.md)
