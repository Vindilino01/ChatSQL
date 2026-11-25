# Diagrama lógico (tabelas e relacionamentos)

[Início](../../README.md) · [Índice](README.md)

Este diagrama é renderizado pelo próprio GitHub — não precisa instalar nada.

```mermaid
erDiagram
    autor {
        bigint id_autor PK
        varchar nome
        varchar nacionalidade
    }
    editora {
        bigint id_editora PK
        varchar nome
        varchar pais
    }
    emprestimo {
        bigint id_emprestimo PK
        bigint id_usuario
        bigint id_exemplar
        date data_emprestimo
        date data_prevista_devolucao
        date data_devolucao
    }
    exemplar {
        bigint id_exemplar PK
        varchar codigo_patrimonio
        bigint id_livro
        varchar estado_conservacao
    }
    livro {
        bigint id_livro PK
        varchar titulo
        varchar isbn
        smallint ano_publicacao
        bigint id_editora
    }
    livro_autor {
        bigint id_livro PK
        bigint id_autor PK
    }
    usuario {
        bigint id_usuario PK
        varchar nome
        varchar documento
        varchar email
        varchar tipo_usuario
        timestamptz data_cadastro
    }

    exemplar ||--o{ emprestimo : "id_exemplar"
    usuario ||--o{ emprestimo : "id_usuario"
    livro ||--o{ exemplar : "id_livro"
    editora ||--o{ livro : "id_editora"
    autor ||--o{ livro_autor : "id_autor"
    livro ||--o{ livro_autor : "id_livro"
```

## Relacionamentos

| De | Para | Coluna | Regra ao apagar |
|---|---|---|---|
| `emprestimo` | `exemplar` | `id_exemplar` | RESTRICT |
| `emprestimo` | `usuario` | `id_usuario` | RESTRICT |
| `exemplar` | `livro` | `id_livro` | RESTRICT |
| `livro` | `editora` | `id_editora` | RESTRICT |
| `livro_autor` | `autor` | `id_autor` | RESTRICT |
| `livro_autor` | `livro` | `id_livro` | CASCADE |

## Contagem de registros

| Tabela | Registros |
|---|---|
| `autor` | 277 |
| `editora` | 40 |
| `emprestimo` | 2.500 |
| `exemplar` | 744 |
| `livro` | 456 |
| `livro_autor` | 481 |
| `usuario` | 800 |
