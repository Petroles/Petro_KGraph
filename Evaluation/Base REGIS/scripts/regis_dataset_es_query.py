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
        self.output_folder = Path("../htmls/regis_analysis")
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

    def remove_term_below_threshold(self, expanded_query, term_threshold):    
        pattern = re.compile("\^[0-1].[0-9]+")
        matches = list()
        start = 0
        while pattern.search(expanded_query, start) is not None:
            matches.append(pattern.search(expanded_query, start))
            start = matches[-1].end() + 1
        for m in reversed(matches):
            if float(expanded_query[m.start()+1:m.end()]) < term_threshold:
                slice_end = m.end()
                slice_beg = m.start()
                while expanded_query[slice_beg] != "(" and expanded_query[slice_beg:slice_beg+2] != " |":
                    slice_beg -= 1
                expanded_query = expanded_query[:slice_beg + 1] + expanded_query[slice_end:]
        
        expanded_query = re.sub("\| *\( *\)", "", expanded_query)
        expanded_query = re.sub("\( *\)", "", expanded_query)
        expanded_query = re.sub(" +", " ", expanded_query)
        expanded_query = re.sub(" *\( *", "(", expanded_query)
        expanded_query = re.sub(" *\) *", ")", expanded_query)

        return expanded_query

    def expand_regis_query(self, query_title, remove_weights, term_threshold):
        response = requests.get(
            self.aqe_url,
            params={"q": query_title}
        )

        expanded_query = response.text.encode('cp1252').decode('utf-8')
        expanded_query = expanded_query.replace("OR", "|")
        if term_threshold:
            expanded_query = self.remove_term_below_threshold(expanded_query, term_threshold)
        if remove_weights:
            expanded_query = re.sub("\^[0-1].[0-9]+", "", expanded_query)

        return expanded_query

    def get_regis_queries(self, query_expansion, remove_weights, term_threshold, regis_queries_filename="regis_queries.json"):
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
            for i, query in enumerate(self.regis_queries):
                query["title"] = self.expand_regis_query(query["title"], remove_weights, term_threshold)

    def retrieve_docs(self, query, size):
        print(query["query"]["query_string"]["query"])
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
            docs = list()

        return [{"document_id": doc["_source"]["docid"], "relevance": doc["_score"]} for doc in docs]

    def regis_es_query(self, query_expansion, filename, size, remove_weights, term_threshold):
        self.get_regis_queries(query_expansion, remove_weights, term_threshold)

        ranking_result = list()
        for query in self.regis_queries:
            es_result = self.retrieve_docs({"query": {"query_string": {"query": query["title"], "default_field": "text"}}}, size)
            ranking_result.extend([{"query_id": query["query_id"]} | dict_result for dict_result in es_result])
        df = pd.DataFrame(ranking_result)
        df.to_csv(filename, index=False)

    def generate_report(self, query_expansion, size, remove_weights, term_threshold):
        self.regis_es_query(query_expansion, self.search_ranking_filename, size, remove_weights, term_threshold)

        expansion = "AQE" if query_expansion else "ES"
        num_docs = size
        thresh = "none" if term_threshold is None else int(term_threshold * 100)
        weights = "no_weights" if remove_weights else "with_weights"

        output_filename = "métricas_de_ranking-{}-{}_docs-{}_thresh_{}.ipynb".format(expansion, num_docs, thresh, weights)
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
        {"query_expansion": False, "size": 50, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 50, "remove_weights": True, "term_threshold": .8},
        {"query_expansion": True, "size": 50, "remove_weights": True, "term_threshold": .7},
        {"query_expansion": True, "size": 50, "remove_weights": True, "term_threshold": .5},
        {"query_expansion": True, "size": 50, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 50, "remove_weights": False, "term_threshold": None},
        {"query_expansion": False, "size": 24, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 24, "remove_weights": True, "term_threshold": .8},
        {"query_expansion": True, "size": 24, "remove_weights": True, "term_threshold": .7},
        {"query_expansion": True, "size": 24, "remove_weights": True, "term_threshold": .5},
        {"query_expansion": True, "size": 24, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 24, "remove_weights": False, "term_threshold": None},
        {"query_expansion": False, "size": 10, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 10, "remove_weights": True, "term_threshold": .8},
        {"query_expansion": True, "size": 10, "remove_weights": True, "term_threshold": .7},
        {"query_expansion": True, "size": 10, "remove_weights": True, "term_threshold": .5},
        {"query_expansion": True, "size": 10, "remove_weights": True, "term_threshold": None},
        {"query_expansion": True, "size": 10, "remove_weights": False, "term_threshold": None},
    ]

    for param in params:
        rh.generate_report(**param)
