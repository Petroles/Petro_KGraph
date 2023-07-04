# Petro_KGraph
 Repository of the PhD research "Petro KGraph: a methodology for extracting knowledge graph from technical documents - an application in a corpus from the oil and gas industry." by Fábio Corrêa Cordeiro.
 
 
# Passo a passo para replicar o trabalho desenvolvido na tese:

### Verificar se os Knowledge Graphs estão no repositórios
1. Os knowledge graphs devem estar nas pastas Petro_KGraph/KnowledgeGraph. A Petro KGraph Ontology (a ontologia básica antes de ser povoada) deve ser nomeada como OntoGeoLogicaEntidadesNomeadas.owl, já o Petro KGraph parcialmente povoado com as listas estruturadas (mas ainda sem ser povoada com as informações extraídas do texto) deve ser nomeada como OntoGeoLogicaInstanciasRelacoes.owl

### Treinar PetroOntoVec
2. Verificar ser os modelos PetroVec que serão usados para inicializar o treinamento do PetroOntoVec estão disponíveis na pasta Petro_KGraph/Embeddings/PetroVec/Petrovec-XXXXXXX-100. Dentro dessa pasta vem estar três arquivos. Ex: "publico-COMPLETO-100.txt.model", "publico-COMPLETO-100.txt.model.trainables.syn1neg.npy", "publico-COMPLETO-100.txt.model.wv.vectors.npy".
3. **(Atenção - Essa treinamento pode demorar cerca de 24h)** Treinar o modelo PetroOntoVec. Os hiperparâmetros necessários para rodar o algoritimo devem ser colocados no arquivo Petro_KGraph/Embeddings/PetroOntoVec/default.cfg e o script rodados via linha de comando. As instruções e de quais parâmetros usar e como rodar o script está no notebook Petro_KGraph/Embeddings/PetroOntoVec/Train_PetroOntoVec.ipynb (Se desejável, o script pode ser rodado usando o notebook)
4. O modelos será gravado na pasta Petro_KGraph/Embeddings/PetroOntoVec/cache. Alterar o nome da pasta para Petro_KGraph/Embeddings/PetroOntoVec/PetroOntoVec_xxxxxxxxxxx (O nome da pasta pode ser configurado no arquivo default.cfg, mas para evitar que versões anteriores sejam sobrescritas por engano, estamos nomeando manualmente ao final do treinamento)
5. Caso deseje visualizar os vetores usando o Tensorflow embedding projector, usar o notebook Petro_KGraph/Embeddings/PetroOntoVec/Visualizing OWL2Vec.ipynb para adaptar os vetores ao formato adequado.
6. No notebook Petro_KGraph/Embeddings/Evaluation/IntrinsicEvaluation.ipynb, é possível rodar a avaliação intrínseca implementada por D. da S. M. Gomes et al., “Portuguese word embeddings for the oil and gas industry: Development and evaluation”, Computers in Industry, vol. 124, p. 103347, jan. 2021, doi: 10.1016/j.compind.2020.103347.
 
### Processando corpus PetroNER
7. Verificar se o corpus anotado com entidades e instâncias no formato Conllu está disponível no seguinte caminho: Petro_KGraph/Corpora/PetroNER/petroner-uri-AAAA-MM-DD.conllu
8. Rodar o notebook Petro_KGraph/Corpora/PetroNER/Separando treino-valid-teste.ipynb para separar o corpus anotado em treino-validação-teste. A definição das sentenças que vão para cada dataset está "hard coded" no notebook, mas foi feita com base no arquivo KGraph/Corpora/PetroNER/PetroNER - Treino-Teste.xlsx.
9. O notebook anterior criará três novos corpora na mesma pasta: petroner-uri-treino.conllu, petroner-uri-validação.conllu, petroner-uri-teste.conllu
10. Rodar o notebook Petro_KGraph/Corpora/PetroNER/Analisando e adaptando PetroNER.ipynb. Esse notebook prepara os datasets que serão usados nas tarefas de entity linking e clustering além de gerar análises e estatísticas dos datasets. Os novos datasets são gravados na pasta KGraph/Corpora/PetroNER-LinkedEntity, são listas de sentenças (já processadas para serem usadas no treinamento), entidades, classes, e URI, todos divididos em PetroNER (corpus completo), treino, validação, e teste.

### Criando dataset para clustering
11. Rodar o notebook Petro_KGraph/Corpora/PetroNER - Clustering/Triplet dataset.ipynb. Esse notebook criar o dataset para ser usado em contrastive learning (um exemplo âncora, um positivo e outro negativo). Os datasets são gravados na mesma pasta Petro_KGraph/Corpora/PetroNER - Clustering.

### Criando Relation Extraction dataset usando distant supervision
12. Rodar o notebook Petro_KGraph/Corpora/PetroRE/Filter_Conllu_URIs_notebook.ipynb para filtrar apenas as sentenças que possuem pelo menos 2 URIs anotadas. Esse notebook salva os arquivos df_filtred_petroner_uri_xxxxxxxxxxxx na mesma pasta.
13. **(Atenção - Essa extração pode demorar várias horas)** Rodar notebook ProcessFiltered_Conllu_URIs_notebook.ipynb para criar o dataset para Relation Extraction. Esse notebook salva os arquivos necessários para o treinamento do modelo na mesma pasta (df_bert_sentences_XXXX.csv, df_relation_xxxxxxx, lista_classe_xxxxx, lista_relacoes_xxxxx, lista_uris_xxxxx), além dos arquivos JSON para usar no label studio nas pastas Petro_KGraph/Corpora/PetroRE/JSONs_XXXXX.

### Criando os Petro KGraph Golden
14. Rodar o notebook Petro_KGraph/KnowledgeGraph/Train-valid-test/Split ontology.ipynb. Com base nos datasets PetroNER separados em treino-validação-teste, esse notebook irá criar os grafos golden que serão referência na avaliação do povoamento dos knowledge graphs (PetroKGraph_treino, PetroKGraph_valid, PetroKGraph_teste).
15. O Notebook Petro_KGraph/KnowledgeGraph/Train-valid-test/Análise Ontologia.ipynb, levanta a quantidade de indivíduos, classes e labels na ontologia parcialmente povoada.

## Treinar modelos
### Treinar o modelo de Named Entity Recognition
(Revisar código elaborado pela PUC)

### Treinar Entity Linking 
(Essa etapa treina um modelo apenas para o entity link, sem a clusterização)
16. Rodar notebook Petro_KGraph/Model/Entity Linking/Training Entity Linking model.ipynb para treinar o modelo de entitiy link. O modelo será salvo na mesma pasta como "Sentence2PetroOntoVec".

(Essa etapa treina um mesmo modelo para fazer o entity link e	 a clusterização)
17. Rodar o notebook Petro_KGraph/Model/Instances clustering/Training Instances Clustering model.ipynb para treinar o modelo de entitiy link. O modelo será salvo na mesma pasta como "Sentence2PetroOntoVec_clustering".




## Usar modelos para predição
18. Rodar o notebook Petro_KGraph/Model/Instances clustering/Entity_Linking_and_clustering-Predict.ipynb. No início do notebook deve ser informado o caminho com o arquivo com as sentenças que deverão ser preditas. As entidades dessas sentenças já devem ter sido preditas. Na pasta Petro_KGraph/Model/Instances clustering/Prediction, serão salvas as listas com sentenças linkadas a URI já existentes no PetroKGraph, sentenças linkadas a URIs novas e sentenças não linkadas. 

