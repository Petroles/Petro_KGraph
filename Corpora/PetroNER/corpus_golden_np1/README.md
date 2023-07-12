# corpus_golden_np1_ner

Resumo da estrutura de diretórios e como rodar as aplicações.

Última atualização: 6 de julho de 2023.

## Pastas

* **raw**: Textos do conjunto "np1" processados pelo Tornado
* **conllu**: Textos do conjunto "np1" processados pelo Tornado e anotados morfossintaticamente, disponibilizados no formato ".conllu"
* **ner**: Inferência de entidades mencionadas nos arquivos do conjunto "np1", dispensando o formato ".conllu"
* **ner_conllu**: Inferência de entidades mencionadas nos arquivos do conjunto "np1", no formato ".conllu"
* **ner_conllu_novo**: Inferência de entidades mencionadas nos arquivos do conjunto "np1", no formato ".conllu" e realizando correções de indexação (onde começam e onde terminam as entidades nos textos)

## **process-np1**

Pasta com os códigos responsáveis por (1) filtrar as frases do "np1", (2) anotar o *golden* do "np1" e (3) comparar os resultados do anotador automático e do modelo estatístico.

* **1-filter-process.py**: Filtrar frases mal segmentadas do material "np1"
	* `$ python3 1-filter-process.py`
	* Resultados:
		* **np1-raw.conllu**: Corpus no formato conllu após os filtros, sem anotação de entidades
		* **np1-ner-model.conllu**: Corpus no formato conllu após os filtros, com as anotações do modelo estatístico
		* **np1-ner-model-fixed.conllu**: Corpus no formato conllu após os filtros, com as anotações do modelo estatístico e com algumas correções de formato na anotação do modelo estatístico
	* Para gerar o arquivo `np1-ner-rules.conllu`, rodamos o código de anotação de léxico e regras (disponíveis no repositório de [entidades mencionadas](https://codigo-externo.petrobras.com.br/buscasemantica/puc-ica/reconhecimento-de-entidade/files-ner)) para anotar o arquivo `np1-raw.conllu`, e renomeamos o *output* para `np1-ner-rules.conllu`:
		* `$ python3 lexicons.py np1-raw.conllu`
		* `$ python3 rules.py tagged/np1-raw.conllu`
		* `$ mv rules.conllu np1-ner-rules.conllu`
	* O código gera ainda alguns relatórios:
		* **log-1-filter.txt**: Resumo de quantas frases foram filtradas após cada etapa da filtragem
		* **filter-english.txt**: Lista de frases que foram removidas do "np1" por conterem palavras em inglês
		* **filter-many-special-characters.txt**: Lista de frases que foram removidas por conterem muitos caracteres epeciais
		* **filter-not_ending_punctuation.txt**: Lista de frases que foram removidas porque não terminavam em ponto final
		* **filter-space_character.txt**: Lista de frases que foram removidas porque continham muitas letras sozinhas seguidas de espaço
* **2-generate-silver-and-golden.py**: Gerar os arquivos "silver" (revisão do "np1" versão "rules") e "golden" (revisão do "np1" com base no contraste da versão "silver" com a "model")
	* `$ python3 2-generate-silver-and-golden.py`
	* Resultados:
		* **np1-ner-rules-silver.conllu**
		* **np1-ner-rules-golden.conllu**
	* O código gera ainda um relatório:
		* **log-2-golden.txt**: Mostra a quantidade de entidades, por classe, que, após a comparação do *silver* com o *golden*, foram (a) adicionadas, (b) modificadas ou (c\) removidas
* **3-align-model-and-rules.py**: Realiza as comparações entre o "np1" anotado pelo anotador com base em regras, pelo modelo estatístico, e ambos em comparação com o *golden*
	* `$ python3 3-align-model-and-rules.py`
	* Resultado:
		* **log-3-align.txt**: Indica o número de frases, tokens e entidades de cada um dos três *datasets*; indica o número de entidades únicas e de interseção entre as duas anotações automáticas; indica precisão, abrangência e média F1 da anotação dos dois anotadores automáticos.
* Além dos três códigos, o repositório conta também com duas planilhas, `fabio.xlsx` e `patricia.xlsx`, responsáveis por indicar quais os documentos que deverão restar no `np1-raw.conllu` após os filtros serem realizados.
