import json
import os

from .make_collection_from_oil_well import make_collection_from_oil_well
from .make_collection_from_skos import make_collection_from_skos

from conf.config import settings


def make_individuals_collections():
    skos_filepath = os.path.join(settings.DATA_DIR, settings.SKOS_FILENAME)
    oi_well_filepath = os.path.join(settings.DATA_DIR, settings.OIL_WELL_FILENAME)

    skos_collection = make_collection_from_skos(
        skos_filepath, term_source="TULSA_THESAURUS"
    )

    oil_well_collection = make_collection_from_oil_well(
        oi_well_filepath, term_source="ANP_WELL_TERMS"
    )

    return (skos_collection, oil_well_collection)


def merge_collections():
    merged_collections = []

    skos_collection, oil_well_collection = make_individuals_collections()

    oil_well_collection = {
        document["text"]: document for document in oil_well_collection
    }
    skos_collection = {document["text"]: document for document in skos_collection}

    for term, document in oil_well_collection.items():
        if term in skos_collection:
            document["source"].extend(skos_collection[term]["source"])
            document["terms"].extend(skos_collection[term]["terms"])
            del skos_collection[term]

        merged_collections.append(document)

    merged_collections.extend([document for document in skos_collection.values()])

    return merged_collections


def generate_collection_file(
    merged_collections: list[dict], file_name: str = settings.MERGED_COLLECTION_FILENAME
):
    with open(f"{settings.DATA_DIR}/{file_name}", "w", encoding="utf8") as json_file:
        json.dump(merged_collections, json_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    merged_collections = merge_collections()
    generate_collection_file(merged_collections)
