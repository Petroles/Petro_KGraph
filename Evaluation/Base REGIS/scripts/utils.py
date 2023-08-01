import unicodedata


def normalize_term(term):
    codes_to_replace = {"%28": "(", "%29": ")", "%26": "&", "%2F": "/", "+": " "}

    for k, v in codes_to_replace.items():
        term = term.replace(k, v)

    return "".join(
        c for c in unicodedata.normalize("NFD", term) if unicodedata.category(c) != "Mn"
    ).lower()


def is_acceptable_term(term: str) -> bool:
    if term.isnumeric():
        return False
    elif len(term) < 4:
        return False

    return True
