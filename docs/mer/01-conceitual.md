# MER conceitual — Biblioteca Universitária

[Início](../../README.md) · [Índice](README.md) · [Diagrama lógico](02-logico.md)

Modelo **conceitual**: entidades, relacionamentos e cardinalidades. Não menciona
tipos nem chaves — é a leitura do negócio, antes de virar tabela.

---

## Entidades

| Entidade | O que representa |
|---|---|
| **Usuário** | Aluno, professor ou funcionário que pega livros emprestados |
| **Livro** | A obra (título, ISBN, ano) — não a cópia física |
| **Exemplar** | Cada cópia física do livro, com etiqueta de patrimônio |
| **Autor** | Quem escreveu a obra |
| **Editora** | Quem publicou a obra |
| **Empréstimo** | O ato de retirar e devolver um exemplar |

## Atributos principais

**Usuário** — nome, documento (CPF), e-mail, tipo (aluno/professor/funcionário), data de cadastro

**Livro** — título, ISBN, ano de publicação

**Exemplar** — código de patrimônio, estado de conservação

**Autor** — nome, nacionalidade

**Editora** — nome, país

**Empréstimo** — data da retirada, data prevista de devolução, data efetiva de devolução

## Relacionamentos

```
EDITORA ──(1)── publica ──(N)── LIVRO
LIVRO   ──(1)── possui   ──(N)── EXEMPLAR
LIVRO   ──(N)── tem      ──(N)── AUTOR          ← resolve com LIVRO_AUTOR
EXEMPLAR──(1)── é emprestado ─(N)── EMPRÉSTIMO
USUÁRIO ──(1)── realiza  ──(N)── EMPRÉSTIMO
```

| Relacionamento | Cardinalidade | Leitura |
|---|---|---|
| Editora publica Livro | 1 : N | uma editora publica vários livros; cada livro tem uma editora |
| Livro possui Exemplar | 1 : N | um livro tem várias cópias; cada cópia é de um livro |
| Livro tem Autor | N : N | um livro pode ter vários autores; um autor pode ter vários livros |
| Exemplar é emprestado | 1 : N | um exemplar tem vários empréstimos ao longo do tempo, mas **só um aberto** por vez |
| Usuário realiza Empréstimo | 1 : N | um usuário faz vários empréstimos; cada empréstimo é de um usuário |

## Diagrama (notação de Chen)

```
        ┌─────────┐            ┌─────────┐
        │ EDITORA │            │  AUTOR  │
        └────┬────┘            └────┬────┘
             │ 1                    │ N
        ◇ publica              ◇ escreve
             │ N                    │
        ┌────┴──────────────────────┴────┐
        │            LIVRO               │
        └────┬───────────────────────────┘
             │ 1
        ◇ possui
             │ N
        ┌────┴─────┐
        │ EXEMPLAR │
        └────┬─────┘
             │ 1
        ◇ é emprestado
             │ N
        ┌────┴──────┐          ┌──────────┐
        │EMPRÉSTIMO │──────────│ USUÁRIO  │
        └───────────┘  N : 1   └──────────┘
                        realiza
```

## Regras de negócio

1. Um **exemplar** pertence a exatamente um **livro**.
2. Um **livro** pertence a exatamente uma **editora**.
3. Um **livro** pode ter vários **autores**, e vice-versa.
4. Um **usuário** pode fazer vários **empréstimos**.
5. Um **exemplar** não pode ter **dois empréstimos abertos** ao mesmo tempo.
6. A **data prevista de devolução** é sempre posterior à data do empréstimo.
7. A **data de devolução** (quando existe) não pode ser anterior à retirada.

> As regras 5, 6 e 7 são garantidas **pelo banco de dados**, não pelo código da
> aplicação. Ver [04-integridade.md](04-integridade.md).

## Decisão de modelagem: uma tabela `usuario`

O modelo inicial previa `ALUNO` e `FUNCIONARIO` separados. Optamos por **uma
tabela `usuario` com `tipo_usuario`**, porque:

| Critério | Duas tabelas | `usuario` + tipo |
|---|---|---|
| Empréstimo aponta para quem? | precisaria de duas FKs (só uma válida) | uma FK só |
| "Quem mais pegou livro?" | `UNION` de duas consultas | `GROUP BY` simples |
| Atributo exclusivo (curso, cargo) | cabe naturalmente | **não cabe** |

O que se perde: `curso` (do aluno) e `cargo` (do funcionário). Se isso for
necessário, o caminho é **herança** (`usuario` + `aluno_detalhe` +
`funcionario_detalhe`), não voltar ao modelo de duas tabelas independentes.

---

[Início](../../README.md) · [Índice](README.md) · [Diagrama lógico](02-logico.md)
