# PRD — Chat SQL

**Projeto A3 — Chatbot de consultas em linguagem natural para qualquer instituicao**
**Metodologia:** pesquisa aplicada + desenvolvimento incremental
**Status:** `fundacao` (base pronta; features do roadmap em desenvolvimento)

---

## 1. Visao Geral

O Chat SQL e um **servico** que permite a qualquer instituicao consultar os seus dados
escrevendo perguntas em portugues. O sistema traduz a pergunta para **SQL somente leitura**,
valida esse SQL com uma camada de seguranca (a **Trava**) e o executa, mostrando o resultado.

O diferencial e funcionar **sem IA**: um motor de regras deterministico resolve as perguntas
mais comuns, sem enviar dados para fora e sem custo por token. Se a instituicao quiser mais
flexibilidade, pode **opcionalmente** configurar uma chave de API de um provedor de IA.

### Problema que resolve

| Problema | Como o Chat SQL resolve |
|----------|-------------------------|
| Pessoas nao tecnicas nao sabem SQL | Perguntas em portugues viram SQL |
| Medo de a IA "inventar" ou apagar dados | A Trava so permite `SELECT`; nada e executado sem revisao |
| Instituicoes que proibem IA | Motor Offline deterministico, sem rede |
| Dados presos em planilhas ou bancos | Planilha, script SQL ou Conexao read-only |

---

## 2. Objetivos

- Traduzir perguntas em PT-BR para SQL somente leitura.
- Garantir seguranca por camadas (Trava + modo leitura + limites).
- Funcionar **sem IA**, com meta mensuravel de acuracia.
- Aceitar planilhas, scripts SQL e (roadmap) conexoes a bancos reais.
- Ser facil de entender e evoluir (projeto de aprendizado, 7 integrantes).

### Metas mensuraveis

| Meta | Valor alvo |
|------|------------|
| Acuracia do Motor Offline | **>= 70%** em ~15-20 perguntas por schema |
| Escrita em banco bloqueada | 100% (testes de bloqueio) |
| Instalacao local | <= 3 comandos |

---

## 3. Arquitetura

```
 Pergunta (PT-BR)
       │
       ▼
 ┌───────────────┐   sem chave    ┌──────────────────┐
 │   Motor       │◄──────────────►│  Regras + sinon. │
 │  Offline      │                └──────────────────┘
 └──────┬────────┘
        │  com chave (opcional)
        ▼
 ┌───────────────┐
 │  Provedor IA  │  (OpenAI-compatible)
 └──────┬────────┘
        │  Consulta SQL
        ▼
 ┌───────────────┐     rejeita DDL/DML, coluna inexistente
 │     Trava     │───────────────────────────────────────┐
 └──────┬────────┘                                       │
        │ aprovada                                       ▼
        ▼                                          Diagnostico
 ┌───────────────┐
 │  Fonte de     │  SQLite em memoria  |  Banco real (roadmap)
 │  Dados        │
 └──────┬────────┘
        ▼
   Resultado (tabela + grafico)
```

Detalhamento de cada modulo em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

---

## 4. Seguranca

A seguranca e em camadas (ver ADRs 0001 e 0008):

1. **Trava** (`chat_sql/guard.py`): uma unica instrucao, apenas `SELECT`, sem funcoes
   perigosas e apenas tabelas/colunas que existem.
2. **Revisao humana**: o SQL aparece na tela e so executa no clique.
3. **Somente leitura**: no modo memoria, `PRAGMA query_only`; no modo Conexao, usuario
   read-only + sessao em modo leitura.
4. **Limites**: tempo de consulta, numero de linhas e tabelas permitidas.

---

## 5. Stack

| Tecnologia | Papel |
|------------|-------|
| Python 3.11+ | Linguagem principal |
| Streamlit | Interface web |
| sqlglot | Parse e validacao do SQL (a Trava) |
| pandas | Planilhas e resultados |
| SQLite | Execucao em memoria |
| Faker | Dados de exemplo deterministicos |
| openpyxl / xlrd | Leitura de Excel |
| SQLAlchemy | Conexao a bancos reais (roadmap) |
| openai | Provedor de IA opcional |

---

## 6. Estrutura do Repositorio

```
ChatSQL/
├── README.md              # comecar por aqui
├── PRD.md                 # este documento
├── ROADMAP.md             # o que falta e quem faz
├── CONTRIBUTING.md        # como contribuir
├── app.py                 # interface Streamlit
├── chat_sql/              # codigo do produto
│   ├── nl/                # Motor Offline (regras PT-BR)
│   ├── guard.py           # a Trava
│   ├── engine.py          # SQLite em memoria
│   ├── spreadsheet.py     # planilhas
│   ├── store.py           # persistencia
│   ├── datasource.py      # interface de Fonte de Dados
│   └── db.py / sheets.py / sql_dump.py   # esqueletos do roadmap
├── schemas/               # schemas de exemplo
├── exemplos/              # planilhas de exemplo
├── tests/                 # testes (especificacao executavel)
└── docs/                  # arquitetura e ADRs
```

---

## 7. Como Executar

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Testes:

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 8. Resultados

> Preencher conforme o roadmap avanca (semana 5).

| Metrica | Valor |
|---------|-------|
| Acuracia do Motor Offline (biblioteca) | a medir |
| Acuracia do Motor Offline (e-commerce) | a medir |
| Perguntas de avaliacao | a definir (15-20 por schema) |
| Testes automatizados | 125 (fundacao) + 7 guias desativados |

---

## 9. Fundamentacao

- **Text-to-SQL**: transformar linguagem natural em consultas e um problema classico de
  PLN; abordagens por regras precedem os modelos neurais e ainda sao uteis por serem
  deterministicas e auditaveis.
- **Seguranca por allowlist**: validar a intencao (apenas leitura) e mais seguro do que
  tentar bloquear comandos proibidos um a um.
- **Engenharia de confiabilidade**: mostrar a consulta antes de executar aumenta a confianca
  do usuario e reduz o risco de resultados errados passarem despercebidos.

---

## 10. Limitacoes e Trabalhos Futuros

- O Motor Offline cobre um **vocabulario controlado**; perguntas fora dele retornam
  "nao entendi" (por design).
- Sem login e sem multi-tenant nesta fase (uma instancia por instituicao).
- Conexoes a bancos reais e Google Sheets estao no `ROADMAP.md`.
- Evolucoes possiveis: ajuste de tipos de coluna na planilha, joins manuais entre arquivos,
  multiusuario, suporte a mais dialetos (SQL Server, Oracle).

---

*Projeto A3 — Chat SQL*
