# Chat SQL

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/sqlglot-Trava-4B5563?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/IA-Opcional-6366F1?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Em%20desenvolvimento-22C55E?style=for-the-badge"/>
</p>

> Converse em português com um banco de dados e receba **SQL somente leitura**, validado e executado na hora — **funcionando sem IA**.

**Projeto A3 — aplicação para qualquer instituição que possua um banco de dados.**

[Índice da documentação](docs/README.md) · [Guia da sua frente](ROADMAP.md) · [Comece aqui (iniciantes)](docs/COMECE-AQUI.md) · [O que cada palavra significa](CONTEXT.md)

---

## Mapa do projeto (comece por aqui)

| Se você quer... | Vá para |
|---|---|
| Rodar o app agora | [Como rodar](#como-rodar-3-passos) |
| Nunca programou | [docs/COMECE-AQUI.md](docs/COMECE-AQUI.md) |
| Saber onde fica cada coisa | [docs/ONDE-FICA-O-QUE.md](docs/ONDE-FICA-O-QUE.md) |
| Ver a sua responsabilidade | [ROADMAP.md](ROADMAP.md) e o guia da sua frente |
| Entender o código | [docs/ARQUITETURA.md](docs/ARQUITETURA.md) |
| O que cada palavra significa | [CONTEXT.md](CONTEXT.md) |
| Índice completo da documentação | [docs/README.md](docs/README.md) |

## Equipe (preencher)

| Frente | Responsáveis | Guia |
|---|---|---|
| A. Banco de dados | (preencher) | [guia](docs/frentes/A-banco-de-dados.md) |
| B. Motor Offline | (preencher) | [guia](docs/frentes/B-motor-offline.md) |
| C. Interface e Design | (preencher) | [guia](docs/frentes/C-interface-e-design.md) |
| D. Dados e biblioteca | (preencher) | [guia](docs/frentes/D-dados-e-biblioteca.md) |
| E. Entrega e apresentação | (preencher) | [guia](docs/frentes/E-entrega-e-apresentacao.md) |

---

## O que ele faz

Você escreve uma pergunta ("os 10 clientes que mais compraram no mês passado") e o Chat SQL:

1. entende a pergunta;
2. gera uma **Consulta SQL somente leitura**;
3. mostra o SQL na tela **antes de executar**;
4. executa e exibe o resultado em tabela (com gráfico quando faz sentido).

Perguntas que ele entende hoje: contar, somar, média, maior/menor, top-N,
agrupar ("por mês", "por editora"), filtrar por texto ("título Dom Casmurro",
"que começam com Dom"), por data ("mês passado", "janeiro de 2025", "últimos 30
dias") e por número ("estoque maior que 500"). Quando não entende, **não chuta**:
mostra o motivo e sugere perguntas.

## Como funciona (em uma imagem)

```
Você escreve:   "quantos clientes existem?"
        |
        v
  O robô entende a pergunta
        |
        v
  Ele escreve o SQL:   SELECT COUNT(*) FROM clientes;
        |
        v
  A Trava confere: é só leitura? as colunas existem?
        |
        v
  Você vê o SQL na tela e clica em Executar
        |
        v
  O resultado aparece na tabela (e no gráfico)
```

## Dois modos

| Modo | Precisa de chave? | Como funciona |
|------|-------------------|---------------|
| **Motor Offline** (padrão) | Não | Regras em PT-BR, sem enviar nada para fora |
| **Provedor de IA** (opcional) | Sim | API compatível com OpenAI (DeepSeek, GPT, Ollama...) |

## Fontes de dados

- **Planilha**: CSV, XLSX ou XLS (uma tabela por aba/arquivo).
- **Script SQL**: `CREATE TABLE` (+ `INSERT INTO` para usar os seus dados).
- **Conexão**: banco real somente leitura (Postgres/SQLite) direto na aba Dados.

## Conectar a um Postgres

1. Copie `.env.example` para `.env` e preencha `CHATSQL_SEED_URL`.
2. Aplique o DDL da biblioteca: `.\venv\Scripts\python scripts\apply_ddl.py`
3. Popule com dados de exemplo: `.\venv\Scripts\python scripts\seed_biblioteca.py`
4. No app: aba **Dados** → **Banco de dados (Postgres/SQLite)** → cole a URL
   `postgresql+psycopg://usuario:senha@host/banco?sslmode=require`.

Use sempre um usuário **somente leitura** no banco. O schema da biblioteca e o
porquê de cada restrição estão em [`docs/BANCO.md`](docs/BANCO.md).

## Demonstração: Biblioteca Universitária

O cenário da apresentação é uma biblioteca com **obras, autores e editoras
reais** (de *Os Lusíadas*, 1572, a *Nexus*, 2024) e cerca de **5.300 registros**:

| Tabela | Registros |
|---|---|
| livro | 456 (obras reais) |
| autor | 277 (autores reais) |
| editora | 40 (editoras reais) |
| livro_autor | 481 |
| exemplar | 744 |
| usuario | 800 |
| emprestimo | 2.500 (399 ativos) |

Os ISBNs são sintéticos e exemplares, usuários e empréstimos são gerados.
Para aumentar o volume:

```powershell
.\venv\Scripts\python scripts\seed_biblioteca.py --usuarios 2000 --emprestimos 8000
```

## Resultado medido

O Motor Offline (sem IA) acerta **14 de 14 perguntas** no banco da biblioteca:

```powershell
.\venv\Scripts\python -m pytest tests/eval/test_biblioteca.py -s
# Acurácia (biblioteca, sem IA): 14/14 = 100%
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

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

Resultado atual: **174 testes passando, 6 guias desativados** (features do roadmap).

Para medir a acurácia do motor no banco da biblioteca (precisa do `.env`):

```powershell
.\venv\Scripts\python -m pytest tests/eval/test_biblioteca.py -s
```

## Estrutura (resumo)

```
app.py                 Interface Streamlit (Chat, Dados, Configurações)
chat_sql/
  nl/                  Motor Offline (regras em PT-BR)
    dialect.py         Diferenças entre SQLite e Postgres
  guard.py             A Trava (só SELECT, colunas existem)
  engine.py            SQLite na memória
  spreadsheet.py       Leitura de planilhas
  store.py             Persistência de fontes e histórico
  pipeline.py          Gerar -> validar -> executar
  datasource.py        Interface de Fonte de Dados
  db.py                Conexão somente leitura (SQLite/Postgres)
schemas/               Schemas de exemplo (inclui biblioteca-postgres.sql)
exemplos/              Planilhas de exemplo
scripts/
  apply_ddl.py         Aplica o DDL da biblioteca no banco do .env
  seed_biblioteca.py   Popula com dados de exemplo
  acervo_biblioteca.py Acervo real (obras, autores, editoras)
tests/                 Testes (também servem de especificação)
tests/eval/            Avaliação de acurácia do motor
docs/                  Arquitetura, banco e decisões (ADRs)
```

## Documentação

- [`docs/README.md`](docs/README.md) — **índice de tudo** (comece por aqui).
- [`docs/COMECE-AQUI.md`](docs/COMECE-AQUI.md) — passo a passo para quem nunca programou.
- [`docs/ONDE-FICA-O-QUE.md`](docs/ONDE-FICA-O-QUE.md) — onde fica cada coisa.
- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) — como o código funciona.
- [`PRD.md`](PRD.md) — documento de produto (visão, arquitetura, resultados).
- [`ROADMAP.md`](ROADMAP.md) — o que falta e quem faz.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — como contribuir e rodar os testes.
- [`CONTEXT.md`](CONTEXT.md) — glossário do domínio.

## Privacidade

No Motor Offline, **nada sai da sua máquina**. As fontes ficam salvas em `~/.chat_sql_sources` e podem ser apagadas em Configurações. Apenas no modo com IA o schema e a pergunta vão para o Provedor escolhido.

---

[Início](README.md) · [Índice da documentação](docs/README.md) · [Guia da sua frente](ROADMAP.md)
