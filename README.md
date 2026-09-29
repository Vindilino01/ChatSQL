# Chat SQL

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/sqlglot-Trava-4B5563?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/IA-Opcional-6366F1?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Status-Fundacao-22C55E?style=for-the-badge"/>
</p>

> Converse em portugues com um banco de dados e receba **SQL somente leitura**, validado e executado na hora — **funcionando sem IA**.

**Projeto A3 — aplicacao para qualquer instituicao que possua um banco de dados.**

---

## O que ele faz

Voce escreve uma pergunta ("os 10 clientes que mais compraram no mes passado") e o Chat SQL:

1. entende a pergunta;
2. gera uma **Consulta SQL somente leitura**;
3. mostra o SQL na tela **antes de executar**;
4. executa e exibe o resultado em tabela (com grafico quando faz sentido).

## Dois modos

| Modo | Precisa de chave? | Como funciona |
|------|-------------------|---------------|
| **Motor Offline** (padrao) | Nao | Regras em PT-BR, sem enviar nada para fora |
| **Provedor de IA** (opcional) | Sim | API compativel com OpenAI (DeepSeek, GPT, Ollama...) |

## Fontes de dados

- **Planilha**: CSV, XLSX ou XLS (uma tabela por aba/arquivo).
- **Script SQL**: `CREATE TABLE` (+ `INSERT INTO` para usar os seus dados).
- **Conexao**: banco real somente-leitura (motor pronto para SQLite/Postgres; ligacao na tela no `ROADMAP.md`).

## Como rodar (3 passos)

```bash
# 1. Crie o ambiente
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/macOS

# 2. Instale as dependencias
pip install -r requirements.txt

# 3. Rode
streamlit run app.py
```

Abra `http://localhost:8501`, va na aba **Dados**, carregue um exemplo e pergunte.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Estrutura (resumo)

```
app.py                 Interface Streamlit (Chat, Dados, Configuracoes)
chat_sql/
  nl/                  Motor Offline (regras em PT-BR)
  guard.py             A Trava (so SELECT, colunas existem)
  engine.py            SQLite em memoria
  spreadsheet.py       Leitura de planilhas
  store.py             Persistencia de fontes e historico
  pipeline.py          Gerar -> validar -> executar
  datasource.py        Interface de Fonte de Dados (base p/ Conexao)
schemas/               Schemas de exemplo
exemplos/              Planilhas de exemplo
tests/                 Testes (tambem servem de especificacao)
docs/                  Arquitetura e decisoes (ADRs)
```

## Documentacao

- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) — como o codigo funciona, passo a passo.
- [`PRD.md`](PRD.md) — documento de produto (visao, arquitetura, resultados).
- [`ROADMAP.md`](ROADMAP.md) — o que falta e o que cada pessoa pode fazer.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — como contribuir e rodar os testes.
- [`CONTEXT.md`](CONTEXT.md) — glossario do dominio.

## Privacidade

No Motor Offline, **nada sai da sua maquina**. As fontes ficam salvas em `~/.chat_sql_sources` e podem ser apagadas em Configuracoes. Apenas no modo com IA o schema e a pergunta vao para o Provedor escolhido.
