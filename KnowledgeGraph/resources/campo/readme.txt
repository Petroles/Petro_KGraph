A lista de campos que povoa a ontologia vem da tabela DEPBR: CAMPO
Os dados de Campos extraídos do SIRR são utilizados para gerar um dicionário dos campos anexados.
NÃO SÃO CONSIDERADOS INDIVÍDUOS OS CAMPOS COM OS SEGUINTES STATUS:
	1. BLOCO EXPLORATÓRIO
	2. BLOCO EXPLORATÓRIO-DEVOLVIDO PARA ANP
	12. ANEXADO (que são levados como sinônimos dos campos de destino)

campo.xlsx:
1. aba depbr, os dados da tabela CAMPO do DEPBR, com as colunas:
	- CAMP_CD_CAMPO: Código numérico que identifica univocamente um campo/áreas de petróleo
	- UNOP_CD_UNID_OPER: Código numérico que identifica uma unidade de negócio da área de Exploração e Produção
	- BACI_CD_BACIA: Código numérico que identifica univocamente uma bacia sedimentar da Petrobras
	- CAMP_SG_CAMPO: Sigla do campo
	- CAMP_NM_CAMPO: Nome completo do campo
	- STCA_CD_CAMPO: Código identificador do status do campo
	- ARBA_CD_AREA_BACIA: Código numérico que identifica uma área de uma bacia sedimentar
	- BLOC_CD_BLOCO: Código do bloco
	- POCO_CD_POCO: Código numérico que identifica univocamente um poço
	- UNAD_CD_UNID_ADM: Código identificador de uma unidade  administrativa
	- CAMP_NM_ABREV: Nome abreviado do campo
	- CAMP_DT_DECL_COMERC: Data de declaração de comercialidade do campo
	- CAMP_DT_INICIO_VIGENCIA: Data do inicio da vigência do campo.[#name]Data Início Vigência[#name]
	- CAMP_DT_FINAL_VIGENCIA: Data em que o campo foi descontinuado. Pode ser por motivo de anexação, ou desdobramento em outros, por exclusão, e etc.[#name]Data Final Vigência[#name]
	- CAMP_IN_OPERADO: [valores válidos]SN[valores válidos]

2. aba sirr, com a extração de tabela SIRR com informações de campo fornecida pela RES/GDTD (Tessarollo)

2. aba dicionario, com a lista de campos originalmente enviada (EXP)

3. aba ppid, com os dados do Information Link Dimensão Campo coletados do Data Mart de Reserva e Reservatórios, com as colunas:
	- DMCP_CD_CAMP
	- DMCP_CD_CBI_UNID_OPER	
	- DMCP_DT_DECL_CMRC	
	- DMCP_NM_BLOC	
	- DMCP_NM_STAT_CAMP	
	- DMCP_SG_CAMP	
	- DMCP_SG_PRFX_POCO_PION	
	- DMCP_SG_UNID_ADMI	
	- DMCP_SG_UNID_OPER	
	- DMCP_NM_BACI	
	- DMCP_NM_CAMP	
	- DMCP_NM_ABRE_CAMP
