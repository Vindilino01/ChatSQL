# Bugfix Requirements Document

## Introduction

O motor offline do ChatSQL (`chat_sql/nl/`) falha silenciosamente em seis cenários
de pergunta comuns em PT-BR. Em vez de retornar SQL válido ou uma mensagem de erro
clara, ele retorna `None` ou gera SQL sintaticamente inválido, bloqueando o usuário
quando o provedor de IA não está disponível. Este documento cobre os seis defeitos
identificados e define o comportamento correto esperado para cada um.

---

## Bug Analysis

### Current Behavior (Defect)

**Defeito 1 — Variações de intenção de agregação não reconhecidas**

1.1 WHEN a pergunta contém palavras como "conte", "some", "calcule a média", "me diga o
total" ou "quanto foi" THEN o sistema não reconhece nenhuma intenção de agregação
(`_detect_aggregation` retorna `"list"`) e gera SQL de listagem em vez de SQL com
`COUNT`, `SUM` ou `AVG`.

---

**Defeito 2 — Fallback de tabela única ignorado quando há casamentos parciais**

1.2 WHEN o schema possui uma única tabela E a pergunta não menciona explicitamente o
nome dessa tabela MAS contém tokens que casam parcialmente com outras entidades
irrelevantes THEN o sistema preenche `scored` com candidatos de baixa qualidade, não
entra no ramo de fallback de tabela única e retorna `subject = None`, produzindo `None`
como SQL.

---

**Defeito 3 — Operador de comparação "maior ou igual" aplicado como "maior"**

1.3 WHEN a pergunta contém a construção "maior ou igual a N" (ou "menor ou igual a N")
THEN o sistema usa o operador curto (`>` ou `<`) em vez do operador longo (`>=` ou
`<=`) porque `_extract_numeric_filter` sempre aplica `short` independente da presença
de "ou igual" na frase, gerando SQL com filtro incorretamente exclusivo.

---

**Defeito 4 — Intenção de agregação descartada silenciosamente quando não há coluna
de medida disponível**

1.4 WHEN a pergunta pede uma agregação (`sum`, `avg`, `min`, `max`) E o schema contém
apenas colunas `INTEGER` cujos nomes incluem tokens como "ano", "codigo" ou "matricula"
THEN `_is_measure_column` rejeita todas as colunas candidatas, `_resolve_measure`
retorna `None` e `_build` silenciosamente rebaixa `intent` para `"list"` sem notificar
o usuário, retornando SQL de listagem onde um erro ou uma mensagem explicativa era
esperada.

---

**Defeito 5 — GROUP BY em tabela relacionada gera SQL inválido com `col() = None`**

1.5 WHEN a coluna de agrupamento (`plan.group`) pertence a uma tabela diferente do
`subject` E essa tabela não foi adicionada à lista `needed` antes de `_build` chamar
`_group_expression` THEN `builder.col()` retorna `None`, `_group_expression` retorna
`None`, e o SQL gerado omite a cláusula `GROUP BY`, produzindo resultados semânticamente
incorretos sem qualquer aviso.

---

**Defeito 6 — `LIKE '%%'` gerado quando o padrão de busca captura apenas stopwords**

1.6 WHEN a pergunta usa uma construção LIKE (ex.: "livros que contenham") sem um valor
concreto após a palavra de gatilho E o valor capturado pelo regex é composto inteiramente
por stopwords THEN `_extract_like_filter` não descarta o filtro (a verificação atual
só elimina valores que sejam *exatamente iguais* a uma única stopword) e cria um
`Filter` com `value` sendo uma stopword ou frase de stopwords, gerando SQL com
`LIKE '%%'` ou `LIKE '%de%'`.

---

### Expected Behavior (Correct)

**Correção 1 — Variações de agregação PT-BR reconhecidas**

2.1 WHEN a pergunta contém palavras como "conte", "some", "calcule a média", "me diga o
total" ou "quanto foi" THEN o sistema SHALL reconhecer a intenção de agregação
correspondente (`count`, `sum` ou `avg`) e gerar SQL com a função de agregação correta.

---

**Correção 2 — Fallback de tabela única robusto a casamentos parciais**

2.2 WHEN o schema possui uma única tabela E a pergunta não menciona explicitamente o
nome dessa tabela THEN o sistema SHALL retornar essa única tabela como `subject`,
independentemente de tokens da pergunta causarem casamentos parciais no loop de
pontuação.

---

**Correção 3 — Operador de comparação reflete "ou igual"**

2.3 WHEN a pergunta contém "maior ou igual a N" THEN o sistema SHALL usar o operador
`>=` no SQL gerado; WHEN a pergunta contém "menor ou igual a N" THEN o sistema SHALL
usar o operador `<=` no SQL gerado.

---

**Correção 4 — Ausência de coluna de medida produz erro explicativo em vez de
rebaixamento silencioso**

2.4 WHEN a pergunta pede agregação E nenhuma coluna de medida adequada é encontrada no
schema THEN o sistema SHALL retornar um `OfflineResult` com `sql = None` e uma mensagem
de erro clara explicando que nenhuma coluna numérica agregável foi encontrada, em vez
de gerar silenciosamente SQL de listagem.

---

**Correção 5 — GROUP BY em tabela relacionada incluída corretamente na query**

2.5 WHEN a coluna de agrupamento pertence a uma tabela diferente do `subject` THEN o
sistema SHALL garantir que essa tabela esteja incluída em `needed` antes que
`_group_expression` seja chamado, de modo que `builder.col()` retorne um valor válido
e a cláusula `GROUP BY alias.coluna` apareça corretamente no SQL gerado.

---

**Correção 6 — Filtro LIKE com valor inválido descartado sem gerar `LIKE '%%'`**

2.6 WHEN o valor capturado por `_extract_like_filter` é vazio, é uma única stopword ou
é uma frase composta inteiramente por stopwords THEN o sistema SHALL descartar o filtro
LIKE completamente (retornar `None`) em vez de criar um `Filter` que produza
`LIKE '%%'` ou `LIKE '%stopword%'`.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a pergunta contém palavras já reconhecidas por `_detect_aggregation` como
"quantos", "media", "soma", "total" ou "faturamento" THEN o sistema SHALL CONTINUE TO
detectar a intenção de agregação correta sem regressão.

3.2 WHEN o schema possui múltiplas tabelas E a pergunta menciona explicitamente o nome
de uma delas THEN o sistema SHALL CONTINUE TO identificar a tabela correta como
`subject` pelo mecanismo de pontuação existente.

3.3 WHEN a pergunta contém comparações simples sem "ou igual" como "maior que 100" ou
"menor que 50" THEN o sistema SHALL CONTINUE TO gerar os operadores `>` e `<`
respectivamente.

3.4 WHEN o schema contém colunas `REAL` elegíveis como medida THEN o sistema SHALL
CONTINUE TO resolver `_resolve_measure` corretamente e gerar SQL de agregação válido.

3.5 WHEN o `group` pertence à própria tabela `subject` THEN o sistema SHALL CONTINUE TO
gerar `GROUP BY` corretamente sem necessidade de JOIN adicional.

3.6 WHEN `_extract_like_filter` recebe uma pergunta com valor concreto após a palavra
de gatilho (ex.: "livros que contenham Dom Casmurro") THEN o sistema SHALL CONTINUE TO
gerar `LIKE '%dom casmurro%'` corretamente.

3.7 WHEN qualquer dos cenários acima é executado THEN o sistema SHALL CONTINUE TO não
introduzir regressões nos casos de teste existentes em `tests/test_offline.py`,
`tests/test_offline_extended.py` e `tests/eval/cases.json`.

---

## Derivação da Condição de Bug

### Bug Condition Functions

```pascal
// Defeito 1 — Variações de intenção
FUNCTION isBugCondition1(X)
  INPUT: X.question: string
  OUTPUT: boolean
  RETURN normalize(X.question) contém qualquer de
         {"conte", "some", "calcule a media", "me diga o total", "quanto foi"}
         E _detect_aggregation(X.question) = "list"
END FUNCTION

// Defeito 2 — Fallback de tabela única
FUNCTION isBugCondition2(X)
  INPUT: X.schema com exatamente 1 tabela, X.question sem o nome da tabela
  OUTPUT: boolean
  RETURN len(X.schema.tables) = 1
         E nome_tabela NÃO aparece em X.question
         E scored NÃO está vazio após o loop de pontuação
END FUNCTION

// Defeito 3 — Operador "ou igual"
FUNCTION isBugCondition3(X)
  INPUT: X.question: string
  OUTPUT: boolean
  RETURN X.question contém "ou igual" E _extract_numeric_filter usa operador curto
END FUNCTION

// Defeito 4 — Sem coluna de medida
FUNCTION isBugCondition4(X)
  INPUT: X.schema, X.question com intenção de agregação
  OUTPUT: boolean
  RETURN plan.intent IN {"sum","avg","min","max"}
         E _resolve_measure(X.schema, X.question, subject) = None
END FUNCTION

// Defeito 5 — GROUP BY tabela relacionada
FUNCTION isBugCondition5(X)
  INPUT: X.plan.group: (Table, Column)
  OUTPUT: boolean
  RETURN plan.group[0].name ≠ plan.subject.name
         E plan.group[0].name NÃO está em needed quando _group_expression é chamado
END FUNCTION

// Defeito 6 — Valor LIKE inválido
FUNCTION isBugCondition6(X)
  INPUT: X.question: string, X.captured_value: string
  OUTPUT: boolean
  RETURN X.captured_value é vazio
         OU todos os tokens de X.captured_value estão em STOPWORDS
END FUNCTION
```

### Fix-Checking Properties

```pascal
// Defeito 1
FOR ALL X WHERE isBugCondition1(X) DO
  intent, _ ← _detect_aggregation'(X.question)
  ASSERT intent IN {"count", "sum", "avg"}
END FOR

// Defeito 2
FOR ALL X WHERE isBugCondition2(X) DO
  subject, _ ← _find_subject'(X.schema, X.question)
  ASSERT subject = first(X.schema.tables.values())
END FOR

// Defeito 3
FOR ALL X WHERE isBugCondition3(X) DO
  filter ← _extract_numeric_filter'(...)
  ASSERT filter.operator IN {">=", "<="}
END FOR

// Defeito 4
FOR ALL X WHERE isBugCondition4(X) DO
  result ← _build'(plan, schema)
  ASSERT result.sql = None AND result.error ≠ None
END FOR

// Defeito 5
FOR ALL X WHERE isBugCondition5(X) DO
  sql ← _build'(plan, schema)
  ASSERT "GROUP BY" IN sql AND sql não contém "None"
END FOR

// Defeito 6
FOR ALL X WHERE isBugCondition6(X) DO
  filter ← _extract_like_filter'(X.question, subject)
  ASSERT filter = None
END FOR
```

### Preservation Property

```pascal
FOR ALL X WHERE NOT isBugCondition1(X)
             AND NOT isBugCondition2(X)
             AND NOT isBugCondition3(X)
             AND NOT isBugCondition4(X)
             AND NOT isBugCondition5(X)
             AND NOT isBugCondition6(X) DO
  ASSERT F(X) = F'(X)   // comportamento inalterado
END FOR
```
