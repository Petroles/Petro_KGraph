# Petro_KGraph
 Repository of the PhD research "Petro KGraph: a methodology for extracting knowledge graph from technical documents - an application in a corpus from the oil and gas industry." by Fábio Corrêa Cordeiro.
 
 
# Passo a passo para replicar o trabalho desenvolvido na tese:

### Verificar se os Knowledge Graphs estão no repositórios
1. Os knowledge graphs devem estar nas pastas Petro_KGraph/KnowledgeGraph. A Petro KGraph Ontology (a ontologia básica antes de ser povoada) deve ser nomeada como OntoGeoLogicaEntidadesNomeadas.owl, já o Petro KGraph parcialmente povoado com as listas estruturadas (mas ainda sem ser povoada com as informações extraídas do texto) deve ser nomeada como OntoGeoLogicaInstanciasRelacoes.owl
 
### Processando corpus PetroNER
2. Verificar se o corpus anotado com entidades e instâncias no formato Conllu está disponível no seguinte caminho: Petro_KGraph/Corpora/PetroNER/petroner-uri-AAAA-MM-DD.conllu
3. Rodar o notebook Petro_KGraph/Corpora/PetroNER/Separando treino-valid-teste.ipynb para separar o corpus anotado em treino-validação-teste. A definição das sentenças que vão para cada dataset está "hard coded" no notebook, mas foi feita com base no arquivo KGraph/Corpora/PetroNER/PetroNER - Treino-Teste.xlsx.
4. O notebook anterior criará três novos corpora na mesma pasta: petroner-uri-treino.conllu, petroner-uri-validação.conllu, petroner-uri-teste.conllu
5. Rodar o notebook Analisando e adaptando Petro_KGraph/Corpora/PetroNER/PetroNER.ipynb. Esse notebook prepara os datasets que serão usados nas tarefas de entity linking e clustering além de gerar análises e estatísticas dos datasets. Os novos datasets são gravados na pasta KGraph/Corpora/PetroNER-LinkedEntity, são listas de sentenças (já processadas para serem usadas no treinamento), entidades, classes, e URI, todos divididos em PetroNER (corpus completo), treino, validação, e teste.







### Criando os Petro KGraph Golden
6. Rodar o notebook Petro_KGraph/KnowledgeGraph/Train-valid-test/Split ontology.ipynb. Com base nos datasets PetroNER separados em treino-validação-teste, esse notebook irá criar os grafos golden que serão referência na avaliação do povoamento dos knowledge graphs.
