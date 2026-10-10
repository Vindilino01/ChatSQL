# Frente B - Motor Offline (o "cérebro" sem IA)

**Responsáveis:** (preencher)

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)

---

## Em uma frase

Ensinar o robô a entender mais perguntas **sem usar IA** (por regras).

## Onde fica no projeto

**O motor offline é a pasta `chat_sql/nl/`.** Ela tem 4 arquivos:

| Arquivo | O que faz (em português) |
|---|---|
| `chat_sql/nl/lexicon.py` | As **palavras que ele conhece**: meses, unidades, sinônimos ("anos" = idade). |
| `chat_sql/nl/engine.py` | **Como ele decide**: a pergunta quer contar? somar? agrupar? filtrar? |
| `chat_sql/nl/builder.py` | **Como ele monta o SQL** e junta as tabelas certas. |
| `chat_sql/nl/text.py` | Limpa o texto (tira acento, entende plural). |

Fora da pasta, mas relacionados:

| Arquivo | O que faz |
|---|---|
| `chat_sql/offline.py` | Atalho que expõe o motor para o resto do sistema. |
| `chat_sql/guard.py` | A Trava: confere se o SQL gerado é seguro. |
| `tests/test_offline.py` e `tests/test_offline_extended.py` | Os testes do motor. |
| `tests/eval/cases.json` | As perguntas usadas para medir a acurácia (meta: 70%). |

## Primeira tarefa (passo a passo): adicionar um sinônimo

Exemplo: fazer o motor entender que "tarifa" é a mesma coisa que a coluna "Fare".

1. Abra `chat_sql/nl/lexicon.py`.
2. Procure o bloco `SEMANTIC_HINTS` (são as unidades: idade, peso, valor...).
3. Adicione a linha:
   ```python
   "tarifa": ["fare", "tarifa", "valor", "preco"],
   ```
4. Rode os testes:
   ```powershell
   .\venv\Scripts\python -m pytest tests/test_offline_extended.py -v
   ```
5. Teste de verdade: rode o app, carregue um exemplo e pergunte
   "qual a tarifa média".

## O que mexer para...

**Ensinar uma palavra que representa um número** (ex.: "faturamento") -> `MEASURE_KEYWORDS` em `nl/lexicon.py`.

**Fazer a pergunta certa ser entendida** (novo tipo de pergunta) -> `nl/engine.py`
(procure por `_detect_aggregation` e as funções que começam com `_extract_`).

**Melhorar a acurácia** -> acrescente perguntas em `tests/eval/cases.json` e rode:
```powershell
.\venv\Scripts\python -m pytest tests/eval -s
```
O placar aparece no terminal. Registre no `PRD.md`.

## Como ver o resultado

```powershell
.\venv\Scripts\streamlit run app.py
```
Carregue um exemplo e faça a pergunta. Se não entender, ele mostra um
**Diagnóstico** (motivo + sugestões) em vez de chutar.

## Pronto quando

- [ ] `pytest` verde.
- [ ] Você adicionou pelo menos 1 teste para o que ensinou.
- [ ] A pergunta nova funciona no app.
- [ ] Se mudou a acurácia, atualizou o `PRD.md`.

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| Motor Offline | O robô que entende a pergunta sem IA |
| Sinônimo | Uma palavra que significa a mesma coisa que outra |
| Intenção | O que a pergunta quer: contar, somar, listar... |
| Acurácia | A porcentagem de perguntas que ele acerta |
| Diagnóstico | A explicação de por que ele não entendeu |

## Dica para não se perder

- "O que ele conhece" = `lexicon.py`.
- "O que ele decide" = `engine.py`.
- "Como ele escreve o SQL" = `builder.py`.

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
