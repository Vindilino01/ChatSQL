# Avaliação do Motor Offline (bateria cega)

[Início](../README.md) · [Índice](README.md) · [Roteiro da apresentação](APRESENTACAO.md)

O número **14/14** do PRD foi medido num conjunto de referência escrito junto
com o motor. Para saber se o motor funciona com perguntas **de verdade**, é
preciso um conjunto que ninguém ensaiou.

---

## Por que isso importa

Um conjunto escrito por quem fez o motor tende a usar as palavras que o motor
já conhece. Isso mede o motor contra ele mesmo. A banca vai perguntar
"funciona com perguntas reais?" — e a resposta precisa ser medida, não
afirmada.

## Como coletar (15 minutos)

Cada integrante escreve **8 perguntas** que faria de verdade numa biblioteca,
**sem abrir o código e sem testar no app**. Depois envia.

Regras:
- Escreva como falaria com um colega, não como escreveria SQL.
- Pode usar gíria ("os livro mais véio"), erro de português, sem acento.
- Não vale perguntar a mesma coisa com palavras diferentes só para inflar.

## Onde colocar

Crie `tests/eval/bateria_cega.txt`, uma pergunta por linha:

```text
quantos livros a gente tem
quais os 5 livros mais emprestados
tem quantos usuários inativos
me mostra os empréstimos atrasados
...
```

## Como medir

Cada pergunta recebe uma de quatro marcas:

| Marca | Significa |
|---|---|
| ✅ | Acertou: gerou o SQL certo e o resultado responde à pergunta |
| ⚠️ | Parcial: gerou SQL válido, mas que não responde exatamente |
| ❌ | Errou: gerou SQL que roda mas responde outra coisa |
| 🚫 | Não entendeu: devolveu o Diagnóstico |

**⚠️ e ❌ contam como erro** no cálculo. 🚫 **não** é erro grave — é o
comportamento projetado (não chutar).

## Planilha de resultado

Preencha e cole a tabela no `PRD.md`:

| Pergunta | Marca | SQL gerado | Observação |
|---|---|---|---|
| quantos livros a gente tem | | | |
| ... | | | |

### Resumo

| Métrica | Valor |
|---|---|
| Total de perguntas | |
| ✅ acertou | |
| ⚠️ parcial | |
| ❌ errou | |
| 🚫 não entendeu | |
| **Acurácia (✅ / total)** | |
| Meta | ≥ 70% |

## Como registrar no PRD

Substitua a nota metodológica por:

> Medido em duas etapas: **14/14** no conjunto de referência e **X/Y (Z%)** na
> bateria cega com perguntas não ensaiadas, coletadas por N integrantes.

Se o número ficar abaixo de 70%, **não esconda**. Registre e liste as
categorias que falharam — isso vira o roadmap da Frente B e é mais convincente
que um número inflado.

## Se ninguém entregar as perguntas

Plano B: escrever 20 perguntas **a partir do schema** (olhando só o
`docs/mer/03-dicionario-dados.md`, não o código do motor) e registrar como
"bateria cega parcial". É honesto e mensurável.

---

[Início](../README.md) · [Índice](README.md) · [Roteiro da apresentação](APRESENTACAO.md)
