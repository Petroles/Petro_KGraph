from rdflib import Graph, Literal, URIRef
from .utils import is_acceptable_term, normalize_term


def make_collection_from_skos(skos_filepath, term_source="TULSA_THESAURUS"):
    try:
        graph = Graph()
        graph.parse(skos_filepath)

        collection = []
        subjects = graph.subjects(unique=True)

        while True:
            subject = next(subjects)

            if not is_acceptable_term(subject.fragment):
                continue

            terms, alt_objects, term_language = make_terms_relationship(graph, subject)

            term_from_subject = normalize_term(subject.fragment)

            term_structure = {
                "text": term_from_subject,
                "normalizedText": normalize_term(term_from_subject),
                "source": [term_source],
                "language": term_language,
                "terms": terms,
            }

            collection.append(term_structure)
            add_altlabels_to_collection(
                collection, alt_objects, term_from_subject, term_language
            )

    except StopIteration:
        return collection


def make_terms_relationship(
    graph: Graph, subject: URIRef, term_source="TULSA_THESAURUS"
):
    terms = []
    alt_objects = []

    for predicate, obj in graph.predicate_objects(subject=subject):
        if predicate.fragment in ["type", "historyNote", "versionInfo"]:
            continue

        if isinstance(obj, URIRef):
            relationship = {
                "text": normalize_term(obj.fragment),
                "relation": get_relation_type(predicate),
                "source": term_source,
            }

        elif isinstance(obj, Literal):
            term_relation = get_relation_type(predicate)

            relationship = {
                "text": obj.value.lower(),
                "relation": term_relation,
                "language": obj.language,
                "source": term_source,
            }

            if term_relation == "SYN":
                term_language = get_term_language(subject, obj)

        if predicate.fragment == "altLabel":
            alt_objects.append(obj)

        terms.append(relationship)

    return terms, alt_objects, term_language


def get_term_language(subject: URIRef, obj: Literal) -> str | None:
    term_text = subject.fragment.replace("+", " ")
    term_language = None

    if term_text == obj.value:
        term_language = obj.language

    return term_language


def get_relation_type(predicate: URIRef) -> str:
    relations_type = {
        "related": "RT",
        "narrower": "NT",
        "broader": "BT",
        "prefLabel": "SYN",
        "altLabel": "AT",
    }

    relation_type = relations_type[predicate.fragment]

    return relation_type


def add_altlabels_to_collection(
    collection: list[dict],
    alt_objects: list[Literal],
    subject_term: str,
    term_language: str,
    term_source="TULSA_THESAURUS",
) -> list[dict]:
    relationship = {
        "text": subject_term,
        "relation": "AT",
        "language": term_language,
        "source": term_source,
    }

    for obj in alt_objects:
        term_structure = {
            "text": normalize_term(obj.value),
            "source": [term_source],
            "normalizedText": normalize_term(obj.value),
            "terms": [relationship],
        }
        collection.append(term_structure)

    return collection
