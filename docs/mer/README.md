# Documentação do banco — Biblioteca Universitária

[Início](../../README.md) · [Como conectar](../COMO-CONECTAR.md)

O banco da demonstração é uma **biblioteca universitária** em PostgreSQL (Neon).
São 7 tabelas, 29 colunas e cerca de 5.300 registros com **obras, autores e
editoras reais**.

## Ordem de leitura sugerida

| # | Arquivo | Para quê |
|---|---|---|
| 1 | [01-conceitual.md](01-conceitual.md) | Entidades, relacionamentos e regras de negócio |
| 2 | [02-logico.md](02-logico.md) | Diagrama de tabelas (o GitHub desenha sozinho) |
| 3 | [03-dicionario-dados.md](03-dicionario-dados.md) | Cada coluna, com tipo e explicação |
| 4 | [04-integridade.md](04-integridade.md) | O que o banco impede que aconteça |
| 5 | [05-indices.md](05-indices.md) | Índices e o único parcial |
| 6 | [06-normalizacao.md](06-normalizacao.md) | Prova de 1FN, 2FN e 3FN |
| 7 | [07-ddl.sql](07-ddl.sql) | O SQL real do banco |

## Para o diagrama do relatório

1. Abra <https://dbdiagram.io>
2. Cole o conteúdo de [`biblioteca.dbml`](biblioteca.dbml)
3. **Export → PNG**
4. Salve em [`docs/imagens/`](../imagens/)

Nada para instalar.

## Resumo das tabelas

| Tabela | O que guarda | Registros |
|---|---|---|
| `livro` | A obra: título, ISBN, ano | 456 |
| `autor` | Quem escreveu | 277 |
| `editora` | Quem publicou | 40 |
| `livro_autor` | Liga livro↔autor (N:N) | 481 |
| `exemplar` | A cópia física | 744 |
| `usuario` | Aluno, professor ou funcionário | 800 |
| `emprestimo` | Retiradas e devoluções | 2.500 |

## Como estes arquivos foram gerados

Os arquivos `02`, `03`, `05`, `07` e `biblioteca.dbml` são **extraídos do banco
em uso** por:

```powershell
.\venv\Scripts\python scripts\exportar_mer.py
```

Ou seja: se o banco mudar, é só rodar de novo. Não são digitados à mão — não
podem divergir do que está no ar.

Os arquivos `01`, `04` e `06` são escritos manualmente, porque exigem
interpretação do negócio (não dá para extrair "por que" do catálogo do banco).

> ⚠️ Os arquivos `biblioteca_mer.png`, `biblioteca_mer.dot` e
> `biblioteca_mer.svg` que existiam antes estão **desatualizados** — o banco
> mudou desde então. Use os links acima.
