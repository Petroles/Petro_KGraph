import re
import random

import json
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from sklearn.metrics import ndcg_score, average_precision_score


def fix_expanded_query(expanded_query, join_operator="OR"):
    derivate_term_start = expanded_query.find("OR") + 3
    derivate_term = expanded_query[derivate_term_start: -1]

    pattern = re.compile("\^[0-1].[0-9]{3}")
    weights_matches = list()
    start = 0
    while pattern.search(derivate_term, start) is not None:
        weights_matches.append(pattern.search(derivate_term, start))
        start = weights_matches[-1].end() + 1

    for i in range(len(weights_matches) - 1, 0, -1):
        start = weights_matches[i - 1].end()
        end = weights_matches[i].start()

        partial_term = derivate_term[start: end]
        if "OR" not in partial_term and join_operator not in partial_term:
            for i, c in enumerate(partial_term):
                if c == '(' or c == '"' or c.isalpha():
                    break
            partial_term = partial_term[:i - 1] + join_operator + partial_term[i - 1:]
            derivate_term = derivate_term[:start] + partial_term + derivate_term[end:]
    
    expanded_query = expanded_query[:derivate_term_start] + derivate_term + ")"
    expanded_query = re.sub(" +", " ", expanded_query)

    return expanded_query


def get_expanded_queries(regis_queries):
    for query in regis_queries:
        response = requests.get(
            "http://buscasemantica.petrobras.com.br/QueryExpansionWS/servicos/query/aqe",
            params={"q": query["title"]}
        )

        expanded_query = response.text.encode('cp1252').decode('utf-8').strip()
        expanded_query = fix_expanded_query(expanded_query)
        query["expanded_query"] = expanded_query
    return regis_queries


def adjust_weights_to_database(expanded_query, database_terms, factor):
    pattern = re.compile("\^[0-1].[0-9]{3}")
    matches = list()
    start = 0
    while pattern.search(expanded_query, start) is not None:
        matches.append(pattern.search(expanded_query, start))
        start = matches[-1].end() + 1

    for m in reversed(matches):
        term_end = m.start()
        term_start = m.start()
        found_quote = False
        while (expanded_query[term_start] != "(" and
               expanded_query[term_start-2:term_start] != "OR" and
               (expanded_query[term_start] != '"' or not found_quote)):
            if expanded_query[term_start] == '"':
                found_quote = True
            term_start -= 1
        term = expanded_query[term_start+1:term_end].strip().strip('"')

        shall_boost = 1
        if term.lower() not in database_terms:
            shall_boost = 0

        expanded_query = "{}{:.3f}{}".format(
            expanded_query[:m.start() + 1],
            float(expanded_query[m.start()+1:m.end()]) * factor * shall_boost,
            expanded_query[m.end():]
        )

    return expanded_query


def get_databases_queries(databases, regis_queries, factors):
    databases_queries = dict()

    for db_name, db_values in databases.items():
        databases_queries[db_name] = list()
        for query in regis_queries:
            for factor in factors:
                q = query.copy()
                databases_queries[db_name].append(q)
                db_query = adjust_weights_to_database(q["expanded_query"], db_values, factor=factor)
                databases_queries[db_name][-1]["expanded_query"] = {"text": db_query, "factor": factor}
    return databases_queries


def retrieve_docs(query, size, cfg):
    res = requests.post(
        "{}/{}/_search".format(cfg["elasticsearch"]["url"], cfg["elasticsearch"]["index"]),
        json=query,
        headers={"Content-Type": "application/json"},
        auth=HTTPBasicAuth(cfg["elasticsearch"]["username"], cfg["elasticsearch"]["password"]),
        params={"size": size, "search_type": "dfs_query_then_fetch"},
        verify=cfg["elasticsearch"]["certificate"]
    )
    try:
        docs = json.loads(res.text)["hits"]["hits"]
    except:
        docs = list()

    return [{"document_id": doc["_source"]["docid"], "relevance_ranking": doc["_score"]} for doc in docs]


def make_elasticsearch_queries(databases_queries, cfg, num_docs):
    ranking_result = list()
    for db_name, db_queries in databases_queries.items():
        print("Started querying database {}".format(db_name))
        for query in db_queries:
            es_result = retrieve_docs({"query": {"query_string": {"query": query["expanded_query"]["text"], "default_field": "text"}}}, num_docs, cfg)
            ranking_result.extend([{"database_name": db_name, "query_id": query["query_id"], "factor": query["expanded_query"]["factor"]} | dict_result for dict_result in es_result])
    ranking_result_df = pd.DataFrame(ranking_result)
    return ranking_result_df

def retrieve_from_elasticsearch(queries, cfg, num_docs):
    ranking_result = list()
    for query_id, query in queries:
        es_query = {
            "query": {
                "query_string": {
                    "query": query,
                    "default_field": "text",
                }
            }
        }
        es_result = retrieve_docs(es_query, num_docs, cfg)
        ranking_result.extend(
            [
                {
                    "query_id": query_id,
                }
                | dict_result
                for dict_result in es_result
            ]
        )

    ranking_result_df = pd.DataFrame(ranking_result)

    return ranking_result_df


def create_ranking_dataset(ranking_result_df, ground_truth):
    ranking_dataset = ranking_result_df.merge(
        ground_truth,
        on=["query_id", "document_id"],
        how="outer"
    ).rename(
        columns={"relevance": "relevance_ground_truth"}
    ).assign(
        evaluated = lambda row: row.relevance_ground_truth.notnull(),
        irrelevant_ground_truth = lambda row: (
            (row.relevance_ranking.isnull()) & (row.relevance_ground_truth == 0)
        ),
    ).query(
            "irrelevant_ground_truth == False"
    ).fillna(
        value={
            "relevance_ranking": 0,
            "relevance_ground_truth": 0,
        }
    ).drop(
        columns="irrelevant_ground_truth"
    )

    return ranking_dataset


def create_metrics(
    validation_dataset,
    groupby_columns=["database_name", "query_id", "factor"],
    thresh=1
):
    metrics_df = validation_dataset.groupby(
        groupby_columns
    ).apply(
        lambda row: (
            ndcg_score([row["relevance_ground_truth"]], [row["relevance_ranking"]]),
            average_precision_score(
                [0 if r <= thresh else 1 for r in row["relevance_ground_truth"]],
                row["relevance_ranking"]
            ),
            row["evaluated"].sum() / row["evaluated"].count()
        )
    ).reset_index(
        name="metrics"
    ).assign(
        ndcg = lambda row: row["metrics"].str[0],
        ap = lambda row: row["metrics"].str[1],
        eval_prop = lambda row: row["metrics"].str[2]
    ).drop(
        columns="metrics"
    )

    return metrics_df


def create_validation_dataset(ranking_result_df, ground_truth):
    validation_dataset = list()
    for db_name in ranking_result_df["database_name"].unique():
        for factor in ranking_result_df["factor"].unique():
            df = ranking_result_df.query(
                "database_name == @db_name and factor == @factor"
            ).merge(
                ground_truth,
                on=["query_id", "document_id"],
                suffixes=("_ranking", "_ground_truth"),
                how="outer"
            ).assign(
                evaluated = lambda row: row.relevance_ground_truth.notnull(),
                irrelevant_ground_truth = lambda row: (row.relevance_ranking.isnull()) & (row.relevance_ground_truth == 0),
            ).query(
                "irrelevant_ground_truth == False"
            ).fillna(
                value={
                    "relevance_ranking": 0,
                    "relevance_ground_truth": 0,
                    "database_name": db_name,
                    "factor": factor
                }
            ).drop(
                columns="irrelevant_ground_truth"
            )

            validation_dataset.append(df)

    validation_dataset = pd.concat(validation_dataset).reset_index(drop=True)
    return validation_dataset


def new_adjust_boost_factors(expanded_query, databases, databases_factors, multiply):
    pattern = re.compile("\^[0-1].[0-9]{3}")
    matches = list()
    start = 0
    while pattern.search(expanded_query, start) is not None:
        matches.append(pattern.search(expanded_query, start))
        start = matches[-1].end() + 1

    for m in reversed(matches):
        term_end = m.start()
        term_start = m.start()
        found_quote = False
        while (expanded_query[term_start] != "(" and
               expanded_query[term_start-2:term_start] != "OR" and
               (expanded_query[term_start] != '"' or not found_quote)):
            if expanded_query[term_start] == '"':
                found_quote = True
            term_start -= 1
        term = expanded_query[term_start+1:term_end].strip().strip('"')

        boost_factor = 0
        for db_name, database_terms in databases.items():
            if term.lower() in database_terms and (boost_factor == 0 or databases_factors[db_name] <= boost_factor):
                boost_factor = databases_factors[db_name]

        if multiply:
            boost_factor *= float(expanded_query[m.start()+1:m.end()])

        expanded_query = "{}{:.3f}{}".format(
            expanded_query[:m.start() + 1],
            boost_factor,
            expanded_query[m.end():]
        )

    return expanded_query


def adjust_new_expanded_queries(databases, regis_queries, databases_factors, multiply=True):
    new_expanded_queries = list()
    for query in regis_queries:
        q = query.copy()
        q["expanded_query"] = new_adjust_boost_factors(
            q["expanded_query"],
            databases,
            databases_factors,
            multiply
        )
        new_expanded_queries.append(q)
    return new_expanded_queries


def make_elasticsearch_new_queries(new_expanded_queries, cfg, num_docs):
    ranking_result = list()
    for query in new_expanded_queries:
        es_result = retrieve_docs({"query": {"query_string": {"query": query["expanded_query"], "default_field": "text"}}}, num_docs, cfg)
        ranking_result.extend([{"query_id": query["query_id"]} | dict_result for dict_result in es_result])
    ranking_result_df = pd.DataFrame(ranking_result)
    return ranking_result_df


def create_new_validation_dataset(ranking_result_df, ground_truth):
    validation_dataset = ranking_result_df.merge(
        ground_truth,
        on=["query_id", "document_id"],
        suffixes=("_ranking", "_ground_truth"),
        how="outer"
    ).assign(
        evaluated = lambda row: row.relevance_ground_truth.notnull(),
        irrelevant_ground_truth = lambda row: (row.relevance_ranking.isnull()) & (row.relevance_ground_truth == 0),
    ).query(
        "irrelevant_ground_truth == False"
    ).fillna(
        value={
            "relevance_ranking": 0,
            "relevance_ground_truth": 0,
        }
    ).drop(
        columns="irrelevant_ground_truth"
    )

    return validation_dataset


def create_new_metrics(validation_dataset, thresh=1):
    metrics_df = validation_dataset.groupby(
        "query_id"
    ).apply(
        lambda row: (
            ndcg_score([row["relevance_ground_truth"]], [row["relevance_ranking"]]),
            average_precision_score(
                [0 if r <= thresh else 1 for r in row["relevance_ground_truth"]],
                row["relevance_ranking"]
            ),
            row["evaluated"].sum() / row["evaluated"].count()
        )
    ).reset_index(
        name="metrics"
    ).assign(
        ndcg = lambda row: row["metrics"].str[0],
        ap = lambda row: row["metrics"].str[1],
        eval_prop = lambda row: row["metrics"].str[2]
    ).drop(
        columns="metrics"
    ).rename(
        columns={"ndcg": "ndcg@24", "ap": "ap@24"}
    )

    return metrics_df


def check_max_boosts(expanded_terms, terms_start_end):
    max_boosts = 0
    for start, end in terms_start_end:
        derivate_term = expanded_terms[start: end]
        boost_matches = [match for match in re.finditer(r"\^[0-1].[0-9]{3}", derivate_term)]
        max_boosts = max(max_boosts, len(boost_matches))
    return max_boosts


def make_variations(expanded_terms, terms_start_end, num_termos, zero_factor, replace_factor, seed=42):
    random.seed(seed)
    new_expanded_terms = expanded_terms
    for start, end in terms_start_end:
        derivate_term = expanded_terms[start: end]
        derivate_term = re.sub(r"[0-1].[0-9]{3}", zero_factor, derivate_term)
        boost_matches = [match for match in re.finditer(zero_factor, derivate_term)]
        if num_termos > len(boost_matches):
            sample_boosts = boost_matches
        else:
            sample_boosts = random.sample(boost_matches, num_termos)
        for boost in sample_boosts:
            derivate_term = derivate_term[:boost.start()] + replace_factor + derivate_term[boost.end():]
        new_expanded_terms = new_expanded_terms[:start] + derivate_term + new_expanded_terms[end:]
    return new_expanded_terms        


def create_new_expanded_queries(expanded_query, expansion=make_variations, factor="0.100", num_termos=None):
    expanded_terms_start = expanded_query.find("OR") + 4
    expanded_terms = expanded_query[expanded_terms_start:-1].strip()[:-1]
    terms_start_end = list()
    expanded_query_idx = 0
    while expanded_query_idx < len(expanded_terms):
        if expanded_terms[expanded_query_idx] == "(":
            next_expanded_query_idx = re.search(r"\) OR", expanded_terms[expanded_query_idx:])
        elif expanded_terms[expanded_query_idx] == "\"":
            next_expanded_query_idx = re.search(r"\"(\^[0-1].[0-9]{3})? OR", expanded_terms[expanded_query_idx:])
        else:
            next_expanded_query_idx = re.search(r"OR", expanded_terms[expanded_query_idx:])
        
        if next_expanded_query_idx is None:
            next_expanded_query_idx = len(expanded_terms)
        else:
            next_expanded_query_idx = next_expanded_query_idx.end() + 1
        terms_start_end.append((expanded_query_idx, expanded_query_idx + next_expanded_query_idx))
        expanded_query_idx += next_expanded_query_idx

    new_expanded_queries = list()
    if num_termos is None:
        num_termos = range(check_max_boosts(expanded_terms, terms_start_end) + 1)
    for i in num_termos:
        new_expanded_queries.append(
            (
                i,
                "{}{}{}".format(
                    expanded_query[:expanded_terms_start],
                    expansion(expanded_terms, terms_start_end, i, "0.000", factor),
                    "))"
                )
            )
        )

    return new_expanded_queries


def make_elasticsearch_new_aqe_queries(new_expanded_queries, cfg, num_docs, attrs=["query_id", "num_termos"]):
    ranking_result = list()
    for query in new_expanded_queries:
        es_result = retrieve_docs({"query": {"query_string": {"query": query["expanded_query"], "default_field": "text"}}}, num_docs, cfg)
        ranking_result.extend([{attr: query[attr] for attr in attrs} | dict_result for dict_result in es_result])
    ranking_result_df = pd.DataFrame(ranking_result)
    return ranking_result_df


def create_new_aqe_validation_dataset(ranking_result_df, ground_truth, boost_cols=["num_termos"]):
    ground_truth_combinations = ranking_result_df.filter(
        items=["query_id"] + boost_cols
    ).drop_duplicates(
    ).reset_index(
        drop=True
    ).merge(
        ground_truth,
        on="query_id",
        how="left"
    )

    return ranking_result_df.merge(
        ground_truth_combinations,
        on=["query_id", "document_id"] + boost_cols,
        how="outer"
    ).assign(
        evaluated = lambda row: row.relevance_ground_truth.notnull(),
        irrelevant_ground_truth = lambda row: (row.relevance_ranking.isnull()) & (row.relevance_ground_truth == 0),
    ).query(
        "irrelevant_ground_truth == False"
    ).fillna(
        value={
            "relevance_ranking": 0,
            "relevance_ground_truth": 0,
        }
    ).drop(
        columns="irrelevant_ground_truth"
    ).reset_index(drop=True)


def create_new_aqe_metrics(validation_dataset, thresh=1, boost_cols=["num_termos"]):
    metrics_df = validation_dataset.groupby(
        ["query_id"] + boost_cols
    ).apply(
        lambda row: (
            ndcg_score([row["relevance_ground_truth"]], [row["relevance_ranking"]]),
            average_precision_score(
                [0 if r <= thresh else 1 for r in row["relevance_ground_truth"]],
                row["relevance_ranking"]
            ),
            row["evaluated"].sum() / row["evaluated"].count()
        )
    ).reset_index(
        name="metrics"
    ).assign(
        ndcg = lambda row: row["metrics"].str[0],
        ap = lambda row: row["metrics"].str[1],
        eval_prop = lambda row: row["metrics"].str[2]
    ).drop(
        columns="metrics"
    ).rename(
        columns={"ndcg": "ndcg@24", "ap": "ap@24"}
    )

    return metrics_df


def expanded_with_aqe_order(expanded_terms, terms_start_end, num_termos, zero_factor, replace_factor):
    new_expanded_terms = expanded_terms
    for start, end in terms_start_end:
        derivate_term = expanded_terms[start: end]
        boost_matches = [match for match in re.finditer(r"[0-1].[0-9]{3}", derivate_term)]
        
        for i, boost in enumerate(boost_matches):
            to_replace = replace_factor if i < num_termos else zero_factor
            derivate_term = derivate_term[:boost.start()] + to_replace + derivate_term[boost.end():]
        new_expanded_terms = new_expanded_terms[:start] + derivate_term + new_expanded_terms[end:]
    return new_expanded_terms  


def expanded_with_aqe_boost_order(expanded_terms, terms_start_end, num_termos, zero_factor, replace_factor):
    new_expanded_terms = expanded_terms
    for start, end in terms_start_end:
        derivate_term = expanded_terms[start: end]
        boost_matches = [match for match in re.finditer(r"[0-1].[0-9]{3}", derivate_term)]
        boost_matches = sorted(boost_matches, reverse=True, key=lambda m: float(m.group(0)))
        
        for i, boost in enumerate(boost_matches):
            if replace_factor is None:
                to_replace = boost.group(0) if i < num_termos else zero_factor
            else:
                to_replace = replace_factor if i < num_termos else zero_factor
            derivate_term = derivate_term[:boost.start()] + to_replace + derivate_term[boost.end():]
        new_expanded_terms = new_expanded_terms[:start] + derivate_term + new_expanded_terms[end:]
    return new_expanded_terms
