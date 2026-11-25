# Roteiro da apresentação

[Início](../README.md) · [Índice](README.md) · [PRD](../PRD.md)

**Duração:** 12 minutos de fala + demo · **Público:** o professor, no papel de
**cliente** (uma instituição que tem um banco de dados e ninguém que saiba SQL).

---

## A ideia central

Não apresentem um trabalho. Apresentem **a solução de um problema dele**.

A frase que guia tudo:

> "Hoje, para saber quantos empréstimos estão atrasados, alguém da biblioteca
> precisa pedir ao TI ou abrir o Excel. Com o Chat SQL, a pessoa digita a
> pergunta em português."

Se a banca sair lembrando dessa frase, a apresentação funcionou.

---

## Divisão do tempo

| Tempo | Quem | O quê |
|---|---|---|
| 0:00–1:30 | 1 pessoa | **O problema** — sem falar de código |
| 1:30–3:00 | mesma | **A promessa** — o que o produto faz |
| 3:00–7:30 | 2 pessoas | **Demo ao vivo** (roteiro abaixo) |
| 7:30–9:00 | Frente A | **Segurança** — a Trava recusando escrita |
| 9:00–10:15 | Frente B | **Funciona sem IA** — custo zero, dado não sai |
| 10:15–11:15 | Frente D | **Números** — banco real, acurácia, testes |
| 11:15–12:00 | todos | **Próximos passos** |

---

## 1. O problema (1min30)

Sem jargão. Sem "nosso sistema".

- "Uma biblioteca tem 456 livros, 800 usuários e 2.500 empréstimos. Esses dados
  estão no banco."
- "Quando o coordenador quer saber *quantos empréstimos atrasaram no mês
  passado*, ele não consegue perguntar ao banco."
- "As opções hoje são: pedir para alguém de TI (demora), abrir uma planilha
  (desatualizada) ou contratar um BI (caro)."
- **"O gargalo não é o dado. É a linguagem."**

## 2. A promessa (1min30)

- "O Chat SQL deixa qualquer funcionário perguntar em português."
- Mostre **uma vez** na tela (sem clicar): o campo de pergunta vazio.
- "Três garantias que fazem isso ser utilizável numa instituição:"
  1. **Só leitura.** Não apaga, não altera.
  2. **Você vê o SQL antes de executar.** Nada roda escondido.
  3. **Funciona sem IA.** Sem chave, sem custo por pergunta, sem dado saindo.

## 3. Demo ao vivo (4min30)

Execute **nesta ordem**. Cada pergunta foi validada contra o banco real.

| # | Pergunta | O que destacar |
|---|---|---|
| 1 | `quantos livros existem` | **456** em destaque. "Esse número veio do banco, agora." |
| 2 | `quais editoras existem` | 40 linhas. "Uma pergunta que antes era um `SELECT DISTINCT`." |
| 3 | `quantos emprestimos por mes` | **Gráfico**. "Ele escolheu agrupar por mês sozinho." |
| 4 | `quais os 5 livros mais antigos` | 1532, 1572... "Dados reais: Os Lusíadas está aqui." |
| 5 | `quais livros com titulo Dom Casmurro` | 1 resultado. "Busca por texto, sem acento, sem caixa." |
| 6 | `qual a previsão do tempo` | **Diagnóstico.** "Ele não chuta. Diz que não entendeu e sugere." |
| 7 | `DELETE FROM livro` | **A Trava recusa.** "Aqui está a garantia de segurança." |

**Regra:** nunca digite durante a fala. Cada pergunta deve estar pronta para
colar, com o resultado já visto antes.

## 4. Segurança (1min30)

- "Três camadas, não uma:"
  1. A **Trava** analisa o SQL e só deixa passar `SELECT`.
  2. O **usuário do banco** é somente leitura — mesmo se a Trava falhasse.
  3. A **sessão** abre em modo leitura no servidor.
- "E mostramos o SQL antes de executar. Transparência é o que gera confiança."
- Frase de efeito: **"Uma consulta errada é pior que consulta nenhuma."**

## 5. Sem IA (1min15)

- "A pergunta óbvia: por que não usar GPT para tudo?"
- Três respostas:
  1. **Custo:** cada pergunta custaria dinheiro. Numa biblioteca, milhares por dia.
  2. **Proibição:** muitas empresas não permitem enviar dados para fora.
  3. **Determinismo:** a mesma pergunta dá a mesma resposta, sempre.
- "O motor por regras acerta 14 de 14 no nosso conjunto de referência. É um
  conjunto pequeno e conhecido — não é a mesma coisa que acertar tudo. Mas
  mostra que o caminho funciona."
- "A IA é opcional: existe uma aba para colar a chave, se a instituição quiser."

## 6. Números (1min)

| O que | Valor |
|---|---|
| Tabelas / colunas | 7 / 29 |
| Registros | ~5.300 |
| Obras reais | 456 (de 1532 a 2024) |
| Tempo de conexão | 6,4 s |
| Tempo por consulta | 0,23 s |
| Testes automatizados | 204 |

- "O banco está no Neon, com usuário somente leitura, e é o mesmo que vocês
  acabaram de ver."

## 7. Próximos passos (45s)

- Multi-instituição (hoje é uma instância por instituição)
- MySQL e SQL Server
- Login e perfis
- **Uma frase de fechamento:** "O dado já existe. O que faltava era a linguagem."

---

## Plano B (o que fazer se der errado)

| Falha | Plano B |
|---|---|
| Wi-Fi da sala cai | Banco **SQLite local** com as planilhas de `exemplos/` |
| Neon não responde | Mesmo plano B; ou vídeo gravado |
| Projetor 1366×768 corta a tela | `Ctrl + -` no navegador (zoom 90%) |
| Streamlit não abre | `streamlit run app.py` de novo; se persistir, vídeo |
| Alguém pergunta algo que o motor não entende | Use como **prova** do Diagnóstico: "veja, ele diz que não entendeu" |

**Antes de entrar na sala:**
1. Rodar o app
2. Conectar no banco (aquece o Neon — evita os 6 s de cold start na frente de todos)
3. Executar as 7 perguntas uma vez, em silêncio
4. Deixar as abas prontas

---

## Perguntas prováveis da banca

| Pergunta | Resposta |
|---|---|
| "E se o banco tiver 10 milhões de linhas?" | A Trava limita linhas, há índice em data e título, e a consulta tem timeout de 5 s. A introspecção lê o catálogo, não a tabela — não fica mais lenta com volume. |
| "Por que não usaram GPT?" | Custo por pergunta, proibição em empresas, e o offline acerta sem mandar dado para fora. A IA continua disponível como opção. |
| "Como impedem SQL malicioso?" | Quatro camadas: allowlist (só `SELECT`), parser sqlglot, usuário read-only no banco, sessão em modo leitura. |
| "Isso é produto ou trabalho de faculdade?" | É um produto com escopo acadêmico: uma instância por instituição hoje; multi-tenant é o próximo passo. |
| "Quantas perguntas ele entende?" | Cobre contar, somar, média, maior/menor, top-N, agrupar, filtrar por texto/data/número e juntar tabelas. Fora disso, avisa que não entendeu. |
| "Como sabem que acerta?" | 14 de 14 num conjunto de referência, medido contra o banco real. O harness está no repositório e aceita novas perguntas. |
| "O que acontece se o usuário pedir para apagar?" | A Trava recusa antes de chegar ao banco. Podemos mostrar agora. |
| "Qual a parte mais difícil?" | Garantir que o SQL gerado só toque no que existe — coluna inventada quebra na execução. Validamos contra o schema antes de rodar. |

---

## O que NÃO mostrar

- A URL crua do banco (senha aparece)
- Tela com 0 linhas
- Log de erro do terminal
- O arquivo `.env`
- Código-fonte durante a fala (a não ser que perguntem)

---

## Slide a slide (se usarem slides)

| # | Slide | Conteúdo |
|---|---|---|
| 1 | Capa | Chat SQL + nomes + A3 |
| 2 | O problema | "O gargalo é a linguagem" |
| 3 | A solução | Diagrama pergunta → SQL → resultado |
| 4 | Demo | (tela ao vivo) |
| 5 | Segurança | 3 camadas + print da Trava recusando |
| 6 | Sem IA | 3 motivos + 14/14 |
| 7 | Banco | 7 tabelas + MER (o diagrama do `dbdiagram.io`) |
| 8 | Resultados | a tabela de números |
| 9 | Próximos passos | roadmap |
| 10 | Obrigado | "O dado já existe. Faltava a linguagem." |

---

## Ensaio

- **Cronometrar.** Se passar de 12 min, cortar do slide 7 (banco) — é o menos
  decisivo ao vivo.
- Cada pessoa fala **só a sua parte**, com uma frase de transição ensaiada.
- Quem não fala na demo fica responsável pelo tempo.
- **Gravar um vídeo de 3 min** da demo funcionando. É o plano B.

---

[Início](../README.md) · [Índice](README.md) · [PRD](../PRD.md)
