# Chat SQL

Aplicativo que converte Perguntas em linguagem natural em Consultas SQL somente leitura, executadas contra um Schema da Sessão fornecido pelo usuário, com resultados exibidos de forma transparente.

## Language

**Pergunta**:
Texto em linguagem natural que o usuário digita pedindo um resultado. É a entrada do sistema.
_Avoid_: Prompt, input, questão

**Consulta**:
A instrução SQL gerada a partir de uma Pergunta. Por definição, é somente leitura.
_Avoid_: Query, statement, comando

**Schema da Sessão**:
O conjunto fixo de instruções `CREATE TABLE` que serve de contexto para todas as Perguntas de uma sessão. Pode ser colado pelo usuário ou inferido de uma Planilha.
_Avoid_: Esquema, DDL, banco

**Trava**:
A verificação obrigatória que impede a execução de qualquer Consulta que não seja de leitura. Nenhuma Consulta é executada sem passar pela Trava.
_Avoid_: Validação, filtro, guard

**Tentativa**:
Um ciclo completo de gerar, validar e executar uma Consulta para responder a uma Pergunta. Uma Pergunta pode consumir mais de uma Tentativa.
_Avoid_: Retry, execução, rodada

**Dados de Exemplo**:
Linhas sintéticas geradas para popular as tabelas do Schema da Sessão, tornando-o consultável sem depender de dados reais.
_Avoid_: Dados de teste, mock, seed

**Motor Offline**:
O gerador determinístico de Consultas por regras, que não usa modelo de linguagem. É o modo padrão.
_Avoid_: Modo local, heurística, regex

**Provedor**:
O serviço de modelo de linguagem escolhido pelo usuário, autenticado por uma chave de API fornecida por ele. É a alternativa opcional ao Motor Offline.
_Avoid_: Modelo, LLM, API

**Fonte de Dados**:
A origem consultável de uma sessão: uma Planilha, um Script SQL ou uma Conexão.
_Avoid_: Origem, input, dataset

**Planilha**:
Um arquivo CSV, XLSX ou XLS fornecido pelo usuário, do qual se infere um Schema da Sessão e se carregam dados reais.
_Avoid_: Spreadsheet, arquivo, Excel

**Instituição**:
A organização que implanta o Chat SQL e fornece a Fonte de Dados.
_Avoid_: Cliente, empresa, tenant

**Conexão**:
O acesso somente-leitura a um banco de dados real fornecido por uma Instituição.
_Avoid_: Link, DSN, banco

**Fonte Salva**:
Uma Fonte de Dados persistida em disco e identificada por um hash do conteúdo, que pode ser reaberta depois.
_Avoid_: Cache, sessão, snapshot

**Histórico**:
A sequência de Perguntas já respondidas e seus Resultados, associada a uma Fonte Salva.
_Avoid_: Log, conversa, sessão

**Par de Exemplos**:
Um par pergunta/SQL específico do Schema da Sessão, incluído no contexto para orientar a geração de novas Consultas.
_Avoid_: Few-shot, exemplo, template

**Correção**:
Uma Tentativa disparada por falha (de validação ou de execução), em que a Consulta anterior e o erro voltam ao Provedor para gerar uma nova Consulta.
_Avoid_: Retry, conserto, ajuste

**Resultado**:
As linhas retornadas pela execução bem-sucedida de uma Consulta.
_Avoid_: Output, retorno, saída

**Avaliação**:
Uma suíte de Perguntas com Resultado esperado, usada para medir a taxa de acerto das Consultas sobre um Schema da Sessão.
_Avoid_: Benchmark, teste, eval

**Diagnóstico**:
O conjunto estruturado que o Motor Offline devolve quando não gera uma Consulta: motivo, tabelas ambíguas e sugestões de Perguntas.
_Avoid_: Erro, log, mensagem
