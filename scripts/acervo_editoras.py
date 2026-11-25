"""Editora plausível para cada obra do acervo.

O seed antigo fazia `rng.choice(editora_ids)`, sorteando entre as 40 editoras
sem nenhum critério: `1984` saía como Artmed e `Vidas Secas` como EDUSP. As
editoras são reais, mas a ligação obra -> editora era aleatória.

Aqui a ligação é determinística e por área:

1. cada autor é classificado numa categoria (computação, humanas, literatura...);
2. a categoria define um conjunto de editoras brasileiras que de fato publicam
   aquele tipo de livro;
3. a escolha dentro do conjunto é um hash estável do título — a mesma obra cai
   sempre na mesma editora, e rodar o seed duas vezes não muda o resultado.

Isso continua sendo uma **atribuição sintética**: não é a edição real que a
biblioteca possui (o ISBN também é sintético). O que se ganha é plausibilidade —
nenhuma obra de computação cai numa editora de poesia.

Autores sem categoria explícita são tratados como literatura.
"""

from __future__ import annotations

import hashlib

# Editoras brasileiras que publicam cada tipo de obra. Todas existem em
# `acervo_biblioteca.EDITORAS`; o teste garante que nenhuma ficou de fora.
EDITORAS_POR_CATEGORIA: dict[str, tuple[str, ...]] = {
    "computacao": (
        "Novatec",
        "Bookman",
        "Casa do Código",
    ),
    "negocios": (
        "Sextante",
        "Objetiva",
        "Intrínseca",
        "Record",
        "Companhia das Letras",
        "Autêntica",
    ),
    "ciencia": (
        "Companhia das Letras",
        "Record",
        "Objetiva",
        "Intrínseca",
        "Zahar",
        "Fiocruz",
        "Artmed",
    ),
    "humanas": (
        "Companhia das Letras",
        "Boitempo",
        "Paz e Terra",
        "Autêntica",
        "Editora 34",
        "Zahar",
        "EDUSP",
        "Editora UNESP",
        "Editora UFMG",
        "Objetiva",
    ),
    "educacao": (
        "Autêntica",
        "Ática",
        "Moderna",
        "Paz e Terra",
        "Editora 34",
    ),
    "literatura": (
        "Companhia das Letras",
        "Record",
        "Rocco",
        "Intrínseca",
        "Alfaguara",
        "Objetiva",
        "Cosac Naify",
        "Autêntica",
        "Sextante",
    ),
    "infantojuvenil": (
        "Companhia das Letrinhas",
        "Ática",
        "Moderna",
        "FTD",
        "Scipione",
        "Rocco",
    ),
}

# Categoria de cada autor. Só os que NÃO são literatura precisam aparecer aqui;
# quem não está no dicionário é tratado como "literatura".
CATEGORIA_AUTOR: dict[str, str] = {
    # ---- Computação e engenharia de software ----
    "Aaron Courville": "computacao",
    "Abraham Silberschatz": "computacao",
    "Alfred V. Aho": "computacao",
    "Andrew Hunt": "computacao",
    "Andrew S. Tanenbaum": "computacao",
    "Aurélien Géron": "computacao",
    "Betsy Beyer": "computacao",
    "Brian W. Kernighan": "computacao",
    "Charles E. Leiserson": "computacao",
    "Chris Jones": "computacao",
    "Christos Papadimitriou": "computacao",
    "David A. Patterson": "computacao",
    "David Farley": "computacao",
    "David Thomas": "computacao",
    "Dennis M. Ritchie": "computacao",
    "Donald E. Knuth": "computacao",
    "Douglas Crockford": "computacao",
    "Eric Evans": "computacao",
    "Erich Gamma": "computacao",
    "Frederick P. Brooks Jr.": "computacao",
    "Gene Kim": "computacao",
    "George Spafford": "computacao",
    "Gerald Jay Sussman": "computacao",
    "Harold Abelson": "computacao",
    "Henry F. Korth": "computacao",
    "Ian Goodfellow": "computacao",
    "Jez Humble": "computacao",
    "Joel Grus": "computacao",
    "John L. Hennessy": "computacao",
    "John Vlissides": "computacao",
    "Kent Beck": "computacao",
    "Kevin Behr": "computacao",
    "Kyle Simpson": "computacao",
    "Martin Fowler": "computacao",
    "Michael C. Feathers": "computacao",
    "Michael Sipser": "computacao",
    "Monica S. Lam": "computacao",
    "Peter Norvig": "computacao",
    "Ralph Johnson": "computacao",
    "Richard Helm": "computacao",
    "Robert C. Martin": "computacao",
    "Sanjoy Dasgupta": "computacao",
    "Stuart Russell": "computacao",
    "Thomas H. Cormen": "computacao",
    "Timothy Lister": "computacao",
    "Tom DeMarco": "computacao",
    "Umesh Vazirani": "computacao",
    "Yoshua Bengio": "computacao",
    # ---- Negócios, gestão e comportamento ----
    "Andrew McAfee": "negocios",
    "Brené Brown": "negocios",
    "Carol S. Dweck": "negocios",
    "Cass R. Sunstein": "negocios",
    "Charles Duhigg": "negocios",
    "Dale Carnegie": "negocios",
    "Daniel Goleman": "negocios",
    "Daniel Kahneman": "negocios",
    "Eric Ries": "negocios",
    "Erik Brynjolfsson": "negocios",
    "Idalberto Chiavenato": "negocios",
    "John Kenneth Galbraith": "negocios",
    "Klaus Schwab": "negocios",
    "Malcolm Gladwell": "negocios",
    "Marshall B. Rosenberg": "negocios",
    "Nassim Nicholas Taleb": "negocios",
    "Peter Drucker": "negocios",
    "Peter Thiel": "negocios",
    "Philip Kotler": "negocios",
    "Richard H. Thaler": "negocios",
    "Richard S. Tedlow": "negocios",
    "Salim Ismail": "negocios",
    "Stephen J. Dubner": "negocios",
    "Steven D. Levitt": "negocios",
    "Viviane Forrester": "negocios",
    # ---- Ciência e divulgação científica ----
    "Bessel van der Kolk": "ciencia",
    "Bill Bryson": "ciencia",
    "Carlo Rovelli": "ciencia",
    "Carl Sagan": "ciencia",
    "Geoffrey Blainey": "ciencia",
    "James Suzman": "ciencia",
    "Joseph A. Schumpeter": "ciencia",
    "Leonard Mlodinow": "ciencia",
    "Michio Kaku": "ciencia",
    "Neil MacGregor": "ciencia",
    "Oliver Sacks": "ciencia",
    "Rachel Carson": "ciencia",
    "Siddhartha Mukherjee": "ciencia",
    "Steve Jones": "ciencia",
    "Yuval Noah Harari": "ciencia",
    "José Marengo": "ciencia",
    # ---- Ciências humanas e sociais ----
    "Abdias Nascimento": "humanas",
    "Baruch Espinosa": "humanas",
    "Bronisław Malinowski": "humanas",
    "Caio Prado Júnior": "humanas",
    "Carlo Ginzburg": "humanas",
    "Christopher Lasch": "humanas",
    "Clóvis Moura": "humanas",
    "Darcy Ribeiro": "humanas",
    "Djamila Ribeiro": "humanas",
    "E. P. Thompson": "humanas",
    "Ernst Gombrich": "humanas",
    "Fernand Braudel": "humanas",
    "Florestan Fernandes": "humanas",
    "Friedrich A. Hayek": "humanas",
    "Georg Wilhelm Friedrich Hegel": "humanas",
    "Gilberto Freyre": "humanas",
    "Gilles Lipovetsky": "humanas",
    "Giorgio Agamben": "humanas",
    "Guy Debord": "humanas",
    "Hannah Arendt": "humanas",
    "Henri Bergson": "humanas",
    "Howard S. Becker": "humanas",
    "Immanuel Kant": "humanas",
    "Jean Baudrillard": "humanas",
    "Jean-Jacques Rousseau": "humanas",
    "Joaquim Nabuco": "humanas",
    "John Dewey": "educacao",
    "John Locke": "humanas",
    "John Maynard Keynes": "humanas",
    "Jonathan Israel": "humanas",
    "Jorge Coli": "humanas",
    "José Ramos Tinhorão": "humanas",
    "Karl Marx": "humanas",
    "Karl Polanyi": "humanas",
    "Lev Manovich": "humanas",
    "Lev Vygotsky": "educacao",
    "Marc Bloch": "humanas",
    "Marco Aurélio": "humanas",
    "Marcos Reigota": "educacao",
    "Martin Heidegger": "humanas",
    "Max Weber": "humanas",
    "Michel Foucault": "humanas",
    "Mikhail Bakhtin": "humanas",
    "Nicolau Maquiavel": "humanas",
    "Norbert Elias": "humanas",
    "Paulo Freire": "educacao",
    "Perdigão Malheiro": "humanas",
    "Peter Burke": "humanas",
    "Pierre Bourdieu": "humanas",
    "Platão": "humanas",
    "Roberto DaMatta": "humanas",
    "Roger Chartier": "humanas",
    "Roland Barthes": "humanas",
    "Ruth Benedict": "humanas",
    "Santo Agostinho": "humanas",
    "Serge Latouche": "humanas",
    "Sérgio Buarque de Holanda": "humanas",
    "Susan Sontag": "humanas",
    "Thomas Hobbes": "humanas",
    "Thorstein Veblen": "humanas",
    "Walter Benjamin": "humanas",
    "Émile Durkheim": "humanas",
    "Ana Teberosky": "educacao",
    "Emilia Ferreiro": "educacao",
    "Aristóteles": "humanas",
    "Arthur Schopenhauer": "humanas",
    "Friedrich Nietzsche": "humanas",
    "Sigmund Freud": "humanas",
    "Viktor E. Frankl": "humanas",
    "Manoel Querino": "humanas",
    # ---- Infantojuvenil ----
    "C. S. Lewis": "infantojuvenil",
    "J. K. Rowling": "infantojuvenil",
    "J. R. R. Tolkien": "infantojuvenil",
    "Monteiro Lobato": "infantojuvenil",
    "José Mauro de Vasconcelos": "infantojuvenil",
    "Antoine de Saint-Exupéry": "infantojuvenil",
    "Markus Zusak": "infantojuvenil",
    "John Boyne": "infantojuvenil",
}


def _indice_estavel(chave: str, total: int) -> int:
    """Índice determinístico: o mesmo título sempre cai na mesma editora."""
    digest = hashlib.sha256(chave.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % total


def categoria_da_obra(titulo: str, autores: tuple[str, ...]) -> str:
    """Categoria da obra, olhando os autores (o primeiro que tiver categoria)."""
    for autor in autores:
        categoria = CATEGORIA_AUTOR.get(autor.strip())
        if categoria:
            return categoria
    return "literatura"


def editora_para(titulo: str, autores: tuple[str, ...]) -> str:
    """Nome da editora atribuída à obra, dentro da categoria dela."""
    categoria = categoria_da_obra(titulo, autores)
    candidatas = EDITORAS_POR_CATEGORIA[categoria]
    return candidatas[_indice_estavel(titulo, len(candidatas))]
