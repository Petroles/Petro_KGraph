# Reconhecimento de Entidade Nomeada para o Domínio de Petróleo e Gás

O Reconhecimento de Entidade Nomeada (Named Entity Recognition - NER) refere-se à identificação de entidades com
categorias específicas (geralmente substantivos) do texto, como nomes de pessoas, nomes de lugares, nomes de 
organizações, etc. O reconhecimento de entidades nomeadas é uma tarefa básica de recuperação de informações, 
classificação de consulta, pergunta e resposta, etc. Seu efeito afeta diretamente o processamento subsequente, por isso 
é um problema recorrente de pesquisa em processamento de linguagem natural.

## Idéia:
Cada vez mais, governos, empresas e organizações científicas precisam extrair informações complexas de documentos
 altamente técnicos. Esses documentos incluem informações críticas que levam a decisões importantes, como perfuração 
 de poços exploratórios, licitar ou comprar, e cronogramas de produção. Embora existam recursos linguísticos em
  alguns  domínios técnicos, eles não estão amplamente disponíveis em português para o domínio de petróleo e gás.

Para tarefas de extração de informações, abordagens que dependem exclusivamente de anotações humanas podem ser
custosas e/ou apresentar escassez de especialistas, principlamente quando as anotação são de natureza granular, como
 é o caso de NER.

O pipeline para anotação automática inclui técnicas de supervisão à distância para construir um conjunto de treinamento 
para Modelos de Reconhecimento de Entidade Nomeada. O principal objetivo é gerar automaticamente um conjunto de
 treinamento. Isso nos permite construir o pipeline de NER sem intervenção humana. 

   
## Abordagem:
 A base de treinamento utilizada permite que os modelos desenvolvidos reconheçam automáticamente entidades
  relacionadas a assuntos de grande importância no dominio de Óleo e Gás.
  - Bacia
  - Campos
  - Unidade Cronoestratigráfica
  - Litologia

Neste repositório encontram-se a versão multiclasse para treinamento e avaliação com base no modelo bert pré-treinado (modelo baseado em PyTorch). Além disso os scripts para treinamento do modelo bert no SD e Atena.

- run_ner_multiclasse.py

Abiaxo segue uma tabela indicando uma fração de 10 amostras da base de dados e o que acontece com cada uma ao aplicar as tranformações propostas:

## Dataset durante o treinamento:
 - Todas as sentenças da base de dados tem 10% da sentença (10% dos tokesn) alterada aleatóriamente para tokens nulos (**[UNK]**) ou tokens aleatórios do vocabulário e outros 5% da sentença (5% dos tokesn) removidos aleatóriamente.

|sentença|Original|Modificado|
|--------|---------|--|--|--|--|
|1|para as amostras dos arenitos do terceiro lote , os resultados a temperatura ambiente e 150oc indicaram o mesmo comportamento apre- sentado pelo poco 7arg296rn .|para as amostras dos arenitos do **Florida** **[UNK]** , os resultados a temperatura ambiente 150oc indicaram o ~~mesmo~~ comportamento apre- sentado pelo poco 7arg296rn . |
|2|alem disso , de acordo com 7rep0031rn ( 2002 ) , um aumento da informacao publica sobre parametros do leilao acaba com a exclusividade de informacoes dos jogadores podendo levar a maiores receitas nos leiloes ( ascendentes , nesse caso ) .|~~alem~~ disso , de acordo com 7rep0031rn ( 2002 ) , um aumento **[UNK]** informacao publica sobre parametros do leilao acaba ~~com~~ a exclusividade de informacoes dos jogadores podendo tática a maiores receitas **[UNK]** leiloes ( ascendentes , nesse caso ) .|
|3|20 apresentam as curvas de tensao-deforma- cao obtidos nos ensaios com as amostras do poco 7mg0485pba a temperatura ambiente.|20 apresentam ~~as~~ curvas de tensao-deforma- cao obtidos nos **[UNK]** com as amostras do ~~poco~~ 7mg0485pba a temperatura ambiente .|
|4|k ( x ) bi em contraste com o caso de um leilao de um unico objeto , as estrategias num leilao sequencial de segundo preco sao otimas somente se todos os outros participantes tambem a adotam ( 7ba364dba , 2010 ) .|k ( x ) bi em contraste com o caso de um **[UNK]** ~~de~~ um unico objeto , ~~as~~ estrategias num leilao sequencial de segundo preco sao otimas somente se todos os outros **[UNK]** tambem a adotam ( Mod , 2010 ) . |
|5|agradecemos tambem aos nossos colegas , especialmente otavio cardoso da costa , geovani lau- rindo filho , rafael 7fp387rn rodrigues e misael porto da silva , que contribuiram para o banco de dados utilizado neste estudo .|agradecemos tambem ~~aos~~ nossos colegas , **##jas** otavio cardoso **[UNK]** costa , geovani lau- rindo filho , rafael 7fp387rn rodrigues e misael **[UNK]** da silva , que contribuiram para ~~o~~ banco de dados utilizado **estacoes** estudo .|


## Treinamento: 
Passo 1: Clonar este repositório;

Passo 2: Criar a imagem docker a partir do Docker file
```
docker build -t <docker image name:tag> .
```

Passo 3: Abrir um container com a imagem docker que foi criada;

```
docker run -it -v /share_gamma/:/share_gamma/ -u $(id -u):$(id -g) --net=host -e HOME=/share_gamma/ --rm <docker image name:tag> /bin/bash
```
Obs: localização dos arquivos .sif
  - Atena: /nethome/projetos30/busca_semantica/buscaict/BigOil/dockers/ner_pytorch_2.1_latest.sif
  - SD: /petrobr/parceirosbr/bigoilict/dockers/ner_pytorch_2.1_latest.sif

Passo 4: Rodar os códigos utilizando o container aberto

- Modelo baseado em BERT
```
python src/run_ner.py --data_dir=data/ --bert_model=neuralmind/bert-base-portuguese-cased  --task_name=ner 
--output_dir=bert_model --train_batch_size 32 --max_seq_length=364 --do_train --num_train_epochs 1000 --do_eval 
--eval_on=dev --eval_batch_size=32 --warmup_proportion=0.1 --num_ealy_stoping_epochs 30
```

```
python src/run_ner_multiclasse.py \
--data_dir=./por_sentencas/ \
--bert_model=./neuralmind/bert-base-portuguese-cased  \
--task_name=ner \
--output_dir=PETRONER_sent \
--train_batch_size 16 \
--max_seq_length=364 \
--do_train \
--num_train_epochs 5 \
--do_eval \
--eval_on=test \
--eval_batch_size=16 \
--warmup_proportion=0.1 \
--num_ealy_stoping_epochs 30 \
--classes 'CAMPO' 'ROCHA' 'UNIDADE_LITO' 'UNIDADE_CRONO' 'BACIA' 'FLUIDODATERRA_i' 'EVENTO_PETRO' 'ESTRUTURA_FÍSICA' 'NÃOCONSOLID' 'FLUIDODATERRA_o' 'POÇO' 'FLUIDO' 'TEXTURA' 'POÇO_R' 'TIPO_POROSIDADE' 'POÇO_T' 'POÇO_Q'
```


Parâmetros Necessários:
- --data_dir: O diretório de dados de entrada. Deve conter os arquivos .tsv de treinamento, de validação e de teste 
 para a tarefa.
- --output_dir: o diretório de saída onde as previsões e pontos de verificação do modelo serão gravados.
- --max_seq_length: O comprimento total máximo da sequência de entrada. Seqüências mais longas do que isso serão 
truncadas e as sequências mais curtas do que isso serão preenchidas.
- --do_train: Se deve executar o treinamento.
- --do_eval: Executar avaliação ou não.
- --eval_on: se deve executar a validação do modelo no conjunto de validação (dev) ou no conjunto de teste (test).
- --eval_batch_size: Tamanho total do lote para validação.
- --num_train_epochs: Número total de épocas de treinamento a serem realizadas.
- --train_batch_size: Tamanho total do lote para treinamento.
- --learning_rate: A taxa de aprendizagem inicial.
- --seed: semente aleatória para inicialização.
- --classes: nome das classes que serão usadas no treinamento.

Outros parâmetros (apenas para o modelo baseado em BERT):
- --bert_model: Modelo BERT pré-treinado selecionado da lista: [neuralmind/bert-base-portuguese-cased
,                 neuralmind/bert-large-portuguese-cased].

- --task_name: O nome da tarefa a treinar.
- --cache_dir: Onde você deseja armazenar os modelos pré-treinados baixados.
- --warmup_proportion: Proporção de treinamento para realizar o aquecimento da taxa de aprendizado linear para, por exemplo, 0,1 = 10% 
do treinamento.
- --weight_decay: Diminui o peso se aplicarmos algum.
- --adam_epsilon: Epsilon para otimizador Adam.
- --max_grad_norm: Norma de gradiente máximo.
- --no_cuda: Se não usar CUDA quando disponível.
- --local_rank: local_rank para treinamento distribuído em gpus.
- --gradient_accumulation_steps: Número de etapas de atualizações a serem acumuladas antes de executar uma passagem de retrocesso/atualização.
- --num_ealy_stoping_epochs: é o número de épocas consideradas para o early stopping.


## Dataset:

O dataset de treinamento e validação é formado por sentenças cujos labels então no formato IOB. O formato IOB (abreviação de dentro, fora, início) é um formato de marcação comum para tokens de marcação em uma tarefa de agrupamento em linguística computacional (por exemplo , reconhecimento de entidade nomeada ). Ele foi apresentado por Ramshaw e Marcus em seu artigo "Text Chunking using Transformation-Based Learning", 1995. 
O prefixo I- antes de uma tag . Uma . O prefixo B- antes de uma tag indica que a tag é o início de um pedaçoque segue imediatamente um outro pedaço sem tags O entre eles. É usado apenas nesse caso: quando um pedaço vem depois de uma etiqueta O, o primeiro token do pedaço leva o prefixo I-.

- *B*: é uma tag que indica o início de um trecho de texto que representa a entidade de interesse.
- *I*: é uma tag que indica que a o token está dentro de um trecho de texto que representa a entidade de interesse.
- *O*: é uma tag indica que um token não pertence a entidade de interece. 

O dataset foi criado com base na técnica de distant supervision utilizando para tal listas de palavras relacionadas a cada entidade de interesse citada acima. Como medida de evitar problemas, listas adicioanis foram criada (cidade, cor, peixes, município, cidade e estado) para realizar a técnida de desambiguação.

Também foram utilizadas técnicas para aumentar a quantidade de dados de treinamento da base de dados utilizando o máximo de palavras ou trechos de texto que representem as entidades de interesse. 

O formato final consistem em um .csv com os tokens e labels respectivos. Um exmeplo pode ser observado abaixo:

||0|	1	|sentence|
|--|--|-----|--|
|0|	as|	O	|72543|
|1|	facilidades	|O|	72543|
|2|	levaram	|O|	72543|
|3|	ao	|O|	72543|
|4|	uso	|O|	72543|
|5|	desenfreado	|O|	72543|
|6|	do	|O|	72543|
|7|	recurso	|O|	72543|
|8|	e	|O|	|72543|
|9|	segundo	|O	|72543|
|10|	os	|O|	72543|
|11|	catadores	|O|	72543|
|12|	isso	|O|	72543|
|13|	diminuiu	|O|	72543|
|14|	o	|O|	72543|
|15|	numero	|O|	72543|
|16|	de	|O|	72543|
|17|	7et0550rn	|B|	72543|
|18|	.	|O|	72543|
|21|	foi	|O|	48925|
|22|	descoberto	|O|	48925|
|23|	pelo	|O|	48925|
|24|	poco	|O|	48925|
|25|	3-brsa-1295-rn	|B|	48925|
|26|	em	|O|	48925|
|27|	agosto	|O|	48925|


## Distributed Process

Dentre da pasta src, existe uma pasta chamada distributed_process ela contem os scripts para treinamento distribuído do NER. Não foi testado no Atena, apenas no SD. Portanto se for usar basta modificar os caminhos e testar para ver se está tudo ok. 



## Mantainer
  - Júlia Potratz: jupotratz@gmail.com | jupotratz@puc-rio.br







