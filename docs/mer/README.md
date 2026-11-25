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

Você tem **três caminhos**. O primeiro é o mais confiável.

### Opção 1 — draw.io com o arquivo pronto (recomendado)

1. Abra <https://app.diagrams.net> (não precisa instalar nem criar conta)
2. **File → Open From → Device…**
3. Escolha [`biblioteca.drawio`](biblioteca.drawio)
4. O diagrama aparece montado: 7 tabelas, colunas com **PK / FK / (nulo)**, e 6 setas
   de relacionamento em notação pé-de-galinha
5. **File → Export as → PNG** (marque *Transparent Background* desmarcado e *Zoom* 200% para ficar nítido)
6. Salve em [`docs/imagens/`](../imagens/) como `diagrama-er.png`

> As caixas vêm posicionadas, mas você pode arrastar para melhorar o layout.
> Se mover uma caixa, as setas acompanham e continuam presas à borda.

**Como ler o diagrama:** cada seta sai da tabela que **guarda** a chave
estrangeira e aponta para a tabela **referenciada**. A ponta em "pé de galinha"
(três traços) fica no lado que pode ter muitos registros; a ponta simples, no
lado do registro único. Exemplo: `EMPRÉSTIMO` (muitos) → `USUÁRIO` (um).

As marcas entre colchetes:

| Marca | Significado |
|---|---|
| `[PK]` | Chave primária — identifica a linha |
| `[FK]` | Chave estrangeira — aponta para outra tabela |
| `[PK, FK]` | As duas coisas (tabelas de ligação, como `LIVRO_AUTOR`) |
| `[(nulo)]` | Campo opcional — aceita vazio |

**Se o arquivo não abrir:** é sinal de que o download corrompeu (acontece no Windows ao salvar pelo navegador). Baixe de novo com `git pull` e abra direto do repositório.

### Opção 2 — importar o Mermaid

1. Abra <https://app.diagrams.net>
2. **Arrange → Insert → Advanced → Mermaid**
3. Cole o bloco de [`02-logico.md`](02-logico.md), começando em `erDiagram` e terminando na última `}` (sem as três crases)
4. Ajuste o layout manualmente

> ⚠️ A conversão do Mermaid pode trazer as tabelas **sem as linhas de relacionamento**. Se isso acontecer, use a Opção 1.

### Opção 3 — dbdiagram.io (alternativa)

1. Abra <https://dbdiagram.io>
2. Cole [`biblioteca.dbml`](biblioteca.dbml)
3. **Export → PNG**

Não é draw.io, mas gera imagem pronta para o relatório.

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

E o arquivo `biblioteca.drawio` (para abrir no draw.io) por:

```powershell
.\venv\Scripts\python scripts\exportar_drawio.py
```

Ou seja: se o banco mudar, é só rodar de novo. Não são digitados à mão — não
podem divergir do que está no ar.

Os arquivos `01`, `04` e `06` são escritos manualmente, porque exigem
interpretação do negócio (não dá para extrair "por que" do catálogo do banco).

> ⚠️ Os arquivos `biblioteca_mer.png`, `biblioteca_mer.dot` e
> `biblioteca_mer.svg` que existiam antes estão **desatualizados** — o banco
> mudou desde então. Use os links acima.
