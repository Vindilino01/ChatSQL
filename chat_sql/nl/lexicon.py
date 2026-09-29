"""Vocabulario PT-BR do Motor Offline."""

from __future__ import annotations

STOPWORDS = {
    "a", "as", "o", "os", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "que", "qual", "quais", "quanto", "quantos", "quantas",
    "e", "ou", "para", "por", "com", "sem", "se", "me", "mostre", "liste", "exiba",
    "traga", "relacao", "todos", "todas", "cada", "meu", "minha", "seu", "sua",
    "existe", "existem", "tem", "ha", "sao", "foi", "foram", "ser", "esta", "estao",
    "mais", "menos", "muito", "pouco", "apenas", "somente", "favor", "por favor",
    "gostaria", "queria", "quero", "saber", "ver", "fazer", "feito", "feitas",
}

NUMBER_WORDS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12,
    "quinze": 15, "vinte": 20, "trinta": 30, "quarenta": 40, "cinquenta": 50,
    "sessenta": 60, "setenta": 70, "oitenta": 80, "noventa": 90, "cem": 100,
    "cento": 100, "duzentos": 200, "quinhentos": 500, "mil": 1000,
}

MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
MONTH_ALIASES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}

WEEKDAYS = {
    "domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado",
}

MEASURE_KEYWORDS: dict[str, list[str]] = {
    "faturamento": ["valor_total", "total", "faturamento", "receita", "valor", "montante"],
    "receita": ["valor_total", "total", "receita", "valor"],
    "venda": ["valor_total", "total", "valor"],
    "vendas": ["valor_total", "total", "valor"],
    "total": ["valor_total", "total", "valor"],
    "valor": ["valor_total", "valor", "total"],
    "preco": ["preco", "preco_unitario", "valor"],
    "salario": ["salario_base", "salario"],
    "nota": ["nota"],
    "quantidade": ["quantidade", "estoque"],
    "estoque": ["estoque"],
    "desconto": ["desconto"],
    "custo": ["custo"],
    "lucro": ["lucro"],
}

MEASURE_WORDS = set(MEASURE_KEYWORDS) | {
    "montante", "custo", "lucro", "despesa", "gasto", "receitas",
}

SEMANTIC_HINTS: dict[str, list[str]] = {
    "idade": ["idade", "age"],
    "anos": ["age", "idade", "anos", "ano", "year"],
    "ano": ["ano", "year", "age"],
    "peso": ["peso", "weight", "kg"],
    "kg": ["peso", "weight", "kg"],
    "quilos": ["peso", "weight"],
    "altura": ["altura", "height"],
    "metros": ["altura", "height", "metro", "meters"],
    "reais": ["valor", "preco", "price", "amount", "total", "faturamento", "fare"],
    "real": ["valor", "preco", "price", "fare"],
    "dolares": ["valor", "preco", "price", "amount", "fare"],
    "euros": ["valor", "preco", "price"],
    "salario": ["salario", "salary"],
    "quilometros": ["distancia", "distance", "km"],
    "km": ["distancia", "distance", "km"],
    "litros": ["litros", "liters", "volume"],
    "tarifa": ["fare", "tarifa", "valor", "preco"],
    "passagem": ["fare", "tarifa", "passagem"],
    "bilhete": ["fare", "tarifa"],
    "nota": ["nota", "score", "rating"],
    "percentual": ["percentual", "percent", "taxa", "rate"],
    "horas": ["horas", "hours", "duracao", "duration"],
    "dias": ["dias", "days", "duracao"],
    "meses": ["meses", "months", "duracao"],
}

LABEL_HINTS = (
    "nome", "name", "titulo", "title", "descricao", "description",
    "razao", "produto", "cliente", "funcionario", "label",
)

DISTINCT_WORDS = {"distintos", "distintas", "unicos", "unicas", "diferentes", "distinto", "unico"}

EXISTS_WORDS = {"existe", "existem", "tem", "ha", "algum", "alguma", "alguns", "algumas"}

NULL_WORDS = {"nulo", "nula", "nulos", "nulas", "vazio", "vazia", "vazios", "vazias"}
NOT_NULL_WORDS = {"preenchido", "preenchidos", "preenchida", "preenchidas", "definido", "definidos"}
NULL_PHRASES = {"sem valor", "sem dados", "sem informacao", "nao informado", "nao preenchido"}

TRUE_WORDS = {"ativo", "ativos", "ativa", "ativas", "sim", "verdadeiro", "verdadeiros", "habilitado", "ligado"}
FALSE_WORDS = {"inativo", "inativos", "inativa", "inativas", "nao", "falso", "falsos", "desabilitado", "desligado"}

COMPARISON_PATTERNS = (
    (r"\b(?:maior|maiores|acima|superior(?:es)?|mais de|mais que|>)\s*(?:ou igual\s*)?(?:a|que|do que)?\s*(\d+(?:[.,]\d+)?)", ">=", ">"),
    (r"\b(?:menor|menores|abaixo|inferior(?:es)?|menos de|menos que|<)\s*(?:ou igual\s*)?(?:a|que|do que)?\s*(\d+(?:[.,]\d+)?)", "<=", "<"),
    (r"\b(?:igual|igual a|exatamente|=)\s*(\d+(?:[.,]\d+)?)", "=", "="),
    (r"\b(?:diferente de|diferente|exceto|!=|<>)\s*(\d+(?:[.,]\d+)?)", "!=", "!="),
)

BETWEEN_PATTERNS = (
    r"\bentre\s+(\d+(?:[.,]\d+)?)\s+e\s+(\d+(?:[.,]\d+)?)",
    r"\bde\s+(\d+(?:[.,]\d+)?)\s+a\s+(\d+(?:[.,]\d+)?)",
)

LIKE_PATTERNS = (
    (r"\b(?:contem|contendo|que tenha|inclui|incluindo)\s+[\"']?([a-z0-9_ ]+?)[\"']?$", "contains"),
    (r"\b(?:comeca|comecam|iniciam|inicia) com\s+[\"']?([a-z0-9_ ]+?)[\"']?$", "startswith"),
    (r"\b(?:termina|terminam|acabam|acaba) com\s+[\"']?([a-z0-9_ ]+?)[\"']?$", "endswith"),
)

ORDER_DESC_WORDS = {
    "maiores", "maior", "melhores", "melhor", "mais caros", "mais caro",
    "decrescente", "desc", "recentes", "ultimos", "ultimas", "mais altos",
}
ORDER_ASC_WORDS = {
    "menores", "menor", "piores", "pior", "mais baratos", "mais barato",
    "crescente", "asc", "antigos", "antigas", "primeiros", "primeiras", "mais baixos",
}

AGG_WORDS = {
    "soma": "sum", "somatorio": "sum", "total": "sum", "faturamento": "sum",
    "receita": "sum", "montante": "sum", "media": "avg", "medias": "avg",
    "medio": "avg", "medios": "avg", "maior": "max", "maximo": "max",
    "menor": "min", "minimo": "min", "quantidade": "count",
}

DATE_RELATIVE_PHRASES = (
    "mes passado", "ultimo mes", "mes anterior", "mes retrasado",
    "este mes", "mes atual", "nesse mes", "neste mes",
    "ano passado", "ultimo ano", "ano anterior",
    "este ano", "ano atual", "nesse ano",
    "semana passada", "ultima semana", "esta semana", "semana atual",
    "hoje", "ontem", "anteontem", "amanha",
    "primeiro trimestre", "segundo trimestre", "terceiro trimestre", "quarto trimestre",
    "primeiro semestre", "segundo semestre",
)
