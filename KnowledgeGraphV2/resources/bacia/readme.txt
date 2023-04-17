A lista de bacias que povoa a ontologia vem da BIAEP: https://biaep4.ep.petrobras.com.br/biaep/rest/api/v2/classification/subjectId/9?pattern=
Os dados de "Bacia" do IL Dimensão Bacia são usados como sinônimos (labels) para bacias sedimentares.

dados_bacia.xlsx:
1. aba depbr_bacia, os dados da tabela BACIA_SEDIMENTAR do DEPBR, com as colunas:
	- BASE_CD_BACIA: Código da bacia ANP
	- BASE_NM_BACIA: Nome da bacia ANP
	- BASE_SG_BACIA: Sigla da Bacia ANP

2. aba dados_dicionario, com a lista de bacias originalmente enviada (EXP)

3. aba dmrr_IL Dimensão Bacia, com os dados do Information Link Dimensão Bacia coletados do Mata Mart de Reserva e Reservatórios, com as colunas:
	- Bacia Código
	- Bacia Nome
	- Bacia Nome Ambiente
	- Bacia Nome Bacia Sedimentar	
	- Bacia Sigla
	- Bacia Sigla Bacia Sedimentar

4. aba AVALIACAO, que leva às conclusoes:
	* a lista de bacias do dicionário contém bacias que não constam da lista do DEPBR. 
	* Algumas dessas bacias (salientadas em amarelo) "estão contidas" em bacias sedimentares (como Alagoas e Sergipe na Bacia Sedimentar SERGIPE-ALAGOAS).
	* Outras (salientadas em laranja) não "estão contidas", e tampouco apresentam poços no ExPlora
	* A Bacia Bragança Vizeu - Ilha Nova (salientada em azul) possui dois poços no ExPlora.
