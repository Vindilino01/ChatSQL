# Chat SQL

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/sqlglot-Trava-4B5563?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/IA-Opcional-6366F1?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/licen%C3%A7a-MIT-22C55E?style=for-the-badge"/>
</p>

> Converse em português com um banco de dados e receba **SQL somente leitura**, visível antes de executar — **funcionando sem IA**.

**Projeto A3 — Sistemas de Controle e Inteligência Artificial.**
Demonstração sobre uma biblioteca universitária real.

[Documentação](docs/README.md) · [Como rodar](#como-rodar-3-passos) · [Resultados medidos](#resultados-medidos) · [Decisões de projeto](#decisões-de-projeto)

---

## O problema

Uma biblioteca acumula dados sobre acervo, usuários e empréstimos. Esses dados
estão estruturados — mas só quem sabe SQL consegue perguntar. O coordenador que
quer saber quantos empréstimos estão atrasados depende do TI, de uma planilha
desatualizada ou de uma ferramenta de BI cara.

O gargalo não está no dado. Está na linguagem.

## O que o projeto faz

Uma pergunta em português vira SQL, e três garantias sustentam o uso real:

| Garantia | Como é implementada |
|---|---|
| **Somente leitura** | A Trava aceita apenas uma instrução `SELECT`; usuário de banco read-only; sessão em modo leitura |
| **O SQL é visível** | Aparece na tela e só executa no clique — decisão explícita contra alucinação |
| **Funciona sem IA** | Motor de regras determinístico: sem chave, sem custo por pergunta, sem dado saindo da instituição |

Quando não entende, o motor **não chuta**: devolve o motivo e sugere perguntas.

## Resultados medidos

| Métrica | Valor |
|---|---|
| Acurácia do motor offline | **95/95 (100%)** em quatro conjuntos, comparados por resultado |
| Acurácia no banco real da demo | **14/14 (100%)** |
| Recusa de pergunta fora do domínio | **6/6** (tempo, piada, futebol, cotação, filme, capital) |
| Testes automatizados | **347** |
| Conexão ao banco (com cold start) | 6,4 s |
| Cada consulta | 0,23 s |

> **Nota metodológica:** os quatro conjuntos foram escritos pela mesma pessoa
> que ajustou o motor. O quarto foi escrito olhando apenas o dicionário de
> dados, o que reduz o viés — mas não substitui uma bateria coletada de
> usuários reais. O harness para isso está pronto (`tests/eval/`); o número
> honesto está registrado no [PRD](PRD.md#8-resultados).

## Decisões de projeto

O que está documentado como **escolha**, não como acidente:

| Decisão | Por quê | Onde |
|---|---|---|
| Motor offline é o padrão; IA é opcional | Custo por pergunta, instituições que proíbem IA, determinismo | [ADR 0005](docs/adr/0005-offline-first.md) |
| O motor nunca falha em silêncio | Resposta errada é pior que resposta nenhuma | [ADR 0006](docs/adr/0006-motor-offline-nunca-falha-em-silencio.md) |
| Conexão read-only a banco real | O dado já existe; copiar para memória não escala | [ADR 0008](docs/adr/0008-conexao-somente-leitura.md) |
| `usuario` único em vez de `aluno` + `funcionario` | Uma FK em vez de duas, `GROUP BY` em vez de `UNION` | [RELATORIO §5.3](RELATORIO.md#53-uma-decisão-de-modelagem) |
| Editora atribuída por área, não sorteada | O acervo não registra a edição; sortear colocava `1984` na Artmed | [RELATORIO §5.1.1](RELATORIO.md#511-o-que-é-real-e-o-que-é-gerado) |

## Arquitetura

```
 Pergunta (PT-BR)
       │
       ▼
 ┌───────────────┐   sem chave   ┌────────────────────┐
 │ Motor Offline │◄─────────────►│ Regras + sinônimos │
 └───────┬───────┘               └────────────────────┘
         │ com chave (opcional)
         ▼
 ┌───────────────┐
 │ Provedor IA   │  (OpenAI-compatible: OpenAI, Groq, Ollama local)
 └───────┬───────┘
         │ SQL
         ▼
 ┌───────────────┐  rejeita DDL/DML, tabela ou coluna inexistente
 │     Trava     │──────────────► Diagnóstico com sugestões
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Fonte de Dados│  SQLite em memória  |  PostgreSQL read-only
 └───────────────┘
```

A junção entre tabelas é resolvida por **busca em largura** no grafo de chaves
estrangeiras, o que permite ligar tabelas sem FK direta (ex.: `livro` e `autor`
passando por `livro_autor`). Detalhes em [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Banco de dados da demonstração

A demo usa uma **Biblioteca Universitária** em PostgreSQL (Neon): 7 tabelas,
29 colunas e ~5.300 registros com **obras, autores e editoras reais**.

| Tabela | O que guarda | Registros |
|---|---|---|
| `livro` | A obra: título, ISBN, ano | 456 |
| `autor` | Quem escreveu | 277 |
| `editora` | Quem publicou | 40 |
| `livro_autor` | Liga livro↔autor (N:N) | 481 |
| `exemplar` | A cópia física | 747 |
| `usuario` | Aluno, professor ou funcionário | 800 |
| `emprestimo` | Retiradas e devoluções | 2.500 |

Números lidos do banco pelo teste `tests/test_documentacao.py` — não são
digitados à mão. Para ver o estado real:

```powershell
.\venv\Scripts\python -m scripts.contagens
```

### Diagramas e documentação do banco

| Eu quero... | Abra |
|---|---|
| **Diagrama pronto para o relatório** | [`biblioteca.drawio`](docs/mer/biblioteca.drawio) → abrir no [draw.io](https://app.diagrams.net) → Export PNG |
| Diagrama rápido sem instalar nada | [`biblioteca.dbml`](docs/mer/biblioteca.dbml) → colar em [dbdiagram.io](https://dbdiagram.io) → Export → PNG |
| Ver o diagrama **aqui no GitHub** | [`02-logico.md`](docs/mer/02-logico.md) (desenha sozinho) |
| MER conceitual (entidades e relacionamentos) | [`01-conceitual.md`](docs/mer/01-conceitual.md) |
| Todas as colunas explicadas | [`03-dicionario-dados.md`](docs/mer/03-dicionario-dados.md) |
| Por que cada restrição existe | [`04-integridade.md`](docs/mer/04-integridade.md) |
| Índices | [`05-indices.md`](docs/mer/05-indices.md) |
| Prova de normalização (1FN/2FN/3FN) | [`06-normalizacao.md`](docs/mer/06-normalizacao.md) |
| O SQL real do banco | [`07-ddl.sql`](docs/mer/07-ddl.sql) |

Índice completo: [`docs/mer/README.md`](docs/mer/README.md)

### Como conectar

Passo a passo: [`docs/COMO-CONECTAR.md`](docs/COMO-CONECTAR.md)

```
postgresql+psycopg://chatsql_ro@ep-royal-hall-b6uo2i82-pooler.c-2.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

A senha não fica no repositório — peça no privado. O usuário é **somente
leitura**: ninguém consegue alterar ou apagar nada.

> ⚠️ Os arquivos `biblioteca_mer.png` / `.dot` / `.svg` de uma versão anterior
> estão **desatualizados**. Use os links acima.

## Equipe (preencher)

| Frente | Responsáveis | Guia |
|---|---|---|
| A. Banco de dados | (preencher) | [guia](docs/frentes/A-banco-de-dados.md) |
| B. Motor Offline | (preencher) | [guia](docs/frentes/B-motor-offline.md) |
| C. Interface e Design | (preencher) | [guia](docs/frentes/C-interface-e-design.md) |
| D. Dados e biblioteca | (preencher) | [guia](docs/frentes/D-dados-e-biblioteca.md) |
| E. Entrega e apresentação | (preencher) | [guia](docs/frentes/E-entrega-e-apresentacao.md) |

## O que ele entende

Contar, somar, média, maior/menor, top-N, agrupar ("por mês", "por editora"),
filtrar por texto ("título Dom Casmurro", "que começam com Dom"), por data
("mês passado", "janeiro de 2025", "últimos 30 dias"), por número ("estoque
maior que 500") e por nacionalidade ("autores brasileiros").

Quando não entende, **não chuta**: mostra o motivo e sugere perguntas.

### Dois modos

| Modo | Precisa de chave? | Como funciona |
|------|-------------------|---------------|
| **Motor Offline** (padrão) | Não | Regras em PT-BR, sem enviar nada para fora |
| **Provedor de IA** (opcional) | Sim | API compatível com OpenAI (DeepSeek, GPT, Ollama...) |

## Fontes de dados

Seis caminhos, todos na aba **Dados**:

| Fonte | Quando usar |
|---|---|
| Planilhas (CSV/Excel) | Você já tem os dados em arquivo |
| Google Sheets (link público) | A planilha está no Google e é pública |
| Banco de dados | Existe um Postgres ou SQLite acessível |
| Script SQL | Você tem `CREATE TABLE` / `INSERT` para colar |
| Arquivo `.sql` (dump) | Você tem o dump em arquivo; MySQL é convertido |
| Schema de exemplo | Não tem dado nenhum; quer só ver funcionando |

Detalhes de conexão: [`docs/COMO-CONECTAR.md`](docs/COMO-CONECTAR.md). O schema
da biblioteca e o porquê de cada restrição: [`docs/BANCO.md`](docs/BANCO.md).

## Demonstração: Biblioteca Universitária

O cenário da apresentação é uma biblioteca com **obras, autores e editoras
reais** (de *Os Lusíadas*, 1572, a *Nexus*, 2024). A tabela de registros está
na [seção do banco](#banco-de-dados-da-demonstração), em um só lugar, conferida
contra o banco por teste.

Os ISBNs são sintéticos; exemplares, usuários e empréstimos são gerados. O
**título, o autor, a nacionalidade do autor e a editora vêm de dados reais**
(`scripts/acervo_biblioteca.py`, `scripts/acervo_nacionalidades.py`,
`scripts/acervo_editoras.py`). A editora é atribuída por área — plausível, mas
não é a edição física que a biblioteca possui.

Para recarregar ou aumentar o volume:

```powershell
.\venv\Scripts\python scripts\seed_biblioteca.py --usuarios 2000 --emprestimos 8000
```

## Como rodar (3 passos)

```bash
# 1. Crie o ambiente
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/macOS

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Rode
streamlit run app.py
```

Abra `http://localhost:8501`, vá na aba **Dados**, carregue um exemplo e pergunte.

> **Deu `venvlauncher.exe` ao criar o ambiente?** Algumas instalações do Python
> 3.14 vêm sem os launchers do `venv`. Use:
> ```powershell
> python -m pip install virtualenv
> python -m virtualenv venv
> ```

## Testes

```bash
pip install -r requirements.txt    # pytest já incluído
pytest
```

Resultado atual: **347 testes** — 340 passando e 2 guias desativados (features fora do escopo).

Para medir a acurácia do motor no banco da biblioteca (precisa do `.env`):

```powershell
.\venv\Scripts\python -m pytest tests/eval/test_biblioteca.py -s
```

## Estrutura (resumo)

```
app.py                 Interface Streamlit (Chat, Dados, Configurações)
chat_sql/
  nl/                  Motor Offline (regras em PT-BR)
    gentilicos.py      "brasileiros" -> Brasil
    dialect.py         Diferenças entre SQLite e Postgres
  guard.py             A Trava (só SELECT, colunas existem)
  engine.py            SQLite na memória
  spreadsheet.py       Leitura de planilhas (CSV/XLSX/XLS)
  sheets.py            Google Sheets público (link -> CSV)
  sql_dump.py          Dump .sql, com conversão de MySQL
  store.py             Persistência de fontes e histórico
  pipeline.py          Gerar -> validar -> executar
  datasource.py        Interface de Fonte de Dados
  db.py                Conexão somente leitura (SQLite/Postgres)
schemas/               Schemas de exemplo (inclui biblioteca-postgres.sql)
exemplos/              Planilhas de exemplo
scripts/
  apply_ddl.py             Aplica o DDL no banco do .env
  seed_biblioteca.py       Popula com o acervo real
  acervo_biblioteca.py     As 456 obras e 40 editoras
  acervo_nacionalidades.py O país de cada um dos 277 autores
  acervo_editoras.py       Editora de cada obra, por área
  contagens.py             Números da demo, lidos do banco
  exportar_mer.py          Gera docs/mer/ a partir do schema
  exportar_drawio.py       Gera o diagrama para o draw.io
  medir_bateria_cega.py    Mede perguntas escritas pelo grupo
tests/                 Testes (também servem de especificação)
tests/eval/            Avaliação de acurácia do motor
docs/                  Arquitetura, banco, ADRs e guias por frente
.github/workflows/     CI (testes + lint em 3 versões de Python)
```

## Documentação

**Para quem vai usar, apresentar ou manter:**

- [`docs/README.md`](docs/README.md) — **índice de tudo** (comece por aqui).
- [`docs/COMECE-AQUI.md`](docs/COMECE-AQUI.md) — passo a passo para quem nunca programou.
- [`docs/ONDE-FICA-O-QUE.md`](docs/ONDE-FICA-O-QUE.md) — onde fica cada coisa.
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) — como o código funciona.
- [`docs/APRESENTACAO.md`](docs/APRESENTACAO.md) — roteiro de 12 minutos.
- [`PRD.md`](PRD.md) — documento de produto (visão, arquitetura, resultados).
- [`RELATORIO.md`](RELATORIO.md) — o documento escrito, com `[PRENCHER]` onde o grupo escreve.
- [`ROADMAP.md`](ROADMAP.md) — o que falta e quem faz.
- [`CONTEXT.md`](CONTEXT.md) — glossário do domínio.

**Para quem quer entender as escolhas:**

- [`PRODUCT.md`](PRODUCT.md) — público, propósito e limites do produto.
- [`DESIGN.md`](DESIGN.md) — o sistema visual, com as regras e o porquê.
- [`docs/adr/`](docs/adr/) — 9 decisões de arquitetura registradas com contexto.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — como contribuir e rodar os testes.

## Privacidade

No Motor Offline, **nada sai da sua máquina**. As fontes ficam salvas em
`~/.chat_sql_sources` e podem ser apagadas em Configurações. A conexão ao banco
lembra host, banco e usuário — **nunca a senha**. Apenas no modo com IA o schema
e a pergunta vão para o Provedor escolhido.

## Licença

[MIT](LICENSE).

---

[Início](README.md) · [Documentação](docs/README.md) · [Guia da sua frente](ROADMAP.md)
