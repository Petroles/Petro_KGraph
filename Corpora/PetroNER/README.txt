# PetroNer

O corpus PetroNer foi construído a partir de um conjunto de 11 Boletins Técnicos da Petrobras, que fazem parte do corpus Petrolês [Cordeiro, 2020] e que foram pré-processados pelo Laboratório de Inteligência Computacional Aplicada (ICA/PUC-Rio). 

O material contém 24.035 frases e 615.418 tokens, que foram anotados morfossintaticamente (utilizando um modelo do PetroGold v2 [De Souza & Freitas, 2022]), além de conterem anotação de entidades mencionadas do domínio do petróleo padrão ouro. 

Posteriormente, essas entidades mencionadas receberam também uma etiqueta de URI, com o objetivo de identificar a qual instância de uma ontologia interna do projeto Petrolês essa entidade se refere.


## Distribuição das entidades anotadas no corpus
(versão de 20 de junho de 2023)

+------------------+--------------------+
|      Classes     | Entidades anotadas |
+------------------+--------------------+
|       BACIA      |        4057        |
+------------------+--------------------+
|       CAMPO      |         708        |
+------------------+--------------------+
| ESTRUTURA_FÍSICA |        2042        |
+------------------+--------------------+
|   EVENTO_PETRO   |         492        |
+------------------+--------------------+
|      FLUIDO      |         175        |
+------------------+--------------------+
|  FLUIDODATERRA_i |        1374        |
+------------------+--------------------+
|  FLUIDODATERRA_o |         246        |
+------------------+--------------------+
|    NÃOCONSOLID   |        1036        |
+------------------+--------------------+
|       POÇO       |        1230        |
+------------------+--------------------+
|      POÇO_Q      |          9         |
+------------------+--------------------+
|      POÇO_R      |          3         |
+------------------+--------------------+
|      POÇO_T      |         35         |
+------------------+--------------------+
|       ROCHA      |        2774        |
+------------------+--------------------+
|      TEXTURA     |         141        |
+------------------+--------------------+
|  TIPO_POROSIDADE |         23         |
+------------------+--------------------+
|   UNIDADE_CRONO  |        2920        |
+------------------+--------------------+
|   UNIDADE_LITO   |        1492        |
+------------------+--------------------+


## Referências

CORDEIRO, Fábio Corrêa. Petrolês-Como Construir um Corpus Especializado em Óleo e Gás em Português. PUC-Rio, Rio de Janeiro, RJ-Brasil: PUC-Rio, 2020.

DE SOUZA, Elvis; FREITAS, Cláudia. Polishing the gold–how much revision do we need in treebanks?. In: Proceedings of the Universal Dependencies Brazilian Festival. 2022. p. 1-11.