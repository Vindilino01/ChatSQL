# Frente C - Interface e Design

**Responsaveis:** (preencher)

## Em uma frase

Deixar o projeto **bonito e facil de usar**: telas, cores, fontes, botoes e graficos.

## Onde fica no projeto

**Quase tudo de visual esta em UM arquivo: `app.py`.**

| Parte dentro de `app.py` | O que e |
|---|---|
| Bloco `CSS = """ ... """` | **As cores, fontes, cantos arredondados, botoes, bolhas.** E aqui que o design mora. |
| `_render_sidebar` | A barra da esquerda (Fonte ativa, tabelas, Provedor). |
| `_render_chat_tab` | A tela de perguntas (sugestoes, campo de pergunta, historico). |
| `_render_data_tab` | A tela de carregar dados (planilhas, banco, script, exemplo). |
| `_render_config_tab` | A tela de configuracoes (Provedor, chave de API, fontes salvas). |
| `_render_result` | A **tabela** e o **grafico** do resultado. |
| `_render_turn` | Como cada pergunta e resposta aparece (o SQL, o botao Executar). |
| `_render_suggestions` / `_render_recent` | Os botoes de perguntas sugeridas e recentes. |
| `main` | Junta tudo: titulo, abas e a ordem das telas. |

**As cores base do tema** ficam em outro arquivo:

| Arquivo | O que e |
|---|---|
| `.streamlit/config.toml` | As cores principais do Streamlit (fundo, destaque, texto). |

## Primeira tarefa (passo a passo): mudar a cor de destaque

1. Abra `.streamlit/config.toml`.
2. Troque o valor de `primaryColor` por outra cor, por exemplo `"#22c55e"` (verde).
3. Salve e rode:
   ```powershell
   .\venv\Scripts\streamlit run app.py
   ```
4. Veja a diferenca nos botoes. Depois mude `backgroundColor` e experimente.

## O que mexer para...

| Eu quero mudar... | Onde |
|---|---|
| A **cor de destaque** (botoes, abas) | `.streamlit/config.toml` -> `primaryColor` |
| A **cor de fundo** da tela | `.streamlit/config.toml` -> `backgroundColor` |
| O **tamanho/estilo dos titulos** | `app.py`, no `CSS`, classe `.chs-title` |
| A **fonte** | `app.py`, no `CSS` (linha `@import` e `font-family`) |
| O visual dos **cartoes** | `app.py`, no `CSS`, classe `.chs-card` |
| A **bolha da pergunta** | `app.py`, no `CSS`, classe `.chs-user` |
| A **cor dos graficos/tabela** | `app.py`, funcao `_render_result` |
| O **texto das abas** (Chat/Dados/Configuracoes) | `app.py`, no final, funcao `main` |
| As **sugestoes de pergunta** | `chat_sql/nl/engine.py` (funcao `suggest_questions`) |

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Se o navegador ja estiver aberto, aperte `Ctrl + F5` para carregar o visual novo.

## Cuidados

- Mexa **so no visual**. Nao apague as funcoes nem mude os nomes delas, senao as
  outras telas param de funcionar.
- Nada de `print`; o resultado aparece na propria tela.
- Se der erro, rode `.\venv\Scripts\python -m pytest tests/test_app.py -v` para ver se a tela ainda abre.

## Pronto quando

- [ ] `pytest` verde.
- [ ] A tela mudou como voce queria e continua funcionando.
- [ ] Tirou um print e colocou em `docs/imagens/` (veja o [guia das imagens](../imagens/README.md)).
