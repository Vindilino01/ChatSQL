"""Normalizacao de texto em PT-BR."""

from __future__ import annotations

import re
import unicodedata


def strip_accents(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )


def normalize(text: str) -> str:
    value = strip_accents((text or "").lower())
    value = re.sub(r"[^a-z0-9_ ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def singular(word: str) -> str:
    rules = (("oes", "ao"), ("aes", "ao"), ("eis", "el"), ("ns", "m"), ("s", ""))
    for suffix, replacement in rules:
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            return word[: -len(suffix)] + replacement
    return word


def plural(word: str) -> str:
    if word.endswith(("r", "z", "n")):
        return word + "es"
    if word.endswith("m"):
        return word[:-1] + "ns"
    if word.endswith("l"):
        return word[:-1] + "is"
    if word.endswith("s"):
        return word
    return word + "s"


def forms(name: str) -> set[str]:
    result: set[str] = set()
    for part in re.split(r"[_ ]+", (name or "").lower()):
        if part:
            result.add(part)
            result.add(singular(part))
            result.add(plural(part))
    if name:
        result.add(name.lower())
    return result


def question_forms(question: str) -> set[str]:
    result: set[str] = set()
    for token in question.split():
        result.add(token)
        result.add(singular(token))
        result.add(plural(token))
    return result


def position(question: str, candidates: set[str]) -> int:
    for index, token in enumerate(question.split()):
        if token in candidates or singular(token) in candidates or plural(token) in candidates:
            return index
    return 999


def quote(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def tokens(question: str) -> list[str]:
    return question.split()
