# Petro_KGraph
 Repositório da pesquisa de doutorado "Petro KGraph: a methodology for extracting knowledge graph from technical documents - an application in a corpus from the oil and gas industry." por Fábio Corrêa Cordeiro.
 
 
# Passo a passo para replicar o trabalho desenvolvido na tese:

### Verificar se os Knowledge Graphs estão no repositórios
1. Os knowledge graphs devem estar nas pastas Petro_KGraph/KnowledgeGraph. A Petro KGraph Ontology (a ontologia básica antes de ser povoada) deve ser nomeada como OntoGeoLogicaEntidadesNomeadas.owl, já o Petro KGraph parcialmente povoado com as listas estruturadas (mas ainda sem ser povoada com as informações extraídas do texto) deve ser nomeada como OntoGeoLogicaInstanciasRelacoes.owl
(Essa é a versão NP1, revisar o passo a passo com a versão pública que está em Petro_KGraph/KnowledgeGraph/resources/dados_publicos/OntoGeoLogicaANPInstanciasRelacoes.owl)

### Treinar PetroOntoVec
2. Verificar ser os modelos PetroVec que serão usados para inicializar o treinamento do PetroOntoVec estão disponíveis na pasta Petro_KGraph/Embeddings/PetroVec/Petrovec-XXXXXXX-100. Dentro dessa pasta devem estar três arquivos. Ex: "publico-COMPLETO-100.txt.model", "publico-COMPLETO-100.txt.model.trainables.syn1neg.npy", "publico-COMPLETO-100.txt.model.wv.vectors.npy".
3. **(Atenção - Esse treinamento pode demorar cerca de 24h)** Treinar o modelo PetroOntoVec. Os hiperparâmetros necessários para rodar o algoritimo devem ser colocados no arquivo Petro_KGraph/Embeddings/PetroOntoVec/default.cfg e o script rodados via linha de comando. As instruções de quais parâmetros usar e como rodar o script está no notebook Petro_KGraph/Embeddings/PetroOntoVec/Train_PetroOntoVec.ipynb (Se desejável, o script pode ser rodado usando o notebook)
4. O modelos será gravado na pasta Petro_KGraph/Embeddings/PetroOntoVec/cache. Alterar o nome da pasta para Petro_KGraph/Embeddings/PetroOntoVec/PetroOntoVec_xxxxxxxxxxx (O nome da pasta pode ser configurado no arquivo default.cfg, mas para evitar que versões anteriores sejam sobrescritas por engano, estamos nomeando manualmente ao final do treinamento)
5. Caso deseje visualizar os vetores usando o Tensorflow embedding projector, usar o notebook Petro_KGraph/Embeddings/PetroOntoVec/Visualizing OWL2Vec.ipynb para adaptar os vetores ao formato adequado.
6. No notebook Petro_KGraph/Embeddings/Evaluation/IntrinsicEvaluation.ipynb, é possível rodar a avaliação intrínseca implementada por D. da S. M. Gomes et al., “Portuguese word embeddings for the oil and gas industry: Development and evaluation”, Computers in Industry, vol. 124, p. 103347, jan. 2021, doi: 10.1016/j.compind.2020.103347.
 
### Processando corpus PetroNER
7. Verificar se o corpus anotado com entidades e instâncias no formato Conllu está disponível no seguinte caminho: Petro_KGraph/Corpora/PetroNER/petroner-uri-AAAA-MM-DD.conllu
8. Rodar o notebook Petro_KGraph/Corpora/PetroNER/Separando treino-valid-teste.ipynb para separar o corpus anotado em treino-validação-teste. A definição das sentenças que vão para cada dataset está "hard coded" no notebook, mas foi feita com base no arquivo KGraph/Corpora/PetroNER/PetroNER - Treino-Teste.xlsx.
9. O notebook anterior criará três novos corpora na mesma pasta: petroner-uri-treino.conllu, petroner-uri-validação.conllu, petroner-uri-teste.conllu
10. Foram feitas duas anotações do PetroNER, uma com materiais públicos (com textos dos Boletins de Geociências) e outra com documentos NP1. A anotação pública está completa, com anotação de dependência sintática, POS, classe e URI das entidades anotadas. Já a anotação pública não tem anotação das URI, o que impossibilita usá-la para as tarefas de entity linking e extração de relações. Nessa etapa, copiamos e colamos os arquivos petroner-uri-treino.conllu e np1-ner-golden-2023-07-11.conllu em um mesmo arquivo chamado petroner-uri-treino - publico e np1.conllu.
11. Rodar o notebook Petro_KGraph/Corpora/PetroNER/Analisando e adaptando PetroNER.ipynb. Esse notebook prepara os datasets que serão usados nas tarefas de entity linking e clustering além de gerar análises e estatísticas dos datasets. Os novos datasets são gravados na pasta KGraph/Corpora/PetroNER-LinkedEntity, são listas de sentenças (já processadas para serem usadas no treinamento), entidades, classes, e URI, todos divididos em PetroNER (corpus completo), treino, validação, e teste.

### Criando dataset para clustering
12. Rodar o notebook Petro_KGraph/Corpora/PetroNER - Clustering/Triplet dataset.ipynb. Esse notebook cria o dataset para ser usado no contrastive learning (um exemplo âncora, um positivo e outro negativo). Os datasets são gravados na mesma pasta Petro_KGraph/Corpora/PetroNER - Clustering.

### Criando Relation Extraction dataset usando distant supervision
13. Rodar o notebook Petro_KGraph/Corpora/PetroRE/Filter_Conllu_URIs_notebook.ipynb para filtrar apenas as sentenças que possuem pelo menos 2 URIs anotadas. Esse notebook salva os arquivos df_filtred_petroner_uri_xxxxxxxxxxxx na mesma pasta.
14. **(Atenção - Essa extração pode demorar várias horas)** Rodar notebook ProcessFiltered_Conllu_URIs_notebook.ipynb para criar o dataset para Relation Extraction. Esse notebook salva os arquivos necessários para o treinamento do modelo na mesma pasta (df_bert_sentences_XXXX.csv, df_relation_xxxxxxx, lista_classe_xxxxx, lista_relacoes_xxxxx, lista_uris_xxxxx), além dos arquivos JSON para usar no label studio nas pastas Petro_KGraph/Corpora/PetroRE/JSONs_XXXXX. 

### Criando os Petro KGraph Golden
15. Rodar o notebook Petro_KGraph/KnowledgeGraph/Train-valid-test/Split ontology.ipynb. Com base nos datasets PetroNER separados em treino-validação-teste, esse notebook irá criar os grafos golden que serão referência na avaliação do povoamento dos knowledge graphs (PetroKGraph_treino, PetroKGraph_valid, PetroKGraph_teste).
16. O Notebook Petro_KGraph/KnowledgeGraph/Train-valid-test/Análise Ontologia.ipynb, levanta a quantidade de indivíduos, classes e labels na ontologia parcialmente povoada.

## Treinar modelos
### Treinar o modelo de Named Entity Recognition
17. Rodar o notebook Petro_KGraph/Model/Named Entity Recognition/training NER.ipynb. Esse notebook irá usar o dataset "petroner-uri-treino.conllu" para treinar o modelo de NER que será salvo como Petro_KGraph/Model/Named Entity Recognition/Model_NER.h5 (O código elaborado pela PUC está na pasta Petro_KGraph/Model/Named Entity Recognition (PUC))

### Treinar Entity Linking 
(avaliar se essa etapa será realizada)(Essa etapa treina um modelo apenas para o entity link, sem a clusterização)
18. Rodar notebook Petro_KGraph/Model/Entity Linking/Training Entity Linking model.ipynb para treinar o modelo de entitiy link. O modelo será salvo na mesma pasta como "Sentence2PetroOntoVec".

(Essa etapa treina um mesmo modelo para fazer o entity link e a clusterização)
18. Rodar o notebook Petro_KGraph/Model/Instances clustering/Training Instances Clustering model.ipynb para treinar o modelo de entitiy link. O modelo será salvo na mesma pasta como "Sentence2PetroOntoVec_clustering". A memória de cálculo dos parâmetros do BDM está na planilha Petro_KGraph\Evaluation\Prâmetros para cálculo do BDM.xlsx

### Treinar Relation Extraction
19. Rodar o notebook Petro_KGraph/Model/Relation Extraction/Training RE.ipynb para treinar o modelo de Extração de Entidades. O modelo será salvo na mesma pasta como "Model_RE.h5".


## Avaliação

### Avaliar a extração de Knowledge Graph do texto
20. Nas etapas de treinamento dos modelos, os datasets de avaliação foram usados isoladamente para avaliar a performance de cada modelo. Nesta etapa, avaliamos a performance do pipeline completo, portanto usamos o PetroNER de teste por todo o ciclo de predição. Devemos verificar se o arquivo 'petroner-uri-teste.conllu' está na pasta "Petro_KGraph/Corpora/Predicao - avaliação/Documentos_conllu/"

21. Rodar o Notebook Petro_KGraph/Model/Prediction/Prediction_NER.ipynb para realizar a predição do NER dos documentos novos. Para cada arquivo da pasta "Petro_KGraph/Corpora/Predicao - avaliação/Documentos_conllu/", será criado um arquivo em formato JSON na pasta "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_json/". Os arquivos json contém o resultado da predição do NER, mas já está pronto para receber a predição dos modelos subequentes.

22. Rodar o Notebook Petro_KGraph/Model/Prediction/Prediction_Entity_Linking.ipynb para linkar as entidades identificadas às URI do PetroOntoVec. Quando encontramos uma URI no PetroOntoVec, essa URI é salva no campo 'Grafo', se não for econtrada, o vetor inferido é gravado no campo 'Embedding' para posterior clusterização. As informações são salvas nos arquivos JSON na pasta "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_json/".

23. Rodar o Notebook Notebook Petro_KGraph/Model/Prediction/Clustering_new_entities.ipynb para identificar entidades que não estão no PetroKGraph mas que foram encontradas nos textos. O Notebook atualiza os JSONs da pasta "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_json/". As informações das novas entidades são salvas em "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_graph/New_entities" para posteriormente ser incluidas na versão povoada do PetroKGraph.

24. Rodar o Notebook Petro_KGraph/Model/Prediction/Prediction_RE.ipynb para identificar as relações no texto. As relações serão gravadas nos JSONs da pasta "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_json/" 

25. Com base nas entidades e relações encontradas, povoar o Knowledge Graph para avaliação. ## Atenção ## O script de clusterização atribui URIs para as entidades novas diferente das URIs anotadas no PetrNER. Para uma avaliação correta é necessário preencher corretamente o DE x Para no notebook. ## Atenção ## Rodar o Notebook "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_graph/Povoando PetroKGraph_pred.ipynb". O grafo com as entidades e relações preditas será salvo como "Petro_KGraph/Corpora/Predicao - avaliação/Prediction_graph/PetroKGraph_pred".

26. Finalmente, rodar o notebook "Petro_KGraph/Evaluation/Avaliação do PetroKGraph.ipynb" para comparar o PetroKGraph_pred com o PetroKGraph_teste. 


## Predição

27. Preprocessar os documentos para que eles fiquem no formato CONLLU. Os documentos brutos que serão processados deverão estar gravados na pasta "Petro_KGraph/Corpora/Predicao/Documentos_brutos/". O script para processar esses documentos está em "Petro_KGraph/Models/tokenizer-main/Processando texto formato conllu.ipynb" e os arquivos já em formato conllu serão gravados em "Petro_KGraph/Corpora/Predicao/Documentos_conllu/".

28. Refazer as etapas de predição (21, 22, 23 e 24), certificando que os notebooks estão apontando para a pasta "Petro_KGraph/Corpora/Predicao".


### Avaliação do uso do PetroKGraph para Recuperação da informação
29. Para comprovar a hipótese da tese, avaliamos um sistema de busca usando um sistema de expansão de consultas (AQE) baseado no knowledge graph. A avaliação se encontra no notebook Petro_KGraph/Evaluation/Base REGIS/notebooks/analise_ontologias.ipynb


