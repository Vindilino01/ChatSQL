---
name: Chat SQL
description: Perguntas em português, respostas em SQL somente leitura, com o número como protagonista.
colors:
  nocturnal-bg: "#0b0d14"
  surface-raised: "rgba(255,255,255,0.035)"
  surface-sidebar: "rgba(15,18,30,0.92)"
  hairline: "rgba(255,255,255,0.07)"
  hairline-strong: "rgba(255,255,255,0.09)"
  halo-indigo: "rgba(99,102,241,0.22)"
  halo-cyan: "rgba(14,165,233,0.14)"
  indigo-signal: "#6366f1"
  indigo-deep: "#4f46e5"
  indigo-soft: "#a5b4fc"
  cyan-accent: "#22d3ee"
  ink-primary: "#f4f5fa"
  ink-body: "#e6e8ef"
  ink-support: "#cfd4e2"
  ink-muted: "#8b93a7"
  ink-faint: "#6f7585"
  ink-on-indigo: "#ffffff"
typography:
  display:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  title:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0em"
  body:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0em"
  label:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  caption:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0em"
  body-sm:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: "0em"
  display-compact:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  display-projector:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  hero-number:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "58px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.03em"
  hero-number-short:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "44px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.03em"
  hero-number-projector:
    fontFamily: "IBM Plex Sans, system-ui, sans-serif"
    fontSize: "46px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.03em"
  mono:
    fontFamily: "IBM Plex Mono, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  xs: "4px"
  sm: "10px"
  md: "12px"
  lg: "16px"
  pill: "999px"
  bubble: "16px 16px 4px 16px"
spacing:
  xs: "3px"
  sm: "6px"
  md: "14px"
  lg: "18px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.indigo-signal}"
    textColor: "{colors.ink-on-indigo}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  card:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-body}"
    rounded: "{rounded.lg}"
    padding: "14px 16px"
  chip:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.ink-body}"
    rounded: "{rounded.sm}"
    padding: "7px 11px"
  user-bubble:
    backgroundColor: "{colors.indigo-signal}"
    textColor: "{colors.ink-on-indigo}"
    rounded: "{rounded.bubble}"
    padding: "12px 16px"
  badge:
    backgroundColor: "rgba(99,102,241,0.18)"
    textColor: "{colors.indigo-soft}"
    rounded: "{rounded.pill}"
    padding: "3px 11px"
---

# Design System: Chat SQL

## Overview

**Creative North Star: "O Painel Noturno"**

A interface é um painel escuro onde **uma coisa brilha por vez**. O fundo quase
preto (`#0b0d14`) carrega dois halos radiais de luz — índigo no canto superior
esquerdo, azul no direito — como iluminação de palco antes da cena começar. Sobre
esse cenário, o resultado da consulta aparece em tipografia grande e clara. Nada
mais na tela tem permissão para competir com ele.

O sistema é **suave e preciso** ao mesmo tempo: cantos generosos (10–16px),
superfícies translúcidas em vez de blocos opacos, e um índigo que aparece só onde
há intenção — ação primária, fala do usuário, seleção de aba. Fora disso, tudo é
cinza-azulado discreto. A precisão vem dos números tabulares, das bordas de 1px e
do silêncio tipográfico em volta da resposta.

Esta é uma superfície **Operate**: o visitante completa uma tarefa, e a ambição
aparece como contenção. Não há ornamento, ilustração ou animação decorativa. O
craft está em fazer o número aparecer no lugar certo, no tamanho certo, com a
informação de apoio recuada ao rodapé.

**Key Characteristics:**
- Fundo escuro com dois halos de luz; nunca preto chapado.
- Um único acento (índigo) usado em ≤10% da tela.
- O número da resposta em 58px é o ponto de maior peso visual, sempre.
- Metadados (linhas, colunas, tempo) em cinza fraco, abaixo de uma borda de 1px.
- Superfícies translúcidas com borda de 1px, nunca sombra dura.

## Colors

Uma paleta noturna de um só acento: índigo como sinal, cinzas azulados como
cenário, ciano apenas como respingo no gradiente do título.

### Primary
- **Índigo Sinal** (#6366f1): ação primária, aba selecionada, fala do usuário,
  borda de destaque. É a cor que diz "aja aqui".
- **Índigo Profundo** (#4f46e5): fim do gradiente do botão primário e da bolha do
  usuário; cria volume sem usar sombra forte.
- **Índigo Suave** (#a5b4fc): texto sobre fundo índigo translúcido — badges e o
  primeiro terço do gradiente do título.

### Secondary
- **Ciano de Acento** (#22d3ee): só no gradiente do título e da marca, como
  segundo ponto de luz. Nunca em texto de corpo, nunca em botão.
- **Halo Ciano** (rgba(14,165,233,0.14)): o segundo clarão do fundo, no canto
  superior direito. É ambiente, não cor de interface — nada interativo o usa.

### Neutral
- **Fundo Noturno** (#0b0d14): base do app. Não usar em cartões — cartões são
  translúcidos por cima dele.
- **Halo Índigo** (rgba(99,102,241,0.22)): o clarão do canto superior esquerdo.
  Faz parte do fundo, nunca de um componente.
- **Superfície Elevada** (rgba(255,255,255,0.035)): cartões, chips, blocos de
  apoio. Quase invisível de propósito.
- **Superfície da Barra** (rgba(15,18,30,0.92)): sidebar. Um tom acima do fundo,
  separada por uma linha de 1px.
- **Linha de Cabelo** (rgba(255,255,255,0.07)): divisores e bordas. A borda mais
  forte é rgba(255,255,255,0.09).
- **Tinta Primária** (#f4f5fa): o número-herói e valores de destaque.
- **Tinta de Corpo** (#e6e8ef): texto comum e títulos.
- **Tinta de Apoio** (#cfd4e2): texto de chips e listas densas, um degrau abaixo
  do corpo.
- **Tinta Atenuada** (#8b93a7): rótulos, legendas, texto secundário.
- **Tinta Esmaecida** (#6f7585): metadados de rodapé — o nível mais baixo de
  hierarquia antes de desaparecer.

### Named Rules
**A Regra do Um Acento.** O índigo aparece em no máximo 10% de qualquer tela. A
raridade é o que faz o botão parecer o próximo passo.

**A Regra do Cenário.** Fundo e superfícies nunca competem com o conteúdo: se um
cartão chama mais atenção que o número dentro dele, o cartão está errado.

## Typography

**Display Font:** IBM Plex Sans (com system-ui, sans-serif)
**Body Font:** IBM Plex Sans (mesma família)
**Label/Mono Font:** IBM Plex Mono (para SQL e código)

**Character:** Uma única família humanista-técnica em toda a interface. O peso e o
tamanho fazem a hierarquia, não a troca de fonte. O monoespaçado entra só onde o
conteúdo é literalmente código — o SQL — e nunca em números de resultado.

### Hierarchy
- **Display / Número-herói** (700, 58px, 1.0, -0.03em): o resultado de uma
  consulta escalar. É o maior objeto da tela e usa numerais tabulares. Cai para
  46px em telas ≤1450px de largura e 44px em ≤800px de altura.
- **Display / Título** (800, 34px, -0.03em): "Chat SQL" no topo, com gradiente
  de texto. Cai para 28px em largura ≤1450px e 26px em altura ≤800px.
- **Headline** (800, 24px, -0.02em): marca na sidebar.
- **Title** (600, 20px): valores de fatos e cabeçalhos de seção.
- **Body** (500, 15px): texto comum; 13–14px para legendas e chips.
- **Body pequeno** (500, 14px): o rótulo ao lado do número-herói e o subtítulo
  do app. É o menor tamanho que ainda pertence ao corpo, não ao rótulo.
- **Caption** (600, 12px): subtítulo da marca na sidebar e texto de badge.
- **Label** (600, 11px, 0.08em, CAIXA ALTA): rótulos de cartão e metadados.
- **Mono** (400, 13px): o SQL exibido no bloco de código.

### Named Rules
**A Regra do Número Nu.** O número da resposta não recebe unidade inventada,
prefixo ou sufixo decorativo. Se precisa de contexto, o contexto vai no rótulo ao
lado, em 14px e cinza.

**A Regra dos Numerais Tabulares.** Todo número que representa dado usa
`font-variant-numeric: tabular-nums`. Números que mudam de largura parecem
instáveis e quebram a leitura em coluna.

## Layout

Um contêiner largo (`layout="wide"`) com sidebar de 260px em telas de até 1450px,
e o conteúdo ocupando o resto. A hierarquia vertical é sempre a mesma: título,
subtítulo, abas, e então a conversa.

Dentro de um turno de conversa, a ordem é fixa e deliberada:

1. a pergunta do usuário, em bolha alinhada à direita;
2. o SQL, em bloco de código com borda de 1px;
3. o botão de executar;
4. **o resultado** — número-herói ou linha de fatos;
5. os metadados, em legenda cinza, abaixo de uma borda.

O espaçamento é generoso na resposta (`18px 4px 10px`) e apertado nos controles
(`6–10px`), o que faz a resposta parecer um objeto e os controles, ferramenta.

**Responsivo:** em largura ≤1450px a sidebar cai para 260px e o número-herói para
46px; em altura ≤800px o padding do contêiner encolhe e o número vai a 44px. O alvo
é o projetor 1366×768 da sala de aula — o pior caso real de uso.

## Elevation & Depth

Profundidade é feita por **luz e transparência**, não por sombra. O fundo tem dois
halos radiais que funcionam como iluminação de ambiente — índigo a 22% no canto
superior esquerdo, ciano a 14% no direito; as superfícies são películas brancas de
3,5% de opacidade com borda de 1px a 7–9% de branco. O resultado é uma sensação de
vidro sobre mesa escura, sem nenhum `box-shadow` estrutural.

A única sombra real do sistema é a da bolha do usuário
(`0 8px 24px rgba(79,70,229,0.28)`): ela brilha, não projeta. É um halo colorido,
não uma sombra cinza.

### Named Rules
**A Regra do Vidro, Não da Pedra.** Superfícies elevam-se tornando-se mais claras e
translúcidas, nunca projetando sombra escura.

## Shapes

Cantos arredondados com intenção: 10px em controles (botões, chips, abas), 12px em
blocos de código e 16px em cartões e na bolha do usuário. O único raio pequeno é
4px, e ele existe por um motivo só: a "cauda" do canto inferior direito da bolha.
Fora isso, nada abaixo de 10px.

Formas pill (999px) ficam reservadas para badges de status. Nada é completamente
quadrado; nada é completamente circular, exceto o badge.

## Components

### Buttons
- **Shape:** cantos de 10px, peso 600.
- **Primary:** gradiente de 135° de #6366f1 a #4f46e5, sem borda, texto branco.
  No hover, `filter: brightness(1.1)` — clareia, não cresce.
- **Secondary:** herdado do Streamlit, com raio de 10px. Sem cor de acento.

### Chips
- **Style:** película branca de 3,5%, borda de 1px a 7%, raio de 10px, texto de
  13px em #cfd4e2. O valor à direita usa numerais tabulares e cor atenuada.
- **State:** sem estado selecionado; chips são listas de fatos, não filtros.

### Cards / Containers
- **Corner Style:** 16px.
- **Background:** rgba(255,255,255,0.035).
- **Border:** 1px rgba(255,255,255,0.09).
- **Shadow Strategy:** nenhuma (ver Elevation).
- **Internal Padding:** 14px 16px.

### Inputs / Fields
- **Style:** herdado do Streamlit; fundo escuro, borda sutil, raio padrão da lib.
- **Focus:** a borda clareia; não há glow colorido.
- **Password:** sempre `type="password"`, com aviso explícito de que não é salvo.

### Navigation
- **Tabs:** lista com gap de 6px; cada aba tem raio de 10px e padding 6px 14px.
  A aba ativa recebe fundo índigo a 16% — nunca texto colorido.
- **Sidebar:** fundo rgba(15,18,30,0.92), borda direita de 1px, marca em gradiente
  de 24px e subtítulo de 12,5px em cinza.

### Signature Component — o Número-Herói
O componente que define o produto. Um `<span>` de 58px, peso 700, numerais
tabulares, alinhado à base com um rótulo de 14px em cinza. Fica sobre uma borda
inferior de 1px que o separa dos metadados. Não tem cartão, fundo ou ícone: é
tipografia pura sobre o fundo noturno. Em telas de projetor, cai para 44–46px.

### Signature Component — a Bolha do Usuário
Alinhada à direita, largura máxima de 78%, gradiente índigo de 135°, raio
16/16/4/16 e halo colorido. É o único lugar onde o índigo ocupa área grande — e
por isso aparece uma vez por turno, no máximo.

## Do's and Don'ts

### Do:
- **Do** manter o número da resposta como o maior objeto da tela (58px, ou 44–46px
  no projetor).
- **Do** usar numerais tabulares em todo número que vem do banco.
- **Do** separar resposta de metadados com uma borda de 1px, nunca com um cartão.
- **Do** deixar o SQL visível e copiável antes de qualquer execução.
- **Do** usar o índigo em no máximo 10% da tela.
- **Do** reduzir a sidebar para 260px em telas ≤1450px.

### Don't:
- **Don't** colocar cartão, sombra ou ícone em volta do número-herói.
- **Don't** usar ciano em texto de corpo, botão ou borda — só no gradiente do
  título.
- **Don't** usar sombra escura para elevar superfícies; use transparência.
- **Don't** exibir a senha do banco em texto puro nem gravá-la em disco.
- **Don't** deixar metadados (linhas, colunas, tempo) com peso maior que a
  resposta.
- **Don't** adicionar animação decorativa: o sistema é estático por decisão.
