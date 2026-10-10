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

## Estrutura (resumo)

```
app.py                 Interface Streamlit (Chat, Dados, Configurações)
chat_sql/
  nl/                  Motor Offline (regras em PT-BR)
  guard.py             A Trava (só SELECT, colunas existem)
  engine.py            SQLite na memória
  spreadsheet.py       Leitura de planilhas
  store.py             Persistência de fontes e histórico
  pipeline.py          Gerar -> validar -> executar
  datasource.py        Interface de Fonte de Dados
  db.py                Conexão somente leitura (SQLite/Postgres)
schemas/               Schemas de exemplo
exemplos/              Planilhas de exemplo
tests/                 Testes (também servem de especificação)
docs/                  Arquitetura e decisões (ADRs)
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
