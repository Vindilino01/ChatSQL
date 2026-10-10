# Frente B - Motor Offline (o "cerebro" sem IA)

**Responsaveis:** (preencher)

## Em uma frase

Ensinar o robo a entender mais perguntas **sem usar IA** (por regras).

## Onde fica no projeto

**O motor offline e a pasta `chat_sql/nl/`.** Ela tem 4 arquivos:

| Arquivo | O que faz (em portugues) |
|---|---|
| `chat_sql/nl/lexicon.py` | As **palavras que ele conhece**: meses, unidades, sinonimos ("anos" = idade). |
| `chat_sql/nl/engine.py` | **Como ele decide**: a pergunta quer contar? somar? agrupar? filtrar? |
| `chat_sql/nl/builder.py` | **Como ele monta o SQL** e junta as tabelas certas. |
| `chat_sql/nl/text.py` | Limpa o texto (tira acento, entende plural). |

Fora da pasta, mas relacionados:

| Arquivo | O que faz |
|---|---|
| `chat_sql/offline.py` | Atalho que expoe o motor para o resto do sistema. |
| `chat_sql/guard.py` | A Trava: confere se o SQL gerado e seguro. |
| `tests/test_offline.py` e `tests/test_offline_extended.py` | Os testes do motor. |
| `tests/eval/cases.json` | As perguntas usadas para medir a acuracia (meta: 70%). |

## Primeira tarefa (passo a passo): adicionar um sinonimo

Exemplo: fazer o motor entender que "tarifa" e a mesma coisa que a coluna "Fare".

1. Abra `chat_sql/nl/lexicon.py`.
2. Procure o bloco `SEMANTIC_HINTS` (sao as unidades: idade, peso, valor...).
3. Adicione a linha:
   ```python
   "tarifa": ["fare", "tarifa", "valor", "preco"],
   ```
4. Rode os testes:
   ```powershell
   .\venv\Scripts\python -m pytest tests/test_offline_extended.py -v
   ```
5. Teste de verdade: rode o app, carregue um exemplo e pergunte
   "qual a tarifa media".

## O que mexer para...

**Ensinar uma palavra que representa um numero** (ex.: "faturamento") -> `MEASURE_KEYWORDS` em `nl/lexicon.py`.

**Fazer a pergunta certa ser entendida** (novo tipo de pergunta) -> `nl/engine.py`
(procure `_detect_aggregation` e as funcoes que comecam com `_extract_`).

**Melhorar a acuracia** -> acrescente perguntas em `tests/eval/cases.json` e rode:
```powershell
.\venv\Scripts\python -m pytest tests/eval -s
```
O placar aparece no terminal. Registre no `PRD.md`.

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Carregue um exemplo e faca a pergunta. Se nao entender, ele mostra um
**Diagnostico** (motivo + sugestoes) em vez de chutar.

## Pronto quando

- [ ] `pytest` verde.
- [ ] Voce adicionou pelo menos 1 teste para o que ensinou.
- [ ] A pergunta nova funciona no app.
- [ ] Se mudou a acuracia, atualizou o `PRD.md`.

## Dica para nao se perder

- "O que ele conhece" = `lexicon.py`.
- "O que ele decide" = `engine.py`.
- "Como ele escreve o SQL" = `builder.py`.
