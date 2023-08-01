# Experimentos

Este repositório disponibiliza os experimentos realizados com objetivo de melhoria da expansão do AQE. O repositório do Hotsite do AQE encontra-se [neste link](https://codigo-externo.petrobras.com.br/buscasemantica/fy3a-aqe/aqe-frontend/aqe-hotsite) e o back-end encontra-se [neste link](https://codigo-externo.petrobras.com.br/buscasemantica/fy3a-aqe/aqe-api/backend).

## Índice

- [Tecnologias necessárias](#tecnologias-necessárias)
- [Estrutura dos diretórios](#estrutura-dos-diretórios)
- [Instalação de dependências](#instalação-de-dependências)
- [Como rodar](#como-rodar)

## Tecnologias necessárias

- Python >= 3.11.0
- Pip


## Estrutura dos diretórios

```
├── conf/                       - Pasta com os arquivos de configurações
│   ├── config.py               - Centralizador das configurações e credenciais
│   └── ...
├── data/
│   ├── regis_ground_truth.csv  - Ground truth da base de dado REGIS
│   ├── regis_queries.json      - Queries da base de dados REGIS
│   └── ...
├── htmls/                      - Pasta com os htmls das análises
├── notebooks/                  - Pasta com os notebooks das análises
├── scripts/                    - Pasta com scripts geradores das análises
├── .gitignore                  - Arquivos e pastas para ignorar
├── README.md                   - README
└── ...
```

## Instalação de dependências

Para facilitar a instalação e gerência das dependências, vamos primeiramente criar um ambiente virtual:

- Linux:

```sh
python -m venv venv
source venv/bin/activate
make install
```

- Windows ([documentação](https://docs.python.org/pt-br/3/library/venv.html)):

```sh
C:\Users\%username%\AppData\Local\Programs\Python\Python36\python.exe

pip install virtualenv

cd my-project
virtualenv --python C:\Path\To\Python\python.exe venv
```

Para instalar as dependências necessárias dos notebooks e scripts, basta rodar o comando abaixo:

> pip install -r requirements.txt

## Como rodar

Para rodar os scripts e notebooks, é necessário primeiramente criar o arquivo de configurações.
Para isso, basta copiar o template, localizado com `.env.example` para o arquivo `.env`.
Dentro dele, vão existir as configurações do Elasticsearch, :

``` shell
MERGED_COLLECTION_FILENAME=MERGED_COLLECTIONS.json # Arquivo de coleção das bases de conhecimento
SKOS_FILENAME=SKOS_Tulsa.nt # Arquivo da base do tesauro de tuls
OIL_WELL_FILENAME=06_Termos_TabelaPocosANP2019.csv # Arquivo da base de poços
DATA_DIR=path/to/base_de_oleo_e_gas # Diretório das bases

# MongoDB
MONGODB_URI=mongodb://<username>:<password>@<server> # URI do MongoDB com username e password
MONGODB_DATABASE_NAME=databaseName # Nome do database do MongoDB
MONGODB_COLLECTION_NAME=collectionName # Nome da collection principal de termos
MONGO_CONFIG_COLLECTION_NAME=config # Nome da collection de configuração


# Elasticsearch
ELASTIC_SEARCH_URL=http://IP:PORT # URL do Elasticsearch
ELASTIC_SEARCH_INDEX=index # Index do Elasticsearch
ELASTIC_SEARCH_USERNAME=username # Username do Elasticsearch
ELASTIC_SEARCH_PASSWORD=password # Password do Elasticsearch

# AQE Python
AQE_URL=http://IP:PORT/api/v1/aqe # URL do AQE Python
```

Caso seja necessário gerar um html das análises dos notebooks, basta rodar o seguinte comando:

> jupyter nbconvert --execute --to html <arquivo-do-notebook>.ipynb --output <arquivo-do-html>.html

O comando para gerar o html da análise também executa o arquivo, como forma de preservar as visualizações interativas feitas através da biblioteca plotly.
Além disso, adiciona uma validação ao rodar todas as células do notebook na ordem que estão dispostas.
