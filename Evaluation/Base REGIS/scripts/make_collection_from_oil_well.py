from .utils import is_acceptable_term, normalize_term


def extract_database_synonyms(data_path):
    database_synonyms = list()
    with open(data_path, "r", encoding="utf-8") as f:
        for row in f.read().split("\n"):
            synonyms = list()
            for term in row.split(";"):
                term = term.strip()
                if term != "":
                    synonyms.append(term.lower())
            database_synonyms.append(synonyms)
    return database_synonyms


def transform_to_mongodb_doc(list_of_synonyms, term_source, relation="SYN"):
    docs = dict()
    edges = set()
    for synonyms in list_of_synonyms:
        for term in synonyms:
            if not is_acceptable_term(term):
                continue

            if term not in docs.keys():
                docs[term] = {
                    "text": term,
                    "normalizedText": normalize_term(term),
                    "source": [term_source],
                    "terms": list(),
                }

        for term_i in synonyms:
            if not is_acceptable_term(term_i):
                continue
            for term_j in synonyms:
                if not is_acceptable_term(term_j):
                    continue
                doc_i = docs[term_i]
                doc_j = docs[term_j]
                edge = (doc_i["text"], doc_j["text"], relation)
                if doc_i != doc_j and edge not in edges:
                    doc_i["terms"].append(
                        {
                            "text": doc_j["text"],
                            "relation": relation,
                            "source": term_source,
                        }
                    )
                    edges.add(edge)

    return list(docs.values())


def make_collection_from_oil_well(
    data_filepath, term_source="ANP_WELL_TERMS"
) -> list[dict]:
    collection = transform_to_mongodb_doc(
        extract_database_synonyms(data_filepath), term_source
    )

    return collection
