from src.name_search import search_names


def test_case_and_accents():

    result = search_names(
        [
            "JOÃO DA SILVA foi citado.",
            "Joao da Silva novamente.",
        ],
        ["João da Silva"],
    )

    assert len(result["João da Silva"]) == 2


def test_compound_name_and_word_boundaries():

    result = search_names(
        [
            "Ana aparece; Mariana não deve corresponder a Ana."
        ],
        ["Ana"],
    )

    assert len(result["Ana"]) == 2


def test_page_and_context():

    result = search_names(
        [
            "Página sem ocorrência.",
            "Nome: Maria de Souza, matrícula 123.",
        ],
        ["Maria de Souza"],
    )

    assert result["Maria de Souza"][0].page == 2

    assert (
        "matrícula 123"
        in result["Maria de Souza"][0].context
    )


def test_whitespace_variations():

    result = search_names(
        ["José   da\nSilva"],
        ["José da Silva"],
    )

    assert len(result["José da Silva"]) == 1