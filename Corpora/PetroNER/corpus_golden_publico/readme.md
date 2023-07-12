# Files NER

Resumo da estrutura de diretórios e arquivos.

Última atualização: 6 de julho de 2023.

## *Pipeline* de anotação de entidades mencionadas:

### (1) **lexicons.py**

* `$ lexicons.py <FILE>`
	* Anota os arquivos da pasta `conllu` (ou o arquivo especificado no argumento \<FILE>) , e salva-os na pasta `tagged`. A variável `APAGAR_ENTIDADES` (default=True) indica se todas as entidades que porventura estejam anotadas no arquivo da pasta `conllu` devem ser apagadas antes de iniciar a nova anotação.
	* Para gerar o PetroNer,

#### Podem ser úteis:

* `$ stats.py`
	* Gera três planilhas, `files_stats.csv`, `tags_stats.csv` e `tagset_stats.csv`, com características dos arquivos anotados da pasta `tagged`

* `$ sentences_subset.py <FILE> <SENT_ID_1|SENT_ID_2...>`
	* Recorta um arquivo conllu, deixando apenas as frases com sent_id especificados na linha de comando.
	* O resultado é salvo no arquivo `conllu/subset.conllu`

### (2) **rules.py**

* `$ rules.py <FILE>`
	* Anota um arquivo conllu com base nas regras codificadas dentro do próprio código. Deve ser acionada após a anotação via léxicos
	* O resultado é salvo no arquivo `rules.conllu`
	* Um relatório com todas as regras executadas (assim como os *tokens* que foram modificados por elas) é salvo no arquivo `log_rules.txt`
	* Uma figura com o número de entidades presentes no *dataset* é salva no arquivo `rules-results-figure.png`

#### Pode ser útil:

* `$ diff.py <FILE_1> <FILE_2>`
	* Compara dois arquivos iguais mas com anotações de entidades diferentes
	* O resultado é salvo em `diff.html`

### (3) **uri.py**

* `$ uri.py <FILE>`
	* Anota o URI das entidades já anotadas anteriormente nas outras duas etapas
	* O URI das entidades é obtido a partir das planilhas `["uri-finalização.xlsx", "uri-entidades-novas.xlsx", "uri-grafias-alternativas.xlsx"]`
	* O resultado é salvo no arquivo `uri.conllu`
	* Um relatório é salvo no arquivo `uri_log.txt`

## Anotando o PetroNer

Para gerar o PetroNer, seguimos o *pipeline* descrito utilizando como base o arquivo `boletins-pt.conllu`, e depois renomeamos o último item do *pipeline* para `petroner-uri.conllu`

* `$ python3 lexicons.py conllu/boletins-pt.conllu`
* `$ python3 rules.py tagged/boletins-pt.conllu`
* `$ python3 uri.py rules.conllu`
* `$ mv uri.conllu petroner-uri.conllu`

## Pastas

### tagset

Pasta onde estão armazenadas as entidades mencionadas que são anotadas na etapa de anotação via léxico. É da pasta `tagset` que o código `lexicons.py` obtém as entidades que irá procurar nos textos a serem anotados.

### tagset/todos-lexicos

Com o objetivo de aumentar a eficiência da revisão do padrão ouro de entidades (o PetroNer), nem todas as entidades são anotadas inicialmente via léxico -- algumas são anotadas apenas via regras. Os arquivos da pasta `todos-lexicos` não são lidos pelo código de anotação, servindo apenas como um repositório para todas as entidades, tanto as que são anotadas nesta etapa quanto as que não são.

### conllu

Pasta onde deverão ficar armazenados os arquivos conllu que serão anotados pelo `lexicons.py`, caso não haja interesse em anotar apenas um arquivo, mas vários.

### tagged

Pasta onde serão salvos os arquivos anotados pelo `lexicons.py`.

### DOCS

Documentação da anotação de entidades mencionadas e Relatório de anotação de entidades no PetroNer
