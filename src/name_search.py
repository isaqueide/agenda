"""Pesquisa de nomes com normalização textual."""

import re
import unicodedata

from dataclasses import dataclass


@dataclass(frozen=True)
class Occurrence:
    name: str
    page: int
    context: str
    ordinal_on_page: int
    normalized_position: int


def _normalize_with_map(value: str):
    """
    Normaliza caracteres e mantém o índice
    do caractere original correspondente.
    """

    chars = []
    positions = []
    previous_space = False

    for original_index, char in enumerate(value):

        decomposed = unicodedata.normalize(
            "NFKD",
            char.casefold(),
        )

        emitted = False

        for part in decomposed:

            if unicodedata.category(part) == "Mn":
                continue

            if part.isspace():

                if chars and not previous_space:
                    chars.append(" ")
                    positions.append(original_index)

                previous_space = True

            else:

                chars.append(part)
                positions.append(original_index)

                previous_space = False
                emitted = True

        if (
            not emitted
            and not decomposed
            and char.isspace()
        ):

            if chars and not previous_space:
                chars.append(" ")
                positions.append(original_index)

            previous_space = True

    while chars and chars[-1] == " ":
        chars.pop()
        positions.pop()

    return "".join(chars), positions


def _normalize(value: str):
    return _normalize_with_map(value)[0]


def search_names(
    pages: list[str],
    names: tuple[str, ...] | list[str],
    context_chars: int = 180,
):

    results = {
        name: []
        for name in names
    }

    for name in names:

        needle = _normalize(name).strip()

        if not needle:
            continue

        pattern = re.compile(
            r"(?<!\w)"
            + re.escape(needle)
            + r"(?!\w)",
            re.UNICODE,
        )

        for page_number, original_text in enumerate(
            pages,
            start=1,
        ):

            normalized_text, index_map = (
                _normalize_with_map(original_text)
            )

            ordinal = 0

            for match in pattern.finditer(
                normalized_text
            ):

                ordinal += 1

                start_norm, end_norm = match.span()

                start_original = index_map[start_norm]

                end_original = (
                    index_map[end_norm - 1] + 1
                )

                left = max(
                    0,
                    start_original - context_chars,
                )

                right = min(
                    len(original_text),
                    end_original + context_chars,
                )

                context = re.sub(
                    r"\s+",
                    " ",
                    original_text[left:right],
                ).strip()

                if left > 0:
                    context = "…" + context

                if right < len(original_text):
                    context += "…"

                results[name].append(
                    Occurrence(
                        name=name,
                        page=page_number,
                        context=context,
                        ordinal_on_page=ordinal,
                        normalized_position=start_norm,
                    )
                )

    return results