# Relatório — Chat SQL

**Projeto A3 · Sistemas de Controle e Inteligência Artificial**
**Integrantes:** (preencher)
**Data:** (preencher)

[Início](README.md) · [PRD](PRD.md) · [Documentação do banco](docs/mer/README.md)

---

> **Como usar este arquivo:** cada seção tem o que escrever e onde buscar o
> conteúdo. As marcações `[PRENCHER]` indicam texto que vocês escrevem. O
> restante já está pronto para copiar.

---

## Sumário

1. [Introdução](#1-introdução)
2. [O problema](#2-o-problema)
3. [A solução](#3-a-solução)
4. [Arquitetura](#4-arquitetura)
5. [O banco de dados](#5-o-banco-de-dados)
6. [Segurança](#6-segurança)
7. [O motor offline](#7-o-motor-offline)
8. [Resultados](#8-resultados)
9. [Limitações](#9-limitações)
10. [Trabalhos futuros](#10-trabalhos-futuros)
11. [Conclusão](#11-conclusão)
12. [Referências](#12-referências)

---

## 1. Introdução

Uma biblioteca universitária acumula dados sobre seu acervo, seus usuários e seus
empréstimos. Esses dados ficam em um banco de dados, mas raramente chegam a quem
toma as decisões no dia a dia — porque consultá-los exige saber SQL.

Este trabalho apresenta o **Chat SQL**, um serviço que permite a qualquer
funcionário fazer perguntas em português e receber a resposta, com a consulta SQL
visível antes da execução e a garantia de que nenhum dado será alterado.

`[PRENCHER: 2 frases sobre o contexto da disciplina e por que este tema foi
escolhido.]`

## 2. O problema

`[PRENCHER: descreva um dia na biblioteca.]` Sugestão: o coordenador quer saber
quantos empréstimos estão atrasados. Hoje as opções são pedir ao TI (leva dias),
abrir uma planilha desatualizada, ou contratar uma ferramenta de BI (cara para o
porte da instituição).

O gargalo não está no dado — ele já existe e está estruturado. Está na
**linguagem**: só quem sabe SQL consegue perguntar.

## 3. A solução

O Chat SQL recebe uma pergunta em português e devolve:

1. a **consulta SQL** gerada;
2. o SQL só após revisão do usuário;
3. o **resultado** em tabela, com gráfico quando faz sentido.

Três características sustentam o uso real:

| Característica | O que significa |
|---|---|
| **Somente leitura** | Não altera nem apaga dados, em nenhuma hipótese |
| **SQL visível** | O usuário vê o que vai rodar antes de rodar |
| **Funciona sem IA** | Sem chave de API, sem custo por pergunta, sem dado saindo da instituição |

## 4. Arquitetura

```
 Pergunta (PT-BR)
       │
       ▼
 ┌───────────────┐   sem chave   ┌────────────────────┐
 │ Motor Offline │◄─────────────►│ Regras em PT-BR    │
 └───────┬───────┘               └────────────────────┘
         │ com chave (opcional)
         ▼
 ┌───────────────┐
 │ Provedor IA   │  (OpenAI-compatible)
 └───────┬───────┘
         │ Consulta SQL
         ▼
 ┌───────────────┐  rejeita DDL/DML e coluna inexistente
 │     Trava     │──────────────► Diagnóstico
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Fonte de Dados│  SQLite em memória  |  PostgreSQL
 └───────┬───────┘
         ▼
   Resultado (tabela + gráfico)
```

`[PRENCHER: 1 parágrafo explicando a figura em palavras próprias.]`

Implementação: Python 3.11+, Streamlit (interface), sqlglot (validação de SQL),
pandas, SQLite e PostgreSQL.

## 5. O banco de dados

A demonstração usa uma **Biblioteca Universitária** em PostgreSQL, hospedada no
Neon.

![Diagrama entidade-relacionamento](docs/imagens/diagrama-er.png)

`[SUBSTITUIR a imagem pelo PNG gerado no draw.io — ver docs/mer/README.md]`

> **A imagem acima ainda não existe.** Ela aparece quebrada até vocês gerarem:
> draw.io → abrir `docs/mer/biblioteca.drawio` → Export PNG → salvar como
> `docs/imagens/diagrama-er.png`. Passo a passo em
> [`docs/imagens/README.md`](docs/imagens/README.md).

### 5.1 Modelo

Sete tabelas, em terceira forma normal:

| Tabela | Função | Registros |
|---|---|---|
| `livro` | A obra (título, ISBN, ano) | 456 |
| `autor` | Quem escreveu | 277 |
| `editora` | Quem publicou | 40 |
| `livro_autor` | Liga livro e autor (N:N) | 481 |
| `exemplar` | A cópia física | 744 |
| `usuario` | Aluno, professor ou funcionário | 800 |
| `emprestimo` | Retirada e devolução | 2.500 |

Detalhamento completo em [`docs/mer/`](docs/mer/README.md): MER conceitual,
dicionário de dados, integridade, índices e prova de normalização.

### 5.2 Integridade

O banco não confia apenas na aplicação. Ele próprio impede estados inválidos:

- **7 chaves primárias** — sem registros duplicados
- **6 chaves estrangeiras** — sem referência a algo inexistente
- **5 restrições de unicidade** — CPF, e-mail, ISBN, patrimônio, nome de editora
- **6 restrições CHECK** — formato de CPF/ISBN, faixa de ano, domínios fechados
- **1 índice único parcial**, a restrição mais importante do projeto:

```sql
CREATE UNIQUE INDEX idx_exemplar_emprestimo_ativo
    ON emprestimo (id_exemplar)
    WHERE data_devolucao IS NULL;
```

Essa linha implementa **no banco** a regra "um exemplar não pode ter dois
empréstimos abertos ao mesmo tempo". A maioria dos sistemas resolve isso no
código da aplicação — onde a regra pode ser burlada. Aqui, nem um `INSERT`
manual consegue violar.

### 5.3 Uma decisão de modelagem

O modelo inicial previa `ALUNO` e `FUNCIONARIO` separados. Optamos por uma única
tabela `usuario` com a coluna `tipo_usuario`, porque:

| Critério | Duas tabelas | `usuario` + tipo |
|---|---|---|
| Empréstimo aponta para quem? | duas FKs, só uma válida | uma FK só |
| "Quem mais pegou livro?" | `UNION` de duas consultas | `GROUP BY` simples |

O que se perde é o atributo exclusivo de cada tipo (`curso`, `cargo`). Se for
necessário, o caminho é herança (`usuario` + tabelas de detalhe), não voltar ao
modelo de duas tabelas independentes.

## 6. Segurança

`[PRENCHER: 1 frase de introdução.]`

A proteção é em camadas, não em uma só:

| Camada | O que faz |
|---|---|
| **Trava** (sqlglot) | Aceita apenas uma instrução `SELECT`; rejeita DDL, DML, `PRAGMA`, `ATTACH` e funções perigosas |
| **Validação de schema** | Recusa coluna ou tabela que não existe — pega a "alucinação" antes de chegar ao banco |
| **Usuário read-only** | O usuário do banco não tem permissão de escrita |
| **Sessão read-only** | `SET TRANSACTION READ ONLY` na conexão |
| **Revisão humana** | O SQL aparece na tela e só executa no clique |

A frase que resume a decisão: **uma consulta errada é pior que consulta nenhuma.**
Por isso o motor, quando não entende, **não chuta** — devolve o motivo e sugere
perguntas.

## 7. O motor offline

`[PRENCHER: por que não usar IA para tudo?]` Três motivos: custo por pergunta,
proibição em muitas instituições, e determinismo (a mesma pergunta dá a mesma
resposta).

O motor funciona por regras: identifica a tabela, a intenção (contar, somar,
agrupar, listar), o filtro (texto, número, data, nulo) e monta o SQL. As
junções são resolvidas por busca em largura no grafo de chaves estrangeiras,
o que permite ligar tabelas que não têm FK direta.

A IA é opcional: há uma aba para colar a chave de um provedor compatível com a
API da OpenAI.

## 8. Resultados

### 8.1 Acurácia do motor

Medida comparando **o resultado** do SQL gerado com o de uma consulta de
referência escrita à mão — não basta "rodou sem erro".

| Conjunto | Perguntas | Acertos |
|---|---|---|
| Bateria de desenvolvimento | 28 | 28 (100%) |
| Validação cega (escrita depois) | 20 | 20 (100%) |
| Linguagem coloquial | 18 | 18 (100%) |
| Quarto conjunto (só do dicionário) | 25 | 25 (100%) |
| **Total** | **91** | **91 (100%)** |

Recusa de perguntas fora do domínio: 5 de 5.

`[PRENCHER: parágrado interpretando o resultado e citando a limitação
metodológica da seção 9.]`

### 8.2 Desempenho

| Operação | Tempo |
|---|---|
| Conectar ao banco remoto | 6,4 s (inclui acordar o banco) |
| Cada consulta | 0,23 s |

### 8.3 Qualidade de software

240 testes automatizados, cobrindo: a Trava (matriz de permitir/negar), o loop de
correção, a integridade referencial do gerador de dados, os dois dialetos SQL, a
leitura de planilhas, Google Sheets público, importação de dump `.sql`, a conexão
lembrada (sem senha) e o fluxo completo de conexão.

## 9. Limitações

`[PRENCHER: esta seção é a mais importante para a banca — mostre que vocês
sabem o que o trabalho não faz.]` Pontos a cobrir:

- Os quatro conjuntos foram escritos pela mesma equipe que ajustou o motor. Isso
  reduz o viés, mas não equivale a uma avaliação com usuários reais ao longo de
  semanas.
- O motor cobre um vocabulário controlado. Perguntas muito distantes desse
  vocabulário recebem "não entendi" — o que é o comportamento projetado.
- Uma instância por instituição; não há login nem multi-tenant.
- O banco da demonstração roda em plano gratuito, que suspende a computação
  após inatividade (a primeira conexão do dia demora alguns segundos).
- Google Sheets só funciona com planilha pública (sem OAuth); dumps `.sql` são
  carregados em memória, o que limita o tamanho aceitável. Dumps do MySQL são
  convertidos automaticamente, mas rotinas, triggers e `DELIMITER` não são.

## 10. Trabalhos futuros

- Multi-instituição com autenticação
- Suporte a MySQL e SQL Server
- Ampliação do vocabulário a partir das perguntas reais dos usuários
- Ajuste manual de tipos de coluna ao importar planilhas
- Integração com o sistema de gestão da biblioteca

## 11. Conclusão

`[PRENCHER: retome o problema da seção 2 e diga se ele foi resolvido.]`
Fechamento sugerido: *o dado já existia; o que faltava era a linguagem.*

## 12. Referências

- ELMASRI, R.; NAVATHE, S. *Sistemas de Banco de Dados*. Pearson.
- SILBERSCHATZ, A.; KORTH, H.; SUDARSHAN, S. *Sistema de Banco de Dados*. Elsevier.
- DATE, C. J. *Introdução a Sistemas de Banco de Dados*. Campus.
- Documentação do PostgreSQL. Disponível em: <https://www.postgresql.org/docs/>.
- sqlglot — SQL parser. Disponível em: <https://github.com/tobymao/sqlglot>.
- Streamlit. Disponível em: <https://docs.streamlit.io/>.

`[PRENCHER: acrescentem a referência da disciplina e quaisquer outras
consultadas.]`

---

[Início](README.md) · [PRD](PRD.md) · [Documentação do banco](docs/mer/README.md)
