# Frente C - Interface e Design

**Responsáveis:** (preencher)

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)

---

## Em uma frase

Deixar o projeto **bonito e fácil de usar**: telas, cores, fontes, botões e gráficos.

## Onde fica no projeto

**Quase tudo de visual está em UM arquivo: `app.py`.**

| Parte dentro de `app.py` | O que é |
|---|---|
| Bloco `CSS = """ ... """` | **As cores, fontes, cantos arredondados, botões, bolhas.** É aqui que o design mora. |
| `_render_sidebar` | A barra da esquerda (Fonte ativa, tabelas, Provedor). |
| `_render_chat_tab` | A tela de perguntas (sugestões, campo de pergunta, histórico). |
| `_render_data_tab` | A tela de carregar dados (planilhas, banco, script, exemplo). |
| `_render_config_tab` | A tela de configurações (Provedor, chave de API, fontes salvas). |
| `_render_result` | A **tabela** e o **gráfico** do resultado. |
| `_render_turn` | Como cada pergunta e resposta aparece (o SQL, o botão Executar). |
| `_render_suggestions` / `_render_recent` | Os botões de perguntas sugeridas e recentes. |
| `main` | Junta tudo: título, abas e a ordem das telas. |

**As cores base do tema** ficam em outro arquivo:

| Arquivo | O que é |
|---|---|
| `.streamlit/config.toml` | As cores principais (fundo, destaque, texto). |

## Primeira tarefa (passo a passo): mudar a cor de destaque

1. Abra `.streamlit/config.toml`.
2. Troque o valor de `primaryColor` por outra cor, por exemplo `"#22c55e"` (verde).
3. Salve e rode:
   ```powershell
   .\venv\Scripts\streamlit run app.py
   ```
4. Veja a diferença nos botões. Depois mude `backgroundColor` e experimente.

## O que mexer para...

| Eu quero mudar... | Onde |
|---|---|
| A **cor de destaque** (botões, abas) | `.streamlit/config.toml` -> `primaryColor` |
| A **cor de fundo** da tela | `.streamlit/config.toml` -> `backgroundColor` |
| O **tamanho/estilo dos títulos** | `app.py`, no `CSS`, classe `.chs-title` |
| A **fonte** | `app.py`, no `CSS` (linha `@import` e `font-family`) |
| O visual dos **cartões** | `app.py`, no `CSS`, classe `.chs-card` |
| A **bolha da pergunta** | `app.py`, no `CSS`, classe `.chs-user` |
| A **cor dos gráficos/tabela** | `app.py`, função `_render_result` |
| O **texto das abas** (Chat/Dados/Configurações) | `app.py`, no final, função `main` |
| As **sugestões de pergunta** | `chat_sql/nl/engine.py` (função `suggest_questions`) |

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Se o navegador já estiver aberto, aperte `Ctrl + F5` para carregar o visual novo.

## Cuidados

- Mexa **só no visual**. Não apague as funções nem mude os nomes delas, senão as
  outras telas param de funcionar.
- Nada de `print`; o resultado aparece na própria tela.
- Se der erro, rode `.\venv\Scripts\python -m pytest tests/test_app.py -v` para ver se a tela ainda abre.

## Pronto quando

- [ ] `pytest` verde.
- [ ] A tela mudou como você queria e continua funcionando.
- [ ] Tirou um print e colocou em `docs/imagens/` (veja o [guia das imagens](../imagens/README.md)).

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| CSS | O lugar onde ficam as cores, fontes e o estilo |
| Tema | As cores principais do app (fundo, destaque, texto) |
| Função | Um bloco de código com um nome (ex.: `_render_result`) |
| Print | Uma foto da tela |

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
