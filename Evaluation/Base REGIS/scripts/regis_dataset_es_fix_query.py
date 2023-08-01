#encoding: utf-8

from pathlib import Path
import json
import re
import requests
import subprocess
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import pandas as pd
import yaml


class REGISHandler:
    def __init__(self):
        self.config_folder = Path("../conf")
        self.notebooks_folder = Path("../notebooks")
        self.data_folder = Path("../../dados/regis")
        self.output_folder = Path("../htmls/regis_analysis_fix_query")
        self.output_folder.mkdir(parents=True, exist_ok=True)

        with open(self.config_folder.joinpath("config.yaml"), "r") as yamlfile:
            cfg = yaml.safe_load(yamlfile)

        self.base_url = cfg["elasticsearch"]["url"]
        self.auth = HTTPBasicAuth(cfg["elasticsearch"]["username"], cfg["elasticsearch"]["password"])
        self.index = cfg["elasticsearch"]["index"]

        self.regis_queries_url = "https://raw.githubusercontent.com/Petroles/regis-collection/master/queries.xml"
        self.regis_queries = list()
        self.aqe_url = "http://buscasemantica.petrobras.com.br/QueryExpansionWS/servicos/query/aqe"
        self.search_ranking_filename = self.data_folder.joinpath("search_ranking.csv")

    def fix_expanded_query(self, expanded_query, join_operator):
        derivate_term_start = expanded_query.find("OR") + 3
        derivate_term = expanded_query[derivate_term_start: -1]

        pattern = re.compile("\^[0-1].[0-9]+")
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
    
    def change_weights(self, expanded_query, factor):
        pattern = re.compile("\^[0-1].[0-9]+")
        matches = list()
        start = 0
        while pattern.search(expanded_query, start) is not None:
            matches.append(pattern.search(expanded_query, start))
            start = matches[-1].end() + 1

        for m in reversed(matches):
            expanded_query = "{}{:.3f}{}".format(
                expanded_query[:m.start() + 1],
                float(expanded_query[m.start()+1:m.end()]) * factor,
                expanded_query[m.end():]
            )
        return expanded_query

    def expand_regis_query(self, query_title, factor, join_operator):
        response = requests.get(
            self.aqe_url,
            params={"q": query_title}
        )

        expanded_query = response.text.encode('cp1252').decode('utf-8').strip()

        if factor is not None:
            expanded_query = self.fix_expanded_query(expanded_query, join_operator)
            expanded_query = self.change_weights(expanded_query, factor)

        return expanded_query

    def get_regis_queries(self, query_expansion, factor, join_operator, regis_queries_filename="regis_queries.json"):
        filepath = self.data_folder.joinpath(regis_queries_filename)
        if filepath.exists():
            with open(filepath, 'r') as regis_file:
                self.regis_queries = json.load(regis_file)
        else:
            regis_github_response = requests.get(
                self.regis_queries_url,
            )
            regis_github_response.history
            tree = ET.fromstring(regis_github_response.content)
            for query in tree.findall("top"):
                title = query.find("title").text
                query_id = query.find("num").text

                self.regis_queries.append({
                    "title": title,
                    "query_id": query_id
                })

            with open(regis_queries_filename, 'w') as regis_file:
                json.dump(self.regis_queries, regis_file)
        
        if query_expansion:
            for query in self.regis_queries:
                query["title"] = self.expand_regis_query(query["title"], factor, join_operator)

    def retrieve_docs(self, query, size):
        res = requests.post(
            "{}/{}/_search".format(self.base_url, self.index),
            json=query,
            headers={"Content-Type": "application/json"},
            auth=self.auth,
            params={"size": size, "search_type": "dfs_query_then_fetch"}
        )
        try:
            docs = json.loads(res.text)["hits"]["hits"]
        except:
            print("Could not retrieve query: {}".format(query["query"]["query_string"]["query"]))
            docs = list()

        return [{"document_id": doc["_source"]["docid"], "relevance": doc["_score"]} for doc in docs]

    def regis_es_query(self, query_expansion, filename, size, factor, join_operator):
        self.get_regis_queries(query_expansion, factor, join_operator)

        ranking_result = list()
        for query in self.regis_queries:
            es_result = self.retrieve_docs({"query": {"query_string": {"query": query["title"], "default_field": "text"}}}, size)
            ranking_result.extend([{"query_id": query["query_id"]} | dict_result for dict_result in es_result])
        df = pd.DataFrame(ranking_result)
        df.to_csv(filename, index=False)

    def generate_report(self, query_expansion, size, factor, join_operator):
        self.regis_es_query(query_expansion, self.search_ranking_filename, size, factor, join_operator)

        expansion = "AQE" if query_expansion else "ES"
        num_docs = size
        factor_value = "None" if factor is None else factor

        output_filename = "métricas_de_ranking-{}-{}_docs-{}_factor-{}_join_operator.ipynb".format(expansion, num_docs, factor_value, join_operator)
        subprocess.call([
            "jupyter",
            "nbconvert",
            "--execute",
            "--to", "html",
            str(self.notebooks_folder.joinpath("ranking_metrics.ipynb")),
            "--output", self.output_folder.joinpath(output_filename)
        ])

        self.search_ranking_filename.unlink()


if __name__ == "__main__":
    rh = REGISHandler()

    params = [
        {"query_expansion": True, "size": 50, "factor": 2.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 2.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 2.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 1.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 1.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 1.0, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 0.9, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 0.9, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 0.9, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 0.75, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 0.75, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 0.75, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 0.5, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 0.5, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 0.5, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 0.25, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 0.25, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 0.25, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 0.1, "join_operator": "AND"},
        {"query_expansion": True, "size": 24, "factor": 0.1, "join_operator": "AND"},
        {"query_expansion": True, "size": 10, "factor": 0.1, "join_operator": "AND"},
        {"query_expansion": True, "size": 50, "factor": 2.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 2.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 2.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 1.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 1.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 1.0, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 0.9, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 0.9, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 0.9, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 0.75, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 0.75, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 0.75, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 0.5, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 0.5, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 0.5, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 0.25, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 0.25, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 0.25, "join_operator": "OR"},
        {"query_expansion": True, "size": 50, "factor": 0.1, "join_operator": "OR"},
        {"query_expansion": True, "size": 24, "factor": 0.1, "join_operator": "OR"},
        {"query_expansion": True, "size": 10, "factor": 0.1, "join_operator": "OR"},
    ]

    for param in params:
        rh.generate_report(**param)
