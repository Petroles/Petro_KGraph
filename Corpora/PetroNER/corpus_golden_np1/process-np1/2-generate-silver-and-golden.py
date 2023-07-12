import re
from collections import defaultdict
import json
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore

files = {'original': "np1-ner-rules.conllu", 'silver': "np1-ner-rules-silver.conllu", 'golden': "np1-ner-golden.conllu"}

# ANCHOR definindo funções
def append_to(original, s, delimiter="|"):
    original = original.split(delimiter)
    novosFeats = s.split(delimiter)
    novosFeats += [x for x in original if x != "_" and not any(y.split("=")[0] == x.split("=")[0] for y in novosFeats)]

    return delimiter.join(sorted(novosFeats))

def remove_from(original, s, delimiter="|"):
    original = original.split(delimiter)
    deletedFeats = s.split(delimiter)
    original = [x for x in original if x not in deletedFeats and not any(y == x.split("=")[0] for y in deletedFeats)]
    if not original: original = ["_"]

    return delimiter.join(sorted(original))

def get_head(tok, sentence):
    return sentence.tokens[sentence.map_token_id[tok.dephead]].word if tok.dephead in sentence.map_token_id else "_"

def regex(exp, col):
    return re.search(r'^(' + exp + r')$', col)

corpus = estrutura_ud.Corpus(recursivo=True)
corpus.load(files['original'])
    
# ANCHOR SILVER
for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        try:
        
            # ANCHOR Maria Clara 23/05/2023
            # BACIA - regras NP1 (Maria Clara - 23/05/2023)

            if regex("Baciado", token.word) and regex("PUNCT", token.next_token.upos) and regex("Parani", token.next_token.next_token.word):
                token.deps = "B=BACIA"
                token.next_token.deps = "I=BACIA"
                token.next_token.next_token.deps = "I=BACIA"
                
            if regex("ba~ia|Baci|baci~s|Bac1a", token.word):
                token.deps = "B=BACIA"
                
            if regex("B~cia", token.word) and regex("\,", token.next_token.word):
                token.deps = "B=BACIA"
                
            if regex("B~cia", token.word) and regex("Po~igua~", token.next_token.word):
                token.deps = "B=BACIA"
                token.next_token.deps = "I=BACIA"
                
            if regex("Bacia", token.word) and regex("de", token.next_token.word) and regex("3", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word) and regex("\(", token.next_token.next_token.next_token.next_token.word) and regex("Recô\~cavo", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=BACIA"

            if regex("Ba\~ia", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("P\~rani", token.next_token.next_token.next_token.word):
                token.deps = "B=BACIA"
                token.next_token.deps = "I=BACIA"
                token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Baoia", token.word) and regex("O", token.next_token.next_token.next_token.deps):
                token.deps = "B=BACIA"
                
            if regex("b\&c1a", token.word) and regex("de", token.next_token.word) and regex("Apucurana", token.next_token.next_token.word):
                token.deps = "B=BACIA"
                token.next_token.deps = "I=BACIA"
                token.next_token.next_token.deps = "I=BACIA"

            if regex("Area|Área", token.word) and regex("\:", token.next_token.word) and regex("Baixo|Médio", token.next_token.next_token.word) and regex("Amazonas", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Bacia", token.word) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Foz", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Amazonas", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Bacia", token.word) and regex("de", token.next_token.word) and regex("Ca\~­", token.next_token.next_token.word) and regex("pos", token.next_token.next_token.next_token.word) and regex("q\?", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Bacia", token.word) and regex("Sedimentar", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
                
            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=BACIA"
                
            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Cear~|Ceará", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=BACIA"

            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Espírito", token.next_token.next_token.next_token.next_token.word) and regex("Santo", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Rio", token.next_token.next_token.next_token.next_token.word) and regex("Grande", token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Norte", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Bacias", token.word) and regex("Paleozóicas", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Dis-camadas", token.next_token.next_token.next_token.next_token.word) and regex("trito", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Bacias", token.word) and regex("Sedimentares|Terrestres", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("Developments", token.word) and regex("\-", token.next_token.word) and regex("Barreirinhas", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("border", token.word) and regex("af", token.next_token.word) and regex("pantanal", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Lin", token.next_token.next_token.word) and regex("guado", token.next_token.next_token.next_token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Badejo|Jandu\{s|Linguado", token.next_token.next_token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("Ponta|sul|Haela|Santa", token.word) and regex("Grossa|de|Catarina", token.next_token.word) and regex("\~|o|e", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("de", token.word) and regex("o", token.next_token.word) and regex("PUNCT", token.next_token.next_token.upos) and regex("Ceará", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("classificação", token.word) and regex("de", token.next_token.word) and regex("são", token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.next_token.word) and regex("Paran", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("o", token.word) and regex("paran", token.next_token.word) and regex("PUNCT", token.next_token.next_token.upos) and regex("ou", token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("costa", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Ceará", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("toRo", token.word) and regex("a", token.next_token.word) and regex("Curitiba", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Developments", token.word) and regex("-", token.next_token.word) and regex("Santos", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("eletr|uim", token.word) and regex("icas|icos", token.next_token.word) and regex("B=BACIA", token.next_token.deps):
                token.next_token.deps = "O"
                
            if regex("empresas", token.word) and regex("de", token.next_token.word) and regex("gás", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Alagoas", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Sergipe", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Formações", token.word) and regex("Emborê", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Cidade", token.word) and regex("de", token.next_token.word) and regex("São", token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.next_token.next_token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("C1NDIDO", token.word) and regex("DE", token.next_token.word) and regex("ABREU", token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.word) and regex("PARANÁ", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Sr.|comments", token.word) and regex("Campos|re|Carlos", token.next_token.word) and regex(",|Campos", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("produção|descobertas|entre|gás", token.word) and regex("de|os", token.next_token.word) and regex("estes|novos|dois", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"
                
            if regex("Plataforma", token.word) and regex("de", token.next_token.word) and regex("Sao", token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Estado", token.word) and regex("de", token.next_token.word) and regex("são", token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.deps):
                token.next_token.next_token.deps = "O"
                
            if regex("Estados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paran", token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("nmEstados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Facies|Litologia|Treze", token.word) and regex("B=BACIA", token.deps):
                token.deps = "O"
                
            if regex("formação", token.word) and regex("campos\/", token.next_token.word) and regex("carapebus\.", token.next_token.next_token.word) and regex("B=BACIA", token.next_token.deps):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("KIn", token.word) and regex("B=BACIA", token.deps):
                token.deps = "O"
                
            if regex("hidraul|Atrnosfer|matem\~t|caracte\~íst|term|cletr", token.word) and regex("ico|icas", token.next_token.word) and regex("B=BACIA", token.next_token.deps):
                token.next_token.deps = "O"
                
            if regex("nmEstados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Norte", token.word) and regex("de", token.next_token.word) and regex("Alagoas", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Norte", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Espírito", token.next_token.next_token.next_token.word) and regex("Santo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("apresenta", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word) and regex("até", token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("PUNCT", token.upos) and regex("pelotas|peLotas", token.next_token.word) and regex("PUNCT", token.next_token.next_token.upos) and regex("B=BACIA", token.next_token.deps):
                token.next_token.deps = "O"
                
            if regex("praias", token.word) and regex("de", token.next_token.word) and regex("Sergipe", token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.word) and regex("Alagoas", token.next_token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Pernambuco", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("projetos", token.word) and regex("de", token.next_token.word) and regex("GNA", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Alagoas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("ReI\.", token.word) and regex("Interno", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                
            if regex("Estados|Km|praias|o|pública", token.word) and regex("de|em|Ide|Rio", token.next_token.word) and regex("Sergipe", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("costa", token.word) and regex("de", token.next_token.word) and regex("Sergipe", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Souza|A.", token.word) and regex("M.|de", token.next_token.word) and regex("S.,1982|Souza", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("Trilha\.", token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                
            if regex("S.M.d", token.word) and regex("os", token.next_token.word) and regex("Campos", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("explotação", token.word) and regex("para", token.next_token.word) and regex("os", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("Campos", token.next_token.next_token.next_token.next_token.word) and regex("situados", token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"
                
            if regex("d\.po\~icionaiil", token.word) and regex("d", token.next_token.word) and regex("são", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Bacia", token.word) and regex("de", token.next_token.word) and regex("\.", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=BACIA"
                token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("bacia", token.word) and regex("dQ\.\.", token.next_token.word) and regex("Amazonas", token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.deps):
                token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Bacia", token.word) and regex("B=BACIA", token.deps) and regex("de", token.next_token.word) and regex("Campos", token.next_token.next_token.word) and regex("O", token.next_token.next_token.deps):
                token.next_token.deps = "I=BACIA"
                
            # UNIDADE_CRONO - regras NP1 (Maria Clara - 23/05/2023)

            if regex("Predevoniano|Algonquiano|Eocênico|Oligocênicas|Oligocênicos|Miocênico|Eocarbonífero|Eosiluriano|\~riúa3ico|cretéceos|Cretácico|Cretãcico|\~etáceo|mesoz6cas|m\~soz\~ico|nifero|neo-paleoceno|d\.vonianas|neo\-01igoceno|eoterciário|paleocênica\-eocênica|aptiana\-maastrichtiana|paleo\-201cas|paleoz6ic\~s|paleoz5icas|paleoz6ica|paleoB6icas|paleoz6icas|Perm1ano|Triássioo|Triissioo|Triásaico|pré\-cretáceas|permo\-carbonífera|permo\-carbonífero|Fermo\-Triassico|paleozõic.*", token.word):
                token.deps = "B=UNIDADE_CRONO"

            if regex("Carboníf\~|Paleo|Mio|Oligo|Quater|devon1|Ap", token.word) and regex("ro|z6ico|ceno|cênicas|nário|anos|tia", token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex(".*idade", token.word) and regex("Albo", token.next_token.word) and regex("PUNCT", token.next_token.next_token.upos) and regex("Cenornaniana", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("paleo", token.word) and regex("\&6ioos", token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("Fermiano|Permlano", token.word) and regex("Inferior|M.*", token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("Paleoz6ico|bevnniano|idade|Permitino", token.word) and regex("[Ss]uperior|neo\-paleoceno|eorrio\-da\-serra", token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("Carbonífero|Carbonifero", token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
                token.next_token.deps = "O"
                
            if regex("Cambriano", token.word) and regex("a", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Jurássico", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "B=UNIDADE_CRONO"
                
            if regex("Carbon\~fero", token.word) and regex("\$uper1or", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("Carbonífero", token.word) and regex("\~up8ri", token.next_token.word) and regex("or", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("de|Provisórios|Compactos", token.next_token.word) and regex("de|Banco|Elevação|Produção", token.next_token.next_token.word) and regex("B=UNIDADE_CRONO", token.deps):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("Pe\~", token.word) and regex("\-", token.next_token.word) and regex("miano", token.next_token.next_token.word) and regex("Inferior", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

            if regex("Série", token.word) and regex("de", token.next_token.word) and regex("Brusque|Minas", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("[sS]érie", token.word) and regex("Itajaí|Tubarão|Brusque", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("de", token.next_token.word) and regex("Produção|Produçio|Piodução", token.next_token.next_token.word) and regex("Antecipada|Ante|Anteci\~ada", token.next_token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("proterozóicas", token.word) and regex("pré\-cambrianas", token.previous_token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            # UNIDADE_LITO - regras NP1 (Maria Clara - 23/05/2023)

            if regex("fo\~|forma", token.word) and regex("mação|ção", token.next_token.word) and regex("Furnas|Macaé", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formaçio|for|form", token.word) and regex("Lagoa|mação|ção", token.next_token.word) and regex("Feia|Macaé|Codó", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("\/MB", token.word) and regex("Oriximiná", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("arenitos", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Carapebus", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("o", token.word) and regex("Codó", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("dem\~is", token.next_token.next_token.next_token.word) and regex("formações", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("coquinas", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Lagoa", token.next_token.next_token.next_token.word) and regex("Feia", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("\/Fm", token.word) and regex("\.", token.next_token.word) and regex("Muribeca", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formações", token.word) and regex("arenito", token.next_token.word) and regex("Carapebus", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("for", token.word) and regex("maç\~o", token.next_token.word) and regex("Nova", token.next_token.next_token.word) and regex("Olinda", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("for|forma", token.word) and regex("mação|çao", token.next_token.word) and regex("Lagoa", token.next_token.next_token.word) and regex("Feia", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formacao|forma", token.word) and regex("Serra|çao", token.next_token.word) and regex("ria|Açu\.", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formaç\[", token.word) and regex("\.", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Codó", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formação", token.word) and regex("\:", token.next_token.word) and regex("Teresina\.", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formação|formacão", token.word) and regex("inferior|superior", token.next_token.word) and regex("Irati|Teresina\.|Palermo", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Formação", token.word) and regex("MUR", token.next_token.word) and regex("\/", token.next_token.next_token.word) and regex("CPS", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("8mb|Fo\~maçio", token.word) and regex("samento|Pend\&ncia", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formação|Fm\.", token.word) and regex("PUNCT|ADP", token.next_token.upos) and regex("Lagoa", token.next_token.next_token.word) and regex("Feia", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formação", token.word) and regex("superior", token.next_token.word) and regex("Serra", token.next_token.next_token.word) and regex("Alta\.", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formaçges", token.word) and regex("Ilhas", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("S\,", token.next_token.next_token.next_token.next_token.word) and regex("Sebastião", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formações", token.word) and regex("inferior", token.next_token.word) and regex("Teresina", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("\.formações|formaçío", token.word) and regex("S\.", token.next_token.word) and regex("Sebastião", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("grupos", token.word) and regex("\:", token.next_token.word) and regex("Itararé", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("Guat.*", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Ilhas", token.word) and regex("\.formações", token.head_token.head_token.word):
                token.deps = "B=UNIDADE_LITO"
                
            if regex("Japostã|Batinga", token.word) and regex("formeções", token.head_token.word):
                token.deps = "B=UNIDADE_LITO"
                
            if regex("MB", token.word) and regex("Oriximiná", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("Curiri", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("superior", token.word) and regex("Morro", token.next_token.word) and regex("Pelado", token.next_token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("llio", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Hasto", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("S\.", token.word) and regex("Sebastigo", token.next_token.word) and regex("Ilhas", token.head_token.word) and regex("formações", token.head_token.head_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("São|Feliz", token.word) and regex("Miguel|Deserto", token.next_token.word) and regex("formeções", token.head_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formeções|formeção|formaç\&o|formaçZo|formaçao", token.word) and regex("Barreires|Alegoas|Codó|Brotas|Ilhas", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("embessmento|embaaamento", token.word):
                token.deps = "B=UNIDADE_LITO"
                
            if regex("s\.\-Formação", token.word) and regex("\:", token.next_token.word) and regex("\~resina", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("for\.", token.word) and regex("maçao", token.next_token.word) and regex("Santo", token.next_token.next_token.word) and regex("Amaro", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formação", token.word) and regex("Muribeca", token.next_token.word) and regex("\/Carmópolis", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Coquinas", token.word) and regex("B=UNIDADE_LITO", token.deps):
                token.deps = "B=ROCHA"
                
            if regex("deslocamento", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("grupo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("DIAGÊNESE", token.word) and regex("B=UNIDADE_LITO", token.deps):
                token.deps = "O"
                
            if regex("FM", token.word) and regex("Curuá\/MB", token.next_token.word) and regex("Curi", token.next_token.next_token.word) and regex("rí", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("formação", token.word) and regex("Curuá\/MB", token.next_token.word) and regex("Curiri\.|Oriximiná", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("tai", token.word) and regex(",", token.next_token.word) and regex("Goias", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("grupos|grupo", token.word) and regex("PECTEN/MARATHON/UNION|ELF/AGIP/CANAMM/NORCEN\.|PECTEN|Golder", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                
            if regex("Grupo|Relatório|grupos", token.word) and regex("Executivo|EXXON|Interno|CiTIES", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                
            if regex("SHELL\/MARATHON|PECTEN\/CHE|mo\.", token.word):
                token.deps = "O"
                
            if regex("Forma", token.word) and regex("ção", token.next_token.word) and regex("Macaé", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Membra", token.word) and regex("Ibura", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("arenitos|arenito|coquinas", token.word) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Lagoa|Rio", token.next_token.next_token.next_token.word) and regex("Bonito|Feia\.", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("arenitos|arenito|coquinas|folhelhos", token.word) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Irati\.|Itarar4|Botucatú|Irati|Botuoatú|Itararé", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("[Aa]renito|arenitos|folhelhos|[Cc]alcário|calcarenitos|tilitos", token.word) and regex("Sergl\.|Carape|Carapebus|Botucatd|Serg|Namorado|Namora|Irati|Macaé\.|Maca\~\.|Itararé\.", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("topo", token.word) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Itararé|\$ergt|Palermo|Sergi", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("formações", token.word) and regex("Gondwanicas", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                

                
            # ESTRUTURA_FÍSICA - regras NP1 (Maria Clara - 23/05/2023)

            if regex("\~\~atura|tratura|fractura|slides|estratifioação|estrati\~icação|discordéncias|discordancias|discordancia|discordlnõia|[aA]lmofadas|laminaçao|laminacões|laminaç\:ões|slumps|d6micas|d5micas|d\~mica|d6mica|fissil|\.estrutura", token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                
            if regex("estratificação\(", token.word) and regex("escamas", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("peixe", token.next_token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("estratifioação", token.word) and regex("paralela", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("oruza", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.next_token.misc = append_to(token.next_token.next_token.next_token.misc, "D=ESTRUTURA_FÍSICA")
                
            if regex("fratura", token.word) and regex("conchoida1|conchoidal", token.next_token.word):
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("contactG1I|estrati\~|fr\~|fra|frat\~", token.word) and regex("abruptos|icação|turas|ras", token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("tubos", token.word) and regex("de", token.next_token.word) and regex("vermes", token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("discordên", token.word) and regex("\=", token.next_token.word) and regex("cia", token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("estratií.*icação", token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                
            if regex("Alg\~mas", token.word) and regex("estruturas", token.next_token.word) and regex("p\~sam", token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("reprojetadas|fabricação|conceito", token.word) and regex("as|de", token.next_token.word) and regex("estruturas", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("fratura", token.word) and regex("irre", token.next_token.word) and regex("gular", token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.word) and regex("conchoidal", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.misc = append_to(token.misc, "D=ESTRUTURA_FÍSICA")
                
            if regex("fratura", token.word) and regex("irregular", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("conchoidal", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.misc = append_to(token.misc, "D=ESTRUTURA_FÍSICA")
                
            if regex("laminações", token.word) and regex("paralelas", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("cruzadas", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.misc = append_to(token.misc, "D=ESTRUTURA_FÍSICA")
                
            if regex("Essas", token.word) and regex("estruturas", token.next_token.word) and regex("podem", token.next_token.next_token.word) and regex("ser", token.next_token.next_token.next_token.word) and regex("utilizadas", token.next_token.next_token.next_token.next_token.word) and regex("em", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("\·", token.word) and regex("B=ESTRUTURA_FÍSICA", token.deps):
                token.deps = "O"
                
            if regex("[eE]strutura", token.word) and regex("de|\,", token.next_token.word) and regex("suporte|armazenamento|fonte|metadados", token.next_token.next_token.word):
                token.deps = "O"
                
            if regex("Estrutura", token.word) and regex("funcional", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("uma", token.next_token.next_token.next_token.word) and regex("biblioteca", token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                
            if regex("estrutura", token.word) and regex("uni\-versitária", token.next_token.word):
                token.deps = "O"
                
            if regex("\~ara", token.word) and regex("o", token.next_token.word) and regex("posicionamento", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.next_token.word) and regex("estrutura", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("N50", token.word) and regex("B=ESTRUTURA_FÍSICA", token.deps):
                token.deps = "O"
                
            if regex("estruturas", token.word) and regex("e", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("alguns", token.next_token.next_token.next_token.next_token.word) and regex("fu6dulos", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                
            if regex("por", token.word) and regex("falha", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("projeto", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("projetos", token.word) and regex("e", token.next_token.word) and regex("instalações", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("estruturas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("estrutura|estruturas", token.word) and regex("funcional|padronizadas|de|danificada", token.next_token.word) and regex("de|e|as", token.next_token.next_token.word) and regex("uma|projetadas|plata|o", token.next_token.next_token.next_token.word) and regex("biblioteca|dentro|fo\~maa|flare", token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                
            if regex("fr\~", token.word) and regex("turas", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("Vugs", token.next_token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.next_token.upos):
                token.next_token.next_token.next_token.next_token.deps = "B=ESTRUTURA_FÍSICA"
                
            # FLUIDODATERRA_i - regras NP1 (Maria Clara - 23/05/2023)

            if regex("acumulação|armazenadoras|ascenção|exsudação|metros|migração|probabilidades|producao|segregação", token.word) and regex("de|o|cubicos|inicial", token.next_token.word) and regex("de|o|pr6prio|encontrar", token.next_token.next_token.word) and regex("6leo|61eo|oleo|\;leo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("produção", token.word) and regex("de", token.next_token.word) and regex("gas", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("agua", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("6leo", token.word) and regex("em|de", token.next_token.word) and regex("as|Lagoa", token.next_token.next_token.word) and regex("jazidas|Parda", token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("6leo", token.word) and regex("trans", token.next_token.word) and regex("portado", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("de", token.next_token.word) and regex("tormação", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("acumulaçoes", token.word) and regex("de", token.next_token.word) and regex("gás", token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.word) and regex("mesmo", token.next_token.next_token.next_token.next_token.word) and regex("oleo", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("acumulacoes|cubicos", token.word) and regex("de", token.next_token.word) and regex("61eo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água|á0ua", token.word) and regex("de|para", token.next_token.word) and regex("injeção", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("forma", token.next_token.next_token.next_token.word) and regex("ção", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("injetada", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("produzida", token.next_token.word) and regex("como", token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.next_token.next_token.word) and regex("for", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("maçao", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("água|gás", token.word) and regex("em", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("PIR\-184D|PIR\-228D", token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("alternância", token.word) and regex("com", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("topo", token.word) and regex("\,", token.next_token.word) and regex("alternando", token.next_token.next_token.word) and regex("com", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("producao|arenito", token.word) and regex("atual|por", token.next_token.word) and regex("de|o", token.next_token.next_token.word) and regex("61eo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("existência", token.word) and regex("ou", token.next_token.word) and regex("nao", token.next_token.next_token.word) and regex("o|de", token.next_token.next_token.next_token.word) and regex("\©leo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("expulse|recuperou", token.word) and regex("oleo", token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("fluido|fluidos|saturação", token.word) and regex("de|critica", token.next_token.word) and regex("base|de", token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("Livre", token.next_token.word) and regex("não", token.next_token.next_token.word) and regex("associado", token.next_token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.word) and regex("oleo", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gis|gas", token.word) and regex("associado|natural", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gis", token.word) and regex("espargido", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injeção", token.word) and regex("com", token.next_token.word) and regex("qualidade", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("agua", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injeção", token.word) and regex("simultânea|conjunta", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("gás", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("água|água\.", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injeção|injeç\~o", token.word) and regex("de", token.next_token.word) and regex("igua", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injetar", token.word) and regex("água", token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injetar", token.word) and regex("aproxima\-dacente", token.next_token.word) and regex("10", token.next_token.next_token.word) and regex("bbl", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injetar", token.word) and regex("gas", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("um", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injetar", token.word) and regex("gás", token.next_token.word) and regex("ou", token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("saida", token.word) and regex("de", token.next_token.word) and regex("agua", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("vasa|vaso", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("m3", token.word) and regex("de", token.next_token.word) and regex("gas", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("óleo", token.word) and regex("e", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("gis", token.next_token.next_token.next_token.next_token.word) and regex("produzidos", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("metros", token.word) and regex("cubicos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("gas\.", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("Produ\~ao|amostras|armazenadoras|base|coletar|ganho|m3|manchas|manifold|ocorrencia|producao|produçao|produçio|reservatorio|reservatorios|saida|todo", token.word) and regex("de|o", token.next_token.word) and regex("Oleo|oleo|6leo|61eo|\;leo|\~leo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("o", token.word) and regex("transporte", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("oleo", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("obtenção", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("61", token.next_token.next_token.next_token.word) and regex("eo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("06|o5", token.word) and regex("leo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.word) and regex("campos", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("6leo", token.word) and regex("seja", token.next_token.word) and regex("proveniente", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.word) and regex("folhelhos", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("6leo|\~leo|oleo", token.word) and regex("migrado|remanescente|lacustre|marítimo", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("para", token.word) and regex("oleo", token.next_token.word) and regex("\,", token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("agua", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("producao", token.word) and regex("adicional", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("oleo", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("produçio", token.word) and regex("de", token.next_token.word) and regex("bleo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("existen\-|deproduçio|região", token.word) and regex("\.|diiria|oferece", token.next_token.word) and regex("cia|mixima|possibilidades", token.next_token.next_token.word) and regex("o|de", token.next_token.next_token.next_token.word) and regex("6leo|oleo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("volumes|Possibilidades|produtores", token.word) and regex("recuperiveisde|de", token.next_token.word) and regex("\~leo|01eo|61eo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("recuperaçio", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("\~leo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("rec", token.word) and regex("upe-raçio", token.next_token.word) and regex("final", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("5leo", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("reservatorios", token.word) and regex("de", token.next_token.word) and regex("oleo", token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("separaç\~6", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("gis", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("leo", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("separaçio", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("gis", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("6leo", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("tratamento", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("oleo|óleo", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("gas\.|gás\.", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("volumes|processarem", token.word) and regex("de|o", token.next_token.word) and regex("oleo|6leo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("de|o", token.next_token.next_token.next_token.next_token.word) and regex("gas|gis", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("engenharia", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("engenharia|empresas", token.word) and regex("de", token.next_token.word) and regex("gás", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("enge|ind\~stria", token.word) and regex("nheiros|de", token.next_token.word) and regex("de|o", token.next_token.next_token.word) and regex("petróleo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("B=FLUIDODATERRA_i", token.deps) and regex("Colunas|Geoquimica|Packers|Tubos", token.word):
                token.deps = "O"
                
            if regex("pesquisa", token.word) and regex("de", token.next_token.word) and regex("gás\/", token.next_token.next_token.word) and regex("óleo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("indóstria|pesquisa", token.word) and regex("de", token.next_token.word) and regex("petróleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("projetos", token.word) and regex("de", token.next_token.word) and regex("transferência", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("gás", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("relações", token.word) and regex("comerciais", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.word) and regex("área", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("petróleo", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("descar\-transfe\~ência|ti", token.word) and regex("continua|recebi\-menta", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("6leo", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("gás|gas", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            # FLUIDODATERRA_o - regras NP1 (Maria Clara - 23/05/2023)

            if regex("volume", token.word) and regex("de", token.next_token.word) and regex("água", token.next_token.next_token.word) and regex("injetado|injetada", token.next_token.next_token.next_token.word) and regex("B=FLUIDODATERRA_o", token.next_token.next_token.deps):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            # FLUIDO - regras NP1 (Maria Clara - 23/05/2023)

            if regex("5l|o", token.word) and regex("eo|leo", token.next_token.word) and regex("dies\~l|diesel", token.next_token.next_token.word):
                token.deps = "B=FLUIDO"
                token.next_token.deps = "I=FLUIDO"
                token.next_token.next_token.deps = "I=FLUIDO"
                
            if regex("injetar", token.word) and regex("diesel", token.next_token.word):
                token.next_token.deps = "B=FLUIDO"
                
            if regex("bombas|transferencia|combustive1", token.word) and regex("de|\,", token.next_token.word) and regex("diesel", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDO"
                
            if regex("diese|dleo|6leo", token.word) and regex("l|diesel", token.next_token.word):
                token.deps = "B=FLUIDO"
                token.next_token.deps = "I=FLUIDO"
                
            if regex("expulsão|translerenc|contaminado|circulação|transfc", token.word) and regex("de|ia|com|reversa|rencia", token.next_token.word) and regex("o|de", token.next_token.next_token.word) and regex("diesel", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDO"
                
            if regex("6leos", token.word) and regex("\~egetais", token.next_token.word):
                token.deps = "B=FLUIDO"
                token.next_token.deps = "I=FLUIDO"

            # ANCHOR Maria Clara (23/05/2023) potencial de esbarrar com Tati

            # nas regras para BACIA (todas são ocorrências de CAMPO que vieram anotados como BACIA)

            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Lin", token.next_token.next_token.word) and regex("guado", token.next_token.next_token.next_token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Badejo|Jandu\{s|Linguado", token.next_token.next_token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("Cidade", token.word) and regex("de", token.next_token.word) and regex("São", token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.next_token.next_token.deps):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                
            if regex("produção|descobertas|entre|gás", token.word) and regex("de|os", token.next_token.word) and regex("estes|novos|dois", token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"
                
            if regex("Trilha\.", token.word) and regex("B=BACIA", token.deps):
                token.deps = "B=CAMPO"
                
            if regex("explotação", token.word) and regex("para", token.next_token.word) and regex("os", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("Campos", token.next_token.next_token.next_token.next_token.word) and regex("situados", token.next_token.next_token.next_token.next_token.next_token.word) and regex("B=BACIA", token.next_token.next_token.next_token.next_token.deps):
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"
                
            # nas regras de UNIDADE LITO

            if regex("Coquinas", token.word) and regex("B=UNIDADE_LITO", token.deps):
                token.deps = "B=ROCHA"

            # ANCHOR Regras Tati (23/05/2023)

            # regras np1 prata
            # TATI 04/23

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("SZ.?", token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("Caioba\~", token.lemma) and regex("Dourado", token.next_token.lemma):
                token.next_token.deps = "B=CAMPO"

            if regex("Luiz", token.lemma) and regex("são", token.previous_token.word) and regex("e", token.previous_token.previous_token.lemma):
                token.previous_token.deps = "B=CAMPO"
                token.deps = "I=CAMPO"

            if regex("campo", token.head_token.lemma) and regex("de", token.previous_token.previous_token.lemma) and regex("o", token.previous_token.lemma) and regex("Taboleiro|Tebeleiro", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Martins", token.next_token.next_token.next_token.lemma):
                token.previous_token.previous_token.deps = "I=CAMPO"
                token.previous_token.deps = "I=CAMPO"
                token.deps = "I=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.head_token.lemma) and regex("de", token.previous_token.previous_token.lemma) and regex("o", token.previous_token.lemma) and regex("Teboleiro", token.lemma) and regex("PUNCT", token.next_token.upos) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("Martins", token.next_token.next_token.next_token.next_token.lemma):
                token.head_token.deps = "B=CAMPO"
                token.previous_token.previous_token.deps = "I=CAMPO"
                token.previous_token.deps = "I=CAMPO"
                token.deps = "I=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Teboleiro", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Mertins", token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Áres|áreas", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Taboleiro|Teboleire", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Martins", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Araçis", token.lemma) and regex("de", token.previous_token.lemma):
                token.deps = "I=CAMPO"
                token.previous_token.deps = "I=CAMPO"

            if regex("Carm6polis", token.lemma) and regex("em", token.previous_token.lemma):
                token.deps = "B=CAMPO"

            if regex("Carm6polis", token.lemma) and regex("de", token.previous_token.lemma) and regex("campo", token.previous_token.previous_token.lemma):
                token.deps = "I=CAMPO"
                token.previous_token.deps = "I=CAMPO"
                token.previous_token.previous_token.deps = "B=CAMPO"

            if regex("Namor\~", token.lemma) and regex("de", token.previous_token.lemma):
                token.deps = "I=CAMPO"
                token.previous_token.deps = "I=CAMPO"

            if regex("Rio", token.word) and regex("são", token.next_token.word) and regex("Mateus", token.next_token.next_token.word):
                token.next_token.next_token.deps = "I=CAMPO"

            if regex(",", token.word) and regex("sio", token.next_token.word) and regex("Mateus", token.next_token.next_token.word):
                token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("de", token.word) and regex("São", token.next_token.word) and regex("Miguel", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Cidade", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("São", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("São", token.word) and regex("Miguel", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Cidade", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("São", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.head_token.lemma) and regex("de", token.previous_token.lemma) and regex("D\.Jo\~o\-Mar", token.lemma):
                token.previous_token.deps = "I=CAMPO"
                token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("E~", token.next_token.next_token.word) and regex("chova", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("camposupergigante|campps|camp~s", token.word):
                token.deps = "B=CAMPO"

            if regex("campo·", token.word) and regex("de", token.next_token.word) and regex("Linguado", token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("camp'o", token.word) and regex("-'", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Caçio", token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("~e", token.next_token.word) and regex("Majnoon", token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("Nahr", token.next_token.next_token.word) and regex("Umr..", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Linguado", token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.word) and regex("Pampo", token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Bandejo", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Trilha", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("L~", token.word) and regex("guado", token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("Lin", token.next_token.next_token.word) and regex("guado", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("formação", token.word) and regex("campos", token.next_token.word) and regex("/Carapebu~·ouve", token.next_token.next_token.word):
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("Formações", token.word) and regex("Pendência", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("Alagamar", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("Ub~", token.next_token.next_token.next_token.next_token.next_token.word) and regex("rana", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Macau", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"

            if regex("Formações", token.word) and regex("\(", token.next_token.word) and regex("Barra", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Itiuba", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Serraria", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("Barra", token.word) and regex("de", token.next_token.word) and regex("Itiuba", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("Coqueiro", token.next_token.next_token.next_token.next_token.word) and regex("Seco.?", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("produtor", token.lemma) and regex("subcomercial", token.next_token.lemma):
                token.deps = "B=POÇO_Q"
                token.next_token.deps = "B=POÇO_Q"

            if regex("perfuraç~es|rações", token.word) and regex("pioneiras", token.next_token.word):
                token.next_token.deps = "B=POÇO_T"

            if regex("pioneiro", token.lemma) and regex("NUM|PROPN|NOUN", token.next_token.upos):
                token.deps = "B=POÇO_T"
                token.next_token.deps = "B=POÇO"

            if regex("considerado", token.word) and regex("9", token.next_token.word) and regex("como", token.next_token.next_token.word) and regex("pioneiros?", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO_T"

            if regex("consi", token.word) and regex("derado", token.next_token.word) and regex("como", token.next_token.next_token.word) and regex("pioneiro", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO_T"

            if regex("classi", token.word) and regex("ficar", token.next_token.word) and regex("como", token.next_token.next_token.word) and regex("estratigrafico", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO_T"

            if regex("descobridor", token.lemma) and regex("1-SES-1A", token.next_token.word):
                token.deps = "B=POÇO_Q"

            if regex("poços", token.word) and regex("se", token.next_token.word) and regex("revelaram", token.next_token.next_token.word) and regex("secos", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO_Q"

            if regex("foram", token.word) and regex("abandonsdos", token.next_token.word) and regex("como", token.next_token.next_token.word) and regex("secos", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO_Q"

            if regex("1-SES-56", token.word) and regex(",", token.next_token.word) and regex("Penedo/Barra", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Itiuba", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("pogos", token.word) and regex("CP-329", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("539", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("1082", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("pecos|pocos", token.word) and regex("Injetores|produtores|injetores", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "B=POÇO_R"

            if regex("produtores", token.word) and regex("injetores", token.head_token.word):
                token.deps = "B=POÇO_R"

            if regex("produtores", token.head_token.word) and regex("injetores", token.word):
                token.deps = "B=POÇO_R"

            if regex("poços", token.word) and regex("4.-RJS-139-A", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("l-RJS-153", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("3-RJS-157", token.next_token.next_token.next_token.next_token.next_token.word) and regex("C", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("7-LI-3-RJS..", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("7-AG-16D-RNS", token.word) and regex(",", token.next_token.word) and regex("7-AG", token.next_token.next_token.word) and regex("-lSD-RNS", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("7-AG-19DB-RNS.", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("conj", token.deprel) and regex("B=POÇO", token.head_token.head_token.deps) and regex("I=POÇO", token.head_token.head_token.next_token.deps) and regex("O", token.deps) and regex("NUM", token.upos):
                token.deps = "B=POÇO"

            if regex("O", token.deps) and regex("conj", token.deprel) and regex("NUM", token.upos) and regex("B=POÇO", token.head_token.head_token.deps) and regex("B=POÇO", token.head_token.deps):
                token.deps = "B=POÇO"

            if regex("PROPN", token.upos) and regex("O", token.deps) and regex("B=POÇO", token.head_token.deps) and regex("conj", token.deprel) and regex("B=POÇO", token.head_token.head_token.deps) and regex("\(", token.head_token.previous_token.word):
                token.deps = "B=POÇO"

            if regex("pecos|Pecos|peços", token.word):
                token.deps = "B=POÇO"

            if regex("Pecos", token.word) and regex("FU-133", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("FU-136", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("pecos", token.word) and regex("FU-133", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("FU-134", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("FU-135", token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("FU-136", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("PROPN", token.upos) and regex("pecos", token.head_token.word) and regex("appos", token.deprel):
                token.deps = "B=POÇO"

            if regex("um|O", token.word) and regex("injetor", token.next_token.word) and regex("mergulho|CP-946", token.next_token.next_token.word):
                token.next_token.deps = "B=POÇO_R"

            if regex("EN\-l", token.word):
                token.deps = "B=POÇO"

            if regex("com", token.word) and regex("poços", token.next_token.word) and regex("prod·ti", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=POÇO_R"

            if regex("pecos", token.word) and regex("GA-50", token.next_token.word) and regex("eGA-53", token.next_token.next_token.word):
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.deps = "B=POÇO"

            if regex("poç6s?", token.word):
                token.deps = "B=POÇO"

            if regex("produto", token.word) and regex("res", token.next_token.word):
                token.deps = "B=POÇO_R"
                token.next_token.deps = "I=POÇO_R"

            if regex("injeção", token.word) and regex("de", token.next_token.word) and regex("igua", token.next_token.next_token.word):
                token.deps = "B=POÇO_R"
                token.next_token.deps = "I=POÇO_R"
                token.next_token.next_token.deps = "I=POÇO_R"

            if regex("p~", token.word) and regex("ços", token.next_token.word) and regex("explorat6rios", token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.deps = "B=POÇO_T"

            if regex("poços", token.word) and regex("\-", token.next_token.word) and regex("expl~ratõrios", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=POÇO_T"

            if regex("explora", token.word) and regex("t~rios?", token.next_token.word):
                token.deps = "B=POÇO_T"
                token.next_token.deps = "I=POÇO_T"

            if regex("pio|pi~", token.word) and regex("neiros?|neiros", token.next_token.word):
                token.deps = "B=POÇO_T"
                token.next_token.deps = "I=POÇO_T"

            if regex("microporosidade|intercristalino|fenestral|intragranular|intrapartículo", token.lemma):
                token.deps = "B=TIPO_POROSIDADE"

            if regex("intergranular", token.lemma) and regex("porosidade", token.head_token.lemma):
                token.deps = "B=TIPO_POROSIDADE"

            if regex("geração", token.word) and regex("de", token.next_token.word) and regex("hidroçarbonetos", token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("geração", token.word) and regex("e", token.next_token.word) and regex("trapeamento", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("hidrocarbonetos", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("geração", token.word) and regex("de", token.next_token.word) and regex("volumes", token.next_token.next_token.word) and regex("significativos", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("hidrocarbonetos", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("potencial|condições", token.word) and regex("de", token.next_token.word) and regex("geração", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=EVENTO_PETRO"

            if regex("ca1careo|calcareo|-Calcáreo", token.word):
                token.deps = "B=ROCHA"

            if regex("cal", token.word) and regex("cário", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("si1titos", token.word):
                token.deps = "B=ROCHA"

            if regex("fo1he1hos|fo1he1hoB|folh·elhos|~01he1hos|folhelho8|olhelhos", token.word):
                token.deps = "B=ROCHA"

            if regex("Igneas", token.word) and regex("Rochas", token.previous_token.word):
                token.previous_token.deps = "I=ROCHA"
                token.deps = "B=ROCHA"

            if regex("diabá~io|arBnitos", token.word):
                token.deps = "B=ROCHA"

            if regex("dia", token.word) and regex("básio", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("roohas?", token.word):
                token.deps = "B=ROCHA"

            if regex("Ard6sias?", token.word):
                token.deps = "B=ROCHA"

            if regex("a", token.word) and regex("vinda", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("coordenador", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("p01|ub|TP-1|TP-2|TP-3|i1|Cn|E&P-SEAL/GERET|I11|Set\.|Aracaju|1m3|p1|i5|sp|i8", token.word) and not regex("Membro", token.previous_token.word):
                token.deps = "O"

            if regex("Producao", token.word) and regex("Construir", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Início", token.word) and regex("de", token.next_token.word) and regex("Operação", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            if regex("Blocos", token.word) and regex("1", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("1A/CPS-3B", token.next_token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"

            if regex("Blocos?", token.word):
                token.deps = "O"

            if regex("Cinzento|Ibirama|Itaquá", token.lemma):
                token.deps = "O"

            if regex("Itupo|Vidal|Trombudo|Pedra", token.lemma) and regex("ranga|Ramos|Central|Branca", token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Prove", token.lemma) and regex("Teresina.", token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Rio", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Oeste", token.next_token.next_token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"

            if regex("rio|Rio", token.word) and regex("Dois", token.next_token.word) and regex("Irmãos", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            if regex("Relatório", token.word) and regex("Interno", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("_\.|angico|cança|est\~|Fig\.18|Jul\.|Qulidust|RPNE/DIAREV/SETEC|sardinha|serraria|SirI|to", token.lemma):
                token.deps = "O"

            if regex("cação", token.lemma):
                token.deps = "O"

            if regex("cé", token.previous_token.word) and regex("lula", token.lemma):
                token.deps = "O"

            if regex("mini", token.lemma) and regex("mizar", token.next_token.lemma) and regex("e", token.previous_token.lemma) and regex("desembolso", token.next_token.next_token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Mohriak|Silva|Silveira|Machado|Gamboa|Freitas", token.lemma):
                token.deps = "O"

            if regex("peroba", token.lemma) and regex("cedro", token.previous_token.previous_token.lemma):
                token.deps = "O"
                token.previous_token.previous_token.deps = "O"

            if regex("tangar", token.lemma):
                token.deps = "O"

            if regex("Tie", token.lemma) and regex("Backpara", token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Campo", token.lemma) and regex("Grande", token.next_token.lemma):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("turma|equipe|amostra|projeto|experiência", token.lemma) and regex("de", token.next_token.lemma) and regex("campo", token.next_token.next_token.lemma):
                token.next_token.next_token.deps = "O"

            if regex("campo", token.lemma) and regex("de", token.next_token.lemma) and regex("engenharia", token.next_token.next_token.next_token.lemma):
                token.deps = "O"

            if regex("campo", token.lemma) and regex("o", token.previous_token.word) and regex("em", token.previous_token.previous_token.word) and regex("serviço", token.previous_token.previous_token.previous_token.lemma):
                token.deps = "O"

            if regex("pesquisa", token.lemma) and regex("campo", token.next_token.next_token.next_token.next_token.lemma):
                token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("conhe", token.lemma) and regex("cimento", token.next_token.lemma):
                token.next_token.deps = "O"

            if regex("cre~­", token.word) and regex("cimento", token.next_token.word):
                token.next_token.deps = "O"

            if regex("cres", token.word) and regex("cimento", token.next_token.word):
                token.next_token.deps = "O"

            if regex("Aqu", token.word) and regex("e", token.next_token.word) and regex("cimento", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"

            if regex("..", token.word) and regex("Lapa", token.next_token.word) and regex("..", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            if regex("Pampo", token.word) and regex("faie", token.next_token.word) and regex("11", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            if regex("Mutum", token.word) and regex("to", token.next_token.word) and regex("about", token.next_token.next_token.word) and regex("400", token.next_token.next_token.next_token.word) and regex("metera", token.next_token.next_token.next_token.next_token.word) and regex("near", token.next_token.next_token.next_token.next_token.next_token.word) and regex("CaiapOnia", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("Guamari", token.lemma) and regex("ati", token.next_token.lemma):
                token.next_token.deps = "O"

            if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("São", token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Cy", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("LOCACOES", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("arenito", token.word) and regex("Namorado", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.word) and regex("Área", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("serraria", token.word) and regex("Jaxinal", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Porto", token.next_token.next_token.next_token.word) and regex("Aleixo", token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("plataforma", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Namorado", token.next_token.next_token.next_token.next_token.next_token.word) and regex("PNA-2", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("Piranema", token.word) and regex("Services", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("Dourado", token.word) and regex("atraves", token.next_token.word):
                token.next_token.deps = "O"

            if regex("reservatório", token.word) and regex("Namorado", token.next_token.word) and regex("ob", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"

            if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("Linguado", token.next_token.next_token.word) and regex("per", token.next_token.next_token.next_token.word) and regex("mitirá", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"

            if regex("o", token.word) and regex("Campo", token.next_token.word) and regex("pro-", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"

            if regex("Tangará", token.word) and regex("·", token.next_token.word):
                token.next_token.deps = "O"

            if regex("Um", token.word) and regex("especial", token.next_token.word) and regex("destaque", token.next_token.next_token.word):
                token.next_token.deps = "O"

            if regex("característica", token.word) and regex("toda", token.next_token.word) and regex("especial", token.next_token.next_token.word) and regex("ocorre", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"

            if regex("L-2", token.word) and regex("vide", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("poco", token.word) and regex("futuro", token.next_token.word):
                token.next_token.deps = "O"

            if regex("poço", token.word) and regex("/manifold", token.next_token.word):
                token.next_token.deps = "O"

            if regex("FU-43", token.word) and regex("Considerar", token.next_token.word):
                token.next_token.deps = "O"

            if regex("poço", token.word) and regex("PRODUÇÃO", token.next_token.word):
                token.next_token.deps = "O"

            if regex("poços|PAF-7-MA|TH.6=Al|poço|Poco", token.word) and regex("c|const|disten.|duas|ma|situ", token.next_token.word):
                token.next_token.deps = "O"

            if regex("I18", token.word) and regex("~SlllkOa", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("6", token.word) and regex("p~", token.next_token.word) and regex("ços", token.next_token.next_token.word):
                token.deps = "O"

            if regex("es-tratierahcos", token.word):
                token.deps = "B=POÇO_T"

            if regex("considerar", token.lemma) and regex("como", token.next_token.word) and regex("pioneiro", token.next_token.next_token.lemma):
                token.next_token.next_token.deps = "B=POÇO_T"

            if regex("furos", token.word) and regex("estratigr[áa]ficos", token.next_token.word):
                token.next_token.deps = "B=POÇO_T"

            if regex("os", token.word) and regex("furos", token.next_token.word) and regex("estratigráficos", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("pioneiros", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=POÇO_T"

            if regex("O", token.word) and regex("injetor", token.next_token.word) and regex("próximo", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("CP-1254", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=POÇO_R"

            if regex("injetor", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("CP-262", token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO_R"

            if regex("injetor", token.word) and regex("abaixo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("CP-1254", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO_R"

            if regex("distância", token.word) and regex("entre", token.next_token.word) and regex("injetores", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=POÇO_R"

            if regex("são", token.word) and regex("produtores", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("óleo", token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=POÇO_R"

            if regex("poços", token.word) and regex("em", token.next_token.word) and regex("produção", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=POÇO_R"

            if regex("2", token.word) and regex("injetores", token.next_token.word):
                token.next_token.deps = "B=POÇO_R"

            if regex("Vugs", token.word):
                token.deps = "B=TIPO_POROSIDADE"

            #regras de revisão pós devolução de dúvidas - 16/06/2023

            if regex("gas|6leo", token.word) and regex("combus.*", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_o"
                
            if regex("arca|aroa", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("alto", token.next_token.next_token.next_token.word) and regex("Jacuipe", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("alto", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Pojuca", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("produção", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Alagoas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("área|SEDCO", token.word) and regex("de|em", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Foz", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Amazonas", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("3|uma|50", token.word) and regex("falhas|falha", token.next_token.word) and regex("por|em", token.next_token.next_token.word) and regex("tubos|4|furos", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("ocasião|de|Dixon", token.word) and regex("de|análise|admite", token.next_token.word) and regex("uma|de|duas", token.next_token.next_token.word) and regex("falha|falhas", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("S\~rie", token.word) and regex("Passa", token.next_token.word) and regex("Dois", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            # regras pós respostas da Sofia 14/06

            if regex("Estação", token.word) and regex("Coletora", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Fazenda", token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.word) and regex("João", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("EN\-l", token.word):
                token.deps = "O"

            if regex("migração", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("sal", token.next_token.next_token.next_token.word):
                token.deps = "O"

            if regex("migração", token.word) and regex("de", token.next_token.word) and regex("finos", token.next_token.next_token.word):
                token.deps = "O"

            if regex("migração", token.word) and regex("de", token.next_token.word) and regex("kaolinita", token.next_token.next_token.word):
                token.deps = "O"

            if regex("vinda", token.word) and regex("a", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("descobridor", token.word) and regex("3", token.next_token.word):
                token.deps = "B=POÇO_Q"

            if regex("típicamente", token.word) and regex("estratigráfico", token.next_token.word):
                token.next_token.deps = "B=POÇO_T"

            if regex("calcarenito", token.word) and regex(",", token.next_token.word) and regex("Macae", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"

            if regex("para", token.word) and regex("geração", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("vapor", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"

            if regex("baseada", token.word) and regex("em", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("geração", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=EVENTO_PETRO"

            if regex("modelo", token.word) and regex("alternativo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("geração", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=EVENTO_PETRO"

            if regex("cavidades", token.word) and regex("alongadas", token.next_token.word):
                token.deps = "B=TIPO_POROSIDADE"

            if regex("canais", token.word) and regex("privilegiados|preferenciais", token.next_token.word):
                token.deps = "B=TIPO_POROSIDADE"

            if regex("[Ii]ndício", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word):
                token.deps = "B=POÇO_Q"
                

        except AttributeError as e:
            print(str(e))
            
corpus.save(files['silver'])
print("[OK] Saved to %s" % files['silver'])

# criando corpus silver para comparar com o golden
silver = estrutura_ud.Corpus()
silver.build(corpus.to_str())

# ANCHOR GOLDEN
for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        try:

            # ANCHOR TATI GOLDEN 07/06/2023
            # matriz de confusão
            if regex("Teboleiro", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("M[ae]rtins", token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo~", token.word) and regex("de", token.next_token.word) and regex("Alto", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Rodrigues", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Em", token.word) and regex("Janduís", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("Cachoeirlnha", token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("dados", token.word) and regex("reais", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("Carmópolis", token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("Existem", token.word) and regex("atualmente", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("Campo\.", token.word):
                token.deps = "B=CAMPO"

            if regex("conhecimento", token.word) and regex("geológico", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("campo", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("Campei", token.word) and regex("de", token.next_token.word) and regex("Namorado", token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("Bloco", token.word) and regex("Norte", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Buracica", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("sedimento\.", token.word):
                token.deps = "B=NÃOCONSOLID"

            if regex("cascal", token.word):
                token.deps = "B=NÃOCONSOLID"

            if regex("argila\.", token.word):
                token.deps = "B=NÃOCONSOLID"

            if regex("argila\~", token.word):
                token.deps = "B=NÃOCONSOLID"

            if regex("alqumas", token.word) and regex("argilas", token.next_token.word):
                token.next_token.deps = "B=NÃOCONSOLID"

            if regex("pogo|pogos|Poços|poçes|pogo\|poço-foi", token.word):
                token.deps = "B=POÇO"

            if regex("AG-2,", token.word) and regex(".BA", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("AG.*", token.next_token.next_token.next_token.word) and regex(";199-BA.", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.deps = "I=POÇO"

            if regex("PAF", token.word) and regex("-4Ro1U", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("PAF-l-IU", token.word) and regex(",", token.next_token.word) and regex("PAF-2-LU", token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.word) and regex("PAF-3-flA", token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.word) and regex("f", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("iF-7-MA", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("PAF-4R-KA", token.word) and regex("e", token.next_token.word) and regex("RP-l-HP", token.next_token.next_token.word) and regex("..", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("CGst-l-MA", token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("CGst-2-MA", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("SLst-l-MA", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("BI", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("t-l-MA", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("VGst-l-MA", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("p~", token.word) and regex("ço", token.next_token.word) and regex("produtor", token.next_token.next_token.word) and regex("foi", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("7-MO-14-RN", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.deps = "B=POÇO_R"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("Poço", token.word) and regex("de", token.next_token.word) and regex("injeção", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.next_token.deps = "B=POÇO_R"
                token.next_token.next_token.next_token.deps = "I=POÇO_R"
                token.next_token.next_token.next_token.next_token.deps = "I=POÇO_R"

            if regex("como", token.word) and regex("FU-133", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex("FU-134", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("FU-135", token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("FU-136", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("3-LI-4", token.word) and regex("~", token.next_token.word) and regex("RJS", token.next_token.next_token.word):
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.deps = "I=POÇO"

            if regex("po", token.word) and regex("ço", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("poço", token.word) and regex("estr", token.next_token.word) and regex(",", token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.word) and regex("1tigráfico", token.next_token.next_token.next_token.next_token.word) and regex("2-CST-I-RJ", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=POÇO_T"
                token.next_token.next_token.deps = "I=POÇO_T"
                token.next_token.next_token.next_token.deps = "I=POÇO_T"
                token.next_token.next_token.next_token.next_token.deps = "I=POÇO_T"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=POÇO"

            if regex("l", token.word) and regex("RJS-IlO", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("O", token.deps) and regex("\[-FU-94-AL|7-EN-14D-RJS..|Pl1F-7-UA|PAF-1-I1IA|PAF-3-UA|PA~4R-MA|PA~-7-MA|PA_-7-11A|9-FZB-1-CE..|l-RNS-7|l-RNS-13|7-AG-14D-RNS.|PIR-184|PIR-153|PIR-09|PIR-009|SES-05|CP-910|SES-113|SES-117|PDO-1|7-SHC-12|7-LI-03-RJS|7-BD-llA-RJS|l-RJS-49|l-RJS-305|2-CST-I-RJ|3-6G-24-RJS.|4~RJS-139A|l-RJS-46|l-RJS-186|l-RJS-90|i-RJS.-12|1~RJS-159|PB-1-RO", token.word):
                token.deps = "B=POÇO"

            if regex("9-SZ-16S-SE.|CP-0137|4-RJS", token.word):
                token.deps = "B=POÇO"

            if regex("poçosurgente", token.word):
                token.deps = "B=POÇO"

            if regex("poçosP~E", token.word):
                token.deps = "B=POÇO"

            if regex("CP", token.word) and regex("1215", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("l-RNS", token.word) and regex("·", token.next_token.word) and regex("7", token.next_token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"
                token.next_token.next_token.deps = "I=POÇO"

            if regex("Ta\'201eiro|Taboleire", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Martins", token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("Agu", token.next_token.next_token.word) and regex("lha", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("For~", token.word) and regex("mação", token.next_token.word) and regex("Berra", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Itiuba", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("Plataforma", token.word) and regex("de", token.next_token.word) and regex("S[aã]o", token.next_token.next_token.word) and regex("Miguel", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"

            if regex("Coqueiro", token.word) and regex("Seco-Coqueiro", token.next_token.word) and regex("Seco", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("[Cc]ampo", token.word) and regex("de", token.next_token.word) and regex("En", token.next_token.next_token.word) and regex("chova", token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("·", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Linguado", token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("deUba-rana", token.next_token.word):
                token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("d.e", token.next_token.word) and regex("Guaricema", token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("D.", token.next_token.next_token.word) and regex("Joio", token.next_token.next_token.next_token.word) and regex("Terra", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("Majnoon", token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("L.agoa|Lagoa", token.word) and regex("Pardé|Pa~da", token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"

            if regex("Campo", token.word) and regex("de", token.next_token.word) and regex(".", token.next_token.next_token.word) and regex("Sirizirih.", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

            if regex("[Ss]istema", token.word) and regex("de", token.next_token.word) and regex("[Pp]rodução", token.next_token.next_token.word) and regex("[Aa]ntecipada", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Enchova", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("Sistema", token.word) and regex("En", token.next_token.word) and regex("chova-Leste", token.next_token.next_token.word):
                token.next_token.deps = "B=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"

            if regex("Sistema", token.word) and regex("Transitório|Provisório", token.next_token.word) and regex("de|de·", token.next_token.next_token.word) and regex("Garoupa", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("deCorvina", token.word):
                token.deps = "B=CAMPO"

            if regex("Sistema", token.word) and regex("de", token.next_token.word) and regex("Produção|Produ", token.next_token.next_token.word) and regex("ção|Anteci", token.next_token.next_token.next_token.word) and regex("Antecipada|pada", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Corvina", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"

            if regex("rochas?", token.word) and regex("reservat[óo]rios?", token.next_token.word):
                token.deps = "B=EVENTO_PETRO"
                token.next_token.deps = "I=EVENTO_PETRO"

            if regex("~oço", token.word) and regex("7-ET-8S-RN.", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("Fluido", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Poço", token.next_token.next_token.next_token.word) and regex("7-LI-3-RJS", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "B=POÇO"
                token.next_token.next_token.next_token.next_token.deps = "I=POÇO"

            if regex("poço", token.word) and regex("PB-I-RO", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("5.6.2-Poço", token.word) and regex("9", token.next_token.word):
                token.deps = "B=POÇO"
                token.next_token.deps = "I=POÇO"

            if regex("rochas", token.word) and regex("vulcinicas", token.next_token.word) and regex("\(", token.next_token.next_token.word) and regex("Basaltos", token.next_token.next_token.next_token.word) and regex("\)", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "I=ROCHA"
                token.next_token.next_token.next_token.deps = "B=ROCHA"

            if regex("extrusões", token.word) and regex("ígneas", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("instrusões", token.word) and regex("ígneas", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("falhas", token.next_token.next_token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("calcário", token.lemma) and regex("Macaé", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"

            if regex("12-Folhelho", token.word) and regex("Iratí", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "B=UNIDADE_LITO"

            if regex("carbonatos", token.word) and regex("Pimenta", token.next_token.word) and regex("Bueno", token.next_token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"

            if regex("Barra", token.word) and regex("Nova", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("geração", token.word) and regex("moderada", token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("Geração", token.word) and regex("local", token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("322B70B3A24C0BC4E0534EEB1D0A84C7-171|322B70B3A24C0BC4E0534EEB1D0A84C7-170|322B70B3A24C0BC4E0534EEB1D0A84C7-169|322B70B3A24C0BC4E0534EEB1D0A84C7-168|322B70B3A24C0BC4E0534EEB1D0A84C7-167|37624BDE76A33A5DE0534EEB1D0A2F3F-59|37624BDE76A33A5DE0534EEB1D0A2F3F-62", sentence.sent_id ) and regex("Geração|Geracao", token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("trapp.?|trapa.", token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("geraçao", token.word) and regex(",", token.next_token.word) and regex("migraçio", token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"
                token.next_token.next_token.deps = "B=EVENTO_PETRO"

            if regex("migraçio|migraçao", token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("37624BDE76A33A5DE0534EEB1D0A2F3F-40|37624BDE76A33A5DE0534EEB1D0A2F3F-41", sentence.sent_id) and regex("geradoras", token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("gera", token.word) and regex("ção", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("hidrocarbonetos", token.next_token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"
                token.next_token.deps = "I=EVENTO_PETRO"

            if regex("fontes", token.word) and regex("geradoras", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("61eo.", token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=EVENTO_PETRO"
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"

            if regex("modelo", token.word) and regex("alternativo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("geração", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=EVENTO_PETRO"

            if regex("geração", token.word) and regex("de", token.next_token.word) and regex("vapor", token.next_token.next_token.word):
                token.deps = "B=EVENTO_PETRO"

            if regex("conglomerados|jgneas|Ígneas", token.word):
                token.deps = "B=ROCHA"

            if regex("conglome", token.word) and regex("rados", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("anfibólios?|gipsite|grenito|iltitos?|folhelhoa|arenito8|areDit08|arenito.|folhelh08|arenit08|Folhelhossilticos|eiltitos|loessitos|ti1itos|folhelhosoem|rochaa|limonita|limonita.|Arenitojfolhelho|folhe1hos|tilito&|anidritas|diarnictitos|diabáaio|crenitos|arenites|Evaporitos|Rochas|Coquinas|diabási.|diamictito.|Packstones|sideritito|camalita|Siltiio", token.word):
                token.deps = "B=ROCHA"

            if regex("rochas", token.word) and regex("vulcânicas", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("carbonáticas", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=ROCHA"

            if regex("Arenlto.*", token.word):
                token.deps = "B=ROCHA"

            if regex("139AC80D5ADC2327E0534EEB1D0AAFD4-45|139AC1F86906255FE0534EEB1D0A15DC-126", sentence.sent_id) and regex("arenitos|Folhelhos", token.word):
                token.deps = "B=ROCHA"

            if regex("areni|Areni|folhe|are|coqui|calcirru|cal", token.word) and regex("tos|to|lhos|nitos?|nas|\.ditos|carenito", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("a", token.word) and regex("nenitos", token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"

            if regex("coqui|areni", token.word) and regex("em|t", token.next_token.word) and regex("as|os", token.next_token.next_token.word):
                token.deps = "B=ROCHA"
                token.next_token.deps = "I=ROCHA"
                token.next_token.next_token.deps = "I=ROCHA"

            if regex("Marituba", token.word) and regex("e", token.next_token.word) and regex("Mosqueiro", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"

            if regex("Itararé", token.word) and regex("e", token.next_token.word) and regex("Tubarão", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"

            if regex("Usina", token.word) and regex("de", token.next_token.word) and regex("São", token.next_token.next_token.word) and regex("Mateus", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"

            if regex("PDF-2|P5|cn|p10", token.word):
                token.deps = "O"

            if regex("Relatórios|Hotel", token.word) and regex("Técnicos|Termas", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Campo|Mossoró", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"

            if regex("Guaricema", token.word) and regex("Previsão", token.next_token.word) and regex("Anual", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Produção", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Oleo", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Gás", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("Movimentação", token.word) and regex("de", token.next_token.word) and regex("Gás", token.next_token.next_token.word) and regex("\(", token.next_token.next_token.next_token.word) and regex("1995", token.next_token.next_token.next_token.next_token.word) and regex("\)", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Páãa.", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            if regex("Rio", token.word) and regex("Sao", token.next_token.word) and regex("Miguel", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"

            if regex("Mato", token.word) and regex("Grosso", token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"

            if regex("campo", token.word) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("exploração", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("petróleo|petr&eo|petgleo", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"

            if regex("Franco|Frade|Maracujá|Tubarao|Carnaubais|Viana", token.word):
                token.deps = "O"

            # ANCHOR MCLARA 13/06/2023

            #BACIA - 06/2023

            if regex("Ba\.cia", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paruná", token.next_token.next_token.next_token.word):
                token.deps = "B=BACIA"
                token.next_token.deps = "I=BACIA"
                token.next_token.next_token.deps = "I=BACIA"
                token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("o", token.word) and regex("Rec\~ncavo", token.next_token.word) and regex("i", token.next_token.next_token.word) and regex("uma", token.next_token.next_token.next_token.word) and regex("bacia", token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=BACIA"
                
            if regex("Campos", token.word) and regex("de", token.next_token.word) and regex("Badejo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("Trilha", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=CAMPO"
                token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.deps = "I=CAMPO"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "B=CAMPO"
                
            if regex("Carlos", token.word) and regex("W\.", token.next_token.word) and regex("Campos", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            #ESTRUTURA_FÍSICA - 06/2023

            if regex("concre", token.word) and regex("ções", token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("contactG1I", token.word) and regex("abruptos", token.next_token.word) and regex("\,", token.next_token.next_token.word) and regex("marcas", token.next_token.next_token.next_token.word) and regex("onduladas", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.next_token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("Estruturaa", token.word) and regex("clar\~mente", token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                
            if regex("filmes", token.word) and regex("de", token.next_token.word) and regex("arailas", token.next_token.next_token.word):
                token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("finamente", token.word) and regex("micáceo", token.next_token.word) and regex("\,", token.next_token.next_token.word) and regex("maciço\.", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=ESTRUTURA_FÍSICA"
                
            if regex("onde", token.word) and regex("exi\~tem", token.next_token.word) and regex("es", token.next_token.next_token.word) and regex("truturas", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=ESTRUTURA_FÍSICA"
                token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
                
            if regex("espalhados", token.word) and regex("por", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("matriz", token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.word) and regex("maciço\.", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=ESTRUTURA_FÍSICA"
                
            #FLUIDODATERRA_i - 06/2023

            if regex("acumulacoes", token.word) and regex("de", token.next_token.word) and regex("61eo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("acumulação|expulsao", token.word) and regex("de", token.next_token.word) and regex("gas|petroleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("a", token.word) and regex("água", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("longo", token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("reservatório", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("seu", token.next_token.next_token.next_token.word) and regex("aquifero", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("gas", token.head_token.word) and regex("injeção", token.head_token.head_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("poços", token.word) and regex("ma", token.next_token.word) and regex("\~s", token.next_token.next_token.word) and regex("antigps", token.next_token.next_token.next_token.word) and regex("já", token.next_token.next_token.next_token.next_token.word) and regex("produzem", token.next_token.next_token.next_token.next_token.next_token.word) and regex("com", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("94", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("\%", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("água\.", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("hidrocarbonetos\/g|hidroçarbonetos|hidrocartonetos", token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("hi|hidro|hidrocar|hidrocarbo", token.word) and regex("drocarbonetos|carbonetos|bonetos|netos", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("injeção|indioios|altIumulações", token.word) and regex("de", token.next_token.word) and regex("âgtia|hidrooarbonetos|hidrocarbonêtos", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("m3", token.word) and regex("\/", token.next_token.word) and regex("dia", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("na", token.next_token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.next_token.word) and regex("gás\.\.", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("contido", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.word) and regex("arenitos", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("em", token.next_token.word) and regex("jazida", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("em", token.next_token.word) and regex("solução", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gás", token.word) and regex("injetado", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("nao", token.next_token.word) and regex("associado", token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("gas", token.word) and regex("produzido", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("Linguado", token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("m\º|m3", token.word) and regex("de", token.next_token.word) and regex("gás\.", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("de", token.word) and regex("hidrocerbonetos", token.next_token.word) and regex("sté", token.next_token.next_token.word):
                token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("produção|injeção", token.word) and regex("de", token.next_token.word) and regex("água\.|petroleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injeção", token.word) and regex("de", token.next_token.word) and regex("água", token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.word) and regex("gás\.", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injeçio|saturação|injecao|injeção|produtor", token.word) and regex("de", token.next_token.word) and regex("gás\.|água\.|gas|õleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("jdia", token.word) and regex("de", token.next_token.word) and regex("gás\.", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("superficiais", token.word) and regex("de", token.next_token.word) and regex("petroleo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("água", token.word) and regex("para", token.next_token.word) and regex("geração", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("vapor", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("injetores", token.word) and regex(",", token.next_token.word) and regex("impedindo", token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("líquidos", token.word) and regex("contidos", token.next_token.word) and regex("em", token.next_token.next_token.word) and regex("este", token.next_token.next_token.next_token.word) and regex("gás\.", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("petroleo", token.word) and regex("bruto", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                
            if regex("porta", token.word) and regex("dora", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("óleo", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("portadora", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("hidrocarbonetos", token.word) and regex("são", token.next_token.word) and regex("portadores", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("gas", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("produção", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.word) and regex("água", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("gás\.", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("produtores", token.word) and regex("de", token.next_token.word) and regex("gas|61eo", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("saturaçÃo", token.word) and regex("4e", token.next_token.word) and regex("água\.", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("separação", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("gás\.", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("porque", token.word) and regex("a", token.next_token.word) and regex("água", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("CP\-592", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("volume", token.word) and regex("original", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("6leo\(", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("Sistemas", token.word) and regex("Compactos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Injeção", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            if regex("Injeção", token.word) and regex("de", token.next_token.word) and regex("Água", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
                
            #FLUIDO - 06/2023
                
            if regex("51", token.word) and regex("eo", token.next_token.word) and regex("diesel", token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDO"
                
            if regex("rocha", token.word) and regex("\,", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.word) and regex("fluidos", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=FLUIDO"
                
            if regex("de", token.word) and regex("o", token.next_token.word) and regex("fluido", token.next_token.next_token.word) and regex("base", token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=FLUIDO"
                
            if regex("Tais", token.word) and regex("poços", token.next_token.word) and regex("deverão", token.next_token.next_token.word) and regex("fluido", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDO"
                
            #UNIDADE_CRONO - 06/2023

            if regex("albo\-turoniana", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("Bacias", token.word) and regex("Paleozóicas", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_CRONO"
                
            if regex("barremiana", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("como", token.word) and regex("Permiana", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_CRONO"
                
            if regex("cretácio", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("Eoterciário", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("formações", token.word) and regex("paleoB6icas", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_CRONO"
                
            if regex("idade", token.word) and regex("Dom", token.next_token.word) and regex("Joao", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("Oligo\-Miocenicos", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("preaptianos", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("pre\-Aratu", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("Turoniana", token.word):
                token.deps = "B=UNIDADE_CRONO"
                
            if regex("idade", token.word) and regex("neo\-paleoceno", token.next_token.word):
                token.deps = "B=UNIDADE_CRONO"
                token.next_token.deps = "I=UNIDADE_CRONO"
                
            if regex("Série", token.word) and regex("Passa", token.next_token.word) and regex("DoiS|Dois", token.next_token.next_token.word):
                token.deps = "O"
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            #UNIDADE_LITO - 06/2023

            if regex("especialmente", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Itarar~", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("FormaçioLagoa", token.word) and regex("Feia", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("interoalados", token.word) and regex("em", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Itarar\~|Palermo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("sedimentos", token.word) and regex("estratigraficamente", token.next_token.word) and regex("situados", token.next_token.next_token.word) and regex("em", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Itarar", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("ormação", token.word) and regex("\:", token.next_token.word) and regex("Teresina", token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.word) and regex("Serrinha", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("formação", token.word) and regex("e", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Irati\.", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("arenit08", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Itarar", token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("\,", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Rio", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Bonito", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Botucatú", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Embasamento", token.word):
                token.deps = "B=UNIDADE_LITO"
                
            if regex("discordantemente", token.word) and regex("sObre", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Fm", token.word) and regex("Riachuelo", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("FM", token.word) and regex("Curuá\/MB", token.next_token.word) and regex("Curi", token.next_token.next_token.word) and regex("rí", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Forma", token.word) and regex("ção", token.next_token.word) and regex("Pimenteiras", token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formacao", token.word) and regex("Barra", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("lnuba\.", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formacao", token.word) and regex("Barra", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("ltiuba", token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Formaçio", token.word) and regex("Açu|Pendência", token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("arenit08", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Itarar.*", token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.word) and regex("Rio", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Bonito", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Botucatú", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("sedimentos", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Botucatú", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("com", token.word) and regex("os", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Teresina", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Serrinha", token.word) and regex("\:", token.next_token.word) and regex("65", token.next_token.next_token.word) and regex("m", token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("Irati", token.word) and regex("\:", token.next_token.word) and regex("58", token.next_token.next_token.word) and regex("m", token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.word) and regex("Serra", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Alta", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("\:", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("82", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("m", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("\,", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Teresina", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Itararé", token.word) and regex("é", token.next_token.word) and regex("constituido", token.next_token.next_token.word) and regex("por", token.next_token.next_token.next_token.word) and regex("sedimentos", token.next_token.next_token.next_token.next_token.word):
                token.deps = "B=UNIDADE_LITO"
                
            if regex("sedimentação", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("sedimentos", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.word) and regex("em", token.next_token.next_token.next_token.next_token.next_token.word) and regex("contacto", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("com", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("os", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Serrinha", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                
            if regex("Fm\.", token.word) and regex("CAA", token.next_token.word):
                token.deps = "O"
                


            #BACIA PT 2 - 06/2023

            if regex("Estado", token.word) and regex("de", token.next_token.word) and regex("são", token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Estados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paran", token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Rio", token.next_token.next_token.next_token.next_token.word) and regex("Grande", token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Norte", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Paraná", token.word) and regex("Junho", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("nmEstados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Treze", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Parani", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("com", token.word) and regex("o", token.next_token.word) and regex("paran", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("ou", token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            #CAMPO (MClara) - 06/2023

            if regex("rio", token.word) and regex("Dois", token.next_token.word) and regex("Irmãos", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos):
                token.next_token.next_token.next_token.deps = "O"
                
            #ESTRUTURA_FÍSICA PT 2 - 06/2023

            if regex("PROPN", token.upos) and regex("Cabos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("suporte\-guia", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Estrutura", token.word) and regex("de", token.next_token.word) and regex("suporte", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("N50", token.word) and regex("0", token.next_token.word):
                token.next_token.deps = "O"
                
            #FLUIDODATERRA_i PT 2 - 06/2023

            if regex("6le", token.word) and regex("o\(", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("saturaçio|viscosidade", token.word) and regex("residual|de", token.next_token.word) and regex("de|o", token.next_token.next_token.word) and regex("dleo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            #POÇO (MClara) - 06/2023

            if regex("i5", token.word) and regex("easi", token.next_token.word):
                token.next_token.deps = "O"
                
            #ROCHA (MClara_ - 06/2023

            if regex("c\.", token.word) and regex("Rochas", token.next_token.word) and regex("Igneas", token.next_token.next_token.word):
                token.next_token.deps = "B=ROCHA"
                token.next_token.next_token.deps = "I=ROCHA"
                
            #UNIDADE_CRONO PT 2 - 06/2023

            if regex("Banco", token.word) and regex("de", token.next_token.word) and regex("Dados", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("Provisórios", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Produção", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("Compactos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Injeção", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            #UNIDADE_LITO PT 2 - 06/2023

            if regex("grupo", token.word) and regex("Golder", token.next_token.word) and regex("Associates", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Grupo", token.word) and regex("Executivo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Desenvolvi", token.next_token.next_token.next_token.word) and regex("mento", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Executivo", token.word) and regex("de", token.next_token.word) and regex("Desenvolvimento", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("grupo", token.word) and regex("para", token.next_token.word) and regex("conhecer", token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("ELF\/AGIP\/CANAMM\/NORCEN\.", token.word) and regex("1", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("para", token.word) and regex("o", token.next_token.word) and regex("Serrinha", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("o|O", token.word) and regex("Irati", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"

            #BACIA PT 2 - 06/2023

            if regex("Estado", token.word) and regex("de", token.next_token.word) and regex("são", token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Estados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paran", token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Bacia", token.word) and regex("Terrestre", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Rio", token.next_token.next_token.next_token.next_token.word) and regex("Grande", token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Norte", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
                
            if regex("Paraná", token.word) and regex("Junho", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("nmEstados", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Treze", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Parani", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("com", token.word) and regex("o", token.next_token.word) and regex("paran", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos) and regex("ou", token.next_token.next_token.next_token.next_token.word) and regex("são", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Paulo", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"

            #CAMPO (MClara) - 06/2023

            if regex("rio", token.word) and regex("Dois", token.next_token.word) and regex("Irmãos", token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.upos):
                token.next_token.next_token.next_token.deps = "O"
                
            #ESTRUTURA_FÍSICA PT 2 - 06/2023

            if regex("PROPN", token.upos) and regex("Cabos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("suporte\-guia", token.next_token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Estrutura", token.word) and regex("de", token.next_token.word) and regex("suporte", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("N50", token.word) and regex("0", token.next_token.word):
                token.next_token.deps = "O"
                
            #FLUIDODATERRA_i PT 2 - 06/2023

            if regex("6le", token.word) and regex("o\(", token.next_token.word):
                token.deps = "B=FLUIDODATERRA_i"
                token.next_token.deps = "I=FLUIDODATERRA_i"
                
            if regex("saturaçio|viscosidade", token.word) and regex("residual|de", token.next_token.word) and regex("de|o", token.next_token.next_token.word) and regex("dleo", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
                
            #POÇO (MClara) - 06/2023

            if regex("i5", token.word) and regex("easi", token.next_token.word):
                token.next_token.deps = "O"
                
            #ROCHA (MClara_ - 06/2023

            if regex("c\.", token.word) and regex("Rochas", token.next_token.word) and regex("Igneas", token.next_token.next_token.word):
                token.next_token.deps = "B=ROCHA"
                token.next_token.next_token.deps = "I=ROCHA"
                
            #UNIDADE_CRONO PT 2 - 06/2023

            if regex("Banco", token.word) and regex("de", token.next_token.word) and regex("Dados", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("Provisórios", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Produção", token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                
            if regex("Sistemas", token.word) and regex("Compactos", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Injeção", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Água", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.next_token.deps = "O"
                
            #UNIDADE_LITO PT 2 - 06/2023

            if regex("grupo", token.word) and regex("Golder", token.next_token.word) and regex("Associates", token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                
            if regex("Grupo", token.word) and regex("Executivo", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Desenvolvi", token.next_token.next_token.next_token.word) and regex("mento", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.deps = "O"
                token.next_token.next_token.next_token.next_token.deps = "O"
                
            if regex("Executivo", token.word) and regex("de", token.next_token.word) and regex("Desenvolvimento", token.next_token.next_token.word):
                token.next_token.deps = "O"
                token.next_token.next_token.deps = "O"
                
            if regex("grupo", token.word) and regex("para", token.next_token.word) and regex("conhecer", token.next_token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("ELF\/AGIP\/CANAMM\/NORCEN\.", token.word) and regex("1", token.next_token.word):
                token.next_token.deps = "O"
                
            if regex("para", token.word) and regex("o", token.next_token.word) and regex("Serrinha", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("Morro", token.next_token.next_token.next_token.next_token.word) and regex("Pelado", token.next_token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
                token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
                
            if regex("o|O", token.word) and regex("Irati", token.next_token.word):
                token.next_token.deps = "B=UNIDADE_LITO"

        except AttributeError as e:
            print(str(e))

remove_sentences = '1D950B01688A6DD0E05354EB1D0AEF49-63'.split(",")
corpus.sentences = {x: y for x, y in corpus.sentences.items() if x not in remove_sentences}
new_corpus = estrutura_ud.Corpus()
new_corpus.sentences = corpus.sentences

new_corpus.save(files['golden'])
print("[OK] Saved to %s" % files['golden'])

# comparando silver e golden
ner_tokens = {'golden': dict(), 'silver': dict()}
for sentid, sentence in silver.sentences.items():
    for t, token in enumerate(sentence.tokens):
        if 'B=' in token.deps:
            ner_tokens['silver']["{}-{}".format(sentid, t)] = token.deps
for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        if 'B=' in token.deps:
            ner_tokens['golden']["{}-{}".format(sentid, t)] = token.deps

log = {
    'new_entities': defaultdict(int),
    'changed_entities': defaultdict(int),
    'deleted_entities': defaultdict(int),
}

for token in ner_tokens['golden']:
    if not token in ner_tokens['silver']:
        log['new_entities']['_total'] += 1
        log['new_entities'][ner_tokens['golden'][token]] += 1
    if token in ner_tokens['silver'] and ner_tokens['golden'][token] != ner_tokens['silver'][token]:
        log['changed_entities']['_total'] += 1
        log['changed_entities']["{} => {}".format(ner_tokens['silver'][token], ner_tokens['golden'][token])] += 1
for token in ner_tokens['silver']:
    if not token in ner_tokens['golden']:
        log['deleted_entities']['_total'] += 1
        log['deleted_entities'][ner_tokens['silver'][token]] += 1

log_save_to = 'log-2-golden.txt'
with open(log_save_to, "w") as f:
    f.write(json.dumps(log, indent=4, ensure_ascii=False))
print('Saved to: %s' % log_save_to)

import matplotlib.pyplot as plt

data = {x: y for x, y in log.items()}

# Extract the required data
new_entities = data['new_entities']
changed_entities = data['changed_entities']
deleted_entities = data['deleted_entities']

# Prepare data for plotting
x_labels = sorted(set([x for x in [*new_entities.keys(), *changed_entities.keys(), *deleted_entities.keys()] if x != "_total"]))
new_counts = [new_entities[label] for label in x_labels]
changed_counts = [changed_entities.get(label, 0) for label in x_labels]
deleted_counts = [deleted_entities.get(label, 0) for label in x_labels]

# Generate the plot
plt.figure(figsize=(10, 7))
bar_width = 0.25
index = range(len(x_labels))

bar1 = plt.bar(index, new_counts, bar_width, label='Novas entidades: %s' % new_entities.get('_total'))
bar2 = plt.bar([i + bar_width for i in index], changed_counts, bar_width, label='Entidades Modificadas: %s' % changed_entities.get('_total'))
bar3 = plt.bar([i + 2 * bar_width for i in index], deleted_counts, bar_width, label='Entidades Removidas: %s' % deleted_entities.get('_total'))

plt.xlabel('Classes de entidades')
plt.ylabel('Qtd.')
plt.title('Mudanças de Entidades (pós-matriz de confusão)')
plt.xticks([i + bar_width for i in index], x_labels, rotation="vertical")
plt.legend()

# Add labels to the bars
def autolabel(bars):
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, '%d' % int(height), ha='center', va='bottom')

autolabel(bar1)
autolabel(bar2)
autolabel(bar3)

plt.tight_layout()
plt.show()

exit()