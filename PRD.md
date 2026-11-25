# PRD — Chat SQL

**Projeto A3 - Chatbot de consultas em linguagem natural para instituições com banco de dados**
**Metodologia:** pesquisa aplicada + desenvolvimento incremental
**Status:** `concluído` — 347 testes coletados, 95/95 perguntas de avaliação, CI verde em Python 3.11/3.12/3.13.

[Início](README.md) · [Índice da documentação](docs/README.md) · [Roadmap](ROADMAP.md)

---

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Objetivos](#2-objetivos)
3. [Arquitetura](#3-arquitetura)
4. [Segurança](#4-segurança)
5. [Stack](#5-stack)
6. [Estrutura do repositório](#6-estrutura-do-repositório)
7. [Como executar](#7-como-executar)
8. [Resultados](#8-resultados)
9. [Fundamentação](#9-fundamentação)
10. [Limitações e trabalhos futuros](#10-limitações-e-trabalhos-futuros)

---

## 1. Visão geral

O Chat SQL é um **serviço** que permite a uma instituição consultar os seus dados
escrevendo perguntas em português. O sistema traduz a pergunta para **SQL somente leitura**,
valida esse SQL com uma camada de segurança (a **Trava**) e o executa, mostrando o resultado.

O diferencial é funcionar **sem IA**: um motor de regras determinístico resolve as perguntas
mais comuns, sem enviar dados para fora e sem custo por token. Se a instituição quiser mais
flexibilidade, pode **opcionalmente** configurar uma chave de API de um provedor de IA.

### Problema que resolve

| Problema | Como o Chat SQL resolve |
|----------|-------------------------|
| Pessoas não técnicas não sabem SQL | Perguntas em português viram SQL |
| Medo de a IA "inventar" ou apagar dados | A Trava só permite `SELECT`; nada é executado sem revisão |
| Instituições que proíbem IA | Motor Offline determinístico, sem rede |
| Dados presos em planilhas ou bancos | Planilha, script SQL ou Conexão read-only |

---

## 2. Objetivos

- Traduzir perguntas em PT-BR para SQL somente leitura.
- Garantir segurança por camadas (Trava + modo leitura + limites).
- Funcionar **sem IA**, com meta mensurável de acurácia.
- Aceitar planilhas, scripts SQL e conexões a bancos reais.
- Ser fácil de entender e evoluir (projeto de aprendizado, 7 integrantes).

### Metas mensuráveis

| Meta | Valor alvo |
|------|------------|
| Acurácia do Motor Offline | **>= 70%** em ~15-20 perguntas por schema |
| Escrita em banco bloqueada | 100% (testes de bloqueio) |
| Instalação local | <= 3 comandos |

---

## 3. Arquitetura

```
 Pergunta (PT-BR)
       |
       v
 +---------------+   sem chave    +------------------+
 |   Motor       |<-------------->|  Regras + sinôn. |
 |  Offline      |                +------------------+
 +-------+-------+
         |  com chave (opcional)
         v
 +---------------+
 |  Provedor IA  |  (OpenAI-compatible)
 +-------+-------+
         |  Consulta SQL
         v
 +---------------+     rejeita DDL/DML, coluna inexistente
 |     Trava     |---------------------------------------+
 +-------+-------+                                       |
         | aprovada                                        v
         v                                          Diagnóstico
 +---------------+
 |  Fonte de     |  SQLite na memória  |  Banco real
 |  Dados        |
 +-------+-------+
         v
   Resultado (tabela + gráfico)
```

Detalhamento de cada módulo em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

---

## 4. Segurança

A segurança é em camadas (ver ADRs 0001 e 0008):

1. **Trava** (`chat_sql/guard.py`): uma única instrução, apenas `SELECT`, sem funções
   perigosas e apenas tabelas/colunas que existem.
2. **Revisão humana**: o SQL aparece na tela e só executa no clique.
3. **Somente leitura**: no modo memória, `PRAGMA query_only`; no modo Conexão, usuário
   read-only + sessão em modo leitura.
4. **Limites**: tempo de consulta, número de linhas e tabelas permitidas.

---

## 5. Stack

| Tecnologia | Papel |
|------------|-------|
| Python 3.11+ | Linguagem principal |
| Streamlit | Interface web |
| sqlglot | Parse e validação do SQL (a Trava) |
| pandas | Planilhas e resultados |
| SQLite | Execução na memória |
| Faker | Dados de exemplo determinísticos |
| openpyxl / xlrd | Leitura de Excel |
| SQLAlchemy + psycopg | Conexão a bancos reais (Postgres/SQLite) |
| openai | Provedor de IA opcional |

---

## 6. Estrutura do repositório

```
ChatSQL/
├── README.md              # comece por aqui
├── PRD.md                 # este documento
├── ROADMAP.md             # o que falta e quem faz
├── CONTRIBUTING.md        # como contribuir
├── app.py                 # interface Streamlit
├── chat_sql/              # código do produto
│   ├── nl/                # Motor Offline (regras PT-BR)
│   ├── guard.py           # a Trava
│   ├── engine.py          # SQLite na memória
│   ├── spreadsheet.py     # planilhas
│   ├── store.py           # persistência
│   ├── datasource.py      # interface de Fonte de Dados
│   └── db.py / sheets.py / sql_dump.py   # conexões e importadores
├── schemas/               # schemas de exemplo e da biblioteca
├── exemplos/              # planilhas de exemplo
├── tests/                 # testes (especificação executável)
└── docs/                  # arquitetura, guias e ADRs
```

---

## 7. Como executar

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app.py
```

Testes:

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 8. Resultados

| Métrica | Valor |
|---------|-------|
| Acurácia — bateria de desenvolvimento | **28/28 (100%)** |
| Acurácia — validação cega (nunca usada no ajuste) | **20/20 (100%)** |
| Acurácia — linguagem coloquial | **18/18 (100%)** |
| Acurácia — quarto conjunto (escrito do dicionário de dados) | **30/30 (100%)** |
| **Total dos quatro conjuntos** | **95/95 (100%)** |
| Recusa de perguntas fora do domínio | **6/6** |
| Testes automatizados | **208** + 6 guias desativados |
| Registros no banco da demo | ~5.300 (456 livros reais, 277 autores, 40 editoras, 747 exemplares, 800 usuários, 2.500 empréstimos) |
| Conexão ao banco remoto | **6,4 s** (inclui cold start do Neon) |
| Cada consulta | **0,23 s** (pool quente) |

### Como a acurácia foi medida

Quatro conjuntos, todos comparados **por resultado** (o SQL do motor precisa
devolver o mesmo que um SQL de referência escrito à mão) — não basta "rodar":

| Conjunto | Perguntas | Uso |
|---|---|---|
| `tests/eval/bateria_cega.py` | 28 | Corrigimos o motor olhando para elas |
| `tests/eval/validacao.py` | 20 | Escritas **depois**, nunca usadas no ajuste |
| `tests/eval/coloquial.py` | 18 | Linguagem de balcão ("ô, me vê quantos livro tem") |
| `tests/eval/quarto_conjunto.py` | 30 | Escritas **só com o dicionário de dados**, sem abrir o código |

Reproduza com:

```powershell
.\venv\Scripts\python -m pytest tests/eval/test_acuracia.py -s
```

> **Nota metodológica honesta:** os quatro conjuntos foram escritos pela mesma
> pessoa que ajustou o motor. O quarto foi escrito olhando apenas
> `docs/mer/03-dicionario-dados.md`, o que reduz o viés — mas não é o mesmo que
> uma bateria coletada por usuários reais ao longo de semanas. O harness está
> pronto para receber perguntas novas (`docs/AVALIACAO-MOTOR.md`); basta
> acrescentar ao arquivo de validação.

---

## 9. Fundamentação

- **Text-to-SQL**: transformar linguagem natural em consultas é um problema clássico de
  PLN; abordagens por regras precedem os modelos neurais e ainda são úteis por serem
  determinísticas e auditáveis.
- **Segurança por allowlist**: validar a intenção (apenas leitura) é mais seguro do que
  tentar bloquear comandos proibidos um a um.
- **Engenharia de confiabilidade**: mostrar a consulta antes de executar aumenta a confiança
  do usuário e reduz o risco de resultados errados passarem despercebidos.

---

## 10. Limitações e trabalhos futuros

- O Motor Offline cobre um **vocabulário controlado**; perguntas fora dele retornam
  "não entendi" (por design).
- Sem login e sem multi-tenant nesta fase (uma instância por instituição).
- Conexão a banco real funciona na tela (SQLite/Postgres), com campos separados ou
  URL, conexão lembrada (sem a senha) e seletor visual de tabelas. Falta MySQL.
- Google Sheets público e upload de dump `.sql` funcionam na aba Dados. Dumps do
  MySQL são convertidos automaticamente (`AUTO_INCREMENT`, `ENGINE`, tipos com
  tamanho); rotinas, triggers e `DELIMITER` não são. Não há suporte a planilhas
  privadas (exigiria OAuth) nem a dumps maiores que a memória da máquina.
- Evoluções possíveis: ajuste de tipos de coluna na planilha, joins manuais entre arquivos,
  multiusuário, suporte a mais dialetos (SQL Server, Oracle).

---

*Projeto A3 — Chat SQL*

---

[Início](README.md) · [Índice da documentação](docs/README.md) · [Roadmap](ROADMAP.md)
