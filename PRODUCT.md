# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Bibliotecários e coordenação da biblioteca universitária.** Trabalham no balcão
de atendimento ou na coordenação, com o banco de dados ao lado, mas sem saber
SQL. Precisam responder perguntas de gestão — quantos empréstimos estão atrasados,
qual editora publicou mais, quantos exemplares estão em manutenção — e hoje
dependem do TI ou de planilhas desatualizadas.

**Secundário: a banca da disciplina.** Avalia o projeto, não usa o sistema no dia
a dia. Precisa entender a solução em 12 minutos de apresentação e checar números
e decisões de projeto.

## Product Purpose

O Chat SQL recebe uma pergunta em português e devolve SQL somente leitura,
mostrado antes da execução, com o resultado em tabela ou gráfico. Existe para
eliminar a dependência de quem sabe SQL dentro da instituição: o dado já está
estruturado, falta a linguagem para perguntar.

Sucesso = um funcionário que nunca escreveu SQL consegue responder uma pergunta
de rotina sem pedir ajuda, e a resposta é confiável o suficiente para ele agir.

## Positioning

O único mecanismo do projeto que um vizinho não copiaria facilmente é o **motor
offline determinístico**: funciona sem IA, sem chave de API, sem custo por
pergunta e sem enviar dados para fora. A IA é acessório opcional, nunca requisito.

Segundo diferencial: a **Trava** valida o SQL contra o schema real antes de
executar e só aceita `SELECT`. Uma resposta errada é pior que resposta nenhuma —
por isso o motor, quando não entende, devolve o motivo em vez de chutar.

## Operating Context

- Interface em **PT-BR**; prompts enviados à IA em **inglês**.
- Demonstração sobre uma **Biblioteca Universitária** em PostgreSQL/Neon,
  com ~5.300 registros e acervo real.
- Uma fonte de dados ativa por sessão (planilha, Google Sheets, banco, script
  SQL, dump `.sql` ou schema de exemplo).
- O SQL **só aparece na tela e só executa no clique** — decisão explícita do
  grupo contra alucinação.
- Uso avaliado em **projetor 1366×768**.

## Capabilities and Constraints

**Funciona:** motor offline por regras (intenção, filtro, agrupamento, junções
por busca em largura no grafo de FKs); loop de correção com 1 geração + até 2
correções quando há IA; execução somente leitura; conexão Postgres read-only;
planilhas CSV/XLSX/XLS; Google Sheets público; upload de dump `.sql`; histórico
e fontes em disco com URL `?src=`.

**Restrições:**

- Um schema ativo por sessão; não há multi-tenant nem login.
- A chave de API vive apenas em `st.session_state` — nunca em disco.
- Nunca escreve no banco real: `SELECT` apenas, usuário read-only, sessão
  `READ ONLY`.
- Deployment: instância única por instituição. Não há promessa comercial de
  multi-instituição — "qualquer instituição" é o enquadramento acadêmico do
  trabalho, e a demo é uma biblioteca.
- O projeto é **peça de portfólio após a disciplina**, não um produto mantido.
  A documentação prioriza quem lê, não quem opera.

**Decisões em aberto:** suporte a MySQL e SQL Server (evolução, não bloqueia);
multi-instituição com autenticação; integração com sistema de gestão.

## Brand Commitments

- Nome: **Chat SQL**. Sem logotipo; a marca é tipográfica (gradiente índigo no
  título).
- Voz: direta, sem jargão, em português do Brasil. Explica o erro em vez de
  culpar o usuário ("Não identifiquei sobre qual tabela a pergunta é").
- Nunca promete o que não faz: quando a resposta é incerta, o texto diz isso.

## Evidence on Hand

- Banco real com **456 obras**, 277 autores, 40 editoras, 747 exemplares,
  800 usuários e 2.500 empréstimos (`scripts/seed_biblioteca.py`).
- **91 perguntas** de avaliação em quatro conjuntos, comparadas por resultado,
  com nota metodológica honesta em `PRD.md`.
- **345 testes automatizados** passando (347 coletados, 2 guias desativados).
- Documentação do banco gerada do schema em uso (`docs/mer/`, 9 arquivos).
- Medições reais: conexão 6,4 s (com cold start do Neon), consulta 0,23 s.
- **Não existe:** pesquisa com usuários reais, depoimentos, teste de usabilidade
  formal, capturas de tela no repositório (a pasta `docs/imagens/` tem as
  instruções, não os arquivos). Nada disso deve ser inventado.

## Product Principles

1. **Nunca falhar em silêncio.** Sem entendimento, o motor devolve motivo e
   sugestões. Recusar é aceitável; chutar não é.
2. **O SQL é público.** O usuário vê exatamente o que vai rodar antes de rodar.
3. **Offline primeiro.** O caminho padrão não depende de rede, chave ou custo.
4. **A resposta é o herói.** A tela existe para mostrar o número; metadados são
   rodapé, não protagonista.
5. **Documentação serve a quem não programa.** Explicar o porquê antes do como.
