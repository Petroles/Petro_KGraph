import json
import os

import numpy as np
import pandas as pd
import pyswarms as ps
import requests
from pymongo import MongoClient, UpdateOne

from .utils import (
    create_metrics,
    create_ranking_dataset,
    retrieve_from_elasticsearch,
)

requests.packages.urllib3.util.connection.HAS_IPV6 = False


class AQEPSO:
    def __init__(
        self,
        params: dict[str, tuple[float, float]],
        relation_keys: list[str],
        source_keys: list[str],
        we_keys: list[str],
        train_queries: list[str],
        test_queries: list[str],
    ) -> None:
        self.params = sorted(params.keys())
        self.train_queries = train_queries
        self.test_queries = test_queries
        self.log_path = "pso_log.csv"

        x_min = np.array([params[p][0] for p in self.params])
        x_max = np.array([params[p][1] for p in self.params])
        self.bounds = (x_min, x_max)

        self.aqe_base_url = os.getenv("AQE_URL")
        with open("../data/regis_queries.json", "r") as json_file:
            self.regis_queries = json.loads(json_file.read())

        self.certificate_path = "../PetrobrasCARootCorporativa.crt"

        self.client = MongoClient(os.getenv("MONGO_CONNECT_STRING"))

        self.es_cfg = {
            "elasticsearch": {
                "url": os.getenv("ELASTIC_SEARCH_URL"),
                "index": os.getenv("ELASTIC_SEARCH_INDEX"),
                "username": os.getenv("ELASTIC_SEARCH_USERNAME"),
                "password": os.getenv("ELASTIC_SEARCH_PASSWORD"),
                "certificate": self.certificate_path,
            }
        }

        self.ground_truth = pd.read_csv("../data/regis_ground_truth.csv")

        self.relation_keys = relation_keys
        self.source_keys = source_keys
        self.we_keys = we_keys

    def __update_mongodb_config(
        self,
        params,
    ) -> None:
        relation_weights = {k: v for k, v in params.items() if k in self.relation_keys}
        source_weights = {k: v for k, v in params.items() if k in self.source_keys}
        word_embedding_config = {k: v for k, v in params.items() if k in self.we_keys}
        data_database = self.client[os.getenv("MONGO_DATABASE_NAME")]
        data_collection = data_database.get_collection(
            os.getenv("MONGO_CONFIG_COLLECTION_NAME")
        )

        update = {
            "$set": {
                f"skosConfig.relationWeights.{r}": v
                for r, v in relation_weights.items()
            }
            | {f"skosConfig.sourceWeights.{k}": v for k, v in source_weights.items()}
            | {f"wordEmbeddingConfig.{k}": v for k, v in word_embedding_config.items()}
        }

        data_collection.bulk_write([UpdateOne(filter={}, update=update)], ordered=False)

    def __query_aqe(self, max_expanded_terms) -> list[str]:
        expanded_queries = list()
        for query in self.regis_queries:
            query_title = query.get("title")
            query_id = query.get("query_id")
            url_query = (
                f"{self.aqe_base_url}?query={query_title}"
                f"&max_expanded_terms={max_expanded_terms}"
            )

            response = requests.get(url_query, verify=self.certificate_path)

            expanded_queries.append((query_id, response.text))
        return expanded_queries

    def __query_elasticsearch(self, expanded_queries):
        ranking = retrieve_from_elasticsearch(expanded_queries, self.es_cfg, 24)
        return ranking

    def __calculate_ndcg(self, ranking, ground_truth):
        ranking_dataset = create_ranking_dataset(ranking, ground_truth)
        ndcgs = create_metrics(ranking_dataset, groupby_columns=["query_id"])
        train_ndcg = ndcgs.query("query_id in @self.train_queries").ndcg.mean()
        test_ndcg = ndcgs.query("query_id in @self.test_queries").ndcg.mean()
        return train_ndcg, test_ndcg

    def __log_metrics(self, train_ndcg, test_ndcg, params):
        df = pd.DataFrame(
            {
                "train_ndcg": [train_ndcg],
                "test_ndcg": [test_ndcg],
                "params": [str(self.__formated_params(params))],
            }
        )
        df.to_csv(
            self.log_path,
            index=False,
            sep=";",
            mode="a",
            header=not os.path.exists(self.log_path),
        )

    def func(
        self,
        params_values,
        params_to_round=["max_expanded_terms", "defaultNumberOfExpansions"],
    ):
        params_values = params_values.tolist()
        for p in params_to_round:
            if p in self.params:
                p_terms_idx = self.params.index(p)
                params_values[p_terms_idx] = round(params_values[p_terms_idx])

        self.__update_mongo_with_params(params_values)
        try:
            self.params.index("max_expanded_terms")
            max_expanded_terms = params_values[p_terms_idx]
        except:
            max_expanded_terms = 5
        expanded_queries = self.__query_aqe(max_expanded_terms)
        ranking = self.__query_elasticsearch(expanded_queries)
        train_ndcg, test_ndcg = self.__calculate_ndcg(ranking, self.ground_truth)
        self.__log_metrics(train_ndcg, test_ndcg, params_values)
        return -train_ndcg

    def __get_ndcg(self, x):
        n_particles = x.shape[0]
        j = [self.func(x[i]) for i in range(n_particles)]
        return np.array(j)

    def __update_mongo_with_params(self, params):
        params_dict = self.__formated_params(params)
        self.__update_mongodb_config(
            {
                key: value
                for key, value in params_dict.items()
                if key != "max_expanded_terms"
            }
        )

    def __formated_params(self, params):
        return {self.params[i]: param for i, param in enumerate(params)}

    def execute_optimizer(
        self,
        iterations=1000,
        n_particles=100,
        options={"c1": 0.3, "c2": 0.3, "w": 0.9},
    ):
        self.optimizer = ps.single.GlobalBestPSO(
            n_particles=n_particles,
            dimensions=len(self.params),
            options=options,
            bounds=self.bounds,
        )
        self.iterations = iterations
        cost, pos = self.optimizer.optimize(self.__get_ndcg, self.iterations)

        best_params = self.__formated_params(pos)

        self.__update_mongo_with_params(pos)

        return -cost, best_params
