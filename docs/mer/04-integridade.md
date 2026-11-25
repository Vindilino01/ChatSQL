# Integridade dos dados

[Início](../../README.md) · [Índice](README.md) · [Dicionário](03-dicionario-dados.md)

O que o banco impede que aconteça — e por quê.

---

## Resumo

| Tipo | Quantidade | Impede |
|---|---|---|
| PRIMARY KEY | 7 | linhas duplicadas |
| FOREIGN KEY | 6 | referência a algo inexistente |
| UNIQUE | 5 | dois iguais onde só cabe um |
| CHECK | 6 | valores fora do domínio |
| Índice único parcial | 1 | dois empréstimos abertos no mesmo exemplar |

## PRIMARY KEY

Identifica cada linha. Em `livro_autor`, a chave é **composta** (`id_livro` +
`id_autor`): o mesmo par não pode repetir, mas o mesmo livro pode aparecer com
autores diferentes.

## FOREIGN KEY

| De | Para | Ao apagar o pai |
|---|---|---|
| `livro.id_editora` | `editora` | bloqueia (RESTRICT) |
| `exemplar.id_livro` | `livro` | bloqueia |
| `livro_autor.id_livro` | `livro` | apaga em cascata (CASCADE) |
| `livro_autor.id_autor` | `autor` | bloqueia |
| `emprestimo.id_usuario` | `usuario` | bloqueia |
| `emprestimo.id_exemplar` | `exemplar` | bloqueia |

**Por que CASCADE só em `livro_autor`:** a ligação livro↔autor não existe
sozinha. Se o livro é apagado, a ligação perde sentido. Já um empréstimo é
**histórico** — apagar um usuário não pode levar junto o registro do que ele
pegou.

**Por que os outros são RESTRICT (explícito):** o padrão do PostgreSQL é
`NO ACTION`, que se comporta como RESTRICT nesse caso. Declaramos explicitamente
para que a intenção fique documentada no schema e não seja alterada por engano.

## UNIQUE

| Tabela | Coluna | Impede |
|---|---|---|
| `usuario` | `documento` | a mesma pessoa cadastrada duas vezes |
| `usuario` | `email` | e-mail repetido |
| `editora` | `nome` | duas editoras com o mesmo nome |
| `livro` | `isbn` | o mesmo livro catalogado duas vezes |
| `exemplar` | `codigo_patrimonio` | duas etiquetas iguais |

### Por que CPF e ISBN são só dígitos

`documento` tem **11 dígitos** e `isbn` tem **13**, sem pontos nem hífen. Um
`CHECK` valida o formato:

```sql
CHECK (documento ~ '^[0-9]{11}$')
CHECK (isbn ~ '^[0-9]{13}$')
```

Se guardássemos formatado, `123.456.789-01` e `12345678901` seriam **strings
diferentes** para o banco, e o `UNIQUE` deixaria passar a mesma pessoa (ou o
mesmo livro) duas vezes. A máscara é responsabilidade da interface, não do
armazenamento.

## CHECK

| Nome | Regra | Por quê |
|---|---|---|
| `ck_usuario_tipo` | `aluno · professor · funcionario` | impede "bolsista" digitado por engano |
| `ck_usuario_documento` | 11 dígitos | formato do CPF |
| `ck_livro_isbn` | 13 dígitos | formato do ISBN-13 |
| `ck_livro_ano` | entre 1400 e 2100 | `> 0` aceitaria o ano 30000 |
| `ck_exemplar_estado` | 5 valores | estado é domínio fechado |
| `ck_emprestimo_datas` | prevista > empréstimo; devolução ≥ empréstimo | coerência temporal |

```sql
-- ck_emprestimo_datas, completo
CHECK (
    data_prevista_devolucao > data_emprestimo
    AND (data_devolucao IS NULL OR data_devolucao >= data_emprestimo)
)
```

A devolução prevista tem de ser **posterior** (não igual) à retirada: emprestar
e devolver no mesmo dia não é empréstimo, é consulta.

## O índice único parcial

```sql
CREATE UNIQUE INDEX idx_exemplar_emprestimo_ativo
    ON emprestimo (id_exemplar)
    WHERE data_devolucao IS NULL;
```

**Esta é a restrição mais importante do projeto.** Ela implementa no banco:

> Um exemplar não pode ter dois empréstimos abertos ao mesmo tempo.

Sem ela, uma falha de concorrência (ou um `INSERT` manual) criaria dois
empréstimos do mesmo exemplar. A maioria dos sistemas resolve isso no código da
aplicação, onde a regra pode ser burlada. Aqui, o banco recusa.

**Por que "parcial":** o índice só considera linhas com `data_devolucao IS NULL`
(empréstimos abertos). Empréstimos já devolvidos não entram na contagem, então o
mesmo exemplar pode ter **vários empréstimos ao longo do tempo** — mas só um
aberto.

---

[Início](../../README.md) · [Índice](README.md) · [Dicionário](03-dicionario-dados.md)
