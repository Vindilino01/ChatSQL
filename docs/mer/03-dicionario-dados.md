# Dicionário de dados

[Início](../../README.md) · [Índice](README.md)

Uma linha por coluna. Gerado a partir do banco em uso.

## `autor`

Quem escreveu a obra.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_autor` | inteiro grande | sim | — | Identificador único do autor. |
| `nome` | texto (120) | sim | — | Nome do autor. |
| `nacionalidade` | texto (60) | não | — | País de origem do autor. |

## `editora`

Empresa que publica o livro.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_editora` | inteiro grande | sim | — | Identificador único da editora. |
| `nome` | texto (120) | sim | — | Razão social. |
| `pais` | texto (60) | sim | — | País de origem. |

## `emprestimo`

Retirada e devolução de um exemplar por um usuário.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_emprestimo` | inteiro grande | sim | — | Identificador único do empréstimo. |
| `id_usuario` | inteiro grande | sim | — | Quem retirou. |
| `id_exemplar` | inteiro grande | sim | — | Qual cópia foi retirada. |
| `data_emprestimo` | data | sim | `CURRENT_DATE` | Data da retirada. |
| `data_prevista_devolucao` | data | sim | — | Prazo combinado (posterior à retirada). |
| `data_devolucao` | data | não | — | Quando devolveu. Vazio = ainda emprestado. |

## `exemplar`

A cópia física do livro, com código de patrimônio e estado.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_exemplar` | inteiro grande | sim | — | Identificador único da cópia física. |
| `codigo_patrimonio` | texto (30) | sim | — | Etiqueta de patrimônio colada no livro. |
| `id_livro` | inteiro grande | sim | — | Qual obra esta cópia representa. |
| `estado_conservacao` | texto (20) | sim | — | bom · danificado · em_manutencao · extraviado · descartado. |

## `livro`

A obra em si — título, ISBN e ano. Não é a cópia física.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_livro` | inteiro grande | sim | — | Identificador único da obra. |
| `titulo` | texto (200) | sim | — | Título da obra. |
| `isbn` | texto (13) | sim | — | ISBN-13 com 13 dígitos, sem hífens. |
| `ano_publicacao` | inteiro curto | sim | — | Ano da edição, entre 1400 e 2100. |
| `id_editora` | inteiro grande | sim | — | Editora que publicou. |

## `livro_autor`

Liga livros a autores (um livro pode ter vários autores).

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_livro` | inteiro grande | sim | — | Obra. |
| `id_autor` | inteiro grande | sim | — | Autor da obra. |

## `usuario`

Quem pega livros emprestados: alunos, professores e funcionários.

| Coluna | Tipo | Obrigatória | Padrão | O que é |
|---|---|---|---|---|
| `id_usuario` | inteiro grande | sim | — | Identificador único do usuário. |
| `nome` | texto (120) | sim | — | Nome completo. |
| `documento` | texto (11) | sim | — | CPF com 11 dígitos, sem pontos nem traço. |
| `email` | texto (150) | sim | — | E-mail institucional. |
| `tipo_usuario` | texto (20) | sim | — | aluno · professor · funcionario. |
| `data_cadastro` | data e hora | sim | `now()` | Quando o usuário foi cadastrado. |
