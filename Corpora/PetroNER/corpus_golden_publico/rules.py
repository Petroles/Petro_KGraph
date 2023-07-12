# ANCHOR begin log
special_log = {}
def log():
    import os, sys, re
    file = sys.argv[1]
    sent_id = input("Test any sent_id? (Press Return to skip or enter the sent_id)\n").strip() if len(sys.argv) < 3 else sys.argv[2]
    if not sent_id: sent_id = None
    with open(sys.argv[0]) as f: rules_py = f.read()
    n_fakelines = len(rules_py.split("# end log\n")[0].splitlines())
    is_rule = re.compile(r"([_]*token[^(\n]*?)\.([^\s._]+?)\s=\s(.*?)\n")
    py = is_rule.sub(r"\1.\2 = change_and_log(\1, '\2', \3, get_linenumber()+" + str(n_fakelines) + r")\n", rules_py.split("# end log\n")[1])
    invisible_rules = [x for x in rules_py.split("# end log\n")[1].splitlines() if 'token.' in x and not 'if ' in x and not is_rule.match(x.strip() + "\n")]
    with open("rules-invisible_rules.txt", "w") as f:
        f.write("\n".join(invisible_rules))
    for i, x in enumerate(py.splitlines()):
        if "# special_log: " in x:
            tag = x.split("# special_log: ")[1]
            if not tag in special_log:
                special_log[tag] = []
            special_log[tag].append(str(i+1+1+1+n_fakelines))
    py = "special_log = {}\n".format(str(special_log) if special_log else "{}") + py
    with open("rules_fake.py", "w") as w: w.write(py)
    os.system("python3 rules_fake.py '{}' '{}'; rm rules_fake.py".format(file, sent_id if sent_id else ""))
    if 1: exit()
log()
# end log

keep_special_log = False
output = "rules.conllu"
available_tags = "POÇO BACIA CAMPO FLUIDO FLUIDODATERRA_i FLUIDODATERRA_o UNIDADE_CRONO NÃOCONSOLID \
    ROCHA UNIDADE_LITO POÇO_R POÇO_T POÇO_Q TEXTURA TIPO_POROSIDADE ESTRUTURA_FÍSICA EVENTO_PETRO ELEMENTO_PETRO".split()#UNIDADE_LITO

# ANCHOR importações e variáveis
import re
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore
import sys
import os
from inspect import currentframe
import time

t1 = time.time()
file = sys.argv[1]
test_sent_id = sys.argv[2] if len(sys.argv) >= 3 else None

all_special_log = {}
for tag, lines in special_log.items():
    for line in lines:
        all_special_log[line] = tag

if os.path.isfile("rules-log.txt") and not test_sent_id: os.remove("rules-log.txt")
if os.path.isfile("rules-log_test.txt") and test_sent_id: os.remove("rules-log_test.txt")
if not test_sent_id:
    for filename in special_log:
        if os.path.isfile("rules-new_{}.txt".format(filename)):
            os.remove("rules-new_{}.txt".format(filename))
if not os.path.isfile(file) or not file.endswith(".conllu"): raise Exception("{} not found.".format(file))

default_token = estrutura_ud.Token()
corpus = estrutura_ud.Corpus(sent_id=test_sent_id)
corpus.load(file)
big_flatnames = []
conj_not_tagged = []
n_sentences = len(corpus.sentences)
rules = set()
n = 0

# ANCHOR definindo funções
def append_to(original, s, delimiter="|"):
    original = original.split(delimiter)
    novosFeats = s.split(delimiter)
    novosFeats += [x for x in original if x != "_" and not any(y.split("=")[0] == x.split("=")[0] for y in novosFeats)]

    return delimiter.join(sorted(novosFeats))

def remove_from(original, s, delimiter="|"):
    original = original.split(delimiter)
    deletedFeats = s.split(delimiter)
    is_sema = False
    for x in deletedFeats:
        if any(y in x for y in ["B=", "I="]):
            is_sema = True
    original = [x for x in original if x not in deletedFeats and not any(y == x.split("=")[0] for y in deletedFeats)]
    if not original: original = ["_"] if not is_sema else ["O"]

    return delimiter.join(sorted(original))

def get_head(tok, sentence):
    return sentence.tokens[sentence.map_token_id[tok.dephead]].word if tok.dephead in sentence.map_token_id else "_"

def regex(exp, col):
    return re.search(r'^(' + exp + r')$', col)

def change_and_log(token, col, value, line):
    if 'sent_id' in token.__dict__ and token.__dict__[col] != value:
        token.special_log = all_special_log[str(line)] if str(line) in all_special_log and token.deps == "O" else ""
        if not line in rules:
            rules.add(line)
        with open("rules-log.txt" if not test_sent_id else "rules-log_test.txt", "a") as f:
            f.write(", ".join([token.sent_id, token.id, token.lemma, col, token.__dict__[col], value, 'l: {}'.format(line)]) + "\n")
    return value

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno

def token_from_id(sent_id, id):
    if not sent_id in corpus.sentences:
        return default_token
    return corpus.sentences[sent_id].tokens[corpus.sentences[sent_id].map_token_id[id]]

def reattach(token, dephead):
    token.dephead = dephead
    token.head_token = token_from_id(token.sent_id, dephead)

def no_iob(s):
    return s.replace("B=", "").replace("I=", "").split("/")[0]

def to_b(s):
    return s.replace("I=", "B=").split("/")[0]

def to_i(s):
    return s.replace("B=", "I=").split("/")[0]

# begin annotation
for sentid, sentence in corpus.sentences.items():
    n += 1
    if not n%100: print("{} / {} sentences processed".format(n, n_sentences))

    # ANCHOR fix attribute errors
    for tokenfix in sentence.tokens:
        attributes = "previous_token next_token head_token".split()
        for att in attributes:
            if not att in tokenfix.__dict__:
                tokenfix.__dict__[att] = sentence.default_token
            for _att in attributes:
                if not _att in tokenfix.__dict__[att].__dict__:
                    tokenfix.__dict__[att].__dict__[_att] = sentence.default_token
        tokenfix.sent_id = sentid
        tokenfix.special_log = ""

    # ANCHOR (1) correções morfossintáticas
    for t, token in enumerate(sentence.tokens):
        if sentid == 'boletins-000005-1719' and token.id == '27':
            reattach(token, '21')
        if sentid == "boletins-000002-1383" and token.id == '27':
            token.deps = "B=BACIA"
        if sentid == 'boletins-000006-1198' and token.id == '99':
            reattach(token, '94')
        if sentid == "boletins-000002-1648" and token.id == "20":
            token.deps = "O"
        if sentid == "boletins-000010-1806" and token.id == "35":
            token.lemma = "ativo"
            token.upos = "NOUN"
        if sentid == "boletins-000009-2064" and token.id == "37":
            reattach(token, "28")
        if sentid == "boletins-000011-2410" and token.id == "7":
            token.deprel = "acl"
        if sentid == "boletins-000003-2041" and token.id == "53":
            reattach(token, "51")
        if sentid == "boletins-000008-1528" and token.id == "85":
            reattach(token, "78")
        if sentid == "boletins-000011-433" and token.id == "44":
            token.deprel = "nmod:appos"
        if sentid == "boletins-000011-187" and token.id == "15":
            reattach(token, "18")
            token.deprel = "nsubj"
        if sentid == "boletins-000011-187" and token.id == "17":
            reattach(token, "15")
        if sentid == "boletins-000008-703" and token.id == "11":
            reattach(token, "7")
        if sentid == "boletins-000008-1528" and token.id in "34 46 48 50 56 61".split():
            reattach(token, "21")
            token.deprel = "conj"
        if sentid == "boletins-000002-119" and token.id == "54":
            reattach(token, "45")
        if sentid == "boletins-000010-234" and token.id == "80":
            reattach(token, "52")
        if sentid == "boletins-000006-110" and token.id == "16":
            reattach(token, "9")
        if sentid == "boletins-000006-110" and token.id == "8":
            token.deprel = "nsubj"
            reattach(token, "22")
        if sentid == "boletins-000003-1168" and token.id == "28":
            reattach(token, "26")
        if token.lemma == "crátom":
            token.lemma = "cráton"
        if sentid == "boletins-000002-1469" and token.id == "22":
            reattach(token, "23")
            token.deprel = "cc"
            reattach(token.next_token, "20")
            token.next_token.deprel = "conj"
        if sentid == "boletins-000009-1154" and token.id == "9":
            reattach(token, "2")
            token.deprel = "obl"
        if sentid == "boletins-000001-1475" and token.id in "12 13 14".split():
            reattach(token, "11")
        if sentid == "boletins-000004-3131" and token.id == "32":
            token.deprel = "cc"
            reattach(token, "33")
        if sentid == "boletins-000004-3131" and token.id == "33":
            reattach(token, "30")
            token.deprel = "conj"
        if sentid == "boletins-000008-1474" and token.id == "15":
            token.deprel = "cc"
            reattach(token, "16")
        if sentid == "boletins-000008-1474" and token.id == "16":
            reattach(token, "14")
            token.deprel = "conj"
        if sentid == "boletins-000002-1485" and token.id == "33":
            token.deprel = "conj"
        if sentid == "boletins-000006-1242" and token.id == "24":
            token.deprel = "nmod"
        if sentid == "boletins-000003-1168" and token.id == "39":
            token.deprel = "nmod"
        if sentid == "boletins-000004-2326" and token.id == "140":
            token.deprel = "nmod"
        if regex("Ceara", token.word):
            token.lemma = "Ceará"
        if regex("Anais|anais", token.word) and regex("anal", token.lemma):
            token.lemma = "anais"
        if regex("megalópol", token.lemma):
            token.lemma = "megalópole"
        if regex("Petrorres", token.lemma):
            token.lemma = "Petrobrás"
        if regex("Petrorras", token.lemma):
            token.lemma = "Petrobras"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("ceno\-zóico", token.next_token.lemma):
            token.next_token.lemma = "cenozóico"
        if regex("flúvio\-deltacuacuaclacre", token.lemma):
            token.lemma = "flúvio-deltaico-lacustre"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("pós\-rift\.", token.next_token.lemma):
            token.next_token.lemma = "pós-rift"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("pré\-alagoo", token.next_token.lemma):
            token.next_token.lemma = "pré-Alagoas"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("santonianos\-campanianos", token.next_token.lemma):
            token.next_token.lemma = "santoniano-campaniano"
        if regex("segiiência", token.lemma):
            token.lemma = "sequência"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("siliciclastico", token.next_token.lemma):
            token.next_token.lemma = "siliciclástico"
        if regex("sedimento", token.lemma) and regex("ADJ", token.next_token.upos) and regex("siluro\-devonianos", token.next_token.lemma):
            token.next_token.lemma = "siluro-devoniano"
        # TIRANDO O HÍFEN DE LEMAS
        if regex("Albaco\-ra", token.lemma):
            token.lemma = "Albacora"
        if regex("Cher\-ne", token.lemma):
            token.lemma = "Cherne"
        if regex("Ju\-barte", token.lemma):
            token.lemma = "Jubarte"
        if regex("Encho\-va", token.lemma):
            token.lemma = "Enchova"
        if regex("Mossoró\.", token.lemma):
            token.lemma = "Mossoró"
        if regex("Barra", token.word) and regex("barra", token.lemma):
            token.lemma = "Barra"
            token.upos = "PROPN"
        if sentence.sent_id == "boletins-000001-1000" and token.id == "79" and regex("de", token.word) and regex("as", token.next_token.word) and regex("bacias", token.next_token.next_token.word) and regex("Mesozdicas", token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "81")
            token.next_token.deprel = "det"
            reattach(token.next_token, "81")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.lemma = "bacia"
            token.next_token.next_token.feats = "Gender=Fem|Number=Plur"
            reattach(token.next_token.next_token, "78")
            token.next_token.next_token.next_token.deprel = "nmod"
            reattach(token.next_token.next_token.next_token, "81")

        if sentence.sent_id == "boletins-000001-872" and token.id == "30" and regex("de", token.word) and regex("as", token.next_token.word) and regex("bacias", token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "32")
            token.next_token.deprel = "det"
            reattach(token.next_token, "32")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.lemma = "bacia"
            token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.feats = "Gender=Fem|Number=Plur"
            reattach(token.next_token.next_token, "21")

        if sentence.sent_id == "boletins-000011-2481" and token.id == "61" and regex("de", token.word) and regex("as", token.next_token.word) and regex("bacias", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "63")
            token.next_token.deprel = "det"
            reattach(token.next_token, "63")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.lemma = "bacia"
            token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            reattach(token.next_token.next_token.next_token.next_token, "63")

        if sentence.sent_id == "boletins-000006-913" and token.id == "20" and regex("Localização", token.word) and regex("de", token.next_token.word) and regex("as", token.next_token.next_token.word) and regex("bacias", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("Campos", token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Pelotas", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.deprel = "case"
            reattach(token.next_token, "23")
            token.next_token.next_token.deprel = "det"
            reattach(token.next_token.next_token, "23")
            token.next_token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.lemma = "bacia"
            token.next_token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.next_token.next_token.next_token.deprel = "case"
            reattach(token.next_token.next_token.next_token.next_token, "25")
            token.next_token.next_token.next_token.next_token.next_token.deprel = "nmod"
            reattach(token.next_token.next_token.next_token.next_token.next_token, "23")
            reattach(token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token, "25")

        if sentence.sent_id == "boletins-000011-2391" and token.id == "21" and regex("de", token.word) and regex("as", token.next_token.word) and regex("bacias", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Santos", token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Potiguar", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Brasil", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "23")
            token.next_token.deprel = "det"
            reattach(token.next_token, "23")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.lemma = "bacia"
            token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.feats = "Gender=Fem|Number=Plur"
            reattach(token.next_token.next_token, "17")
            token.next_token.next_token.next_token.deprel = "case"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            reattach(token.next_token.next_token.next_token, "25")
            token.next_token.next_token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            reattach(token.next_token.next_token.next_token.next_token, "23")
            reattach(token.next_token.next_token.next_token.next_token.next_token.next_token, "25")
            reattach(token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token, "25")

        # PORTILEXICON
        # MCLARA

        if regex("o", token.lemma) and regex("ADP", token.upos):
            token.lemma = "a"
        if regex("a", token.word) and regex("ela", token.lemma) and regex("PRON", token.upos) and regex("Case=Acc\|Gender=Fem\|Number=Sing\|Person=3\|PronType=Prs", token.feats):
            token.lemma = "o"
        if regex("a", token.word) and regex("o", token.lemma) and regex("PRON", token.upos) and regex("Gender=Fem\|Number=Sing\|PronType=Ind", token.feats):
            token.feats = append_to(token.feats, "Person=3")
        if regex("a", token.word) and regex("ela", token.lemma) and regex("PRON", token.upos) and regex("Gender=Fem\|Number=Sing\|PronType=Dem", token.feats):
            token.lemma = "o"
            token.feats = append_to(token.feats, "Person=3")
        if regex("aceitar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "aceito"
        if regex("básico", token.lemma) and regex("NOUN", token.upos) and regex("ácido", token.head_token.lemma) and regex("NOUN", token.head_token.upos):
            token.upos = "ADJ"
            token.head_token.upos = "ADJ"
            token.head_token.deprel = "amod"
        if regex("acorrente", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "corrente"
        if regex("acumulo", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "acúmulo"
        if regex("acunha", token.word) and regex("acunhar", token.lemma) and regex("Mood=Ind\|Number=Sing\|Person=3\|Tense=Imp\|VerbForm=Fin", token.feats):
            token.feats = remove_from(token.feats, "Tense=Imp")
            token.feats = append_to(token.feats, "Tense=Pres")
        if regex("adsorvir", token.lemma) and regex("VERB", token.upos):
            token.lemma = "adsorver"
        if regex("agua", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "água"
        if regex("alargar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "alargado"
        if regex("alcalina", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "alcalino"
        if regex("alternativa", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "alternativo"
        if regex("alumino", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "alumina"
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("sílica\/", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "sílica"
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("amplitude", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("anal", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "anais"
        if regex("analise", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "análise"
        if regex("anexos", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "anexo"
            token.feats = "Gender=Masc|Number=Plur"
        if regex("anguloso", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("aniônico", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("anular", token.word) and regex("ADJ", token.upos) and regex("Number=Sing\|Person=3\|VerbForm=Inf", token.feats):
            token.feats = "Gender=Masc|Number=Sing"
        if regex("aportar", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "aporte"
        if regex("aptiana", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "aptiano"
            token.upos = "ADJ"
        if regex("aquosa", token.lemma) and regex("NOUN", token.upos) and regex("óleo|orgânico", token.head_token.lemma):
            token.lemma = "aquoso"
            token.upos = "ADJ"
        if regex("argila", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("as", token.word) and regex("o", token.lemma) and regex("PRON", token.upos) and regex("Gender=Fem\|Number=Plur\|PronType=Dem", token.feats):
            token.feats = append_to(token.feats, "Person=3")
        if regex("assine", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "Assine"
            token.upos = "PROPN"
        if regex("atendo", token.word) and regex("VERB", token.upos):
            token.feats = "VerbForm=Ger"
        if regex("atenuar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "atenuado"
        if regex("autora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "autor"
        if regex("auxilio", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "auxílio"
        if regex("bactericido", token.lemma):
            token.lemma = "bactericida"
        if regex("baixa", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "baixo"
        if regex("beto", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "beta"
        if regex("bibliogrefico|bibliogrofico", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "bibliográfico"
            token.upos = "ADJ"
        if regex("boi", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("brasileira", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "brasileiro"
        if regex("cada", token.lemma) and regex("DET", token.upos) and regex("Gender=Masc\|Number=Sing\|PronType=Tot", token.feats):
            token.feats = remove_from(token.feats, "PronType=Tot")
            token.feats = append_to(token.feats, "PronType=Ind")
        if regex("cada", token.lemma) and regex("DET", token.upos) and regex("Gender=Fem\|Number=Sing\|PronType=Tot", token.feats):
            token.feats = remove_from(token.feats, "PronType=Tot")
            token.feats = append_to(token.feats, "PronType=Ind")
        if regex("cada", token.lemma) and regex("DET", token.upos) and regex("Gender=Masc\|Number=Sing", token.feats):
            token.feats = append_to(token.feats, "PronType=Ind")
        if regex("campu", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "campus"
        if regex("cancerígeno", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
            token.deprel = "xcomp"
        if regex("capitulo", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "capítulo"
        if regex("característica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "característico"
        if regex("carbonato", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("cara", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "caro"
        if regex("caulin", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "caulim"
        if regex("ceara", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "Ceará"
            token.upos = "PROPN"
        if regex("centrifugo", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "centrífugo"
        if regex("cerâmica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "cerâmico"
        if regex("certificadora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "certificador"
        if regex("chave", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("cheirar", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "cheiro"
        if regex("clorofórmio", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("com", token.lemma) and regex("SCONJ", token.upos) and regex("DET", token.next_token.upos) and regex("passar", token.next_token.next_token.lemma):
            token.upos = "ADP"
            token.deprel = "case"
        if regex("compor", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "composto"
        if regex("concho", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "concha"
        if regex("conclusce", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "conclusão"
        if regex("conforme", token.word) and regex("ADV", token.upos) and regex("advcl", token.head_token.deprel):
            token.upos = "SCONJ"
            token.deprel = "mark"
        if regex("consorcio", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "consórcio"
        if regex("contem", token.word) and regex("contar", token.lemma):
            token.lemma = "conter"
        if regex("contrario", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "contrário"
        if regex("correlata", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "correlato"
        if regex("costeira", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "costeiro"
            token.upos = "ADJ"
            token.deprel = "amod"
        if regex("costeira", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "costeiro"
        if regex("critico", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "crítico"
        if regex("cruzadas", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "cruzada"
        if regex("dado", token.lemma) and regex("DET", token.upos):
            token.feats = remove_from(token.feats, "Definite=Ind")
        if regex("datam", token.word) and regex("datar", token.lemma) and regex("VERB", token.upos):
            token.feats = remove_from(token.feats, "Tense=Imp")
            token.feats = append_to(token.feats, "Tense=Pres")
        if regex("definir", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "definido"
        if regex("deionizar", token.lemma) and regex("VERB", token.upos):
            token.lemma = "deionizado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("delgar", token.lemma) and regex("delgada|delgadas|delgados", token.word) and regex("acl", token.deprel) and regex("VERB", token.upos):
            token.lemma = "delgado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("argila", token.lemma) and regex("amod", token.deprel):
            token.deprel = "nmod"
        if regex("decida", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "descida"
        if regex("descontinuo", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "descontínuo"
        if regex("descrever", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "descrito"
        if regex("desenvolver", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "desenvolvido"
        if regex("desfolha", token.word) and regex("desfolhar", token.lemma) and regex("VERB", token.upos):
            token.feats = remove_from(token.feats, "Tense=Past")
            token.feats = append_to(token.feats, "Tense=Pres")
        if regex("determinar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "determinado"
        if regex("devido", token.lemma) and regex("ADV", token.upos):
            token.upos = "ADP"
        if regex("diferente", token.lemma) and regex("DET", token.upos) and regex("Gender=Masc\|Number=Plur\|PronType=Ind", token.feats):
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Masc|Number=Plur"
        if regex("diferente", token.lemma) and regex("DET", token.upos) and regex("Gender=Fem\|Number=Plur\|PronType=Ind", token.feats):
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Fem|Number=Plur"
        if regex("dinâmica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "dinâmico"
        if regex("dinoflagelar", token.lemma) and regex("VERB", token.upos):
            token.lemma = "dinoflagelado"
            token.upos = "NOUN"
            token.deprel = "obj"
            token.feats = "Gender=Masc|Number=Plur"
        if regex("direto", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADV"
            token.deprel = "advmod"
            token.feats = "_"
        if regex("dispersar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "disperso"
        if regex("distanciar", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "distância"
        if regex("distam", token.word) and regex("dizer", token.lemma) and regex("VERB", token.upos):
            token.lemma = "distar"
        if regex("divisa", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("dominó", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("download|grid|core", token.lemma) and regex("NOUN", token.upos):
            token.feats = append_to(token.feats, "Foreign=Yes")
        if regex("dupla", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "duplo"
        if regex("econcmico", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "econômico"
        if regex("ela", token.lemma) and regex("Case=Nom\|Gender=Fem\|Number=Sing\|Person=3\|PronType=Prs", token.feats):
            token.lemma = "ele"
        if regex("ela", token.word) and regex("ela", token.lemma) and regex("Gender=Fem\|Number=Sing\|Person=3\|PronType=Prs", token.feats):
            token.lemma = "ele"
        if regex("elástica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "elástico"
        if regex("eles", token.word) and regex("eles", token.lemma) and regex("Gender=Masc\|Number=Plur\|Person=3\|PronType=Prs", token.feats):
            token.lemma = "ele"
        if regex("elétrico", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("em", token.lemma) and regex("SCONJ", token.upos):
            token.upos = "ADP"
            token.deprel = "case"
        if regex("emissora", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "emissor"
        if regex("emissora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "emissor"
        if regex("enquanto", token.lemma) and regex("ADP", token.upos) and regex("mark", token.deprel):
            token.upos = "SCONJ"
        if regex("entres", token.lemma) and regex("ADP", token.upos):
            token.lemma = "entre"
        if regex("eólica", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
            token.lemma = "eólico"
        if regex("eólica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "eólico"
        if regex("equações", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "equação"
        if regex("especificamente", token.lemma) and regex("especificadamente", token.word) and regex("ADV", token.upos):
            token.lemma = "especificadamente"
        if regex("especifico", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "específico"
        if regex("esperar", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "esperado"
        if regex("espessa", token.word) and regex("espessar", token.lemma) and regex("Mood=Ind\|Number=Sing\|Person=3\|VerbForm=Fin\|Voice=Pass", token.feats):
            token.feats = append_to(token.feats, "Tense=Pres")
        if regex("estabelecer", token.lemma) and regex("estabelecido", token.word) and regex("ADJ", token.upos):
            token.lemma = "estabelecido"
        if regex("estabelecer", token.lemma) and regex("estabelecido", token.word) and regex("NOUN", token.upos):
            token.lemma = "estabelecido"
        if regex("esta", token.word) and regex("este", token.lemma) and regex("DET", token.upos) and regex("Definite=Def\|Gender=Fem\|Number=Sing\|PronType=Art", token.feats):
            token.feats = remove_from(token.feats, "PronType=Art")
            token.feats = append_to(token.feats, "PronType=Dem")
        if regex("estiveram", token.word) and regex("Mood=Ind\|Number=Plur\|Person=3\|VerbForm=Fin", token.feats):
            token.feats = append_to(token.feats, "Tense=Past")
        if regex("estugo", token.lemma) and regex("ADJ", token.upos):
            token.deprel = "compound"
            token.upos = "NOUN"
            token.lemma = "estufa"
        if regex("evoluido", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "evoluído"
        if regex("existir", token.word) and regex("existir", token.lemma) and regex("VERB", token.upos) and regex("Mood=Sub\|Number=Sing\|Person=3\|VerbForm=Fin", token.feats):
            token.feats = append_to(token.feats, "Tense=Fut")
        if regex("experimental", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("explodam", token.word) and regex("explodar", token.lemma) and regex("VERB", token.upos):
            token.lemma = "explodir"
        if regex("externo", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
            token.deprel = "amod"
        if regex("estremo", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "extremo"
        if regex(".*am", token.word) and not regex("preponderam|mascaram", token.word) and regex("VERB", token.upos) and regex("Mood=Ind\|Number=Plur\|Person=3\|VerbForm=Fin", token.feats):
            token.feats = append_to(token.feats, "Tense=Past")
        if regex("fenól", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "fenol"
        if regex("ficar", token.lemma) and regex("AUX", token.upos):
            token.upos = "VERB"
        if regex("figuras", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "figura"
        if regex("fissuradas", token.word) and regex("fissurar", token.lemma) and regex("VERB", token.upos):
            token.lemma = "fissurado"
            token.upos = "ADJ"
            token.feats = "Gender=Fem|Number=Plur"
        if regex("flash", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("gel", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "nmod"
        if regex("forçaste", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "forçante"
        if regex("formadora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "formador"
        if regex("formula", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "fórmula"
        if regex("fornecedora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "fornecedor"
        if regex("fótom", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "fóton"
        if regex("gase", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "gás"
        if regex("gere", token.word) and regex("gerar", token.lemma):
            token.feats = "Mood=Sub|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin"
        if regex("gerar", token.lemma) and regex("giram", token.word):
            token.lemma = "girar"
        if regex("gira", token.word) and regex("gerir", token.lemma):
            token.lemma = "girar"
        if regex("gravimétrica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "gravimétrico"
        if regex("gravitacional", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("graxos", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "graxo"
            token.upos = "ADJ"
            token.deprel = "amod"
        if regex("guso", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "gusa"
            token.upos = "NOUN"
            token.deprel = "compound"
        if regex("hidrofílica", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "hidrofílico"
            token.upos = "ADJ"
        if regex("hidrófila", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "hidrófilo"
        if regex("hidrostática", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "hidrostático"
        if regex("hidroxilo", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "hidroxila"
            token.upos = "NOUN"
            token.deprel = "nmod"
            token.feats = "Gender=Fem|Number=Sing"
        if regex("imiscível", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("inclinar", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "inclinado"
        if regex("incolor", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
            token.deprel = "xcomp"
        if regex("indefinido", token.word) and regex("indefinir", token.lemma) and regex("VERB", token.upos):
            token.lemma = "indefinido"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("individualizad", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "individualizado"
        if regex("industria", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "indústria"
        if regex("inédita", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "inédito"
        if regex("influencia", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "influência"
        if regex("inicio", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "inicial"
        if regex("injetora", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "injetor"
        if regex("intermediario", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "intermediário"
        if regex("interpretar", token.lemma) and regex("interprete", token.word) and regex("NOUN", token.upos):
            token.lemma = "intérprete"
        if regex("intervalado", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "intervalar"
            token.upos = "VERB"
            token.deprel = "acl"
            token.feats = "Gender=Masc|Number=Plur|VerbForm=Part"
        if regex("inversa", token.lemma) and regex("NOUN", token.upos):
            token.lemma = "inverso"
        if regex("iônico", token.lemma) and regex("NOUN", token.upos):
            token.upos = "ADJ"
        if regex("iônio", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "iônico"
        if regex("isolar", token.lemma) and regex("ADJ", token.upos):
            token.upos = "VERB"
            token.feats = "Gender=Fem|Number=Plur|VerbForm=Part"
        if regex("juntas", token.lemma):
            token.lemma = "junto"
        if regex("lamina", token.lemma):
            token.lemma = "lâmina"
        if regex("estearato", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "compound"
        if regex("anexem|ascendam|decaia|entre", token.word) and regex("Mood=Ind\|Number=Plur\|Person=3\|Tense=Pres\|VerbForm=Fin|Mood=Ind\|Number=Sing\|Person=3\|Tense=Pres\|VerbForm=Fin", token.feats):
            token.feats = remove_from(token.feats, "Mood=Ind")
            token.feats = append_to(token.feats, "Mood=Sub")
        if regex("delgar", token.lemma) and regex("delgados", token.word) and regex("conj", token.deprel) and regex("VERB", token.upos):
            token.lemma = "delgado"
            token.upos = "ADJ"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("a", token.lemma) and regex("DET", token.upos):
            token.lemma = "o"
        if regex("as", token.lemma) and regex("DET", token.upos):
            token.lemma = "o"
        if regex("o", token.lemma) and regex("Gender=Fem\|Number=Sing\|PronType=Dem", token.feats):
            token.feats = append_to(token.feats, "Person=3")
            
        # PORTILEXICON
        # TATI

        if regex("voláteis", token.word):
            token.lemma = "volátil"
        if regex("vários|várias", token.word):
            token.lemma = "vários"
        if regex("vales", token.word) and regex("val", token.lemma):
            token.lemma = "vale"
        if regex("âniom", token.lemma):
            token.lemma = "ânion"
        if regex("maior|maiores", token.word) and regex("grande", token.lemma):
            token.lemma = "maior"
        if regex("máximo|máxima|máximos|máximas", token.word) and regex("grande", token.lemma):
            token.lemma = "máximo"
        if regex("melhor|melhores", token.word) and regex("bom", token.lemma):
            token.lemma = "melhor"
        if regex("menor|menores", token.word) and regex("pequeno", token.lemma):
            token.lemma = "menor"
        if regex("principio", token.lemma):
            token.lemma = "princípio"
        if regex("mínimo|mínima|mínimos|mínimas", token.word) and regex("pequeno", token.lemma):
            token.lemma = "mínimo"
        if regex("primária", token.lemma):
            token.lemma = "primário"
        if regex("seca", token.lemma):
            token.lemma = "seco"
        if regex("provém", token.word) and regex("provar", token.lemma):
            token.lemma = "provir"
        if regex("alcalina", token.lemma):
            token.lemma = "alcalino"
        if regex("íom", token.lemma):
            token.lemma = "íon"
        if regex("termos", token.lemma):
            token.lemma = "termo"
        if regex("superiores", token.word) and regex("alto", token.lemma):
            token.lemma = "superior"
        if regex("resmltado", token.lemma):
            token.lemma = "resultado"
        if regex("tabelas", token.lemma):
            token.lemma = "tabela"
            token.feats = "Gender=Fem|Number=Plur"
        if regex("salgar", token.lemma):
            token.lemma = "salgado"
            token.upos = "ADJ"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("(240-20140220-MONOGRAFIA_0-344|25-20150123-MONOGRAFIA_0-94|240-20140220-MONOGRAFIA_0-166|240-20140220-MONOGRAFIA_0-193|20-20140904-TESEDSC_0-1144|398-20160721-MONOGRAFIA_0-289|20-20140904-TESEDSC_0-1116|20-20140904-TESEDSC_0-414)", sentence.sent_id ) and regex("primeiro", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.feats = remove_from(token.feats, "NumType=Ord")
        if regex("química", token.lemma):
            token.lemma = "químico"
        if regex("sistemática", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "sistemático"
        if regex("medida", token.word) and regex("ADP", token.upos):
            token.feats = "Gender=Fem|Number=Sing"
            token.upos = "NOUN"
        if regex("molibdênio", token.lemma) and regex("ADJ", token.upos):
            token.upos = "NOUN"
            token.deprel = "compound"
        if regex(".*PronType=Neg", token.feats) and regex("nenhum", token.lemma):
            token.feats = remove_from(token.feats, "PronType=Neg")
            token.feats = append_to(token.feats, "PronType=Ind")
         
        if regex("Alagoas/", token.lemma):
            token.lemma = "Alagoas"
            
        if regex("Bacia/", token.lemma):
            token.lemma = "Bacia"            

        if regex("\-bacia", token.lemma):
            token.lemma = "bacia"
            
        if regex("Mucuri\.", token.lemma):
            token.lemma = "Mucuri"

        if sentence.sent_id == "boletins-000002-119" and token.id == "62" and regex("de", token.word) and regex("o", token.next_token.word) and regex("Araripe", token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "64")
            token.next_token.deprel = "det"
            reattach(token.next_token, "64")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.deps = "B=BACIA"
            
        if sentence.sent_id == "boletins-000011-400" and token.id == "32" and regex("de", token.word) and regex("o", token.next_token.word) and regex("Paraná", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.next_token.word) and regex("Parnaíba", token.next_token.next_token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "34")
            token.next_token.deprel = "det"
            reattach(token.next_token, "34")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
            
        if sentence.sent_id == "boletins-000006-1377" and token.id == "16" and regex("Pernambuco", token.word) and regex("/", token.next_token.word) and regex("Paraíba", token.next_token.next_token.word):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.deprel = "flat:name"
            reattach(token.next_token, "16")
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deprel = "flat:name"
            reattach(token.next_token.next_token, "16")

        # mclara 06-07-22
        # entidades que não receberam a etiqueta por problema no lema
        if regex("Aptianos", token.lemma) and regex("evaporitos", token.head_token.word):
            token.lemma = "aptiano"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("albiana", token.lemma):
            token.lemma = "albiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("aptiana", token.lemma):
            token.lemma = "aptiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("cambriana", token.lemma):
            token.lemma = "cambriano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("campaniana", token.lemma):
            token.lemma = "campaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("carbonifera/", token.lemma):
            token.lemma = "carbonífero"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("carbonifera", token.lemma):
            token.lemma = "carbonífero"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("cenomaniana", token.lemma):
            token.lemma = "cenomaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("cenozóica", token.lemma):
            token.lemma = "cenozóico"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("cretácea", token.lemma):
            token.lemma = "cretáceo"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Eocarbonifera", token.lemma):
            token.lemma = "Eocarbonífera"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Eocar\-bonífero\-Permiano", token.lemma):
            token.lemma = "Eocarbonífero-Permiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eocena", token.lemma):
            token.lemma = "eoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eocenomaniana", token.lemma):
            token.lemma = "eocenomaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eocretácea\/neo\-jurássica", token.lemma):
            token.lemma = "eocretáceo/neo-jurássico"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eoeocena", token.lemma):
            token.lemma = "eoeoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eoligocena\/", token.lemma):
            token.lemma = "eoligoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eopaleocena\/neo\-maastrichtiana", token.lemma):
            token.lemma = "eopaleoceno/neo-maastrichtiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("fanerozóica", token.lemma):
            token.lemma = "fanerozóico"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("intra\-neocomiana", token.lemma):
            token.lemma = "intra-neocomiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("médio\-eocena", token.lemma):
            token.lemma = "médio-eoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("mesozóica", token.lemma):
            token.lemma = "mesozóico"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("neo\-albiana", token.lemma):
            token.lemma = "neo-albiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("neocam\-paniano", token.lemma):
            token.lemma = "neocampaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Neo\-eoceno\/", token.lemma):
            token.lemma = "Neo-eoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("neocomiana\/", token.lemma):
            token.lemma = "neocomiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("neocomiana", token.lemma):
            token.lemma = "neocomiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("neo\-eocena", token.lemma):
            token.lemma = "neo-eoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("paleozóica", token.lemma):
            token.lemma = "paleozóico"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("permiana\/", token.lemma):
            token.lemma = "permiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("pré\-aptiana", token.lemma):
            token.lemma = "pré-aptiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("pré\-cambriana", token.lemma):
            token.lemma = "pré-cambriano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("quaternária", token.lemma):
            token.lemma = "quaternário"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("santoniana", token.lemma):
            token.lemma = "santoniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("santoniana\-coniaciana\/", token.lemma):
            token.lemma = "santoniano-coniaciano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Santoniano\?", token.lemma):
            token.lemma = "Santoniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("turoniana", token.lemma):
            token.lemma = "turoniano"
            token.deps = "B=UNIDADE_CRONO"
            

        #entidades que já estavam anotadas apesar do problema no lema

        if regex("\/Campaniano", token.lemma):
            token.lemma = "Campaniano"
            
        if regex("Carbonifero", token.lemma):
            token.lemma = "Carbonífero"
            
        if regex("carbonifero", token.lemma):
            token.lemma = "carbonífero"

        if regex("Cenomaniano\-", token.lemma):
            token.lemma = "Cenomaniano"
            
        if regex("\-Cenomaniano", token.lemma):
            token.lemma = "Cenomaniano"
            
        if regex("\-Cenozóicas", token.lemma):
            token.lemma = "Cenozóicas"
            
        if regex("Coniaciano\/", token.lemma):
            token.lemma = "Coniaciano"
            
        if regex("Cretaceo", token.lemma):
            token.lemma = "Cretáceo"
            
        if regex("cretaceo", token.lemma):
            token.lemma = "cretáceo"
            
        if regex("cretacico", token.lemma):
            token.lemma = "cretácico"
            
        if regex("Neojurássico\-", token.lemma):
            token.lemma = "Neojurássico"
            
        if regex("Neovalan\-giniano", token.lemma):
            token.lemma = "Neovalanginiano"
            
        if regex("Oligoceno\/", token.lemma):
            token.lemma = "Oligoceno"
            
        if regex("\-Ordoviciano", token.lemma):
            token.lemma = "Ordoviciano"
            
        if regex("Pleistoceno\/", token.lemma):
            token.lemma = "Pleistoceno"
            
        if regex("Plio\-ceno\-Pleistoceno", token.lemma):
            token.lemma = "Plioceno-Pleistoceno"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("pre-AlagUds", token.lemma):
            token.lemma = "pré-Alagoas"
            
        if regex("eoal\-biano", token.lemma):
            token.lemma = "eoalbiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eoceno\-maniano", token.lemma):
            token.lemma = "eocenomaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eopliens-baquiano", token.lemma):
            token.lemma = "eopliensbaquiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Hauterivia\-no/Barremiano", token.lemma):
            token.lemma = "Hauteriviano/Barremiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("mesoap\-tiana\-mesoalbiano", token.lemma):
            token.lemma = "mesoaptiano-mesoalbiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Neoco\-miano", token.lemma):
            token.lemma = "Neocomiano"
            token.deps = "B=UNIDADE_CRONO"

        if regex("Neovalangi\-niano", token.lemma):
            token.lemma = "Neovalanginiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("pré\-cam\-briano", token.lemma):
            token.lemma = "pré-cambriano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("pré\-cenoma\-niano", token.lemma):
            token.lemma = "pré-cenomaniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("san\-toniano", token.lemma):
            token.lemma = "santoniano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("santoniano\-maastrich\-tiano", token.lemma):
            token.lemma = "santoniano-maastrichtiano"
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Santoniano\-Maas\-trichtiano", token.lemma):
            token.lemma = "Santoniano-Maastrichtiano"
            token.deps = "B=UNIDADE_CRONO"

        if sentence.sent_id == "boletins-000011-578" and token.id == "31" and regex("Paleozóica", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Paraná", token.next_token.next_token.next_token.word):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "O"
            token.next_token.deprel = "case"
            reattach(token.next_token, "34")
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.deprel = "det"
            reattach(token.next_token.next_token, "34")
            token.next_token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.deprel = "nmod"

        if regex("Acu", token.lemma):
            token.lemma = "Açu"
            
        if regex("Qiteirinhos|Oiterrinhos", token.lemma) and regex("[mM]embro", token.head_token.lemma):
            token.lemma = "Oiteirinhos"
            token.deps = "I=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"

        # MCLARA 8/11/22

        if sentence.sent_id == "boletins-000011-694" and token.id == "23" and regex("Piauí-Camocim", token.word):
                reattach(token, "14")
                token.deps = "B=BACIA"
                
        if sentence.sent_id == "boletins-000004-93" and token.id == "14" and regex("Camboriú", token.word):
                token.deps = "B=UNIDADE_LITO"
                reattach(token, "6")
                
        if sentence.sent_id == "boletins-000004-93" and token.id == "21" and regex("Cabiúnas", token.word):
                token.deps = "B=UNIDADE_LITO"
                reattach(token, "6")

        # ANCHOR eliminar frases
        # ANCHOR em inglês
        if t == 0:
            if sentence.sent_id in "boletins-000001-1603|boletins-000001-1607|boletins-000001-1619|boletins-000001-1632|boletins-000001-1676|boletins-000001-1697|boletins-000001-1718|boletins-000001-1744|boletins-000001-1767|boletins-000001-3530|boletins-000001-3532|boletins-000001-3721|boletins-000002-462|boletins-000003-1573|boletins-000003-1804|boletins-000004-3046|boletins-000004-537|boletins-000005-289|boletins-000005-294|boletins-000005-349|boletins-000005-368|boletins-000005-392|boletins-000006-2418|boletins-000009-196|boletins-000010-1854|boletins-000003-1804|boletins-000004-2841|boletins-000003-1810|boletins-000003-1813|boletins-000001-1930|boletins-000001-3538|boletins-000001-3543|boletins-000001-3552|boletins-000001-3556|boletins-000001-3566|boletins-000001-3570|boletins-000001-3579|boletins-000001-3583|boletins-000004-1788|boletins-000004-2499|boletins-000004-2638|boletins-000004-2679|boletins-000004-2780|boletins-000004-2836|boletins-000005-2146|boletins-000006-75|boletins-000007-115|boletins-000009-245|boletins-000010-626|boletins-000011-889|boletins-000011-891|boletins-000011-786|boletins-000002-1363|boletins-000008-884|boletins-000001-3477|boletins-000011-151|boletins-000011-2480|boletins-000004-533|boletins-000011-786|boletins-000001-3579|boletins-000001-3583|boletins-000003-1147|boletins-000009-1679|boletins-000009-1680|boletins-000009-1681|boletins-000009-1683|boletins-000009-1685|boletins-000009-1686|boletins-000009-1694|boletins-000009-1695|boletins-000009-1697|boletins-000009-1703|boletins-000005-2146|boletins-000005-2188|boletins-000005-2276|boletins-000001-253|boletins-000001-3099|boletins-000001-3101|boletins-000001-3114|boletins-000001-3124|boletins-000001-3130|boletins-000001-3202|boletins-000002-1132|boletins-000002-1164|boletins-000002-1178|boletins-000002-1179|boletins-000002-1180|boletins-000002-1182|boletins-000002-1183|boletins-000002-1184|boletins-000002-1185|boletins-000002-1198|boletins-000002-1199|boletins-000002-1220|boletins-000002-1222|boletins-000002-1225|boletins-000002-1226|boletins-000002-1227|boletins-000002-1328|boletins-000002-1331|boletins-000002-1344|boletins-000002-1349|boletins-000002-1351|boletins-000002-1358|boletins-000002-1362|boletins-000002-1363|boletins-000002-1807|boletins-000002-1842|boletins-000002-1843|boletins-000002-1844|boletins-000002-1845|boletins-000002-1846|boletins-000002-1847|boletins-000002-1848|boletins-000002-1849|boletins-000002-1850|boletins-000002-2093|boletins-000002-2162|boletins-000002-2344|boletins-000002-2400|boletins-000002-2401|boletins-000002-2537|boletins-000002-2555|boletins-000002-2558|boletins-000002-273|boletins-000002-58|boletins-000002-59|boletins-000002-60|boletins-000002-61|boletins-000002-62|boletins-000002-633|boletins-000002-634|boletins-000002-635|boletins-000002-636|boletins-000002-637|boletins-000002-7|boletins-000002-811|boletins-000002-812|boletins-000003-1147|boletins-000003-470|boletins-000004-1215|boletins-000004-1552|boletins-000004-1554|boletins-000004-1811|boletins-000004-330|boletins-000004-963|boletins-000005-1937|boletins-000005-366|boletins-000005-391|boletins-000005-502|boletins-000005-506|boletins-000006-2140|boletins-000007-103|boletins-000008-415|boletins-000008-884|boletins-000008-902|boletins-000009-1838|boletins-000010-133|boletins-000010-397|boletins-000010-626|boletins-000011-1011|boletins-000011-1012|boletins-000011-1041|boletins-000011-1043|boletins-000011-1046|boletins-000011-1047|boletins-000011-1068|boletins-000011-1071|boletins-000011-1072|boletins-000011-1076|boletins-000011-1077|boletins-000011-1078|boletins-000011-1080|boletins-000011-1081|boletins-000011-1088|boletins-000011-1089|boletins-000011-1090|boletins-000011-1091|boletins-000011-1092|boletins-000011-1093|boletins-000011-1094|boletins-000011-1095|boletins-000011-1096|boletins-000011-1097|boletins-000011-1098|boletins-000011-1099|boletins-000011-1100|boletins-000011-1102|boletins-000011-1103|boletins-000011-1104|boletins-000011-1105|boletins-000011-1106|boletins-000011-1107|boletins-000011-1109|boletins-000011-1110|boletins-000011-1111|boletins-000011-1112|boletins-000011-1114|boletins-000011-1233|boletins-000011-1234|boletins-000011-1460|boletins-000011-1461|boletins-000011-1462|boletins-000011-1489|boletins-000011-1490|boletins-000011-1491|boletins-000011-1492|boletins-000011-1499|boletins-000011-1500|boletins-000011-1504|boletins-000011-1505|boletins-000011-1506|boletins-000011-1507|boletins-000011-1508|boletins-000011-1511|boletins-000011-1512|boletins-000011-1513|boletins-000011-1514|boletins-000011-1516|boletins-000011-1517|boletins-000011-1518|boletins-000011-1520|boletins-000011-1533|boletins-000011-1534|boletins-000011-1535|boletins-000011-1537|boletins-000011-1538|boletins-000011-1539|boletins-000011-1540|boletins-000011-1541|boletins-000011-1542|boletins-000011-1543|boletins-000011-1544|boletins-000011-1545|boletins-000011-1547|boletins-000011-1549|boletins-000011-1550|boletins-000011-1551|boletins-000011-1558|boletins-000011-1559|boletins-000011-1560|boletins-000011-1561|boletins-000011-1562|boletins-000011-1563|boletins-000011-1564|boletins-000011-1565|boletins-000011-1566|boletins-000011-1567|boletins-000011-1575|boletins-000011-1576|boletins-000011-1581|boletins-000011-1593|boletins-000011-1689|boletins-000011-1692|boletins-000011-178|boletins-000011-1840|boletins-000011-1846|boletins-000011-1929|boletins-000011-1930|boletins-000011-1931|boletins-000011-1935|boletins-000011-1941|boletins-000011-1948|boletins-000011-1949|boletins-000011-1953|boletins-000011-1974|boletins-000011-1982|boletins-000011-2152|boletins-000011-2153|boletins-000011-2166|boletins-000011-2173|boletins-000011-2175|boletins-000011-2176|boletins-000011-2179|boletins-000011-2180|boletins-000011-2183|boletins-000011-2227|boletins-000011-2239|boletins-000011-2282|boletins-000011-2286|boletins-000011-2416|boletins-000011-2417|boletins-000011-513|boletins-000011-579|boletins-000011-583|boletins-000011-584|boletins-000011-631|boletins-000011-640|boletins-000011-641|boletins-000011-771|boletins-000011-772|boletins-000011-784|boletins-000011-786|boletins-000011-816|boletins-000011-817|boletins-000011-825|boletins-000011-826|boletins-000011-827|boletins-000011-838|boletins-000011-839|boletins-000011-841|boletins-000011-842|boletins-000011-856|boletins-000011-868|boletins-000011-873|boletins-000011-879|boletins-000011-880|boletins-000011-881|boletins-000011-884|boletins-000011-889|boletins-000011-890|boletins-000011-891|boletins-000011-892|boletins-000011-893|boletins-000011-895|boletins-000011-915|boletins-000011-917|boletins-000011-919|boletins-000011-922|boletins-000011-925|boletins-000011-927|boletins-000001-1026|boletins-000001-2615|boletins-000001-3477|boletins-000001-3532|boletins-000001-46|boletins-000001-50|boletins-000002-448|boletins-000002-854|boletins-000003-1017|boletins-000003-1518|boletins-000003-2317|boletins-000003-2656|boletins-000003-2694|boletins-000003-831|boletins-000004-2217|boletins-000004-2235|boletins-000004-3831|boletins-000004-537|boletins-000004-944|boletins-000005-1071|boletins-000005-2237|boletins-000005-2269|boletins-000005-275|boletins-000006-1107|boletins-000006-2313|boletins-000006-2316|boletins-000006-895|boletins-000009-1834|boletins-000009-2161|boletins-000010-1110|boletins-000010-1173|boletins-000010-1555|boletins-000010-158|boletins-000010-1710|boletins-000010-599|boletins-000011-1155|boletins-000011-1159|boletins-000011-1263|boletins-000011-151|boletins-000011-1898|boletins-000011-2211|boletins-000011-2480|boletins-000011-673".split("|"):
                token.misc = "eliminar"

        # ANCHOR frases interrompidas
        if t == 0:
            if sentence.sent_id == "boletins-000003-90|boletins-000001-2298|boletins-000001-3579|boletins-000001-3583|boletins-000004-1347|boletins-000004-3759|boletins-000006-52|boletins-000011-1431|boletins-000001-2101|boletins-000001-2090|boletins-000004-3760|boletins-000005-277":
                token.misc = "eliminar"

        # 26/07/2022
        if regex("alagoo", token.lemma) and regex("idade", token.head_token.lemma):
            token.lemma = "Alagoas"
            token.upos = "PROPN"
            token.deprel = "nmod"
            token.feats = "Gender=Fem|Number=Sing"

        if sentence.sent_id == "boletins-000011-2362" and token.id == "25" and regex("de", token.word) and regex("a", token.next_token.word) and regex("Chapada", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Araripe", token.next_token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            token.deps = "O"
            reattach(token, "27")
            token.next_token.deprel = "det"
            token.next_token.deps = "O"
            reattach(token.next_token, "27")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deprel = "case"
            token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token, "30")
            token.next_token.next_token.next_token.next_token.deprel = "det"
            token.next_token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token.next_token, "30")
            token.next_token.next_token.next_token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token.next_token.next_token, "27")

        if token.lemma == "Campaniano" and token.next_token.word == "a" and token.next_token.next_token.lemma == "Recente" and token.next_token.deprel == "flat:name":
            reattach(token.next_token, token.next_token.next_token.id)
            token.next_token.deprel = "cc"
            token.next_token.upos = "ADP"
            token.next_token.feats = "_"
            token.next_token.lemma = "a"
            token.next_token.next_token.deprel = "conj"

        if sentence.sent_id == "boletins-000003-358" and token.id == "9" and regex("de", token.word) and regex("o", token.next_token.word) and regex("Granito", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Cabo", token.next_token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            token.deps = "O"
            reattach(token, "11")
            token.next_token.deprel = "det"
            token.next_token.deps = "O"
            reattach(token.next_token, "11")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token, "6")
            token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token, "11")
            token.next_token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token.next_token, "11")
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token.next_token.next_token, "11")

        if sentence.sent_id == "boletins-000009-38" and token.id == "4" and regex("Bacia/", token.word) and regex("Embasamento", token.next_token.word):
            token.lemma = "bacia"
            token.upos = "NOUN"
            token.deprel = "nmod"
            token.next_token.deprel = "nmod"
            token.feats = "Gender=Fem|Number=Sing"
            token.next_token.lemma = "embasamento"
            token.next_token.upos = "NOUN"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "B=UNIDADE_LITO"
            reattach(token.next_token, "4")

        if sentence.sent_id == "boletins-000009-61" and token.id == "26" and regex("de", token.word) and regex("o", token.next_token.word) and regex("Proterozóico", token.next_token.next_token.word) and regex("Superior", token.next_token.next_token.next_token.word):
            token.deprel = "case"
            token.deps = "O"
            reattach(token, "28")
            token.next_token.deprel = "det"
            token.next_token.deps = "O"
            reattach(token.next_token, "28")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            reattach(token.next_token.next_token.next_token, "28")

        if regex("Formação", token.word) and regex("Marizal", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Andar", token.next_token.next_token.next_token.next_token.word) and regex("Alagoas", token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.next_token.deprel = "case"
            token.next_token.next_token.next_token.deprel = "det"
            token.next_token.next_token.next_token.next_token.deprel = "nmod"
            reattach(token.next_token.next_token, token.next_token.next_token.next_token.next_token.id)
            reattach(token.next_token.next_token.next_token, token.next_token.next_token.next_token.next_token.id)
            reattach(token.next_token.next_token.next_token.next_token, token.id)
            reattach(token.next_token.next_token.next_token.next_token.next_token, token.next_token.next_token.next_token.next_token.id)

        if sentence.sent_id == "boletins-000011-405" and token.id == "39" and regex("impreg-nado", token.word) and regex("de", token.next_token.word) and regex("óleo", token.next_token.next_token.word):
            token.deprel = "acl"
            token.upos = "VERB"
            token.feats = "Gender=Masc|Number=Sing|VerbForm=Part"
            token.deps = "O"
            token.lemma = "impregnar"
            reattach(token, "34")
            token.next_token.next_token.deprel = "obl"
            reattach(token.next_token.next_token, "39")

        if sentence.sent_id == "boletins-000009-2197" and token.id == "28":
            reattach(token, "20")

        # TATI 02/08/22

        if regex("bioestratigrágico|bioestratigrafico", token.lemma):
            token.lemma = "bioestratigráfico"

        if regex("rígido", token.lemma) and regex("VERB|NOUN", token.upos):
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = remove_from(token.feats, "VerbForm=Part")

        if regex("feldspatos?", token.word) and regex("feldspar", token.lemma):
            token.lemma = "feldspato"
            token.deprel = "appos"
            token.upos = "NOUN"
            token.feats = remove_from(token.feats, "VerbForm=Part")

        if regex("ar\-ranjar", token.lemma):
            token.lemma = "arranjar"

        if regex("canal", token.head_token.lemma) and regex("amod", token.deprel) and regex("D", token.lemma):
            token.deprel = "nmod"
            token.upos = "PROPN"

        if regex("restrinar", token.lemma):
            token.lemma = "restringir"

        if regex("pro\-posição", token.lemma):
            token.lemma = "proposição"

        if regex("super\-por", token.lemma):
            token.lemma = "superpor"

        if regex("incom\-pleto", token.lemma):
            token.lemma = "incompleto"

        # MCLARA 15/08/2022

        if regex("albo\-cenomaniana", token.lemma):
            token.lemma = "albo-cenomaniano"
            
        if regex("cenomaniana\-santoniana", token.lemma):
            token.lemma = "cenomaniano-santoniano"
            
        if regex("cre\-táceo", token.lemma):
            token.lemma = "cretáceo"
            
        if regex("devo\-niana", token.lemma):
            token.lemma = "devoniano"
            
        if regex("frasniana", token.lemma):
            token.lemma = "frasniano"
            
        if regex("jurássica\-cretá\-cea|jurássica\-cretácea", token.lemma):
            token.lemma = "jurássico-cretáceo"
            
        if regex("juro\-cretácea", token.lemma):
            token.lemma = "juro-cretáceo"
            
        if regex("kazaniana", token.lemma):
            token.lemma = "kazaniano"
            
        if regex("lanvirniana", token.lemma):
            token.lemma = "lanvirniano"
            
        if regex("necaptiano", token.lemma):
            token.lemma = "neoaptiano"
            
        if regex("neo\-albiana\-eoturoniana", token.lemma):
            token.lemma = "neo-albiano-eoturoniano"
            
        if regex("neocampaniano\.", token.lemma):
            token.lemma = "neocampaniano"
            
        if regex("pré\-alagoo", token.lemma):
            token.lemma = "pré-Alagoas"
            
        if regex("sil\-uriano", token.lemma):
            token.lemma = "siluriano"
            
        if regex("permocarbonifero|permocarbonífera", token.lemma):
            token.lemma = "permocarbonífero"
            
        if regex("turoniano\-santoniana", token.lemma):
            token.lemma = "turoniano-santoniano"

        if sentence.sent_id == "boletins-000011-728" and token.id == "42" and regex("eoalbia", token.word) and regex("na", token.next_token.word):
            token.lemma = "eoalbiano"
            token.next_token.deprel = "goeswith"
            token.next_token.upos = "X"
            token.next_token.feats = "_"
            reattach(token.next_token, "42")
            
        if sentence.sent_id == "boletins-000001-1344" and token.id == "8" and regex("atokana", token.word):
            token.upos = "ADJ"
            token.lemma = "atokano"
            token.deps = "B=UNIDADE_CRONO"
            reattach(token, "6")

        if regex("no", token.word) and regex("Eocampania", token.previous_token.lemma):
            token.deprel = "goeswith"
            token.feats = "_"
            token.upos = "X"
            token.lemma = "no"
            token.previous_token.lemma = "Eocampaniano"
            token.previous_token.deps = "B=UNIDADE_CRONO"

        # MCLARA 29/08/2022

        if regex("almofar", token.lemma):
            token.lemma = "almofadado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Fem|Number=Plur"
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("estratificação", token.lemma) and regex("cruzada", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("baixo", token.next_token.next_token.next_token.lemma) and regex("ângulo", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[eE]stratificação", token.lemma) and regex("[Cc]ruzada", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[eE]stratificação|Estratificações", token.lemma) and regex("[Cc]ruzadas", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("foliação", token.lemma) and regex("milonitico|milonítico", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "milonítico"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[lL]aminação", token.lemma) and regex("[Oo]ndulada", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "ondulado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[lL]aminação", token.lemma) and regex("[Pp]aralele", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "paralelo"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("puil\-apart", token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.lemma = "pull-apart"
            
        if regex("[lL]aminação", token.lemma) and regex("[Oo]nduladas", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "ondulado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"

        if regex("estratificação", token.lemma) and regex("cruzadas", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("baixo", token.next_token.next_token.next_token.lemma) and regex("ângulo", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("estratificação", token.lemma) and regex("cruzadas", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("baixo", token.next_token.next_token.next_token.lemma) and regex("ângulo", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[eE]stratificação|Estratificações", token.lemma) and regex("plano\-paralela", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "plano-paralelo"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("estratificação", token.lemma) and regex("cruzar|cruzado", token.next_token.lemma) and regex("acanala\-da", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.lemma = "acanalado"
            token.next_token.next_token.upos = "ADJ"
            token.next_token.next_token.deprel = "amod"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("estratificação", token.lemma) and regex("cruzar|cruzado", token.next_token.lemma) and regex("acanalar|acanalado", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.lemma = "acanalado"
            token.next_token.next_token.upos = "ADJ"
            token.next_token.next_token.deprel = "amod"
            token.next_token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[lL]aminação", token.lemma) and regex("[Cc]ruzada", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[lL]aminação", token.lemma) and regex("[Cc]ruzadas", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.lemma = "cruzado"
            token.next_token.upos = "ADJ"
            token.next_token.deprel = "amod"
            token.next_token.feats = "Gender=Fem|Number=Plur"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("ondular", token.lemma) and regex("cruzada", token.head_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.lemma = "ondulado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Fem|Number=Sing"
            
        if regex("cruzada", token.word) and regex("laminação", token.head_token.previous_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.lemma = "cruzado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Fem|Number=Sing"
            
        if regex("acanaladas", token.word) and regex("estratificação", token.head_token.head_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.lemma = "acanalado"
            token.upos = "ADJ"
            token.deprel = "amod"
            token.feats = "Gender=Fem|Number=Plur"

        if sentence.sent_id == "boletins-000003-2561" and token.id == "5" and regex("estruturas", token.word) and regex("de", token.next_token.word) and regex("chama", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("pseudonódulos", token.next_token.next_token.next_token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            reattach(token.next_token, "7")
            token.next_token.next_token.lemma = "chama"
            token.next_token.next_token.upos = "NOUN"
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.feats = "Gender=Fem|Number=Sing"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            reattach(token.next_token.next_token.next_token.next_token, "1")

        # correções lemma e sintaxe_eventos do sist petro
        # tati 30/08/2022

        if regex("rachas", token.word) and regex("gerador", token.next_token.lemma):
            token.lemma = "rocha"

        if regex("inicial|alto|original", token.lemma) and regex("gerador", token.head_token.lemma) and regex("VERB", token.head_token.head_token.upos) and regex("potencial", token.head_token.previous_token.lemma) and regex("ADJ", token.head_token.head_token.next_token.upos):
            token.head_token.previous_token.dephead = token.head_token.dephead
            token.head_token.previous_token.upos = "NOUN"
            token.head_token.previous_token.deprel = "obj"
            token.head_token.dephead = token.head_token.previous_token.id
            token.head_token.upos = "ADJ"
            token.head_token.deprel = "amod"
            token.dephead = token.head_token.previous_token.id

        if regex("inicial|alto|original", token.lemma) and regex("gerador", token.head_token.lemma) and regex("VERB", token.head_token.head_token.upos) and regex("potencial", token.head_token.previous_token.lemma) and regex("DET", token.head_token.head_token.next_token.upos):
            token.head_token.previous_token.dephead = token.head_token.dephead
            token.head_token.previous_token.upos = "NOUN"
            token.head_token.previous_token.deprel = "obj"
            token.head_token.dephead = token.head_token.previous_token.id
            token.head_token.upos = "ADJ"
            token.head_token.deprel = "amod"
            token.dephead = token.head_token.previous_token.id
            token.head_token.head_token.next_token.dephead = token.head_token.previous_token.id

        if regex("potencial", token.lemma) and regex("gerador", token.next_token.lemma) and regex("S", token.next_token.next_token.lemma):
            token.deprel = "appos"
            token.upos = "NOUN"
            token.next_token.deprel = "amod"
            token.next_token.upos = "ADJ"
            token.next_token.next_token.deprel = "nmod"

        if regex("original", token.lemma) and regex("gerador", token.head_token.lemma) and regex("NOUN", token.head_token.head_token.upos) and regex("potencial", token.head_token.previous_token.lemma) and regex("ADP", token.head_token.head_token.next_token.upos) and regex("DET", token.head_token.head_token.next_token.next_token.upos):
            token.head_token.previous_token.dephead = token.head_token.dephead
            token.head_token.previous_token.upos = "NOUN"
            token.head_token.previous_token.deprel = "nmod"
            token.head_token.dephead = token.head_token.previous_token.id
            token.head_token.upos = "ADJ"
            token.head_token.deprel = "amod"
            token.dephead = token.head_token.previous_token.id
            token.head_token.head_token.next_token.dephead = token.head_token.previous_token.id
            token.head_token.head_token.next_token.next_token.dephead = token.head_token.previous_token.id

        if regex("potencial", token.lemma) and regex("gerador", token.next_token.lemma) and regex("ADJ", token.upos):
            token.dephead = token.next_token.dephead
            token.deprel = token.next_token.deprel
            token.upos = token.next_token.upos
            token.next_token.dephead = token.id
            token.next_token.deprel = "amod"
            token.next_token.upos = "ADJ"

        if regex("óleo/rocho", token.lemma):
            token.lemma = "óleo/rocha"

        if regex("gerador|potencial", token.lemma) and regex("correlação", token.head_token.lemma) and regex("ADJ", token.head_token.next_token.upos):
            token.dephead = token.head_token.next_token.id
            token.head_token.next_token.upos = "NOUN"
            token.head_token.next_token.deprel = "nmod"

        if regex("gerador", token.head_token.lemma) and regex("como", token.head_token.previous_token.lemma) and regex("tanto", token.head_token.previous_token.previous_token.lemma) and regex("gerador", token.lemma) and regex("quanto", token.previous_token.lemma) and regex("de", token.next_token.lemma) and regex("NOUN", token.next_token.next_token.upos):
            token.deprel = "conj"
            token.upos = "NOUN"
            token.previous_token.upos = "CCONJ"
            token.previous_token.deprel = "cc"
            token.next_token.next_token.deprel = "nmod"

        if regex("procer", token.lemma):
            token.lemma = "processar"

        if regex("hetero\-geneidade", token.lemma):
            token.lemma = "heterogeneidade"

        if regex("modifi\-car", token.lemma):
            token.lemma = "modificar"

        if regex("exce\-der", token.lemma):
            token.lemma = "exceder"

        if regex("desa\-fiar", token.lemma):
            token.lemma = "desafiar"

        if regex("roto|ro\-ta", token.lemma):
            token.lemma = "rota"

        if regex("dis\-posição", token.lemma):
            token.lemma = "disposição"

        if regex("enge\-nheiro", token.lemma):
            token.lemma = "engenheiro"

        if regex("provín\-", token.lemma):
            token.lemma = "província"

        if regex("riftea\-mento", token.lemma):
            token.lemma = "rifteamento"

        if regex("segúência", token.lemma):
            token.lemma = "sequência"

        if regex("suít", token.lemma):
            token.lemma = "suíte"

        if regex("be\-tume", token.lemma):
            token.lemma = "betume"

        if regex("Forma\-cio|Formacão", token.lemma):
            token.lemma = "Formação"

        if regex("excep\-cional", token.lemma):
            token.lemma = "excepcional"

        if regex("má", token.lemma):
            token.lemma = "mau"

        if regex("pom", token.lemma):
            token.lemma = "péssimo"

        if regex("adequada\.", token.lemma):
            token.lemma = "adequado"

        if regex("bra\-sileiro", token.lemma):
            token.lemma = "brasileiro"

        if regex("com\-plexo", token.lemma):
            token.lemma = "complexo"

        if regex("cam\-paniano", token.lemma):
            token.lemma = "campaniano"

        if regex("pré\-alagoo", token.lemma):
            token.lemma = "pré-Alagoas"

        if regex("fratu\-rados", token.lemma):
            token.lemma = "fraturar"
            token.upos = "VERB"
            token.deprel = "acl"
            token.feats = append_to(token.feats, "VerbForm=Part")

        if regex("oligocê\-rico", token.lemma):
            token.lemma = "oligocênico"

        if regex("oligocênico\-mnicosênico", token.lemma):
            token.lemma = "oligocênico-miocênico"

        if regex("paleocênicos\-mico", token.lemma):
            token.lemma = "paleocênico-miocênico"

        if regex("inter\-mediário", token.lemma):
            token.lemma = "intermediário"

        if regex("turbiditico", token.lemma):
            token.lemma = "turbidítico"

        if regex("fácio|fácie", token.lemma):
            token.lemma = "fácies"

        if regex("siciliclástico", token.lemma):
            token.lemma = "siliciclástico"

        if regex("int\-cio", token.lemma):
            token.lemma = "início"

        if regex("misturar", token.lemma) and regex("mist[oa]s?", token.word):
            token.lemma = "misto"
            token.upos = "ADJ"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("misto", token.lemma) and regex("acl", token.deprel):
            token.deprel = "amod"

        if sentence.sent_id == "boletins-000004-3420" and token.id == "10" and regex("e", token.word) and regex("Pelotas", token.next_token.word):
            token.deps = "O"
            token.deprel = "cc"
            reattach(token, "11")
            token.next_token.deps = "B=BACIA"
            token.next_token.deprel = "conj"

        if sentence.sent_id == "boletins-000001-3704" and token.id == "26" and regex("de", token.word) and regex("os", token.next_token.word) and regex("Desmoinesian", token.next_token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "28")
            token.next_token.deps = "O"
            token.next_token.deprel = "det"
            reattach(token.next_token, "28")
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000001-3796" and token.id == "8" and regex("de", token.word) and regex("a", token.next_token.word) and regex("Amazônia", token.next_token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "10")
            token.next_token.deps = "O"
            token.next_token.deprel = "det"
            reattach(token.next_token, "10")
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000001-1475" and token.id == "9" and regex("de", token.word) and regex("as", token.next_token.word) and regex("Bacias", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Amazonas", token.next_token.next_token.next_token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("Solimões", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "11")
            token.next_token.deps = "O"
            token.next_token.deprel = "det"
            reattach(token.next_token, "11")
            token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            reattach(token.next_token.next_token.next_token.next_token.next_token.next_token.next_token, "11")
            
        if sentence.sent_id == "boletins-000010-14" and token.id == "24" and regex("de", token.word) and regex("o", token.next_token.word) and regex("Texas", token.next_token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "26")
            token.next_token.deps = "O"
            token.next_token.deprel = "det"
            reattach(token.next_token, "26")
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000006-6" and token.id == "18" and regex("de", token.word) and regex("Peniche", token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "19")
            token.next_token.deps = "O"
            token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000006-132" and token.id == "17" and regex("de", token.word) and regex("Peniche", token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "18")
            token.next_token.deps = "O"
            token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000006-52" and token.id == "25" and regex("de", token.word) and regex("Peniche", token.next_token.word):
            token.deps = "O"
            token.deprel = "case"
            reattach(token, "26")
            token.next_token.deps = "O"
            token.next_token.deprel = "nmod"
            
        if sentence.sent_id == "boletins-000011-400" and token.id == "34" and regex("Paraná", token.word) and regex("e", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Parnaíba", token.next_token.next_token.next_token.next_token.word):
            token.deps = "B=BACIA"
            token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
            reattach(token.next_token.next_token.next_token.next_token, "34")

        # MCLARA 10/10/2022

        if sentence.sent_id == "boletins-000006-110" and token.id == "7" and regex("as", token.word) and regex("Formações", token.next_token.word) and regex("Bucomazi", token.next_token.next_token.word):
            token.deprel = "det"
            reattach(token, "8")
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token, "8")
            
        if sentence.sent_id == "boletins-000006-110" and token.id == "16" and regex("Iabe", token.word):
            token.deps = "B=UNIDADE_LITO"
            reattach(token, "8")

        if sentence.sent_id == "boletins-000011-216" and token.id == "16" and regex("de", token.word) and regex("a", token.next_token.word) and regex("Formação", token.next_token.next_token.word) and regex("Pojuca", token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "18")
            token.next_token.deprel = "det"
            reattach(token.next_token, "18")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token.next_token, "18")

        if sentence.sent_id == "boletins-000011-217" and token.id == "10" and regex("de", token.word) and regex("a", token.next_token.word) and regex("Formação", token.next_token.next_token.word) and regex("Pojuca", token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "12")
            token.next_token.deprel = "det"
            reattach(token.next_token, "12")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token.next_token, "12")

        if sentence.sent_id == "boletins-000003-19" and token.id == "29" and regex("de", token.word) and regex("a", token.next_token.word) and regex("Formação", token.next_token.next_token.word) and regex("Pendência", token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "31")
            token.next_token.deprel = "det"
            reattach(token.next_token, "31")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token.next_token, "31")

        if sentence.sent_id == "boletins-000003-2722" and token.id == "22" and regex("sobre", token.word) and regex("a", token.next_token.word) and regex("Formação", token.next_token.next_token.word) and regex("Água", token.next_token.next_token.next_token.word) and regex("Grande", token.next_token.next_token.next_token.next_token.word):
            token.deprel = "case"
            reattach(token, "24")
            token.next_token.deprel = "det"
            reattach(token.next_token, "24")
            token.next_token.next_token.deprel = "nmod"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token.next_token, "24")
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            reattach(token.next_token.next_token.next_token.next_token, "24")

        if sentence.sent_id == "boletins-000003-1241" and token.id == "21" and regex("Dom", token.word) and regex("João", token.next_token.word):
            token.deps = "B=UNIDADE_CRONO"
            reattach(token, "17")
            token.next_token.deps = "I=UNIDADE_CRONO"

        # MCLARA 23/12/2022
        if sentence.sent_id == "boletins-000009-1529" and token.id == "15" and regex("Coqueiro", token.word) and regex("Seco", token.next_token.word) and regex("li", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("IV", token.next_token.next_token.next_token.next_token.word):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.lemma = "II"
            token.next_token.next_token.upos = "PROPN"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.deprel = "flat:name"
            reattach(token.next_token.next_token, "15")
            token.next_token.next_token.next_token.next_token.deps = "O"
            reattach(token.next_token.next_token.next_token.next_token, "15")

        #regras de correção pós-uri - Tati 15/02/2023

        if regex("1-TP", token.word) and regex("0001|0002", token.next_token.word) and regex("SC", token.next_token.next_token.word) and regex("poços", token.previous_token.previous_token.word):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"
            token.next_token.deprel = "flat:name"
            token.next_token.dephead = token.id
            token.next_token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deprel = "flat:name"
            token.next_token.next_token.dephead = token.id
            token.dephead = token.previous_token.previous_token.id
            token.deprel = "nmod"
            token.upos = "PROPN"
            token.feats = "_"

        if regex("2-PUst-1", token.word) and regex("-SC", token.next_token.word) and regex("poço", token.previous_token.previous_token.lemma) and regex("1-CN-2-SC.", token.next_token.next_token.next_token.word):
            token.next_token.deps = "I=POÇO"
            token.next_token.dephead = token.id
            token.next_token.deprel = "flat:name"
            token.dephead = token.previous_token.previous_token.id
            token.upos = "PROPN"
            token.feats = "Gender=Masc|Number=Sing"
            token.deprel = "nmod"
            token.next_token.next_token.next_token.lemma = "1-CN-2-SC"
            token.next_token.next_token.next_token.upos = "PROPN"
            token.next_token.next_token.next_token.deprel = "conj"
            token.next_token.next_token.next_token.dephead = token.id
            token.next_token.next_token.next_token.feats = "Gender=Masc|Number=Sing"

    # ANCHOR (2) léxico via regra
    for token in sentence.tokens:
        if token.lemma in "Cedro Tucano Jatobá Recôncavo-Tucano-Jatobá".split():
            token.deps = "B=BACIA"
        if token.word == "Tucano" and token.next_token.word == "e" and token.next_token.next_token.word == "Jatobá":
            token.deps = "B=BACIA"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "B=BACIA"
        if token.word == "Dom" and token.next_token.word == "Jodo":
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
        if regex("Canto", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Amaro", token.next_token.next_token.next_token.word):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.deps = "I=CAMPO"
        if token.lemma == "Arenitos":
            token.deps = "B=ROCHA"
        if regex(".*cret[áa]cico.*|[pP]roteroz[eé]ico", token.word):
            token.deps = "B=UNIDADE_CRONO"
        if regex("subvulcânico", token.lemma):
            token.deps = "B=ROCHA"
        if regex("campo|Campo", token.lemma):
            token.deps = "B=CAMPO"
        if regex("[Pp]ocos?", token.word):
            token.lemma = "poço"
            token.deps = "B=POÇO"

        #bacias Mesozóicas -Cenozóicas

        if regex("Mesozóicas-Cenozóicas|Proterozóica|Mesozóicas|Mesozóica|mesozóica|Cenozóica|cenozóica|-cenozóica|\-Cenozóicas", token.lemma) and regex("bacia|Bacia|Bacias", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"

        if regex("neo-Rio", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.deps = "I=CAMPO"

        #betume

        if regex("grão", token.lemma) and regex("paleovulcânico|neovulcânico", token.next_token.lemma):
            token.deps = "B=NÃOCONSOLID"
            token.next_token.deps = "I=NÃOCONSOLID"
        if regex("NOUN", token.upos) and regex("de", token.next_token.lemma) and regex("origem", token.next_token.next_token.lemma) and regex("vulcânica", token.next_token.next_token.next_token.word):
            token.deps = "B=NÃOCONSOLID"
            token.next_token.deps = "I=NÃOCONSOLID"
            token.next_token.next_token.deps = "I=NÃOCONSOLID"
            token.next_token.next_token.next_token.deps = "I=NÃOCONSOLID"
        if regex("vulcanoclástico", token.lemma) and regex("material", token.previous_token.lemma):
            token.deps = "I=NÃOCONSOLID"
            token.previous_token.deps = "B=NÃOCONSOLID"
        if regex("vulcânica|vulcânico", token.next_token.lemma) and regex("material|fragmento|lava|partícula", token.lemma):
            token.deps = "B=NÃOCONSOLID"
            token.next_token.deps = "I=NÃOCONSOLID"
        if regex("vulcânica|vulcânico", token.next_token.lemma) and regex("intrusivo|vidro|corpo|extrusivo|tufo", token.lemma):
            token.deps = "B=ROCHA"
            token.next_token.deps = "I=ROCHA"
        if regex("vulcanoclasto|vulcanoclastos", token.word):
            token.deps = "B=NÃOCONSOLID"
        if regex("sedimento", token.lemma):
            token.deps = "B=NÃOCONSOLID"
        if regex("vulcanoclástico", token.lemma) and regex("rocha|litofácie|turbidito", token.previous_token.lemma):
            token.deps = "I=ROCHA"
            token.previous_token.deps = "B=ROCHA"

        # QUALIFICAÇÕES DO POÇO
        # TATI
        # 24/05/2022

        if regex("descobridor", token.lemma) and regex("poço", token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.lemma):
            token.deprel = "nmod:appos"
            token.dephead = token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.id
            token.deps = "B=POÇO_Q"
            token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.deprel = "flat:name"
            token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.dephead = token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.id
            token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.deps = "I=POÇO"
            token.previous_token.previous_token.previous_token.previous_token.dephead = token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.id

        if regex("prospecto|jazida", token.lemma) and regex("mais", token.next_token.lemma) and regex("raso|profundo", token.next_token.next_token.lemma):
            token.deps = "B=POÇO_T"
            token.next_token.deps = "I=POÇO_T"
            token.next_token.next_token.deps = "I=POÇO_T"
        if regex("prospecto|jazida", token.lemma) and regex("raso|profundo", token.next_token.lemma):
            token.deps = "B=POÇO_T"
            token.next_token.deps = "I=POÇO_T"   
        if regex("seco", token.lemma) and regex("xcomp", token.deprel) and regex("abandonar", token.head_token.lemma):
            token.deps = "B=POÇO_Q"

        if regex("Formação", token.word) and regex("Barra", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Itiúba", token.next_token.next_token.next_token.word):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Membro", token.word) and regex("Água", token.next_token.word) and regex("Grande", token.next_token.next_token.word):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
        if regex("Alto", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Rodrigues", token.next_token.next_token.next_token.word):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.deps = "I=CAMPO"
        
        #Pensilvaniano (na planillha aparece com Pennsylvaniano)
        if regex("Pensilvaniano", token.lemma):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Rio", token.lemma) and regex("Ribeira", token.next_token.lemma) and regex("bacia", token.head_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"

        if token.word.lower() == "siltitos":
            token.deps = "B=ROCHA"

        if regex("pioneiro|estratigráfico|estratigrafico|especial|explotatório|explotatorio", token.lemma) and regex("DET|NUM", token.previous_token.upos):
            token.deps = "B=POÇO_T"

        if regex("Acaraú|Icaraí|Mundaú", token.lemma) and regex("Piauí\-Camocim", token.head_token.lemma) and regex("Bacia", token.head_token.head_token.lemma):
            token.deps = "B=BACIA"
            token.head_token.deps = "B=BACIA"

        # mclara 06-07-2022

        if regex("Alagoas", token.lemma) and regex("pós\-deposional", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Alagoas", token.lemma) and regex("Jequiá", token.head_token.lemma) and regex("estágio", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Jequiá", token.lemma) and regex("estágio", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Rio", token.lemma) and regex("[aA]ndar", token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("Inferior", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("Mesozóicas\-Cenozóicas|Mesozóicas\-Ceno\-zóicas", token.word) and regex("Bacias", token.previous_token.lemma):
            token.lemma = "Mesozóicas-Cenozóicas"
            token.deps = "B=UNIDADE_CRONO"

        if regex("Boipeba|Capianga", token.lemma) and regex("Afligidos", token.head_token.lemma) and regex("[mM]embro", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            
        if regex("2", token.lemma) and regex("CC", token.head_token.lemma) and regex("[mM]embro", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Itararé|Coruripe", token.lemma) and regex("[sS]ubgrupo", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        if regex("de", token.lemma) and regex("o", token.next_token.lemma) and regex("Sul", token.next_token.next_token.lemma) and regex("Grupo", token.head_token.head_token.head_token.lemma):
            token.deps = "I=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Campo", token.lemma) and regex("Mourão", token.next_token.lemma) and regex("formação", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Taciba", token.lemma) and regex("formação", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Tenente", token.next_token.next_token.next_token.word):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Serra|Rio", token.lemma) and regex("Alta|Doce", token.next_token.lemma) and regex("[Ff]ormação|Formações|[Gg]rupo|Grupos", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Serraria|Penedo|Guamaré|Alagamar", token.lemma) and regex("[Ff]ormação|Formações|[Gg]rupo|Grupos", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        if regex("Serraria|Penedo|Guamaré|Alagamar", token.lemma) and regex("[Ff]ormação|Formações|[Gg]rupo|Grupos", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        if regex("Tito\-niano", token.lemma):
            token.lemma = "Titoniano"
            token.deps = "B=UNIDADE_CRONO"

        if regex("mesozóico", token.lemma) and regex("Cenozóicas", token.next_token.lemma) and regex("[bB]acia|Bacias", token.head_token.lemma):
            token.next_token.deps = "I=UNIDADE_CRONO"

        # ANOTAÇÃO DE TEXTURA
        # TATI
        # 27/07/2022

        if regex("alongar|alongado", token.lemma) and regex("grão|poro", token.head_token.lemma):
            token.deps = "B=TEXTURA"

        if regex("cataclástico|cimento|dendrítico|estromatolítico|cripto\-cristalino|criptocristalino|fanerítico|grumoso|hipohialino|microcristalino|milonítico|pseudomorfo|traquítico|zonar|poiquilotópico", token.lemma):
            token.deps = "B=TEXTURA"

        if regex("contato", token.head_token.lemma) and regex("irregular|côncavo-convexo", token.lemma):
            token.head_token.deps = "B=TEXTURA"
            token.deps = "I=TEXTURA"

        if regex("inequigranular", token.lemma):
            token.deps = "B=TEXTURA"
        if regex("inequigranular", token.head_token.lemma) and regex("porfirítico", token.lemma):
            token.head_token.deps = "B=TEXTURA"
            token.deps = "I=TEXTURA"

        if regex("fratura", token.head_token.lemma) and regex("intergranular", token.lemma):
            token.head_token.deps = "B=TEXTURA"
            token.deps = "I=TEXTURA"

        if regex("alveolar|alveolado", token.lemma) and regex("feldspato", token.head_token.lemma):
            token.deps = "B=TEXTURA"

        if regex("fácies", token.word) and regex("caótico", token.next_token.lemma):
            token.next_token.deps = "B=TEXTURA"

        if regex("(boletins-000004-952|boletins-000004-1089|boletins-000009-1771|boletins-000004-1095)", sentence.sent_id ) and regex("caótico", token.lemma):
            token.deps = "B=TEXTURA"

        if regex("pacote", token.lemma) and regex("caótico", token.next_token.lemma):
            token.next_token.deps = "B=TEXTURA"

        if regex("material", token.lemma) and regex("argiloso", token.next_token.lemma) and regex("intersticial", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "B=TEXTURA"

        if regex("formar", token.head_token.lemma) and regex("mosaico", token.lemma):
            token.deps = "B=TEXTURA"

        if regex("megacristalina", token.lemma):
            token.lemma = "megacristalino"
            token.deps = "B=TEXTURA"

        if regex("meso", token.lemma) and regex("textura", token.head_token.lemma):
            token.deps = "B=TEXTURA"

        if regex("subofítico|subofitica", token.lemma):
            token.lemma = "subofítico"
            token.deps = "B=TEXTURA"

        if regex("ofitico", token.lemma):
            token.lemma = "ofítico"
            token.deps = "B=TEXTURA"

        if regex("neoaptiano|eoalbiano|arenigiano|ordoviciana\-cretácico|permiana\-triássico|pleistocênico|pré\-Alagoas|jurássico\-cretáceo|juro\-cretáceo|cretáceo|devoniano|kazaniano|albo\-cenomaniano|frasniano|neocampaniano|cenomaniano\-santoniano|neo\-albiano\-eoturoniano|siluriano", token.lemma) and regex("[Ii]dade", token.previous_token.lemma):
            token.deps = "I=UNIDADE_CRONO"
            token.previous_token.deps = "B=UNIDADE_CRONO"

        # add deps TIPO POROSIDADE
        # TATI 18/08/2022
        if regex("[Cc]averna", token.lemma):
            token.deps = "B=TIPO_POROSIDADE"

        if regex("porosidade", token.lemma) and regex("secundário", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("contração", token.next_token.next_token.next_token.lemma) and regex("shrinkage", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "B=TIPO_POROSIDADE"
            token.next_token.next_token.next_token.next_token.next_token.deps = "B=TIPO_POROSIDADE"

        if regex("intragranular", token.lemma):
            token.deps = "B=TIPO_POROSIDADE"

        if regex("microporosidade", token.lemma):
            token.deps = "B=TIPO_POROSIDADE"

        if regex("móldico", token.lemma):
            token.deps = "B=TIPO_POROSIDADE"

        if regex("[Vv]ugs?|[Vv]ugues?", token.word):
            token.deps = "B=TIPO_POROSIDADE"

        if regex("microvugues?|microvugs?", token.word):
            token.deps = "B=TIPO_POROSIDADE"

        # MCLARA 29/08/2022

        if regex("Barra", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Itiúba", token.next_token.next_token.next_token.lemma) and regex("Serraria", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("estrada", token.lemma) and regex("Nova", token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Irati", token.lemma) and regex("Serra", token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Regência", token.lemma) and regex("São", token.head_token.lemma) and regex("Algodões", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Riachuelo", token.lemma) and regex("Muribeca", token.head_token.lemma) and regex("[fF]ormação", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("São", token.lemma) and regex("Mateus", token.next_token.lemma) and regex("Algodões", token.head_token.lemma) and regex("[fF]ormação", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Serra", token.lemma) and regex("Alta\-Teresina", token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Tatuí", token.lemma) and regex("Paulo", token.previous_token.previous_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Ubarana", token.lemma) and regex("Tibau", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Dom", token.lemma) and regex("João", token.next_token.lemma) and regex("Aliança", token.head_token.lemma) and regex("[fF]ormação", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("[cC]amadas", token.lemma) and regex("Ponta", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("Tubarão", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Aratu\/Rio", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("amigdaloidal|bandamento|Bandamentos|[cC]livagem|[cC]olunar|concreção|dômico|[Ee]squeletal|xistosidade|[Ff]alhamento|[Gg]náissico|[lL]aminação|[Ll]enticular|[Ll]ineação|[lL]insen|flaser|veio|vesicular|wavy|[Rr]ipple|[Rr]ipples|sulco", token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"

        if regex("chevron|mound|mounds|faulting|scour|[Ss]lickensides|slump", token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"

        if regex("[Cc]ontato", token.lemma) and regex("abrupto|discordante|erosivo|gradacional", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("corte", token.lemma) and regex("e", token.next_token.lemma) and regex("preenchimento", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("cruzadas", token.word) and regex("de", token.next_token.lemma) and regex("baixo", token.next_token.next_token.lemma) and regex("ângulo", token.next_token.next_token.next_token.lemma) and regex("estratificação", token.head_token.lemma) and regex(",", token.previous_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[eE]strutura", token.lemma) and regex("de", token.next_token.lemma) and regex("[Cc]arga", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("prato", token.lemma) and regex("em", token.previous_token.lemma) and regex("[eE]strutura|Estruturas", token.head_token.lemma):
            token.deps = "I=ESTRUTURA_FÍSICA"
            token.previous_token.deps = "I=ESTRUTURA_FÍSICA"
            token.head_token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("feição", token.lemma) and regex("de", token.next_token.lemma) and regex("exposição", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("filme", token.lemma) and regex("de", token.next_token.lemma) and regex("argila", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Ff]ratura", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("[Tt]ipo", token.next_token.next_token.next_token.lemma) and regex("I|II", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Ff]ratura", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("[Tt]ipo", token.next_token.next_token.next_token.lemma) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("R|T", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("gradação", token.lemma) and regex("normal", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[gG]reta|Gretas", token.lemma) and regex("de", token.next_token.lemma) and regex("[Cc]ontração|[Rr]essecamento", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[lL]aminação", token.lemma) and regex("[Hh]orizontal|[Ii]ncipiente|[Pp]aralelo|[Cc]onvoluto", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("lineação", token.lemma) and regex("de", token.next_token.lemma) and regex("estiramento", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Mm]arca", token.lemma) and regex("de", token.next_token.lemma) and regex("[cC]arga", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("sistema|negativo|ostracode|grão", token.lemma) and regex("molde", token.head_token.lemma):
            token.head_token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("[Mm]ud", token.word) and regex("[Cc]ouplet|[Cc]ouplets", token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Cc]onvoluto", token.lemma) and regex("[Ee]stratificação|Estratificações", token.head_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.head_token.deps = "O"
            
        if regex("estratificação", token.lemma) and regex("cruzar|cruzado", token.next_token.lemma) and regex("sigmoidal", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Ee]stratificação|Estratificações", token.lemma) and regex("cruzar|cruzado", token.next_token.lemma) and regex("tabular|tangencial", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[Vv]eio", token.lemma) and regex("de", token.next_token.lemma) and regex("[Cc]isalhamento", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("ripple|ripples", token.lemma) and regex("bidirecional", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("[eE]stratificação|Estratificações", token.lemma) and not regex("convoluto", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("fratura", token.lemma) and not regex("intergranular", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        # MCLARA 12/09/2022

        if regex("[Bb]ioturbação|boudinage|dilatação|[fF]alha|gradação|maciço|septária|interlaminação", token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("contato", token.lemma) and regex("basal|planar|alto", token.next_token.lemma) and regex("abrupto", token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.next_token.misc = append_to(token.next_token.next_token.misc, "D=ESTRUTURA")
            
        if regex("contato", token.lemma) and regex("basal", token.next_token.lemma) and regex("e", token.next_token.next_token.lemma) and regex("superior", token.next_token.next_token.next_token.word) and regex("abrupto", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.misc = append_to(token.next_token.next_token.next_token.next_token.misc, "D=ESTRUTURA")
            
        if regex("[Dd]iscordância?", token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("[Dd]obra?", token.lemma) and regex("NOUN", token.upos):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        if regex("[Ee]struturas?", token.lemma) and not regex("cristalino", token.next_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"

        # TATI
        # 08/09/2022

        # geração

        if regex("de", token.lemma) and regex("hidrocarboneto|óleo|petróleo|gás", token.head_token.lemma) and regex("geração", token.head_token.head_token.lemma) and regex("nmod", token.head_token.deprel):
            token.head_token.head_token.deps = "B=EVENTO_PETRO"

        if regex("totalidade|quantidade", token.head_token.lemma) and regex("geração", token.head_token.head_token.lemma) and regex("nmod", token.head_token.deprel) and regex("hidrocarboneto|óleo|petróleo|gás", token.lemma) and regex("nmod", token.deprel):
            token.head_token.head_token.deps = "B=EVENTO_PETRO"

        if regex("expulsão|migração|acumulação|preservação", token.head_token.lemma) and regex("conj", token.head_token.deprel) and regex("geração", token.head_token.head_token.lemma) and regex("hidrocarboneto|óleo|petróleo|gás", token.lemma) and regex("nmod", token.deprel):
            token.head_token.head_token.deps = "B=EVENTO_PETRO"

        if regex("(boletins-000004-3741|boletins-000005-943|boletins-000011-374|boletins-000009-186|boletins-000009-2082|boletins-000009-20|boletins-000002-2049|boletins-000008-1597|boletins-000002-1856|boletins-000008-1698|boletins-000010-240|boletins-000011-277)", sentence.sent_id ) and regex("geração", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        if regex("janela", token.lemma) and regex("de", token.next_token.lemma) and regex("geração", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "B=EVENTO_PETRO"

        if regex("janela", token.lemma) and regex(".*", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("geração", token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "B=EVENTO_PETRO"

        if regex("cozinha", token.lemma) and regex("de", token.next_token.lemma) and regex("geração", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "B=EVENTO_PETRO"

        if regex("cozinha", token.lemma) and regex(".*", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("geração", token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "B=EVENTO_PETRO"

        if regex("migração", token.lemma) and regex("geração", token.head_token.lemma):
            token.deps = "B=EVENTO_PETRO"
            token.head_token.deps = "B=EVENTO_PETRO"
        if regex("geração", token.lemma) and regex("e", token.next_token.lemma) and regex("migração", token.next_token.next_token.lemma):
            token.deps = "B=EVENTO_PETRO"
            token.next_token.next_token.deps = "EVENTO_PETRO"

        if regex("expulsão", token.lemma) and regex("geração", token.head_token.lemma):
            token.head_token.deps = "B=EVENTO_PETRO"

        # gerador

        if regex("de", token.lemma) and regex("gás|hidrocarboneto|óleo|petróleo", token.head_token.lemma) and regex("gerador", token.head_token.head_token.lemma):
            token.head_token.head_token.deps = "B=EVENTO_PETRO"

        if regex("gerador", token.lemma) and regex("Curuá", token.next_token.lemma):
            token.deps = "B=EVENTO_PETRO"

        if regex("gerador", token.lemma) and regex("amod", token.deprel) and regex("potencial|seção|intervalo|nível|pacote|play|sedimento|unidade", token.head_token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # migração

        if regex("migração|remigração", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # preservação

        if regex("de", token.lemma) and regex("matéria|organolita|petróleo|hidrocarboneto", token.head_token.lemma) and regex("preservação", token.head_token.head_token.lemma) and regex("nmod", token.head_token.deprel):
            token.head_token.head_token.deps = "B=EVENTO_PETRO"

        if regex("(boletins-000004-3645|boletins-000003-560|boletins-000005-2221|boletins-000006-125|boletins-000005-1407|boletins-000010-891|boletins-000004-2313)", sentence.sent_id ) and regex("preservação", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # selo

        if regex("selo", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # soterramento

        if regex("soterramento", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # trapa

        if regex("trapa", token.lemma):
            token.deps = "B=EVENTO_PETRO"

        # MCLARA 20/09/2022

        if regex("hidrocarboneto|asfalto|betume|petróleo|asfalteno", token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("condensado", token.lemma) and regex("presença", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        #ÁGUA leva de dúvidas de julho (07/22) - fluidodaterra_i

        if regex("poro", token.lemma) and regex("conter", token.head_token.lemma) and regex("água", token.head_token.head_token.lemma):
            token.head_token.head_token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("expulsão", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("poro|percolação", token.lemma) and regex("água", token.head_token.lemma):
            token.head_token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("em", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("fase", token.next_token.next_token.next_token.lemma) and regex("óleo", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("saturação|saída|isoprodução|coleta|preencher|influxo|expulsão|migrar|percolação|corte|saturar", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("percolação", token.head_token.lemma) and regex("meteórico", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("influxo", token.head_token.lemma) and regex("salino|meteórico", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("zonas", token.head_token.word):
            token.deps = "B=FLUIDODATERRA_i"
            
        #ÁGUA leva de dúvidas de agosto (08/22) - fluidodaterra_i

        if regex("água", token.lemma) and regex("poder", token.next_token.lemma) and regex("ser", token.next_token.next_token.lemma) and regex("aprisionar", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("formação", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("de", token.next_token.lemma) and regex("formação", token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("salgado", token.next_token.lemma) and regex("gás", token.head_token.lemma) and regex("abaixo", token.head_token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("\(", token.next_token.lemma) and regex("salmoura", token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("deslocamento|breakthrough|avanço|varrer", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("areia", token.head_token.lemma) and regex("com", token.previous_token.lemma) and regex("\(", token.previous_token.previous_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("mar", token.next_token.next_token.next_token.lemma) and regex("por", token.next_token.next_token.next_token.next_token.lemma) and regex("fôrça", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("doce", token.next_token.word) and regex("em", token.previous_token.lemma) and regex("enxofre", token.previous_token.previous_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("percorridos", token.word) and regex("por", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("água", token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("sendo", token.next_token.word) and regex("doce", token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("mar", token.next_token.next_token.next_token.lemma) and regex("misturada", token.head_token.word) and regex("com", token.previous_token.word):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("salgadas", token.next_token.word) and regex("\(", token.next_token.next_token.lemma) and regex("Eh", token.next_token.next_token.next_token.word):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("portador|produção|injeção|explotação", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("água", token.lemma) and regex("até", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("intervalo", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"

        #GÁS leva de dúvida de agosto (08/22) - fluidodaterra_i

        if regex("gás", token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            
        if regex("gás", token.lemma) and regex("condensado|condensar", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_i"
            token.next_token.deps = "I=FLUIDODATERRA_i"
            
        #leva de dúvidas de agosto (08/22)

        if regex("óleo", token.lemma):
            token.deps = "B=FLUIDODATERRA_i"

        #ÁGUA leva de dúvidas de agosto (08/22) - fluidodaterra_o

        if regex("águas", token.word) and regex("O", token.head_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("doce|doce\/", token.next_token.lemma) and regex("ambiente|massa", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            token.next_token.deps = "I=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("salinidade", token.head_token.lemma) and regex("em", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("seu", token.next_token.next_token.next_token.lemma) and regex("deslocamento", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("marinho", token.next_token.lemma) and regex("compatível|revelar|misturar|mistura|chegada|temperatura", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            token.next_token.deps = "I=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("meteórico", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            token.next_token.deps = "I=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("mineral", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("se", token.next_token.lemma) and regex("tornar", token.next_token.next_token.lemma) and regex("hipersalina", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("superficial", token.lemma) and regex("água", token.head_token.lemma) and not regex("percolação", token.head_token.head_token.lemma):
            token.head_token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("calientes", token.next_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("mar", token.next_token.next_token.next_token.lemma) and regex("dissolver|suspensão|mistura|lava|encontrar|condicionante|quantidade|temperatura|suspen\-sato", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            token.next_token.deps = "I=FLUIDODATERRA_o"
            token.next_token.next_token.deps = "I=FLUIDODATERRA_o"
            token.next_token.next_token.next_token.deps = "I=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("depocentro", token.head_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("temperatura", token.head_token.lemma) and regex("diminuição|aumento", token.head_token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("O2\/l", token.previous_token.word) and regex("\)", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("salgado", token.next_token.lemma) and regex("fluxo", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            token.next_token.deps = "I=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("incremento", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"

        if regex("mistura", token.lemma) and regex("de", token.next_token.lemma) and regex("águas", token.next_token.next_token.word):
            token.next_token.next_token.deps = "B=FLUIDODATERRA_o"
            
        if regex("mistura", token.lemma) and regex("água", token.next_token.lemma) and regex("\+", token.next_token.next_token.lemma):
            token.next_token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("em", token.previous_token.lemma) and regex("rico", token.previous_token.previous_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("em", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("interior", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"

        #ÁGUA leva de dúvidas de julho (07/22) - fluidodaterra_o

        if regex("água", token.lemma) and regex("continental", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("puxada", token.next_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("profundidade|fria|frio|quente|Atlântico|braço|fluvial|oceânico|fundo|estratificar|vir", token.lemma) and regex("água", token.head_token.lemma):
            token.head_token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("que", token.next_token.lemma) and regex("recobrem", token.next_token.next_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("que", token.next_token.lemma) and regex("banhar", token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("volume|magma|aprisionamento|movimento|frente|evaporação|excesso|profundidade|solúvel|ingresso|incursão|entrada|corpo|circulação|disponibilidade|peso|pluma|extensão|cobertura|trânsito", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("tranquilo", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("nível|agitação|interface", token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("areia", token.lemma) and regex("com", token.next_token.lemma) and regex("água", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("dissolver", token.head_token.lemma) and regex("PUNCT", token.head_token.previous_token.upos) and regex("\.", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("vento", token.head_token.lemma) and regex("dispersos", token.head_token.head_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("espécie", token.previous_token.previous_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("Malvinas|progradam", token.head_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("massa", token.head_token.lemma) and not regex("doce", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("movimentação", token.head_token.lemma) and regex("região", token.next_token.next_token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("nor\-malizando", token.head_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("quantidade", token.head_token.lemma) and not regex("de|filtrar", token.next_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("tornar", token.head_token.lemma) and regex("turvas", token.next_token.word):
            token.deps = "B=FLUIDODATERRA_o"
            
        if regex("água", token.lemma) and regex("sedimento", token.head_token.lemma) and regex("volume", token.head_token.head_token.lemma):
            token.deps = "B=FLUIDODATERRA_o"

        #leva de dúvidas de julho (07/22)

        if regex("água", token.lemma) and regex("desmineralizar", token.next_token.lemma):
            token.deps = "B=FLUIDO"
            
        if regex("água", token.lemma) and regex("destilado", token.next_token.lemma):
            token.deps = "B=FLUIDO"
            token.next_token.deps = "I=FLUIDO"
            
        #fluido simplesmente fluido

        if regex("fluido", token.lemma) and regex("NOUN", token.upos):
            token.deps = "B=FLUIDO"

        if regex("[Rr]ocha|[Gg]ouge", token.lemma) and regex("de", token.next_token.lemma) and regex("falha", token.next_token.next_token.lemma) and regex("O", token.next_token.next_token.deps):
            token.deps = "B=ROCHA"
            token.next_token.deps = "I=ROCHA"
            token.next_token.next_token.deps = "I=ROCHA"

        if regex("rocha", token.lemma) and regex("gerador", token.next_token.lemma):
            token.deps = "B=EVENTO_PETRO"
            token.next_token.deps = "I=EVENTO_PETRO"

        if regex("rocha", token.lemma) and regex("reservatório", token.next_token.lemma):
            token.deps = "B=EVENTO_PETRO"
            token.next_token.deps = "I=EVENTO_PETRO"

        if regex("carbonato|terrígeno|terrigeno|siliciclástico", token.lemma) and regex("NOUN", token.upos):
            token.deps = "B=ROCHA"

        # TATI 04/11/22
        if regex("Arenitos", token.word) and regex("Cretáceos", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("Terciários", token.next_token.next_token.next_token.word):
            token.next_token.deps = "B=UNIDADE_LITO"
            token.next_token.next_token.next_token.dephead = token.next_token.id
            token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"

        # MCLARA 12/12/2022

        #fluidodaterra_o - 10/12/2022 pt 2 que não depende de sema

        if regex("CO2", token.lemma):
            token.deps = "B=FLUIDODATERRA_o"
            
        #unidade_crono - 10/12/2022 pt 2 que não depende de sema

        if regex("série", token.lemma) and regex("cocobeach", token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        #unidade_lito - 10/12/2022 pt 2 que não depende de sema

        if regex("e", token.lemma) and regex("o", token.next_token.lemma) and regex("Bananeiras", token.next_token.next_token.lemma) and regex("compor", token.head_token.lemma):
            token.next_token.next_token.deps = "B=UNIDADE_LITO"
            
        if regex("Formação", token.lemma) and regex("de", token.next_token.lemma) and regex("Vale", token.next_token.next_token.lemma) and regex("de", token.next_token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.next_token.lemma) and regex("fonte", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.next_token.lemma = "Fontes"
            
        if regex("intra-Formação", token.lemma) and regex("Pendência", token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Jandaíra", token.lemma) and regex("Açu-1", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Pirambóia|Botucatu|Teresinanou", token.lemma) and regex("dunas|deserto|mar", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("membro", token.lemma) and regex("afligir", token.next_token.lemma):
            token.lemma = "Membro"
            token.deps = "B=UNIDADE_LITO"
            token.next_token.lemma = "Afligidos"
            token.next_token.deprel = "flat:name"
            token.next_token.upos = "PROPN"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Ponta", token.lemma) and regex("Grossa", token.next_token.lemma) and regex("Rio", token.head_token.lemma) and regex("Ivaí", token.head_token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Furnas", token.lemma) and regex("Rio", token.head_token.lemma) and regex("Ivaí", token.head_token.next_token.lemma) and regex("evento", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            token.head_token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Botucatu|Bauru", token.lemma) and regex("Pirambóia", token.head_token.lemma) and regex("excetuar", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            
        if regex("Siderópolis|Paraguaçu", token.lemma) and regex("Triunfo", token.head_token.lemma) and regex("unidade", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"    

        # TATI 16/12/2022

        if regex("Campo|CAMPO", token.lemma) and regex("de|DE", token.next_token.lemma) and regex("Pilar", token.next_token.next_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"

        if regex("Campo", token.lemma) and regex("de", token.next_token.lemma) and regex("Viola", token.next_token.next_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"

        if regex("Campo", token.lemma) and regex("de", token.next_token.lemma) and regex("Canto", token.next_token.next_token.lemma) and regex("de", token.next_token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.next_token.lemma) and regex("Amaro", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=CAMPO"

        if regex("boletins-000008-996|boletins-000007-690|boletins-000011-11|boletins-000007-780|boletins-000007-788", sentence.sent_id ) and regex("Carmópolis", token.lemma):
            token.deps = "B=CAMPO"

        if regex("ígneo", token.lemma) and regex("intrusão|intrusiv[oa]|corpo", token.head_token.lemma):
            token.head_token.deps = "B=ROCHA"
            token.deps = "I=ROCHA"

        if regex("rocha", token.lemma) and regex("intrusivo", token.next_token.lemma) and regex("ígneo", token.next_token.next_token.lemma):
            token.deps = "B=ROCHA"
            token.next_token.deps = "I=ROCHA"
            token.next_token.next_token.deps = "I=ROCHA"
            
        if regex("[Ww]ell", token.lemma) and regex("CBP-1A|PP-11|PP-10|PP-12|11|2-CA-1-AM|13|14|3|1|8|HL-1", token.next_token.lemma):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"

        # MCLARA E TATI 20/01/23

        #bacia - 16/01/2023 (planilha de novas entidades)
        if regex("Bacia", token.word) and regex("Basco", token.next_token.word) and regex("\–", token.next_token.next_token.word) and regex("Cantábrica", token.next_token.next_token.next_token.word):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            
        if regex("bacia", token.lemma) and regex("de", token.next_token.lemma) and regex("Recife", token.next_token.next_token.lemma) and regex("-", token.next_token.next_token.next_token.lemma) and regex("João", token.next_token.next_token.next_token.next_token.lemma) and regex("Pessoa", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            
        if regex("[bB]acia", token.lemma) and regex("Recife", token.next_token.lemma) and regex("\-", token.next_token.next_token.lemma) and regex("João", token.next_token.next_token.next_token.lemma) and regex("Pessoa", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.next_token.deps = "I=BACIA"
            
        if regex("bacia", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Cabo", token.next_token.next_token.next_token.lemma) and regex("O", token.next_token.deps):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"

        #poço - 16/01/2023 (planilha das entidades novas)

        if regex("1SPS|3SPS", token.word) and regex("0036|0038A", token.next_token.word) and regex("SP", token.next_token.next_token.word) and regex("B=POÇO", token.deps):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"
        

    # ANCHOR (3) regras de expansão
    # ANCHOR regras do trigger

    tagged_triggers = "formação fm. bacia sub-bacia fluido poço poco fazenda campo".split()
    only_without_prep = "poço poco membro grupo subgrupo formação idade".split()
    triggers = {
        "bacia": "bacia sub-bacia",
        "campo": "fazenda",
        "unidade_lito": "formação formações fm. subgrupo grupo gr. membro mb.",
        "unidade_crono": "carbonífero sistema idade época série sub-série sub-época éon eonotema eratema era andar andares",
        "poço": "poço poco",
        "fluido": "fluido",
        "O": "cráton fossa falha unidade gráben"
    }

    for sema in triggers:
        triggers[sema] = triggers[sema].split()

    all_triggers = {}
    for sema, words in triggers.items():
        for word in words:
            all_triggers[word] = sema
            all_triggers[word + "s"] = sema # adicionando plural
    for item in list(only_without_prep):
        only_without_prep.append(item + "s")

    # [trigger] (de) (o) (PROPN ou .*=X)
    for token in sentence.tokens:
        token.is_trigger = token.lemma.lower() in all_triggers
        token.tagged_trigger = token.lemma.lower() in all_triggers # passa a anotar todos os triggers -- tagged_triggers
        if token.is_trigger:
            trigger_sema = all_triggers[token.lemma.lower()].upper()
            # Bacia PROPN_I=
            if (token.next_token.upos == "PROPN" or (token.deps != "O" and no_iob(token.next_token.deps) == no_iob(token.deps))):
                token.next_token._trigger = token.word
                if token.next_token.deps == "O":
                    if token.tagged_trigger:
                        # special_log: trigger
                        token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                    else:
                        # special_log: trigger
                        token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
                else:
                    if token.tagged_trigger:
                        token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                    else:
                        token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
            if token.lemma.lower() not in only_without_prep:
                # Bacia de_I= PROPN_I=
                if token.next_token.lemma.lower() == "de" and (token.next_token.next_token.upos == "PROPN" or (token.deps != "O" and no_iob(token.next_token.next_token.deps) == no_iob(token.deps))):
                    if trigger_sema == "O" and token.next_token.next_token.lemma.lower() in list(all_triggers) + ["campo"]:
                        continue
                    token.next_token.next_token._trigger = token.word
                    if token.next_token.next_token.deps == "O":
                        if token.tagged_trigger:
                            token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            # special_log: trigger
                            token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                        else:
                            # special_log: trigger
                            token.next_token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
                    else:
                        if token.tagged_trigger:
                            token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                        else:
                            token.next_token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
                # Bacia de_I= o_I= PROPN_I=
                if token.next_token.lemma.lower() == "de" and token.next_token.next_token.lemma.lower() == "o" and (token.next_token.next_token.next_token.upos == "PROPN" or (token.deps != "O" and no_iob(token.next_token.next_token.next_token.deps) == no_iob(token.deps))):
                    if trigger_sema == "O" and token.next_token.next_token.next_token.lemma.lower() in list(all_triggers) + ["campo"]:
                        continue
                    token.next_token.next_token.next_token._trigger = token.word
                    if token.next_token.next_token.next_token.deps == "O":
                        if token.tagged_trigger:
                            token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            # special_log: trigger
                            token.next_token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                        else:
                            # special_log: trigger
                            token.next_token.next_token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
                    else:
                        if token.tagged_trigger:
                            token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                            token.next_token.next_token.next_token.deps = "I={}".format(trigger_sema) if trigger_sema != "O" else "O"
                        else:
                            token.next_token.next_token.next_token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"
            # bacia_B=
            if token.tagged_trigger and token.deps != "I={}".format(trigger_sema) and token.deps == "O" and token.next_token.deps not in ["O", "_"]:
                token.deps = "B={}".format(trigger_sema) if trigger_sema != "O" else "O"

    # ANCHOR regra do conj
    for token in sentence.tokens:
        if token.deprel == "conj" and token.upos == "PROPN" and token.head_token.deps != "O":
            if token.is_trigger:
                continue
            if token.deps != "O" and not '|' in token.deps:
                if no_iob(token.deps) != no_iob(token.head_token.deps):
                    conj_not_tagged.append([sentence.sent_id, token.id])
                continue
            # special_log: conj
            token.deps = to_b(token.head_token.deps)

    # ANCHOR regra do barra
    for token in sentence.tokens:
        if token.upos == "PROPN" and token.next_token.word in "-/" and token.next_token.next_token.upos == "PROPN" and token.deps != "O" and no_iob(token.next_token.next_token.deps) != no_iob(token.deps):
            if token.next_token.next_token.is_trigger:
                continue
            # special_log: barra
            token.next_token.deps = to_i(token.deps)
            # special_log: barra
            token.next_token.next_token.deps = to_i(token.deps)

    # ANCHOR regra do flat:name
    for token in sentence.tokens:
        if token.deprel == "flat:name" and token.head_token.deps != "O" and token.deps != to_i(token.head_token.deps):
            if token.is_trigger:
                continue
            # special_log: flat:name
            token.deps = to_i(token.head_token.deps)

    # ANCHOR (4) regras de limpeza
    for token in sentence.tokens:
        if '-' in token.id:
            continue

        # MCLARA

        if regex("raso|profundo", token.lemma) and regex("água", token.head_token.lemma):
            token.head_token.deps = "O"
        if regex("água", token.lemma) and regex("coluna|fóssil", token.head_token.lemma):
            token.deps = "O"
        if regex("gás", token.lemma) and regex("indústria", token.head_token.head_token.lemma):
            token.deps = "O"
        if regex("soja|vegetal|comercial|coco|fritura|dendê|girassol|palma", token.lemma) and regex("óleo", token.head_token.lemma):
            token.head_token.deps = "O"

        # Aline

        if regex("acidente|dano", token.lemma) and regex("ou|e", token.next_token.lemma) and regex("falha", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "O"

        # PetroNer-v2

        if token.lemma == "filtrado":
            token.deps = "O"
        if "ESCALA" in token.deps:
            token.deps = "O"
        if token.lemma == "petro-lífero":
            token.lemma = "petrolífero"

        # 09/03/2022
        # LIMPAR SEMA DE REFERÊNCIAS E OUTRAS PALAVRAS

        if token.deps != "O" and token.next_token.word == "et":
            token.deps = "O"
        if token.lemma == "mero" and token.upos == "ADJ":
            token.deps = "O"

        if token.head_token.lemma in "cidade estado Cidade Estado Universidade Pontifícia Católica".split() and token.upos == "PROPN" and token.deps != "O":
            token.deps = "O"
            if token.deprel == "flat:name":
                token.head_token.deps = "O"
                for _token in sentence.tokens:
                    if _token.deprel == "flat:name" and _token.dephead == token.dephead:
                        token.deps = "O"

        if token.word == "Revista" and token.next_token.word == "Brasileira" and token.next_token.next_token.word == "de" and token.next_token.next_token.next_token.word == "Geociências" and token.next_token.next_token.next_token.next_token.word == "," and token.next_token.next_token.next_token.next_token.next_token.word == "São" and token.next_token.next_token.next_token.next_token.next_token.next_token.word == "Paulo":
            token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"

        if token.id == "1" and token.word == "São" and token.next_token.word == "Paulo":
            token.deps = "O"
            token.next_token.deps = "O"
        if token.word == "São" and token.next_token.word == "Paulo" and token.next_token.next_token.word in ", :".split() and token.next_token.next_token.next_token.word in "v. v Universidade".split():
            token.deps = "O"
            token.next_token.deps = "O"
        if token.word == "São" and token.next_token.word == "Paulo" and token.previous_token.lemma == "em":
            token.deps = "O"
            token.next_token.deps = "O"
        if token.previous_token.previous_token.word == "Núcleo" and token.word == "São" and token.next_token.word == "Paulo":
            token.deps = "O"
            token.next_token.deps = "O"

        # ANCHOR BIB

        if not "BIB" in sentence.metadados:
            if sentence.text.startswith("___"):
                sentence.metadados["BIB"] = "Yes"
            if sentence.tokens[0].word.upper() == sentence.tokens[0].word and \
                    sentence.tokens[0].next_token.word == "," and \
                        re.search(r"^([A-ZÇ-]\.?)+$", sentence.tokens[0].next_token.next_token.word):
                sentence.metadados["BIB"] = "Yes"
            if sentence.tokens[0].word.lower() == "in" and sentence.tokens[1].word == ":":
                sentence.metadados["BIB"] = "Yes"
        # tirar sema de ref bibliográficas
        if re.search(r"^([A-ZÇÕ-]\.?)+$", token.word):
            token.deps = "O"

        # 29/03/22
        # MCLARA

        #lista de lemas que não são bacias

        if regex("B=BACIA.*", token.deps) and regex("Aymar|B\.|BABINSKI|Baia|C|CFB|CTPetro/FINEP/PETROBRAS|Caroline|Centro|Cerqueira|Claiton|Craton|Cretáceo|Dantas|Austrália|Asmus|Arenito|Antônio|Albiano|Alberto|universidade|Zona|Urbano|Regina|M\.|J\.|G\.|Eugenio|Clóvis|Carlos|Carla|Canhão|Arco|Cone|Cráton|SW|S\.|A\.|-Cenozóicas|Microplaca|Falha|Chapada|C\.|Enxame|Triunfo|Platô|Dorsal|Baía|F\.|Aliança|ASC|A|Unidade|Baixo|Província|NOGUTI|D\.|Canyon|SOUZA", token.lemma):
            token.deps = "O"
        if regex("Península|Atlântico|Nordeste|Brasil|Oriente", token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
        if regex("Eoceno|Eugênio|EUA|África|Setor|Saulo|Rogério|Rodrigues|Projeto|Milton|Sudeste|Leste|UNIVERSIDADE", token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
        if regex("nordeste|península|Heriber\-to|Heriberto|Itália|Leque|Margem|Martinez|Noguti|Oliveira|Olinto|Paulo|Sul/Sudeste", token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
        if regex("Distrito|1-Distrito|Diagênese|evaporito|Faixa|Ferradaes|Folhelho|Galm|Gangorra|Gerência|Golfo|Horst|ITEM|Ilha|Jailton|Destes|K\.W\.B\|LATIN|MEMBRO|MV|Mesozdicas|Missão|N\.|N\.;|NE\-SW|NU\-CLEO|Neo\-aptiano|Núcleo|PROCAP/GER\-02|Paleocanyon|Plateau|Porção|Poços|Prinzhofer|Proterozóico|R\.|Rua|S5|SDR|Sede|Supergrupo|modelo|projeto|\|\.|área", token.lemma) and regex(".*=BACIA", token.deps):
            token.deps = "O"

        #casos específicos

        if regex("Francisco", token.lemma) and regex("B=BACIA", token.deps) and regex("Celso", token.next_token.lemma):
            token.deps = "O"
            
        #revisão do lema Alagoas

        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("andar|Andar", token.head_token.head_token.lemma):
            token.deps = "O"
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("durante", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("pós.*|pré.*", token.previous_token.lemma):
            token.deps = "O"
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("Rio", token.head_token.lemma) and regex("ADP", token.previous_token.upos):
            token.deps = "O"
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("haver", token.next_token.lemma) and regex("algum", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("tempo|final|terminar|topo|intervalo|estágio|seção-tipo|São|costa|holoestratotipo|norte|pacote|questão|área|porção|reservatório|direção|problema|Andar|andar|região|largo", token.head_token.lemma):
            token.deps = "O"

        #revisão do lema Sergipe

        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("evaporito|área|território|mina", token.head_token.lemma):
            token.deps = "O"
        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("obl", token.deprel) and regex("econtrar|retirar|observar", token.head_token.lemma):
            token.deps = "O"
        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("costa|Serraria", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Santos

        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("e", token.next_token.lemma) and regex("Brito", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("planície|jazida", token.head_token.lemma):
            token.deps = "O"
        if regex("Santos|Campos", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("serras|grábem|gráben", token.head_token.head_token.lemma):
            token.deps = "O"
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("informação", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("J\.|Sul|NETO|Neto", token.next_token.lemma):
            token.deps = "O"
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("NUM", token.next_token.next_token.upos):
            token.deps = "O"
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("S\.|J\.|p\.|C\.|A\.|R\.|r\.|E\.|M\.|D\.|F\.", token.next_token.next_token.lemma):
            token.deps = "O"

        #revisão lema Recôncavo

        if regex("Recôncavo", token.lemma) and regex("Baiano", token.next_token.lemma):
            token.deps = "O"
        if regex("Recôncavo", token.lemma) and regex("B=BACIA", token.deps) and regex("borda|coluna|evolução|atuação|atributo", token.head_token.lemma):
            token.deps = "O"
        if regex("Recôncavo", token.lemma) and regex("B=BACIA", token.deps) and regex("obl", token.deprel) and regex("representar", token.head_token.lemma):
            token.deps = "O"

        #revisão lema São

        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.previous_token.upos) and regex("NUM", token.previous_token.previous_token.upos):
            token.deps = "O"
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("root", token.deprel) and regex("\[|\]", token.previous_token.lemma):
            token.deps = "O"
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("appos", token.deprel) and regex("Bacia", token.head_token.lemma):
            token.deps = "O"
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("Dorsal|dorsal|Craton|Cráton|cráton|baixo|Platô|platô|gráben|grábem|rio|vale|Maceió|sul|revista|Boletim|universidade|Universidade|UNIVERSIDADE|litoral|área|megalópole|resumo|Cerâmica|evaporito|anais", token.head_token.lemma):
            token.deps = "O"
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("[pP]lataforma|rifte", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Paraná

        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("desde", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("latitude|Etendeka|rio|sede|derrame|folhelho|Estado|estado|Distrito|sonda|trapa|NW|exploração", token.head_token.lemma):
            token.deps = "O"
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("UFPA/MPEG", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("estado|Estado", token.head_token.head_token.lemma):
            token.deps = "O"
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("PRON", token.head_token.upos) and regex("região", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Souza

        if regex("Souza|SOUZA", token.lemma) and regex("B=BACIA", token.deps) and regex("de", token.previous_token.lemma) and regex("p\.", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("Souza|SOUZA", token.lemma) and regex("B=BACIA", token.deps) and regex("Jr\.|Cruz", token.next_token.lemma):
            token.deps = "O"
        if regex("Souza|SOUZA", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("NUM", token.next_token.next_token.upos):
            token.deps = "O"
            
        #revisão lema Ceará

        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.previous_token.upos) and regex("iguatu|Iguatu", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("centro|litoral|encontrar", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Espírito

        if regex("Espírito", token.lemma) and regex("B=BACIA", token.deps) and regex("observar|fluxo|plataforma|ESS-4|porção|poço|gerente", token.head_token.lemma):
            token.deps = "O"
        if regex("Espírito", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("costa|Sul|grupo|associar|natureza|unidade", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Pelotas

        if regex("Pelotas", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.previous_token.upos) and regex("1992", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("Pelotas", token.lemma) and regex("B=BACIA", token.deps) and regex("nascer|local|SDR", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Acre

        if regex("Acre", token.lemma) and regex("B=BACIA", token.deps) and regex("território|trabalhar", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Alto

        if regex("Alto", token.lemma) and regex("B=BACIA", token.deps) and regex("de", token.next_token.lemma) and regex("Goiana", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Alto", token.lemma) and regex("B=BACIA", token.deps) and regex("Ferrer-Urbano", token.next_token.lemma):
            token.deps = "O"
        if token.lemma == "Alto" and token.next_token.lemma == "de" and token.next_token.next_token.upos == "PROPN":
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
        if token.lemma == "Alto" and token.next_token.lemma == "Regional":
            token.deps = "O"
            token.next_token.deps = "O"
            
        #revisão lema Pantanal

        if regex("Pantanal", token.lemma) and regex("B=BACIA", token.deps) and regex("norte|sul|ponto|ombreira", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Rio

        if regex("Rio", token.lemma) and regex("B=BACIA", token.deps) and regex("dique|relacionar|trabalhar|foz", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Curitiba

        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("v.", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("metrópole", token.head_token.lemma):
            token.deps = "O"
        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("p.150-158", token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.previous_token.upos) and regex("NUM", token.previous_token.previous_token.upos):
            token.deps = "O"
        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("NUM", token.next_token.next_token.upos):
            token.deps = "O"
        if regex("Curitiba", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.next_token.upos) and regex("Sociedade", token.next_token.next_token.lemma):
            token.deps = "O"
            
        #revisão lema Amazonas

        if regex("Amazonas", token.lemma) and regex("B=BACIA", token.deps) and regex("rio|plataforma|lobo|Cone|cone|Mississippi|Carapebus|área|parte|operar|leque|área-fonte|upper", token.head_token.lemma):
            token.deps = "O"

        #revisão  do lema Almada

        if regex("Almada", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("exemplo|rio", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Solimões

        if regex("Solimões", token.lemma) and regex("B=BACIA", token.deps) and regex("região", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Mucuri

        if regex("Mucuri", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("plataforma", token.head_token.head_token.lemma):
            token.deps = "O"
        if regex("Mucuri", token.lemma) and regex("B=BACIA", token.deps) and regex("sedimento", token.head_token.lemma):
            token.deps = "O"
                    
        #revisão do lema Barreirinha e Barreirinhas

        if regex("Barreirinha", token.lemma) and regex("B=BACIA", token.deps) and regex("folhelho", token.head_token.lemma):
            token.deps = "O"
        if regex("Barreirinhas", token.lemma) and regex("B=BACIA", token.deps) and regex("costa", token.head_token.lemma):
            token.deps = "O"
        if regex("Barreirinhas", token.lemma) and regex("B=BACIA", token.deps) and regex("trabalho", token.head_token.lemma):
            token.deps = "O"

        #revisão do lema Taubaté

        if regex("Taubaté", token.lemma) and regex("B=BACIA", token.deps) and regex("PROPN", token.head_token.upos) and regex("grábem|gráben", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema foz

        if regex("foz", token.lemma) and regex("B=BACIA", token.deps) and regex("apresentar", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Médio

        if regex("Médio", token.lemma) and regex("B=BACIA", token.deps) and regex("Amazonas", token.next_token.lemma) and not regex("Bacia|bacia", token.head_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
              
        #água oxigenada e água destilada

        if regex("água", token.lemma) and regex("oxigenado|destilado", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
                
        #revisão lema Sistema e sistema

        if regex("flat:name", token.deprel) and regex("I=UNIDADE_CRONO", token.deps) and not regex("Cretáceo", token.lemma) and regex("Sistema", token.head_token.lemma) and regex("B=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("I=UNIDADE_CRONO", token.deps) and regex("B=UNIDADE_CRONO", token.head_token.deps) and regex("sistema", token.head_token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=UNIDADE_CRONO", token.deps) and regex("sistema", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Série

        if regex("Série", token.lemma) and regex("B=UNIDADE_CRONO", token.deps) and regex("Cartografia|B|Científica|Geologia|Projeto", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        #revisão lema Formação

        if regex("I=UNIDADE_CRONO", token.deps) and regex("Formação", token.head_token.lemma) and regex("B=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "O"
            token.head_token.deps = "O"
            
        #revisão lema Atlântico

        if regex("Norte|Sul", token.lemma) and regex("I=UNIDADE_CRONO", token.deps) and regex("Atlântico", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
            
        #revisão lema Almirante

        if regex("Câmara", token.lemma) and regex("I=UNIDADE_CRONO", token.deps) and regex("Almirante", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
            
        #casos específicos

        if regex("nordeste", token.lemma) and regex("I=UNIDADE_CRONO", token.deps) and regex("Compartimento", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("I=UNIDADE_CRONO", token.deps) and regex("Granito", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("I=UNIDADE_CRONO", token.deps) and regex("Trato", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("D\.|Recôncavo|TF|40Ar/39|C\.|K/Ar|V\.|Af,|Ar\-Ar|Ar/Ar|arcabouço|CHUR|Congo|DPR|Correlação|Dr\.|Gabão|M’Vone|Nd|SAJ|b\-Sr|Projeto|Palinoestratigrafia|P\-270|Sweet|b\.|c\.|rift", token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"

        #lema úmidar

        if regex("úmidar", token.lemma):
            token.deprel = "amod"
            token.upos = "ADJ"
            token.lemma = "úmido"
            
        #lema barri

        if regex("barri", token.lemma):
            token.lemma = "barril"
            
        #lema perfi

        if regex("perfi", token.lemma):
            token.lemma = "perfil"

        # 29/03/22
        # TATI
        # CAMPO

        if regex("B=CAMPO", token.deps) and regex("3D", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("A\.", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Arenito|Arenitos", token.word) and regex("PROPN", token.next_token.upos):
            token.deps = "O"
            token.lemma = "Arenito"
            token.next_token.deps = "O"
        if regex("Bonito", token.word) and regex("bonito", token.lemma):
            token.lemma = "Bonito"
            token.upos = "PROPN"
        if regex("flat:name", token.deprel) and regex("I=CAMPO", token.deps) and regex("C\.", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=CAMPO", token.deps) and regex("C\.|L\.|M\.", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("flat:name", token.deprel) and regex("Conceição|CONCEIÇÃO", token.head_token.lemma) and regex("et", token.head_token.next_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Conceição", token.lemma):
            token.deps = "O"
        if regex("PROPN", token.upos) and regex("flat:name", token.deprel) and regex("B=CAMPO", token.head_token.deps) and regex("Formações|Formação", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("Geoquimica", token.lemma):
            token.lemma = "Geoquímica"
        if regex("B=CAMPO", token.deps) and regex("\|\.", token.lemma):
            token.deps = "O"
        if regex("PROPN", token.upos) and regex("flat:name", token.deprel) and regex("B=CAMPO", token.head_token.deps) and regex("João|Luiz|Maria|Antônio|Armando", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=CAMPO|I=CAMPO", token.deps) and regex("Petrorras|Petrobras", token.lemma):
            token.deps = "O"
        if regex("Profeto", token.head_token.word) and regex("PROPN", token.upos):
            token.head_token.lemma = "Projeto"
            token.head_token.deps = "O"
            token.deps = "O"
        if regex("PROPN", token.upos) and regex("Projeto", token.previous_token.word):
            token.deps = "O"
        if regex("Quererá", token.word):
            token.lemma = "Quererá"
            token.upos = "PROPN"
            token.feats = "Gender=Masc|Number=Sing"
        if regex("de", token.word) and regex("I=CAMPO", token.deps) and regex("Represa", token.previous_token.lemma):
            token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=CAMPO", token.deps) and regex("B=CAMPO", token.head_token.deps) and regex("Represa", token.head_token.lemma):
            token.head_token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Rússia", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Sergi", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("T", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Y", token.lemma):
            token.deps = "O"
        if re.search( r"^(" + r"campo" + r")$", token.__dict__['lemma'] ) and re.search( r"^(" + r"dado|curso|nível|estudo|excursão|evidência|geofísico|geologia|guia|laboratório|levantamento|mapeamento|roteiro|trabalho|viagem|etapa|grupo|conhecimento" + r")$", token.head_token.__dict__['lemma'] ):
            token.deps = "O"
        if re.search( r"^(" + r"campo" + r")$", token.__dict__['lemma'] ) and re.search( r"^(" + r"estocástico|magnético|pesqueiro|resultante|total|médio" + r")$", token.next_token.__dict__['lemma'] ):
            token.deps = "O"
        if regex("bonito", token.lemma) and regex("B=CAMPO|I=CAMPO", token.deps):
            token.deps = "O" 
        if regex("B=CAMPO", token.deps) and regex("but", token.lemma):
            token.deps = "O"
        if regex("flat:name", token.deprel) and regex("but", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Búzios|Palmital", token.lemma):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Sísmica|Geoquímica|Estratigrafia|Sedimentologia|Geomatemática|Geologia|Bioestratigrafia|Paleoecologia|Geotermia|Informática|Matemática|Química|Física", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("Sísmica|Geoquímica|Estratigrafia|Sedimentologia|Geomatemática|Geologia|Bioestratigrafia|Paleoecologia|Geotermia|Informática|Matemática|Química|Física", token.lemma) and regex("a", token.previous_token.word) and regex("de", token.previous_token.previous_token.word) and regex("campo", token.head_token.lemma):
            token.deps = "O"
        if regex("Sísmica|Geoquímica|Estratigrafia|Sedimentologia|Geomatemática|Geologia|Bioestratigrafia|Paleoecologia|Geotermia|Informática|Matemática|Química|Física", token.lemma) and regex("nmod", token.deprel) and regex("campo", token.head_token.lemma):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("específico", token.next_token.lemma) and regex("de", token.next_token.next_token.word) and regex("Sísmica|Geoquímica|Estratigrafia|Sedimentologia|Geomatemática|Geologia|Bioestratigrafia|Paleoecologia|Geotermia|Informática|Matemática|Química|Física", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
        if regex("campo", token.head_token.lemma) and regex("o", token.previous_token.lemma) and regex("em", token.previous_token.previous_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("estocástico|magnético|pesqueiro|resultante", token.next_token.word):
            token.deps = "O"
        if re.search( r"^(" + r"campo" + r")$", token.__dict__['lemma'] ) and re.search( r"^(" + r"de" + r")$", token.next_token.__dict__['word'] ) and re.search( r"^(" + r"esforço|stress|tensão|distribuição|traquito|deformação" + r")$", token.next_token.next_token.__dict__['lemma'] ):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("médio", token.next_token.lemma):
            token.deps = "O"
        if regex("pressão", token.lemma) and regex("nmod", token.deprel) and regex("campo", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("coral", token.lemma):
            token.deps = "O"
        if regex("campo", token.word) and regex("em", token.previous_token.word):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("fig\.|Fig\.", token.word):
            token.deps = "O"
        if regex("geoquimica", token.lemma):
            token.lemma = "geoquímica"
        if regex("B=CAMPO", token.deps) and regex("PROPN", token.upos) and regex("de", token.previous_token.word) and regex("campo", token.previous_token.previous_token.word) and regex("de", token.previous_token.previous_token.previous_token.word) and regex("guia", token.previous_token.previous_token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("I=CAMPO", token.deps) and regex("Serra", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("lapa", token.lemma):
            token.deps = "O"
        if regex("Vermelho", token.word) and regex("Mar", token.head_token.word):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Mar", token.lemma):
            token.deps = "O"
        if regex("Namorado", token.word) and regex("namorado", token.lemma):
            token.lemma = "Namorado"
            token.upos = "PROPN"
        if regex("neo-Rio", token.lemma) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Serra", token.next_token.next_token.next_token.word):
            token.next_token.dephead = token.id
            token.next_token.next_token.dephead = token.id
            token.next_token.next_token.next_token.dephead = token.id
        if regex("nivel", token.lemma):
            token.lemma = "nível"
        if regex("campo", token.lemma) and regex("o", token.previous_token.word) and regex("em|a", token.previous_token.previous_token.word) and regex("revisão|excursão", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("\-\-\.==", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("<", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("projeto|Projeto", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("r\.", token.lemma):
            token.deps = "O"
        if regex("Roncador", token.word) and regex("roncador", token.lemma):
            token.lemma = "Roncador"
            token.upos = "PROPN"
        if regex("B=CAMPO", token.deps) and regex("serra", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("Serra", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("tartaruga", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("tubar", token.lemma):
            token.lemma = "tubarão"
            token.upos = "NOUN"
            token.feats = "Gender=Masc|Number=Sing"
            token.deps = "O"
        if regex("campo", token.word) and regex("em", token.previous_token.word) and regex("observar|coletar|descrever|levantar", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("vermelho", token.lemma):
            token.deps = "O"
        if regex("Agua|Águas", token.lemma):
            token.lemma = "Água"

        # 29/03/22
        # TATI
        # POÇO

        if regex("B=POÇO", token.deps) and regex("7c", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("A\-4", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("Ats", token.lemma):
            token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=POÇO", token.deps) and regex("Based", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("C\-14", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("c|C", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("Cheloniceras", token.lemma) and regex("sp", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("Dominio|Domínio", token.lemma) and regex("PROPN", token.next_token.upos):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("PROPN", token.upos) and regex("I=POÇO", token.deps) and regex("Hamilton", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=POÇO", token.deps) and regex("IH", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=POÇO", token.deps) and regex("Joumal|Journal", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("L\-1", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("MG", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("Mg", token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("Poços|Poco", token.lemma):
            token.lemma = "Poço"
        if regex("I-RB", token.word) and regex("I=POÇO", token.deps) and regex("SP", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("SP", token.lemma) and regex("PUNCT", token.previous_token.upos):
            token.deps = "O"
        if regex("PROPN", token.upos) and regex("I=POÇO", token.deps) and regex("Sequência|Seqüência|Sequencia", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
            token.head_token.lemma = "Sequência"
        if regex("B=POÇO", token.deps) and regex("Wells", token.lemma):
            token.lemma = "Well"
        if regex("PROPN", token.upos) and regex("I=POÇO", token.deps) and regex("amostra", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("I=POÇO", token.deps) and regex("c|C", token.head_token.lemma):
            token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("cm\-1", token.lemma):
            token.deps = "O"
        if regex("compound|flat:name", token.deprel) and regex("I=POÇO", token.deps) and regex("elta", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("I=POÇO", token.deps) and regex("Figure", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("flat:name", token.deprel) and regex("I=POÇO", token.deps) and regex("intervalo", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("mg", token.lemma):
            token.deps = "O"
        if regex("NOUN|PROPN", token.upos) and regex("I=POÇO", token.deps) and regex("parâmetro", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("parâmetro", token.lemma) and regex("C", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("PROPN", token.upos) and regex("I=POÇO", token.deps) and regex("valor", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
        if regex("B=POÇO", token.deps) and regex("°", token.lemma):
            token.deps = "O"
        if regex("I=POÇO", token.deps) and regex("°", token.head_token.lemma):
            token.deps = "O"
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("acumuiação", token.head_token.lemma):
            token.head_token.lemma = "acumulação"
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("barri|bar\-ri", token.head_token.lemma):
            token.head_token.lemma = "barril"
        if regex("acl", token.deprel) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("desmine\-ralizar", token.lemma):
            token.lemma = "desmineralizar"
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("exsu\-dação", token.head_token.lemma):
            token.head_token.lemma = "exudação"
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("gôta", token.head_token.lemma):
            token.head_token.lemma = "gota"
        if regex("de", token.word) and regex("óleo", token.previous_token.lemma) and regex("nmod", token.head_token.deprel) and token.head_token.dephead == token.previous_token.id and regex("inclusnao", token.head_token.lemma):
            token.head_token.lemma = "inclusão"
        if regex("de", token.lemma) and regex("água", token.head_token.lemma) and regex("nmod", token.head_token.deprel) and regex(".*", token.head_token.head_token.lemma) and regex("libe\-tação", token.head_token.head_token.lemma):
            token.head_token.head_token.lemma = "libertação"
        if regex("menor|menores", token.word):
            token.upos = "ADJ"
        if regex("acl", token.deprel) and regex("óleo", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("misto", token.lemma):
            token.deprel = "amod"
            token.upos = "ADJ"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("de", token.lemma) and regex("água", token.head_token.lemma) and regex("nmod", token.head_token.deprel) and regex(".*", token.head_token.head_token.lemma) and regex("movi\-mentação", token.head_token.head_token.lemma):
            token.head_token.head_token.lemma = "movimentação"
        if regex("amod", token.deprel) and regex("óleo", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("pesa\-do", token.lemma):
            token.lemma = "pesado"
        if regex("acl", token.deprel) and regex("óleo", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("pesar", token.lemma):
            token.deprel = "amod"
            token.upos = "ADJ"
            token.lemma = "pesado"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("poco", token.head_token.lemma):
            token.head_token.lemma = "pouco"
        if regex("óleo", token.lemma) and regex("nmod", token.deprel) and regex("NOUN|PROPN", token.head_token.upos) and regex("satu\-ração", token.head_token.lemma):
            token.head_token.lemma = "saturação"
        if regex("amod", token.deprel) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("subterrâ\-neo", token.lemma):
            token.lemma = "subterrâneo"
        if regex("de", token.lemma) and regex("água", token.head_token.lemma) and regex("nmod", token.head_token.deprel) and regex(".*", token.head_token.head_token.lemma) and regex("teore", token.head_token.head_token.lemma):
            token.head_token.head_token.lemma = "teor"
        if regex("amod", token.deprel) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("tranqiiilo", token.lemma):
            token.lemma = "tranquilo"
        if regex("destilada", token.word) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id:
            token.lemma = "destilado"
            token.upos = "ADJ"
            token.deprel = "compound"
            token.feats = remove_from(token.feats, "VerbForm=Part")
            token.previous_token.deps = "O"
            token.deps = "O"
        if regex("oxigenada", token.word) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id:
            token.lemma = "oxigenado"
            token.upos = "ADJ"
            token.deprel = "compound"
            token.feats = remove_from(token.feats, "VerbForm=Part")
            token.previous_token.deps = "O"
            token.deps = "O"
        if regex("acl", token.deprel) and regex("água", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("salgar", token.lemma):
            token.lemma = "salgado"
            token.upos = "ADJ"
            token.deprel = "compound"
            token.feats = remove_from(token.feats, "VerbForm=Part")
        if regex("baleia", token.lemma) and regex("óleo", token.head_token.lemma):
            token.deps = "O"
        if regex("amod", token.deprel) and regex("óleo", token.previous_token.lemma) and token.dephead == token.previous_token.id and regex("diesel", token.lemma):
            token.upos = "NOUN"
            token.deprel = "nmod"

        # 30/03/2022
        # Formação de Alameda não é BACIA, apesar de Alameda estar como BACIA (tirar anotação de BACIA)
        # Elvis
        #if token.lema in "Rifte Rift Canyon".split():
            #token.deps = "O"

        # ANCHOR limpando palavras que nunca são entidade
        if token.deps != "O" and regex("Museu|Ocean|.*-B\.|C\.e|______|Deep|\.|94|\d{4}|parte|Parte|b|Szatmari|Ma|\.g|\.g\.|Faixa|Discussão|Petrobras|Floresta|Richter|Viviers|etrobras|Bahia|Oriente|PETROBRÁS/RPBA/DIREX|.*Figura.*|Geocronologia|Modelagem|Cinemática|Teisserenc|Ouro|Gerson|Bengtson|Margem|Renato|seu|Marco|Paleozói-|França|Camboriú", token.lemma):
            token.deps = "O"

        # 26/07/2022
        if regex("Amaro", token.lemma) and regex("Cidade", token.head_token.lemma):
            token.deps = "O"
        if regex("Amaro", token.lemma) and regex("Ferreira|shale", token.next_token.lemma):
            token.deps = "O"

        #E para Cabiúnas (só precisa dessa porque em todas as outras ocorrências o pai é Formação):

        if regex("Cabiúnas", token.lemma) and regex("Bacia", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        if regex("B=.*", token.deps) and regex("África|América|Golfo|Mar|Brasil|Portugal|Francisco|Haroldo", token.lemma):
            token.deps = "O"
        if regex(".*CRONOESTRATIGRÁFICA.*", token.deps) and regex("Lima", token.lemma):
            token.deps = "O"

        if token.word == "São" and token.next_token.word == "Paulo" and token.next_token.next_token.upos == "PUNCT" and token.next_token.next_token.next_token.upos == "NUM":
            token.deps = "O"
        if regex("Rabelo|Antônio", token.word) and token.next_token.word == "de" and token.next_token.next_token.word == "os" and token.next_token.next_token.next_token.word == "Santos":
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
        if token.word == "José" and token.next_token.word == "de" and token.next_token.next_token.word == "Souza":
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
        if token.word == "-" and token.next_token.word == "Jatobá":
            token.next_token.deps = token.previous_token.deps
        if regex("André", token.word) and regex("L.", token.next_token.word) and regex("Ferrari", token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
        if regex("Moura", token.word) and regex("e", token.next_token.word) and regex("Oddone", token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
        if regex("PETROBRAS", token.word) and regex(",", token.next_token.word) and regex("Rio", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("Janeiro", token.next_token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
        if regex("Maria", token.word) and regex("Augusta", token.next_token.word) and regex("Martins", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("a", token.next_token.next_token.next_token.next_token.word) and regex("Silva", token.next_token.next_token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"
        if regex("Tim", token.word) and regex("Lowestein", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("Michael", token.word) and regex("Timofeeff", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
        if token.word == "Rio" and token.next_token.word == "de" and token.next_token.next_token.word == "Janeiro":
            token.deps = "O"

        # limpando rochas que não são rochas mas estavam coordenadas
        if regex("Munbeca|Oiteirinhos|Aptiano|Sylvia|Mateo", token.word) and regex(".*ROCHA.*", token.deps):
            token.deps = "O"
        if regex("<UNK>SES", token.word) and regex(".*POÇO.*", token.deps):
            token.deps = "O"
        
        # limpando "campos" que não são campo mas estavam coordenados
        if regex("P\d+", token.lemma) and regex(".*CAMPO.*", token.deps):
            token.deps = "O"
        if regex("CONCEIÇÃO", token.lemma) and token.next_token.word == ",":
            token.deps = "O"
        if token.lemma == "Rio" and token.next_token.lemma == "Bonito" and regex("B=.*", token.next_token.deps):
            token.next_token.deps = "O"
        if token.lemma == "conforme" and token.next_token.word == "Campos":
            token.next_token.deps = "O"

        # limpando "bacias" conj
        if regex("megalópol.*|cidade.*", token.head_token.lemma) and token.deps != "O":
            token.deps = "O"
        if token.word == "(" and regex("[A-Za-z]", token.next_token.word) and token.next_token.next_token.word == ")" and token.next_token.deps != "O":
            token.next_token.deps = "O"
        if regex("Eocretaceous", token.lemma) and regex("B=BACIA.*", token.deps):
            token.deps = "O"

        # limpar em o Espírito|em a Foz|em o Iêmen
        if token.lemma == "em" and token.next_token.lemma == "o" and token.next_token.next_token.deps != "O" and regex("Espírito|Foz|Iêmen", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "O"
        if token.lemma == "em" and token.next_token.deps != "O" and regex("Campos|Alagoas", token.next_token.lemma):
            token.next_token.deps = "O"

        # ANCHOR limpar flat:name
        if token.deprel == "flat:name" and regex("Member|Emersa|Su-THIERSTEIN|Brasil|deltaic|fluvial|turbidites|André|turbiditos|y|ev|Della|Geociências|PE/PB|6\.\.|\{|Structural|\||\./n|are|\.|2-Distrito|Geological|comprise|Rogério|Carlos|Ativo|location|Conodonts|and|Mé-|\?|3\.1|Low|\&|Ocean|Deep|#5|Fig\.|\}|7-|1-", token.word):
            token.deps = "O"

        # 11/04/2022
        # MCLARA
        # BACIA

        #revisão lema Marajó

        if regex("Marajó", token.lemma) and regex("B=BACIA", token.deps) and regex("Ilha", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Acre

        if regex("Acre", token.lemma) and regex("B=BACIA", token.deps) and regex("Rua", token.head_token.word):
            token.deps = "O"
            
        #revisão lema Souza

        if regex("Souza", token.lemma) and regex("B=BACIA", token.deps) and regex("Caroline|Rogério|Jailton", token.head_token.lemma):
            token.deps = "O"

        #revisão lema Ceará

        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("Rio|encontrar", token.head_token.lemma):
            token.deps = "O"
            
        #revisão lema Curitiba

        if regex("Curitiba", token.lemma) and regex("PUNCT", token.next_token.upos) and regex("Universidade|Museu|\[", token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("Curitiba", token.lemma) and regex("Falha", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Solimões

        if regex("Solimões", token.lemma) and regex("B=BACIA", token.deps) and regex("Rio|rio", token.previous_token.lemma):
            token.deps = "O"
            
        #revisão do lema São

        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("Maceió", token.previous_token.previous_token.lemma):
            token.deps = "O"
            
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("Foz|conjunto|NU-CLEO|anais|Plateau|Baixo|Supergrupo", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Mucuri

        if regex("Mucuri", token.lemma) and regex("B=BACIA", token.deps) and regex("Arenito", token.previous_token.lemma):
            token.deps = "O"

        #revisão do lema Araripe

        if regex("Araripe", token.lemma) and regex("B=BACIA", token.deps) and regex("Chapada|chapada|Eduardo|Paulo", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Almada

        if regex("Almada", token.lemma) and regex("B=BACIA", token.deps) and regex("Canhão|Rio", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Paraná

        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("região|CFB", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("Etendeka", token.next_token.next_token.lemma):
            token.deps = "O"
            
        #revisão do lema Alagoas

        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("pré-Alagoas", token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("Área|neocomiano|Andares|andar|Andar|Baixo|idade|pós-deposional|Cronoestratigrafia|Jequiá|parte|conter", token.head_token.lemma):
            token.deps = "O"

        #revisão do lema Campos

        if regex("Campos", token.lemma) and regex("B=BACIA", token.deps) and regex("1970|2001|classificação|Jordão", token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("Campos", token.lemma) and regex("B=BACIA", token.deps) and regex("planalto|Antonio|Humberto|São|Carlos|Diógenes|Siqueira|Carlos|Cruz|falha", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Santos

        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("Baía|Urbano|Antônio|Arco|Heriber\-to|Falha|Carla|Heriberto|Eugenio|Clóvis|Saulo|Claiton|Alberto|Queiroz", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("Bay|resumo", token.next_token.lemma):
            token.deps = "O"

        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("10|0", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
            
        #revisão do lema Espírito

        if regex("Espírito", token.lemma) and regex("B=BACIA", token.deps) and regex("Bahia", token.head_token.lemma) and regex("região", token.head_token.head_token.lemma):
            token.deps = "O"

        if regex("Espírito", token.lemma) and regex("B=BACIA", token.deps) and regex("Centro|Unidade", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Sergipe

        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("Área|Carmópolis|Aracaju|Evaporitos|Microplaca", token.head_token.lemma):
            token.deps = "O"
            
        #revisão do lema Ceará

        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("Neto|Sede", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("Rio|rio", token.previous_token.lemma):
            token.deps = "O"
        
        #petróleo

        if regex("petróleo", token.lemma) and regex("indústria|engenharia|geologia|setor|exploração|companhia|pesquisa|geólogo|geoquímica|Geoquímica|geografia|monopólio|setor|comércio|independência", token.head_token.lemma):
            token.deps = "O"

        # CRONOESTRATIGRÁFICA

        if regex("Regressivo|Rb\-Sr|Paleohidrológico|de|Arenoso|Lamoso|Petrolífero|Turbidítico|Internacional|Petrobrás|Petrorres|Aqüífero|Cartografia|Científica|ESTATÍSTICO|Estatístico|Geologia|Granulometric|Legal|Almirante|Atlântico|Carapebus|Cisalhamento|Câmara|Dobramentos|Documentação|Falhas|Frei|Informação|Irati|Irati\-Pirambóia|Itabapoana|Martinho|Medida|Namorado|Orós|Recôncavo|Riftes|Salvador|Talude|Temática|Turbiditos|Técnica|Ubarana|Unidades|Vulcanismo|Zonas|e|final|medida|o", token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"

        # ROCHA MCLARA
        # LEMA
        if regex("B=ROCHA", token.deps) and regex("Marga", token.lemma):
            token.lemma = "marga"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("Lamito", token.lemma):
            token.lemma = "lamito"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("Gipsita", token.lemma):
            token.lemma = "gipsita"
            token.upos = "NOUN"

        if regex("Folhelho", token.lemma) and regex("B=ROCHA", token.deps) and not regex("Livramento|Barreirinha|Lontras", token.next_token.lemma):
            token.lemma = "folhelho"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("Diamictito", token.lemma):
            token.lemma = "diamictito"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("Cataclasito", token.lemma):
            token.lemma = "cataclasito"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("Calcilutito", token.lemma):
            token.lemma = "calcilutito"
            token.upos = "NOUN"
            
        if regex("Anidrita", token.lemma) and regex("B=ROCHA", token.deps) and not regex("Principal", token.next_token.lemma):
            token.lemma = "anidrita"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("anidritar", token.lemma):
            token.lemma = "anidrita"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("anidrito", token.lemma):
            token.lemma = "anidrita"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("conglomerar", token.lemma):
            token.lemma = "conglomerado"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("evaporitar", token.lemma):
            token.lemma = "evaporito"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("halitar", token.lemma):
            token.lemma = "halita"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("halito", token.lemma):
            token.lemma = "halita"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("ortoconglomerar", token.lemma):
            token.lemma = "ortoconglomerado"
            token.upos = "NOUN"

        if regex("B=ROCHA", token.deps) and regex("paraconglomerar", token.lemma):
            token.lemma = "paraconglomerado"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("peridotitar", token.lemma):
            token.lemma = "peridotito"
            token.upos = "NOUN"
            
        if regex("B=ROCHA", token.deps) and regex("siltitar", token.lemma):
            token.lemma = "siltito"
            token.upos = "NOUN"

        if regex("metassedimentar", token.lemma) and regex("metassedimento|metassedimentos", token.word) and regex("B=ROCHA", token.deps):
            token.lemma = "metassedimento"
            token.upos = "NOUN"

        #lemma Pedra

        if regex("Pedra", token.lemma) and regex("B=ROCHA", token.deps) and regex("região|Membro|Uruçanga", token.head_token.lemma):
            token.deps = "O"
            
        #lemma Rocha

        if regex("Rocha", token.lemma) and regex("B=ROCHA", token.deps) and regex("Hélio|Luiz|Perfis|Dr\.", token.head_token.lemma):
            token.deps = "O"
            
        #lemma Vulcânico

        if regex("Vulcânico", token.lemma) and regex("B=ROCHA", token.deps) and regex("Alto|Complexo", token.previous_token.lemma):
            token.deps = "O"

        # TATI
        # CAMPO
        
        if regex("Fazenda", token.word) and regex("fazenda", token.lemma):
            token.lemma = "Fazenda"
        if regex("campo", token.lemma) and regex("de", token.previous_token.word) and regex("análise", token.previous_token.previous_token.lemma):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("NUM", token.next_token.upos):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("um", token.previous_token.lemma) and regex("a|b|c", token.next_token.lemma):
            token.deps = "O"
        if regex("bioestratigráfico|estratigráfico", token.lemma) and regex("amod|appos", token.deprel) and regex("campo", token.head_token.lemma):
            token.head_token.deps = "O"
        if regex("campo", token.lemma) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.lemma) and regex("bioestratigrafia|estratigrafia", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
        if re.search( r"^(" + r"cações" + r")$", token.__dict__['word'] ):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("CONCEIÇÃO", token.lemma) and regex(",", token.next_token.word) and regex("J\.|L\.", token.next_token.next_token.word):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("CONCEIÇÃO", token.lemma) and regex(";", token.previous_token.word) and regex("P\.|S\.|C\.", token.previous_token.previous_token.word):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("dado", token.head_token.head_token.lemma) and regex("conj", token.deprel):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("de", token.previous_token.word) and regex("escala", token.previous_token.previous_token.lemma):
            token.deps = "O"

        if regex("área|áreas|Área|Áreas", token.head_token.word) and regex("Plataforma|Física|Geofísica|Internacional|Estratigrafia|Exploração|del|E\&P|Rua|Geologia", token.word):
            token.deps = "O"
        if regex("área|áreas|Área|Áreas", token.previous_token.word) and regex("Física|Geofísica|Internacional|Estratigrafia|Exploração|del|E\&P|Rua|Geologia", token.word):
            token.deps = "O"

        if token.deps == "B=CAMPO" and regex("Campo", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Tenente", token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"

        # NÃOCONSOLID

        if regex("B=NÃOCONSOLID", token.deps) and regex("areio", token.lemma):
            token.lemma = "areia"
        if regex("B=NÃOCONSOLID", token.deps) and regex("Argila", token.lemma):
            token.lemma = "argila"
        if regex("B=NÃOCONSOLID", token.deps) and regex("silte/", token.lemma):
            token.lemma = "silte"

        if regex("B=POÇO", token.deps) and regex("Sp|sp|Rep|lv", token.lemma) and regex("\.|\)|\;", token.next_token.lemma):
            token.deps = "O"

        if regex("Morro", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Barro", token.next_token.next_token.next_token.word) and token.next_token.next_token.next_token.deps == "B=BACIA|B=NÃOCONSOLID":
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"

        # TATI
        # 27/04/2022 PÓS DÚVIDAS

        if regex("vulcânica|vulcânico", token.next_token.lemma) and regex("plug|plugs|estrutura|construção|elemento|fase", token.lemma):
            token.next_token.deps = "O"
        if regex("vulcânica|vulcânico", token.next_token.lemma) and regex("cinza|cinzas", token.word):
            token.next_token.deps = remove_from(token.next_token.deps, "B=ROCHA")
        if regex("bloco", token.lemma) and regex("B=NÃOCONSOLID", token.deps):
            token.deps = "O"
        if regex("vulcânica|vulcânico", token.next_token.lemma) and regex("cone|alto|atividade|manifestação|natureza|erupção|evento|edifício|acreção|arquipélago|conduto|cunha|emanação|extrusão|fonte|ilha|margem|monte|muralha|passado|pluma|processo|região", token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("vulcânica", token.lemma) and regex("ADJ", token.upos):
            token.lemma = "vulcânico"
        if regex("aglomerado", token.lemma) and regex("indistinto", token.next_token.lemma):
            token.deps = "O"
        if regex("aglomerados", token.word) and regex("de", token.next_token.lemma) and regex("cristal", token.next_token.next_token.lemma):
            token.lemma = "aglomerado"
            token.upos = "NOUN"
            token.deps = "O"
            token.feats = remove_from(token.feats, "VerbForm=Part")
            token.next_token.next_token.deprel = "nmod"

        # querer e sair como campo
        if regex("sair|querer", token.lemma) and token.deps == "B=CAMPO" and token.upos == "VERB":
            token.deps = "O"

        if regex("pioneiro", token.lemma) and regex("proje", token.next_token.lemma):
            token.deps = "O"

        # TATI AMBIGUIDADES
        if regex("Gomo|Tauá|Caruaçu|Pitanga", token.lemma) and regex("B=CAMPO.*", token.deps):
            token.deps = remove_from(token.deps, "B=CAMPO")
        if regex("rio", token.lemma) and regex("São", token.next_token.lemma) and regex("Francisco", token.next_token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
        if regex("São", token.lemma) and regex("Luiz", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("Quitunde", token.next_token.next_token.next_token.next_token.lemma) and regex("B=BACIA\|B=CAMPO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"

        if regex("B=CAMPO", token.deps) and regex("Congr\.\.", token.lemma):
            token.deps = "O"
        
        if regex("I=CAMPO", token.deps) and regex("O", token.previous_token.deps) and regex("Serra", token.lemma):
            token.deps = "O"

        if regex("Jacutinga", token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"
        
        if regex("barra", token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"

        if regex("obl", token.deprel) and regex("Carmópolis", token.lemma) and regex("descobrir", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("estreito", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("franco", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("furado", token.lemma):
            token.deps = "O"
        if regex("graben|gráben", token.lemma) and regex("de", token.next_token.lemma) and regex("B=CAMPO", token.next_token.next_token.deps) and regex("I=CAMPO", token.next_token.next_token.next_token.deps):
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
        if regex("campo", token.lemma) and regex("laboratório", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("alagamar", token.lemma):
            token.lemma = "Alagamar"
        if regex("B=CAMPO", token.deps) and regex("Ca\-vala", token.lemma):
            token.lemma = "Cavala"
        if regex("B=CAMPO", token.deps) and regex("leste", token.lemma):
            token.lemma = "Leste"
            token.upos = "PROPN"
        if regex("B=CAMPO", token.deps) and regex("nordeste", token.lemma):
            token.lemma = "Nordeste"
        if regex(".*CAMPO.*", token.deps) and regex("boletins-000004-2437|boletins-000008-1474|boletins-000004-3360|boletins-000005-58|boletins-000009-312|boletins-000001-1948|boletins-000003-1149|boletins-000010-1504|boletins-000009-371|boletins-000003-497|boletins-000006-800|boletins-000002-1008|boletins-000008-780|boletins-000001-3413|boletins-000002-1421|boletins-000009-1320|boletins-000008-828|boletins-000003-1263|boletins-000007-690|boletins-000009-2140|boletins-000001-2088|boletins-000011-1719|boletins-000009-1275|boletins-000003-1048|boletins-000009-1323|boletins-000004-600|boletins-000006-1290|boletins-000009-1522|boletins-000001-1211|boletins-000009-367|boletins-000004-1412|boletins-000011-2514|boletins-000011-430|boletins-000004-1571|boletins-000004-1407|boletins-000004-1524|boletins-000002-1420|boletins-000003-1923|boletins-000008-1041|boletins-000002-2317|boletins-000004-3375|boletins-000006-1965|boletins-000001-3599|boletins-000001-2010|boletins-000009-67|boletins-000003-1859|boletins-000003-2185|boletins-000003-2087|boletins-000003-79|boletins-000009-1529|boletins-000008-996|boletins-000011-724|boletins-000011-1186|boletins-000008-67|boletins-000001-2042|boletins-000008-581|boletins-000002-1465|boletins-000010-1459|boletins-000001-2090|boletins-000009-374|boletins-000008-1034|boletins-000008-1003|boletins-000011-11|boletins-000011-208|boletins-000008-1583|boletins-000002-1995|boletins-000003-1005|boletins-000001-3547|boletins-000011-1201|boletins-000011-1230|boletins-000003-1961|boletins-000009-380|boletins-000008-826|boletins-000008-822|boletins-000003-1441|boletins-000004-720|boletins-000006-1265|boletins-000004-608|boletins-000008-1059|boletins-000003-2027|boletins-000001-422|boletins-000003-2272|boletins-000001-2192|boletins-000001-2083|boletins-000009-2207|boletins-000008-749|boletins-000009-53|boletins-000002-2383|boletins-000007-46|boletins-000007-803|boletins-000002-1466|boletins-000009-172|boletins-000002-1464|boletins-000011-57|boletins-000004-3221|boletins-000001-2091|boletins-000002-199|boletins-000009-1418|boletins-000001-1579|boletins-000006-2350|boletins-000009-1528|boletins-000007-780|boletins-000003-2046|boletins-000002-143|boletins-000001-994|boletins-000007-389|boletins-000008-1892|boletins-000005-2172|boletins-000001-2101|boletins-000001-3423|boletins-000003-1874|boletins-000010-1554|boletins-000008-246|boletins-000003-1871|boletins-000009-1527|boletins-000008-1040|boletins-000002-1529|boletins-000008-773|boletins-000008-464|boletins-000006-1968|boletins-000009-368|boletins-000011-2497|boletins-000002-1537|boletins-000003-1175|boletins-000007-276|boletins-000008-789|boletins-000009-1354|boletins-000006-438|boletins-000001-2701|boletins-000001-1649|boletins-000009-393|boletins-000008-994|boletins-000004-2959|boletins-000006-2463|boletins-000001-2997|boletins-000007-592|boletins-000003-1972|boletins-000007-735|boletins-000008-661|boletins-000001-3333|boletins-000011-2523|boletins-000009-490|boletins-000004-3061|boletins-000004-158|boletins-000002-1444|boletins-000008-995|boletins-000006-2308|boletins-000006-2298|boletins-000003-2436|boletins-000004-622|boletins-000002-1459|boletins-000010-1507|boletins-000011-385|boletins-000002-520|boletins-000004-3224|boletins-000006-1177|boletins-000011-1015|boletins-000001-3579|boletins-000004-3123|boletins-000002-1417|boletins-000002-119|boletins-000011-1666|boletins-000006-1275|boletins-000003-2141|boletins-000006-1254|boletins-000011-498|boletins-000011-1447|boletins-000001-1365|boletins-000003-1869|boletins-000010-1467|boletins-000002-454|boletins-000011-251|boletins-000004-694|boletins-000001-3583|boletins-000003-1965|boletins-000006-1130|boletins-000006-1610|boletins-000008-750|boletins-000001-3499|boletins-000006-1293|boletins-000011-1005|boletins-000007-788|boletins-000001-3303|boletins-000002-152|boletins-000006-1963|boletins-000008-315|boletins-000001-2298|boletins-000008-761|boletins-000004-3075", sentence.sent_id ):
            token.deps = "O"
        if regex("petró-lec", token.lemma):
            token.lemma = "petróleo"
        if regex("B=CAMPO", token.deps) and regex("pilar", token.lemma):
            token.deps = "O"
        if regex("Carmópolis", token.lemma) and regex("região", token.head_token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("tie", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("tigre", token.lemma):
            token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("área", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("1-RJS-203|1-RJS-15", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
        if regex("B=CAMPO", token.deps) and regex("São", token.lemma) and regex("I=CAMPO", token.next_token.deps) and regex("boletins-000007-697|boletins-000011-2402|boletins-000003-2290|boletins-000007-704|boletins-000006-1374|boletins-000011-2387", sentence.sent_id ):
            token.deps = "O"
            token.next_token.deps = "O"
        

        # UNIDADE_LITO
        # MCLARA

        #revisão lema formação
        if regex("B=UNIDADE_LITO", token.deps) and regex("formação", token.lemma) and regex("teste|processo|Processos|mecanismo|maneira|fluido|perspectiva|condição|pressão", token.head_token.lemma):
            token.deps = "O"

        if regex("reativação|propagação|desenvolvimento|evolução|estruturamento|preenchimento|precoce|significativo|simultâneo", token.lemma) and regex("formação", token.head_token.lemma) and regex("B=UNIDADE_LITO", token.head_token.deps):
            token.head_token.deps = "O"
            
        if regex("B=UNIDADE_LITO", token.deps) and regex("formação", token.lemma) and not regex("formações", token.word) and regex("de", token.next_token.lemma) and not regex("bacia|Bacia", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("ainda|bacia", token.lemma) and regex("em", token.next_token.lemma) and regex("formação", token.next_token.next_token.lemma) and regex("B=UNIDADE_LITO", token.next_token.next_token.deps):
            token.next_token.next_token.deps = "O"
            
        if regex("bacia", token.lemma) and regex("em", token.next_token.lemma) and regex("B=UNIDADE_LITO", token.next_token.next_token.deps) and regex("formação", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "O"
            
        if regex("de|a", token.lemma) and regex("sua|suas", token.next_token.word) and regex("formação", token.next_token.next_token.lemma) and regex("B=UNIDADE_LITO", token.next_token.next_token.deps):
            token.next_token.next_token.deps = "O"
            
        if regex("B=UNIDADE_LITO", token.deps) and regex("formação", token.lemma) and regex("de", token.next_token.lemma) and regex("o|um", token.next_token.next_token.lemma) and regex("bacia|Bacia", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
            token.next_token.next_token.next_token.deps = "B=BACIA"
            
        #grupo de [n é uni lito]
        if regex("B=UNIDADE_LITO", token.deps) and regex("Tectônica|Interpretação|Análise|Aguiar|7FC|1|Cocobeach|Canadá|Geologia|Exinita|Estudos|Cp|Iner\-tinita|Petrobras/Cenpes/Pdexp/Geoq|Pe|Pensilvaniano", token.lemma):
            token.deps = "O"

        #Bam-buf -> Bambuí
        if regex("B=UNIDADE_LITO", token.deps) and regex("Bam\-buf", token.lemma):
            token.lemma = "Bambuí"
            
        #Pa-lermo -> Palermo
        if regex("B=UNIDADE_LITO", token.deps) and regex("Pa\-lermo", token.lemma):
            token.lemma = "Palermo"

        # REVISÃO 06-06-22
        # MCLARA
        if regex("Gabão", token.lemma) and regex("B=BACIA", token.deps) and regex("Alagoas", token.head_token.lemma) and regex("B=BACIA", token.head_token.deps):
            token.deps = "O"
            token.head_token.deps = "O"

        if regex("Tapajós", token.lemma) and regex("I=BACIA", token.deps) and regex("Alto", token.head_token.lemma) and regex("B=BACIA", token.head_token.deps):
            token.deps = "O"
            token.head_token.deps = "O"

        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("UNIVERSIDADE", token.head_token.word):
            token.deps = "O"

        if regex("Santos", token.word) and regex("B=BACIA", token.deps) and regex("para", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("regime", token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.lemma = "Santos"
            token.upos = "PROPN"

        if regex("bacia", token.word) and regex("bacio", token.lemma):
            token.lemma = "bacia"
            token.upos = "NOUN"
            token.deprel = "nmod"
            token.feats = "Gender=Fem|Number=Sing"

        if regex("Lima", token.lemma) and regex("B=UNIDADE_CRONO", token.deps) and regex("Nt", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("Rifts", token.lemma) and regex("B=UNIDADE_CRONO", token.deps) and regex("Sistema", token.head_token.lemma):
            token.deps = "O"

        if regex("Tricornites|elongatus|Globotruncana|Rugoglobigerina|reicheli/|Proteacidites|longispinosu", token.lemma) and regex(".*=UNIDADE_CRONO", token.deps):
            token.deps = "O"

        # 10/06/2022
        # TATI
        # 3.1
        if regex("I=CAMPO", token.deps) and regex("3\.1", token.lemma):
            token.deps = "O"
            token.upos = "NUM"
            token.feats = "NumType=Card"
            token.deprel = "parataxis"
        # MAIS CASOS DE CAMPO_X ou X_DE_CAMPO
        if regex("campo", token.lemma) and regex("distensivo", token.next_token.lemma):
            token.deps = "O"
        if regex("campo", token.lemma) and regex("de", token.next_token.lemma) and regex("carvão|visão", token.next_token.next_token.lemma):
            token.deps = "O"
        if re.search( r"^(" + r"campo" + r")$", token.__dict__['lemma'] ) and re.search( r"^(" + r"Guia" + r")$", token.head_token.__dict__['lemma'] ):
            token.deps = "O"

        # 21/02/2022
        # TATI
        # ROCHA_LEMA COM /
        if regex("B=ROCHA", token.deps) and regex("arenito/", token.lemma):
            token.lemma = "arenito"
        if regex("B=ROCHA", token.deps) and regex("gipsita/", token.lemma):
            token.lemma = "gipsita"
        if regex("B=ROCHA", token.deps) and regex("anidrita/", token.lemma):
            token.lemma = "anidrita"
        if regex("B=ROCHA", token.deps) and regex("folhelho/", token.lemma):
            token.lemma = "folhelho"

        # NÃO CONSOLIDADO
        if regex("B=NÃOCONSOLID", token.deps) and regex("Bloco", token.lemma) and regex("I=NÃOCONSOLID", token.next_token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
        if regex("I=NÃOCONSOLID", token.deps) and regex("Araticum", token.lemma):
            token.deps = "O"
        if regex("Arenitos", token.lemma):
            token.lemma = "Arenito"
        if regex("B=NÃOCONSOLID", token.deps) and regex("Areia", token.lemma):
            token.lemma = "areia"

        if regex("pioneiro", token.head_token.lemma) and regex("B=POÇO_T", token.head_token.deps) and regex("trabalho", token.lemma):
            token.head_token.deps = "O" 

        if regex("geólogo|geologo|Geólogo|Geologo", token.head_token.lemma) and regex("Poço|poço", token.lemma):
            token.deps = "O"

        # MCLARA
        # BACIA
        # 29/06/2022

        #lema Alagoas

        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("dar", token.previous_token.lemma):
            token.deps = "O"
            
        if regex("Alagoas", token.lemma) and regex("B=BACIA", token.deps) and regex("e|by", token.previous_token.lemma) and regex("Jiquiá|overlain", token.previous_token.previous_token.lemma):
            token.deps = "O"
            
        #lema Almada

        if regex("Almada", token.lemma) and regex("B=BACIA", token.deps) and regex("região", token.head_token.word):
            token.deps = "O"
            
        #lema Amazonas

        if regex("Amazonas", token.lemma) and regex("B=BACIA", token.deps) and regex(",", token.next_token.lemma) and regex("algum", token.next_token.next_token.lemma) and regex("faixa", token.next_token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("Amazonas", token.lemma) and regex("B=BACIA", token.deps) and regex("Gráben|GLORIA|Leque|sistema|Rio", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Amazonas", token.lemma) and regex("B=BACIA", token.deps) and regex("Foz", token.head_token.lemma) and regex("visualizar", token.head_token.head_token.lemma):
            token.deps = "O"
            
        if regex("Amazonas", token.lemma) and regex("B=BACIA", token.deps) and regex("foz|Foz", token.head_token.lemma) and regex("apresentar|mapear|atingir", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #lema Araripe

        if regex("Araripe", token.lemma) and regex("B=BACIA", token.deps) and regex("\(", token.next_token.word) and regex("500", token.next_token.next_token.word):
            token.deps = "O"
            
        if regex("Araripe", token.lemma) and regex("B=BACIA", token.deps) and regex("Eduardo", token.previous_token.lemma):
            token.deps = "O"
            
        #lema Santos

        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("os", token.previous_token.word) and regex("Todos", token.previous_token.previous_token.word):
            token.deps = "O"

        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("de", token.previous_token.word) and regex("áea", token.previous_token.previous_token.word):
            token.deps = "O"
            
        if regex("Santos", token.lemma) and regex("B=BACIA", token.deps) and regex("Ferrer-Urbano", token.previous_token.word):
            token.deps = "O"
            
        #lema Sergipe

        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("Well", token.previous_token.word):
            token.deps = "O"
            
        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("de", token.previous_token.word) and regex("Continental", token.previous_token.previous_token.word):
            token.deps = "O"
            
        if regex("Sergipe", token.lemma) and regex("B=BACIA", token.deps) and regex("et", token.previous_token.word) and regex("Bahia", token.previous_token.previous_token.word):
            token.deps = "O"

        #lema Paraná

        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("Província|ela", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("miogeos-syncline|Myogeosyncline|miogeosyncline|flood", token.next_token.lemma):
            token.deps = "O"
            
        #lema Pelotas

        if regex("Pelotas", token.lemma) and regex("B=BACIA", token.deps) and regex("província", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Pelotas", token.lemma) and regex("B=BACIA", token.deps) and regex("de", token.previous_token.lemma) and regex("o", token.previous_token.previous_token.lemma) and regex("que", token.previous_token.previous_token.previous_token.lemma):
            token.deps = "O"
            
        #lema Rio

        if regex("Rio", token.lemma) and regex("B=BACIA", token.deps) and regex("Paraíba", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma):
            token.deps = "O"

        #lema Recôncavo

        if regex("Recôncavo", token.lemma) and regex("B=BACIA", token.deps) and regex("campo", token.head_token.lemma) and regex("o", token.previous_token.lemma):
            token.deps = "O"
            
        if regex("Recôncavo", token.lemma) and regex("B=BACIA", token.deps) and regex("sul", token.head_token.lemma):
            token.deps = "O"
            
        #lema Taubaté

        if regex("Taubaté", token.lemma) and regex("B=BACIA", token.deps) and regex(",", token.next_token.word) and regex("\(", token.next_token.next_token.word):
            token.deps = "O"
            
        #lema Ceará

        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("o", token.previous_token.lemma) and regex("em", token.previous_token.previous_token.lemma):
            token.deps = "O"
            
        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("root", token.deprel):
            token.deps = "O"

        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("Maranhão", token.head_token.lemma) and regex("plataforma", token.head_token.head_token.lemma):
            token.deps = "O"
            
        if regex("Ceará", token.lemma) and regex("B=BACIA", token.deps) and regex("Terraço", token.head_token.lemma):
            token.deps = "O"
            
        #lema São

        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex("Plataforma", token.head_token.lemma):
            token.deps = "O"
            
        if regex("São", token.lemma) and regex("B=BACIA", token.deps) and regex(",", token.previous_token.word) and regex("Taubaté", token.previous_token.previous_token.word):
            token.deprel = "appos"
            token.deps = "O"

        #lema Espírito

        if regex("Espírito", token.lemma) and regex("B=BACIA", token.deps) and regex("o", token.previous_token.lemma) and regex("a", token.previous_token.previous_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        #lema Paraná

        if regex("Paraná", token.lemma) and regex("B=BACIA", token.deps) and regex("o", token.previous_token.lemma) and regex("de", token.previous_token.previous_token.lemma) and regex("Estado", token.previous_token.previous_token.previous_token.lemma):
            token.deps = "O"
            
        #lema Icó

        if regex("Icó", token.lemma) and regex("B=BACIA", token.deps) and regex("Horst", token.head_token.lemma):
            token.deps = "O"
            
        #lema Mucuri

        if regex("Mucuri", token.lemma) and regex("B=BACIA", token.deps) and regex("Member", token.next_token.word):
            token.deps = "O"

        #revisão de I=BACIA

        if regex("emersa\.|Terrestre", token.lemma) and regex("I=BACIA", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma):
            token.deps = "O"

        if regex("I=BACIA", token.deps) and regex("Ocidental|Oriental|Ibérica", token.lemma) and regex("África|Mediterrâneo|península", token.previous_token.lemma) and regex("o", token.previous_token.previous_token.lemma) and regex("de", token.previous_token.previous_token.previous_token.lemma):
            token.deps = "O"
            token.previous_token.deps = "O"
            token.previous_token.previous_token.deps = "O"
            token.previous_token.previous_token.previous_token.deps = "O"

        if regex("Cretáceo", token.lemma) and regex("Superior", token.next_token.lemma) and regex("[bB]acia|Bacias", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"

            
        if regex("I=BACIA", token.deps) and regex("Norte|Sul/Sudeste", token.lemma) and regex("o", token.previous_token.lemma) and regex("de", token.previous_token.previous_token.lemma) and not regex("Grande", token.previous_token.previous_token.previous_token.lemma):
            token.deps = "O"
            token.previous_token.deps = "O"
            token.previous_token.previous_token.deps = "O"
            
        if regex("I=BACIA", token.deps) and regex("Costa|Sudeste|Itália|[nN]ordeste|Brasil", token.lemma) and regex("o", token.previous_token.lemma) and regex("de", token.previous_token.previous_token.lemma):
            token.deps = "O"
            token.previous_token.deps = "O"
            token.previous_token.previous_token.deps = "O"

        # mclara 06-07-2022

        if regex("Buracica", token.lemma) and regex("B=CAMPO", token.deps) and regex("[iI]dade|[aA]ndar|[aA]ndares", token.head_token.lemma) and regex("Inferior", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Aratu|Buracica|Jequiá", token.lemma) and regex("Rio", token.head_token.lemma) and regex("estágio", token.head_token.head_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            
        if regex("Aratu|Jiquiá|Buracica", token.lemma) and regex("B=CAMPO", token.deps) and regex("Dom", token.head_token.lemma) and regex("[aA]ndar", token.head_token.head_token.lemma):
            token.deps = "O"
            
        if regex("Buracica", token.lemma) and regex("[iI]nferior|[sS]uperior", token.next_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            
        if regex("Buracica|Aratu", token.lemma) and regex("B=CAMPO", token.deps) and regex(".*=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "O"
            
        if regex("Dom", token.lemma) and regex("[aA]ndar", token.head_token.lemma) and regex("B=CAMPO", token.deps) and regex("João", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        #if regex("Rio", token.lemma) and regex("B=CAMPO", token.deps) and regex("[aA]ndar", token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("Inferior", token.next_token.next_token.next_token.next_token.lemma):
            #token.deps = "O"
            #token.next_token.deps = "O"
            #token.next_token.next_token.deps = "O"
            #token.next_token.next_token.next_token.deps = "O"
            #token.next_token.next_token.next_token.next_token.deps = "O"

        if regex("Rio", token.lemma) and regex("estágio|[aA]ndar", token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            
        if regex("Rio", token.lemma) and regex("Dom", token.head_token.lemma) and regex("andar", token.head_token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            
        if regex("Serra", token.lemma) and regex("I=CAMPO", token.deps) and regex("[Aa]ndar|[iI]dade", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Aratu", token.lemma) and regex("o", token.previous_token.lemma) and regex("para|desde", token.previous_token.previous_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"

        if regex("Vittatina", token.lemma) and regex("B=UNIDADE_CRONO", token.deps) and regex("costabilis", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("de", token.lemma) and regex("o", token.next_token.lemma) and regex("Apodi", token.next_token.next_token.lemma) and regex("Bacia", token.head_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("de", token.lemma) and regex("o", token.next_token.lemma) and regex("Midcontinent", token.next_token.next_token.lemma) and regex("Pensilvaniano", token.head_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("Serviço|Centro|Área|Barberena|Suíte|Paleogeografia|Af|Pliensbaquiano|Terciário|mi\-", token.lemma) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"

        if regex("Canyon", token.lemma) and regex("São", token.next_token.lemma) and regex("Tomé", token.next_token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("grupo", token.lemma) and regex("Pe|7FC", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("Poços", token.word) and regex("de", token.next_token.word) and regex("Caldas.*", token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("Caldas-Cabo", token.previous_token.lemma) and regex("Frio", token.lemma):
            token.deps = "O"

        if sentence.sent_id == "boletins-000009-2062" and token.id == "20" and regex("Alvorada", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Norte", token.next_token.next_token.next_token.word):
            token.deps = "O"
            reattach(token, "15")
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"

        # MCLARA 29/08/2022
        if regex("Candeias", token.lemma) and regex("Lamarão", token.head_token.lemma) and regex("falha", token.head_token.head_token.lemma):
            token.deps = "O"

        # MCLARA 12/09/2022

        if regex("dilatação", token.lemma) and regex("área", token.head_token.lemma):
            token.deps = "O"
            
        if regex("laminação", token.lemma) and regex("e", token.next_token.lemma) and regex("petrografia", token.next_token.next_token.lemma):
            token.deps = "O"
            
        if regex("falha", token.lemma) and regex("rocha|gouge", token.head_token.lemma):
            token.deps = "O"
            token.head_token.deps = "O"
            
        if regex("grão", token.lemma) and regex("fratura", token.head_token.lemma):
            token.head_token.deps = "O"
            
        if regex("bioturbação", token.lemma) and regex("nem", token.previous_token.lemma):
            token.deps = "O"
            
        if regex("maciço", token.lemma) and regex("presença", token.head_token.lemma):
            token.deps = "O"

        # TATI
        # 08/09/2022

        if regex("de", token.lemma) and regex("case", token.deprel) and regex("CO|alimentação", token.head_token.lemma) and regex("reservatório", token.head_token.head_token.lemma) and regex("nmod", token.head_token.deprel):
            token.head_token.head_token.deps = "O"

        if regex("reservatório", token.head_token.lemma) and regex("auxiliar", token.lemma):
            token.head_token.deps = "O"

        if regex("(boletins-000002-210|boletins-000004-1916|boletins-000003-371|boletins-000010-28)", sentence.sent_id ) and regex("migração", token.lemma):
            token.deps = "O"

        if regex("de", token.lemma) and regex("depocentro|canal|direção|eixo|esforço|falha", token.head_token.lemma) and regex("migração", token.head_token.head_token.lemma) and regex("nmod", token.head_token.deprel):
            token.head_token.head_token.deps = "O"

        if regex("petróleo", token.lemma) and regex("geografia|pesquisa|companhia|geólogo", token.head_token.lemma):
            token.deps = "O"

        # MCLARA 20/09/2022
            
        #GÁS leva de dúvidas de julho (07/22)

        if regex("gás", token.lemma) and regex("enriquecer", token.head_token.lemma):
            token.deps = "O"
            
        if regex("iluminação", token.lemma) and regex("gás", token.head_token.lemma):
            token.head_token.deps = "O"
            
        #ÓLEO leva de dúvidas de julho (07/22)

        if regex("óleo", token.lemma) and regex("lamparina", token.head_token.lemma):
            token.deps = "O"
            
        if regex("baleia", token.lemma) and regex("óleo", token.head_token.lemma):
            token.head_token.deps = "O"
            
        if regex("imersão", token.lemma) and regex("óleo", token.head_token.lemma):
            token.head_token.deps = "O"

        if regex("petróleo", token.lemma) and regex("inclusão|setor", token.head_token.lemma):
            token.deps = "O"

        if regex("carbonato", token.lemma) and regex("presença|ausência|eliminação|teor", token.head_token.lemma):
            token.deps = "O"
            
        if regex("cálcio", token.lemma) and regex("carbonato", token.head_token.lemma):
            token.head_token.deps = "O"

        #gás

        if regex("gás", token.lemma) and regex("petróleo", token.head_token.lemma) and regex("setor", token.head_token.head_token.lemma):
            token.deps = "O"

        # MCLARA 7/10/22
        if regex("petróleo", token.lemma) and regex("exploração|indústria|geologia|geoquímica|monopólio|comércio|independência", token.head_token.lemma):
            token.deps = "O"

        if regex("Bacia", token.word) and regex("Costeira", token.next_token.word) and regex("PE\/PB", token.next_token.next_token.word):
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "B=BACIA"
            
        if regex("Bacia", token.word) and regex("Costeira", token.next_token.word) and regex("Pernambuco", token.next_token.next_token.word) and regex("\-Paraíba", token.next_token.next_token.next_token.word):
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.lemma = "Paraíba"

        if regex("Bacia", token.word) and regex("Cretácea", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("Barreirinhas", token.next_token.next_token.next_token.lemma):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "B=BACIA"
            
        if regex("Bacia", token.word) and regex("Paleozóica", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("Paraná", token.next_token.next_token.next_token.next_token.lemma):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
            
        if regex("Bacia", token.word) and regex("Pré\-Aptiana", token.next_token.word):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Bacia", token.word) and regex("Proterozóica", token.next_token.word) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("São", token.next_token.next_token.next_token.next_token.word) and regex("Francisco", token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=BACIA"

        if regex("Bacias", token.word) and regex("Sedimentares|Sedimenta\-res", token.next_token.lemma) and regex("evolução|Evolução|Simpósio|Sim\-pósio|Análises|Avaliação", token.head_token.lemma):
            token.deps = "O"

        if regex("Bacias", token.word) and regex("Sedimentares", token.next_token.lemma) and regex("\(", token.previous_token.lemma):
            token.next_token.deps = "O"

        if regex("Bacias", token.word) and regex("Setor", token.head_token.lemma):
            token.deps = "O"

        if regex("idade", token.word) and regex("Granulometric", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Sistema", token.word) and regex("de", token.next_token.lemma) and regex("Fraturas", token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            
        if regex("Sistemas", token.word) and regex("de", token.next_token.lemma) and regex("Leques", token.next_token.next_token.word) and regex("Submarinos", token.next_token.next_token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            
        if regex("Sistemas", token.word) and regex("Tectônicos|Complexos|Cohen", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Cretáceo", token.word) and regex("Brasileiro|Marinho", token.next_token.word):
            token.next_token.deps = "O"
            
        if regex("Paleoceno", token.word) and regex("Estudos", token.next_token.word):
            token.next_token.deps = "O"

        if regex("Campo", token.word) and regex("de", token.next_token.word) and regex("Alba", token.next_token.next_token.word) and regex("3\.1", token.next_token.next_token.next_token.word):
            token.next_token.next_token.next_token.deps = "O"

        # MCLARA 10/10/2022
        
        if regex("Membro|Grupo", token.word) and regex("Triunfo|Araxá", token.next_token.word) and regex("/", token.next_token.next_token.word):
            token.next_token.next_token.deps = "O"

        # MCLARA 18/10/2022

        if regex("Andar", token.word) and regex("Dom", token.next_token.word) and regex("João", token.next_token.next_token.word) and regex("\...", token.next_token.next_token.next_token.word):
            token.next_token.next_token.next_token.deps = "O"

        if regex("Paleógeno", token.word) and regex("/", token.next_token.word):
            token.next_token.deps = "O"

        if regex("Proterozóico", token.word) and regex("sp\.", token.next_token.word):
            token.next_token.deps = "O"

        if regex("Discordância", token.word) and regex("pré-Aptiano", token.next_token.word) and regex("Superior", token.next_token.next_token.word):
            token.deps = "B=ESTRUTURA_FÍSICA"
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Falhamento", token.word) and regex("limite", token.next_token.word):
            token.next_token.deps = "O"

        # TATI 4/11/22

        if regex("[Aa]nidrita", token.lemma) and regex("[Pp]rincipal", token.next_token.lemma):
            token.next_token.deps = "O"

        if regex("migração", token.head_token.lemma) and regex("sistema", token.lemma) and regex("fluvial", token.next_token.lemma):
            token.head_token.deps = "O"

        # MCLARA 16/11/22

        if regex("idade|Idades|idades", token.word) and regex("40Ar/39|Rb-Sr|Ar/Ar|K/Ar|K-Ar|Potássio", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"

        # TATI 1/12/22
        
        if regex("bomb.*", token.lemma):
            token.deps = "O"

        # MCLARA 12/12/2022
        #bacia - 10/12/2022 pt 2 que não depende de sema

        if regex("Ceará", token.lemma) and regex("MIURA", token.head_token.lemma):
            token.deps = "O"
            
        if regex("Alagoas", token.lemma) and regex("desde", token.previous_token.lemma) and regex("até", token.next_token.lemma) and regex("Macaé", token.next_token.next_token.lemma):
            token.deps = "O"

        # TATI 16/12/2022

        if regex("ígneo", token.lemma) and regex("atividade|evento|composição", token.head_token.lemma):
            token.deps = "O"

        if regex("Alto", token.lemma) and regex("Regional", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("Badejo", token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "O"

        if regex("Baixo", token.lemma) and regex("de", token.next_token.lemma) and regex("Camaçari", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "O"

        if regex("boletins-000004-3609", sentence.sent_id ) and regex("Enchova", token.lemma):
            token.deps = "O"

        if regex("Faixa", token.lemma) and regex("de", token.next_token.lemma) and regex("Garoupa", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "O"


        if regex("Bonito", token.lemma) and regex("Ribeirão", token.previous_token.lemma):
            token.deps = "O"

        if regex("boletins-000002-1882", sentence.sent_id ) and regex("Rocha", token.lemma):
            token.deps = "O"

        if regex("P\-31", token.lemma):
            token.deps = "O"

        # MCLARA 23/12/2022
        #unidade_lito - 23/12/2022

        if regex("Coqueiro", token.lemma) and regex("Seco", token.next_token.lemma) and regex("[Ii][Vv]|Il", token.next_token.next_token.lemma) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "O"
            
        #unidade_crono - 23/12/2022

        if regex("Sistema", token.lemma) and regex("Cretáceo", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "B=UNIDADE_CRONO"

        # regras de limpeza pós uri - Tati 15/02/2023

        if regex("/N", token.lemma):
            token.deps = "O"

        if regex("Atlanta", token.lemma):
            token.deps = "O"

        if regex("CO2", token.word) and regex("reduction", token.next_token.word) and regex("vs.", token.next_token.next_token.word) and regex("acetate", token.next_token.next_token.next_token.word) and regex("fermentation-isotopic", token.next_token.next_token.next_token.next_token.word) and regex("evidence.", token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"

        if regex("Alba", token.lemma) and regex("3.1", token.next_token.lemma):
            token.next_token.deps = "O"

        if regex("Fazenda", token.lemma) and regex("Brasileiro", token.next_token.lemma):
            token.next_token.deps = "O"
            token.deps = "O"

        if regex("Itaparica", token.lemma) and regex("Island", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("Jequia", token.lemma) and regex("Lagoa", token.previous_token.lemma):
            token.deps = "O"

        if regex("Alagoas-Eomesoalbianolfigs.", token.word) and regex("1", token.next_token.word):
            token.lemma = "Alagoas-Eomesoalbiano"
            token.next_token.deps = "O"

        if regex("Ul", token.word) and regex("SMCOMUdGd", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("Lenticular", token.word) and regex("and", token.next_token.word):
            token.deps = "O"

        if regex("Pai", token.word) and regex("Vitório", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("Fazenda", token.lemma) and regex("Betumita", token.next_token.lemma):
           token.deps = "O"
           token.next_token.deps = "O"

        if regex("Grupo", token.lemma) and regex("Dom", token.next_token.lemma) and regex("João", token.next_token.next_token.lemma) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"
            token.next_token.deps = "B=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"

    # ANCHOR (5) regras positivas mas que dependem de outros semas
    for t, token in enumerate(sentence.tokens):
        # CAMPOS QUE NÃO ESTAVAM NO LÉXICO MAS QUE SÃO CAMPOS
        if regex("Catu", token.lemma) and regex("O", token.deps) and regex("de", token.previous_token.lemma) and regex("campo", token.previous_token.previous_token.lemma):
            token.deps = "I=CAMPO"
            token.previous_token.deps = "I=CAMPO"
        if regex("Catu", token.lemma) and regex("O", token.deps):
            token.deps = "B=CAMPO"
        if regex("Anin\-gas", token.lemma) and regex("O", token.deps) and regex("de", token.previous_token.lemma):
            token.lemma = "Aningas"
            token.deps = "I=CAMPO"
            token.previous_token.deps = "I=CAMPO"
        if regex("Asmari", token.lemma) and regex("O", token.deps):
            token.deps = "B=CAMPO"
        if regex("Oligo\-Mioceno", token.lemma) and regex("O", token.deps):
            token.deps = "B=CAMPO"
        if regex("poços?|pocos?", token.lemma) and regex("O", token.deps):
            token.deps = "B=POÇO"
        if regex("Campo", token.head_token.lemma) and regex("flat:name", token.deprel) and regex("ADP|PROPN|NOUN|DET", token.upos) and regex("O", token.deps):
            token.deps = "I=CAMPO"

        if regex("Médio", token.lemma) and regex("B=BACIA", token.deps) and regex("PUNCT", token.previous_token.upos) and regex("Amazonas", token.next_token.lemma) and regex("bacia", token.head_token.lemma):
            token.deps = "O"
            token.next_token.deps = "B=BACIA"

        #revisão lema Bacia

        if regex("I=UNIDADE_CRONO", token.deps) and regex("Bacia", token.head_token.lemma):
            token.deps = "I=BACIA"
            token.head_token.deps = "B=BACIA"

        # 5 lemma = ".*iano" and @token.deps == "O"

        if regex("pré\-cambriano|Pré\-Cambriano|Pré\-cambriano|Pliensbaquiano|neo\-aptiano|neo\-albiano|pré\-aptiano|pós\-aptiano|Neo\-Albiano|mississipiano|Aptiano/Albiano|aptiano|Aptiano\-Albiano|albo\-cenomianiano|Cenomaniano/Turoniano|Mesoaptiano|Neo\-Albiano|Santoniano\-Campaniano|campaniano|mississipiano|Albo\-Maastrichtiano|Aptiano/Albiano|albo\-cenomianiano|intra\-albiano|intra\-cenomaniano|Albiano/Cenomaniano|Aptiano\-Albiano|Cenomaniano\-Turoniano|Eo\-Mesoalbiano|Eocambriano|Eoeoturoniano|Mississipiano|Neo\-albiano|Neopliensbaquiano|Santoniano/Campaniano|albo\-aptiano|carbonífera\-permiano|cenomaniano|intra\-campaniano|neovalanginiano\-eobarremiano|\-Cenomaniano|\-Ordoviciano|Alagoas\-Albiano|Albiano|Albiano/Turoniano|Albo\-Aptiano|Albo\-Turoniano|Berriasiano\-Valanginiano|Cambriano\-Ordoviciano|Campaniano\-Maastrichtiano|Carbonífero\-Permiano|Cenomaniano\-Santoniano|Coniaciano\-Maastrichtiano|Maactrichtiano|Meso\-campaniano|Neo\-Aptiano|Neobarremiano/Eoaptiano|Neoberriasiano/Eobarremiano|Neocomiano/Barremiano|Neopermiano|précambriano|pós\-maastrichtiano|pós\-albiano|pós\-maastrichtiano|pós\-Maastrichtiano", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        # 5 lemma = ".*oceno" and @token.deps == "O"

        if regex("Pleistoceno/Holoceno|Aptiano\-Mioceno|Eoceno\-Oligoceno|Holoceno/Pleistoceno|Cretáceo\-Paleoceno|Eoceno|Eoceno/Oligoceno|Neo\-eoceno|Neocretáceo/Paleoceno|Neoeopaleoceno|Neopaleoceno\-Mioceno|Neopaleoceno/Eoeoceno|Plio\-ceno\-Pleistoceno", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
        if regex("B=CAMPO", token.deps) and regex("Bacia", token.lemma) and regex("de", token.next_token.word) and regex("PROPN", token.next_token.next_token.upos):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
        if regex("flat:name", token.deprel) and regex("Represa", token.head_token.lemma) and regex("de", token.head_token.next_token.word) and regex("Barra", token.head_token.next_token.next_token.lemma) and regex("Bonita", token.head_token.next_token.next_token.next_token.lemma):
            token.head_token.next_token.next_token.deps = "B=CAMPO"
        if regex("Sub\-Bacia", token.lemma) and regex("PROPN", token.next_token.upos):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
        if regex("Sub\-Bacia", token.lemma) and regex("de", token.next_token.word) and regex("PROPN", token.next_token.next_token.upos):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
        if 'B=ROCHA' in token.deps and 'I=NÃOCONSOLID' in token.deps:
            token.deps = "I=NÃOCONSOLID"
        if regex("Jiquiá", token.word) and regex("e", token.next_token.word) and regex("Buracica|Alagoas", token.next_token.next_token.word):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = ""
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"

        #condensado

        #if regex("Campo", token.word) and regex("Mourão", token.next_token.word) and token.deps == "B=CAMPO":
            #token.deps = "B=UNIDADE_LITO"
            #token.next_token.deps = "I=UNIDADE_LITO"
        if regex("poço|Poço", token.lemma) and regex("NUM", token.next_token.upos) and regex("O", token.next_token.deps):
            token.next_token.deps = "I=POÇO"
        if regex("Tucano", token.word) and regex("PROPN", token.next_token.upos) and regex("e", token.next_token.next_token.word) and regex("PROPN", token.next_token.next_token.next_token.upos):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "B=BACIA"
        # corrigindo allfieldsnames (expansão do léxico de campo)
        if token.deps == "B=CAMPO|B=POÇO":
            token.deps = "B=POÇO"

        # TATI NOVOS CAMPOS (não tem regra de expansão pra Campo pois é palavra ambígua)
        if regex("I=CAMPO", token.deps) and regex("O", token.previous_token.deps) and regex("Barra", token.lemma):
            token.previous_token.deps = "I=CAMPO"
        if regex("campo|Campo", token.lemma) and regex("I=CAMPO", token.deps):
            token.deps = "B=CAMPO"
        if regex("D.", token.lemma) and regex("João", token.next_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
        if regex("B=CAMPO.*", token.deps) and regex("flat:name|nmod", token.deprel) and regex("B=CAMPO", token.head_token.deps) and regex("[Cc]ampo|CAMPO", token.head_token.lemma) and regex("boletins-000002-602|boletins-000011-260|boletins-000002-441|boletins-000004-1854|boletins-000004-2113|boletins-000009-1804|boletins-000007-749|boletins-000004-3565|boletins-000011-1212|boletins-000008-596|boletins-000009-1725|boletins-000010-80|boletins-000008-1527|boletins-000009-1276|boletins-000011-713|boletins-000007-747|boletins-000009-896|boletins-000003-2651|boletins-000003-714|boletins-000001-1149|boletins-000008-1058|boletins-000010-99|boletins-000010-1716|boletins-000008-1056|boletins-000008-823|boletins-000004-2069|boletins-000004-2577|boletins-000002-2451|boletins-000010-187|boletins-000011-1237|boletins-000004-2175|boletins-000004-3609|boletins-000007-785|boletins-000011-382|boletins-000001-2009|boletins-000001-1995|boletins-000010-86|boletins-000011-1408|boletins-000010-1787|boletins-000004-3576|boletins-000011-769|boletins-000010-1749|boletins-000001-1151|boletins-000008-548|boletins-000007-830|boletins-000008-835|boletins-000008-1788|boletins-000004-2092|boletins-000008-638|boletins-000001-50|boletins-000011-255|boletins-000011-1380|boletins-000009-2177|boletins-000009-2134|boletins-000011-491|boletins-000001-2014|boletins-000008-486|boletins-000011-1369|boletins-000009-1807|boletins-000011-1552|boletins-000008-696|boletins-000011-1497|boletins-000008-515|boletins-000004-2101|boletins-000001-3444|boletins-000002-2508|boletins-000010-1481|boletins-000006-636|boletins-000008-539|boletins-000001-1290|boletins-000011-445|boletins-000011-719|boletins-000002-2484|boletins-000008-707|boletins-000011-13|boletins-000011-706|boletins-000011-458|boletins-000011-702|boletins-000011-741|boletins-000009-1732|boletins-000011-383|boletins-000003-688|boletins-000011-727|boletins-000011-493|boletins-000009-1723|boletins-000011-360|boletins-000011-1301|boletins-000004-2099|boletins-000008-1774|boletins-000011-1141|boletins-000011-412|boletins-000001-1120|boletins-000011-494|boletins-000001-3451|boletins-000008-499|boletins-000008-816|boletins-000005-2160|boletins-000011-387|boletins-000002-543|boletins-000008-2001|boletins-000009-1256|boletins-000011-1468|boletins-000011-690|boletins-000011-1303|boletins-000009-2132|boletins-000011-716|boletins-000003-674|boletins-000008-1827|boletins-000011-441|boletins-000007-786|boletins-000001-1917|boletins-000001-1920|boletins-000004-3556|boletins-000004-3552|boletins-000009-1790|boletins-000011-1164|boletins-000011-1157|boletins-000011-206|boletins-000011-384|boletins-000011-345|boletins-000011-379|boletins-000008-1791|boletins-000011-131|boletins-000011-14|boletins-000008-872|boletins-000011-1402|boletins-000011-466|boletins-000004-3547|boletins-000010-1518|boletins-000009-1519|boletins-000010-1474|boletins-000011-310|boletins-000008-743|boletins-000011-800|boletins-000007-743|boletins-000004-3550|boletins-000001-3508|boletins-000011-1225|boletins-000008-1559|boletins-000009-2105|boletins-000011-94|boletins-000001-1287|boletins-000003-119|boletins-000011-474|boletins-000011-55|boletins-000011-558|boletins-000001-2378|boletins-000009-1727|boletins-000009-1803|boletins-000003-687|boletins-000011-456|boletins-000009-1306|boletins-000004-3582|boletins-000008-490|boletins-000009-819|boletins-000011-675|boletins-000004-2017|boletins-000010-113|boletins-000011-1147|boletins-000011-298|boletins-000008-623|boletins-000001-1281|boletins-000009-1333|boletins-000008-677|boletins-000009-1293|boletins-000011-746|boletins-000011-1324|boletins-000001-1141|boletins-000009-1521|boletins-000001-1868|boletins-000004-3920|boletins-000011-1165|boletins-000001-2372|boletins-000009-1406|boletins-000011-726|boletins-000011-1502|boletins-000008-660|boletins-000011-422|boletins-000001-3438|boletins-000011-217|boletins-000008-803|boletins-000011-1371|boletins-000011-766|boletins-000011-435|boletins-000011-1158|boletins-000001-2039|boletins-000010-1096|boletins-000008-915|boletins-000008-578|boletins-000011-342|boletins-000009-1712|boletins-000011-426|boletins-000011-92|boletins-000011-1481|boletins-000001-2339|boletins-000008-549|boletins-000011-392|boletins-000002-606|boletins-000011-1289|boletins-000011-472|boletins-000011-216|boletins-000007-791|boletins-000008-768|boletins-000011-263|boletins-000004-2150|boletins-000011-388|boletins-000008-799|boletins-000011-1219|boletins-000001-2173", sentence.sent_id ):
            token.deps = "I=CAMPO"
        if regex("B=CAMPO.*", token.deps) and regex("flat:name|nmod", token.deprel) and regex("de", token.previous_token.lemma) and regex("campo|Campo", token.previous_token.previous_token.lemma):
            token.deps = "I=CAMPO"
            token.previous_token.deps = "I=CAMPO"
        if regex("I=CAMPO", token.deps) and regex("O", token.previous_token.deps) and regex("de", token.previous_token.lemma):
            token.previous_token.deps = "I=CAMPO"

        # QUALIFICAÇÕES DO POÇO
        # TATI
        # 24/05/2022
        if regex("B=POÇO_Q", token.head_token.deps) and regex("conj", token.deprel):
            token.deps = "B=POÇO_Q"
        if regex("B=POÇO_T", token.head_token.deps) and regex("pioneiro|estratigráfico|estratigrafico|especial|explotatório|explotatorio", token.lemma) and regex("conj", token.deprel):
            token.deps = "B=POÇO_T"
        if regex("B=POÇO|I=POÇO", token.deps) and regex("de", token.next_token.lemma) and regex("produção|injeção", token.next_token.next_token.lemma):
            token.next_token.next_token.deps = "B=POÇO_R"
        if regex("B=POÇO|I=POÇO", token.head_token.deps) and regex("descobridor|comercial|subcomercial|sub-comercial|seco|portador|portar|abandonado|abandonar", token.lemma):
            token.deps = "B=POÇO_Q"
        if regex("B=POÇO|I=POÇO", token.head_token.deps) and regex("produtor|injetor", token.lemma):
            token.deps = "B=POÇO_R"
        if regex("pioneiro|estratigráfico|estratigrafico|especial|explotatório|explotatorio", token.lemma) and regex("B=POÇO", token.next_token.deps) and regex("O", token.deps):
            token.deps = "B=POÇO_T"
        if regex("B=POÇO", token.head_token.deps) and regex("pioneiro|estratigráfico|estratigrafico|especial|explotatório|explotatorio", token.lemma):
            token.deps = "B=POÇO_T"
        if regex("B=POÇO", token.head_token.deps) and regex("explotação|extensão|estocagem", token.lemma):
            token.deps = "B=POÇO_T"
        if regex("B=POÇO", token.deps) and regex("revelar", token.next_token.lemma) and regex("se", token.next_token.next_token.lemma) and regex("produtor", token.next_token.next_token.next_token.lemma) and regex("de", token.next_token.next_token.next_token.next_token.lemma) and regex("petróleo", token.next_token.next_token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deprel = "xcomp"
        if regex("Barra", token.lemma) and regex("de", token.next_token.lemma) and regex("Itiúba", token.next_token.next_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"


        # MCLARA BACIA 29/06/2022

        if regex("Alagoas", token.lemma) and regex("O", token.deps) and regex("Serraria", token.head_token.lemma) and regex("\/", token.next_token.lemma) and regex("Sergipe", token.next_token.next_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.next_token.deps = "B=BACIA"
            
        if regex("Maranhão", token.lemma) and regex("Amazônia", token.head_token.lemma) and regex("O", token.head_token.deps) and regex("bacia", token.head_token.head_token.lemma):
            token.deps = "B=BACIA"
            token.head_token.deps = "B=BACIA"
            
        if regex("Bacia", token.lemma) and regex("O", token.deps) and regex("Pernambuco-Paraíba", token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            
        if regex("O", token.deps) and regex("Bahia", token.lemma) and regex("Sul", token.next_token.lemma) and regex("bacia", token.head_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            
        if regex("Cabiúnas", token.lemma) and regex("O", token.deps) and regex("Bacia", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Camboriú", token.lemma) and regex("O", token.deps) and regex("Bacia", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Foz", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Amazonas", token.next_token.next_token.next_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            
        if regex("Gabão", token.lemma) and regex("O", token.deps) and regex("África", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("O", token.deps) and regex("Macacu", token.lemma) and regex("São", token.head_token.lemma) and regex("I=BACIA", token.head_token.deps):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Maranhão", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Paraíba", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia", token.head_token.lemma) and regex("Pernambuco\-Paraíba", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Pernambuco\-Paraiba", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Recôncavo\-Tucano", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Santos/Campos", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Francisco", token.lemma) and regex("São", token.previous_token.lemma):
            token.deps = "I=BACIA"
            token.previous_token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Sergipe/Alagoas", token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Camumu|Almada", token.lemma) and regex("B=BACIA", token.deps) and regex("Sergipe\-Alagoas", token.head_token.lemma):
            token.head_token.deps = "B=BACIA"
            
        if regex("PROPN", token.upos) and regex("O", token.deps) and regex("bacia|Bacia|Bacias", token.head_token.lemma) and regex("Sergipe\-Alagoas", token.lemma) and regex("de", token.previous_token.lemma) and regex("sedimentar", token.previous_token.previous_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Gabão", token.lemma) and regex("O", token.deps) and regex("Cuanza", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Bacia", token.lemma) and regex("O", token.deps) and regex("Sergipe\-Alagoas", token.next_token.lemma):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"

        # mclara 06-07-2022

        if regex("Alagoas", token.lemma) and regex("O", token.deps) and regex("[aA]ndar|[aA]ndares|[iI]dade|[eE]stágio|[tT]opo", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("[mM]eso\-[rR]io|[nN]eo\-[rR]io", token.lemma) and regex("O", token.deps) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Eo", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Atokano|Cenomaniano|Cenozóico|Cenozóicos|Cretácea|cretácico|[dD]esmoinesiano|Eojiquiá|Eomesoalbiano|eo\-mesoalbiano|Eoturoniano|Jiquiá|Kunguriano|Lutetiano|Maastrichtiano|Mesoalagoas|Mesoalbiano|[nN]eo\-[aA]lagoas|Neo\-aptiano|[nN]eocomiano|neocretácico|Neodevoniana|Neomesoalbiano|neopaleozóico|neopermiano|Oligoceno|Ordoviciano-Devoniano|Paleoceno|Paleozóica|Permiano|Pliensbaquiano|pliocênico|[pP]ré\-[aA]lagoas|[pP]ós\-[aA]lagoas|[pP]ré\-[aA]ratu|Pré\-Cambriana|Aptiana|Santoniano|Turoniano|Valanginiano", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("eo/meso\-albiano|albo\-cenomaniano|Maestrichtiano|turoniano\-sansoniano|santoniano\-panemianianiano|santoniano\-maastranstriano|santoniano\-campaniano|pré\-cenomaniano|pré\-westphaliano|ordovício\-siluriano|neosinemuriano|pré\-albiano|intra\-Maestrichtiano|eomaastrichtiano|eopermiano|neosinemuriano|intra\-Devoniano|cenomaniano\-santoniano|coniaciano\-maastrantiano|eo\-/meso\-albiano|eo\-cambriano|cambro\-ordoviciano|albiano\-cenomaniano|Valengiano|Turoniano\-Campaniano|Santoniano/Turoniano|Neo\-albiano\-Eocenomaniano|Neo\-albiano\-Eoturoniano|albo\-santoniano|Albo\-Cenomaniano|Barremiano/Aptiano|Eohauteriviano|Eopermiano|Neo\-Aibiano|Paleoceno\-Eoceno", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("de", token.lemma) and regex("O", token.deps) and regex("o", token.next_token.lemma) and regex("O", token.next_token.deps) and regex("Serra", token.next_token.next_token.lemma) and regex("O", token.next_token.next_token.deps) and regex("Rio", token.previous_token.lemma) and regex("B=UNIDADE_CRONO", token.previous_token.deps):
            token.deps = "I=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("[iI]nferior|[sS]uperior|[mM]édio|[fF]inal|[tT]erminal|[Ii]nicial", token.word) and regex("O", token.deps) and regex(".*=UNIDADE_CRONO", token.previous_token.deps):
            token.deps = "I=UNIDADE_CRONO"

        if regex("Buracica", token.lemma) and regex("O", token.deps) and regex("[iI]dade|[aA]ndar|[aA]ndares", token.head_token.lemma) and regex("Inferior", token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Aratu|Buracica|Jequiá", token.lemma) and regex("Rio", token.head_token.lemma) and regex("estágio", token.head_token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Aratu|Jiquiá|Buracica", token.lemma) and regex("Dom", token.head_token.lemma) and regex("[aA]ndar", token.head_token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Buracica|Aratu", token.lemma) and regex("O", token.deps) and regex(".*=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Buracica", token.lemma) and regex("[iI]nferior|[sS]uperior", token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Dom", token.lemma) and regex("[aA]ndar", token.head_token.lemma) and regex("O", token.deps) and regex("João", token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("Rio", token.lemma) and regex("estágio|[aA]ndar", token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Rio", token.lemma) and regex("Dom", token.head_token.lemma) and regex("andar", token.head_token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("Inferior", token.next_token.next_token.next_token.next_token.lemma):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("Rio", token.lemma) and regex("Dom", token.head_token.lemma) and regex("andar", token.head_token.head_token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Serra", token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Serra", token.lemma) and regex("O", token.deps) and regex("o", token.previous_token.lemma) and regex("O", token.previous_token.deps) and regex("de", token.previous_token.previous_token.lemma) and regex("O", token.previous_token.previous_token.deps) and regex("[iI]dade", token.head_token.lemma):
            token.deps = "I=UNIDADE_CRONO"
            token.previous_token.deps = "I=UNIDADE_CRONO"
            token.previous_token.previous_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Aratu", token.lemma) and regex("o", token.previous_token.lemma) and regex("para|desde", token.previous_token.previous_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Mesozóica", token.lemma) and regex("Bacia", token.head_token.lemma):
            token.deps = "B=UNIDADE_CRONO"

        # MCLARA 11/07/2022

        if regex("O", token.deps) and regex("Missão", token.lemma) and regex("Velha", token.next_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Serraria", token.lemma) and regex("O", token.deps) and regex("em", token.next_token.word) and regex("Alagoas", token.next_token.next_token.word):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Coqueiro", token.lemma) and regex("O", token.deps) and regex("Seco", token.next_token.lemma) and regex(".*=UNIDADE_LITO", token.head_token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Campo", token.lemma) and regex("O", token.deps) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Tenente", token.next_token.next_token.next_token.lemma) and regex("[gG]rupo", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Espírito", token.lemma) and regex("O", token.deps) and regex("Santo", token.next_token.lemma) and regex("[gG]rupo", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Rio", token.lemma) and regex("O", token.deps) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Sul", token.next_token.next_token.next_token.lemma) and regex("[gG]rupo", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Amaro", token.lemma) and regex("O", token.deps) and regex("[gG]rupo", token.head_token.lemma):
            token.deps = "I=UNIDADE_LITO"
            
        if regex("Mcg", token.lemma) and regex("O", token.deps) and regex("[mM]embro", token.previous_token.lemma):
            token.deps = "I=UNIDADE_LITO"
            token.previous_token.deps = "B=UNIDADE_LITO"
            
        if regex("CC|Cabo", token.lemma) and regex("O", token.deps) and regex("Carvoeiro|Blanco|1|2", token.next_token.lemma) and regex("[mM]embro", token.head_token.lemma):
            token.deps = "I=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            
        if regex("Triunfo|Mcup|Ballena|Carapebus|Ilha\-bela|Polvoeira|Macabu|Coqueiros|Coqueiros|Lontras|Mcnb", token.lemma) and regex("O", token.deps) and regex("[mM]embro", token.head_token.lemma):
            token.deps = "I=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            
        if regex("Verde|Constancia|Paraguaçu|Siderópolis|Mcg", token.lemma) and regex("O", token.deps) and regex("[mM]embro", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Somatito", token.lemma) and regex("O", token.deps) and regex("Inferior|Superior", token.next_token.lemma) and regex("[mM]embro", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"

        if regex("Mesozóicas\-Cenozóicas|Mesozóicas\-Ceno\-zóicas", token.word) and regex("I=BACIA", token.deps) and regex("Bacias", token.previous_token.lemma):
            token.lemma = "Mesozóicas-Cenozóicas"
            token.deps = "B=UNIDADE_CRONO"

        if regex("Morrowano", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("[Ss]istemas?", token.lemma) and regex("Deposicionais|Tectônico|Almirante|MgO\-Si05\-H5O0\/CO>|N20\-30E|Riedel|CG-EM|EW|DOS|CH4-H2O-NaCl|ChemRock|Petrolíferos?|Recôncavo|H\<UNK\>O|Fraturas|Lamoso|Petrobrás|Regressivo", token.next_token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"

        if regex("[Ss]istema", token.lemma) and regex("de", token.next_token.lemma) and regex("Riftes|Dobramentos", token.next_token.next_token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("FORMAÇÕES", token.lemma) and regex("Santana", token.next_token.lemma) and token.deps == "O":
            token.lemma = "formação"
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"

        if regex("BACIA", token.word) and regex("DE", token.next_token.word) and regex("O", token.next_token.next_token.word) and regex("ARARIPE", token.next_token.next_token.next_token.word) and token.deps == "O":
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"

        if regex("BACIA", token.word) and regex("DE", token.next_token.word) and regex("O", token.next_token.next_token.word) and regex("PARANA", token.next_token.next_token.next_token.word) and token.deps == "O":
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"

        if token.word == "IRATI" and token.head_token.word == "SANTANA" and token.deprel == "conj" and token.deps == "O":
            token.deps = to_b(token.head_token.deps)

        if regex("Bahia", token.lemma) and regex("[Ss]éries?", token.head_token.lemma) and regex("B=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("pré\-Alagoas|jurássico\-cretáceo|juro\-cretáceo|ordoviciana\-cretácico|neoaptiano|turoniano-santoniano|permocarbonífero|holocênico|albo\-cenomaniano|jurocretáceo|neo\-jurássica|morrowano|pleistocênica|pleistocênico", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        # MCLARA 29/08/2022
        if regex("P44", token.lemma) and regex("O", token.deps):
            token.deps = "B=POÇO"

        if regex("Açu\-1|Açu\-2|Açu\-3|Açu\-4", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"

        if regex("unidade", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Jiquiá", token.next_token.next_token.next_token.lemma) and regex("O", token.next_token.next_token.next_token.deps) and regex("Superior", token.next_token.next_token.next_token.next_token.lemma):
            token.next_token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("unidade", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Permiano", token.next_token.next_token.next_token.lemma) and regex("O", token.next_token.next_token.next_token.deps):
            token.next_token.next_token.next_token.deps = "B=UNIDADE_CRONO"

        if regex("Morrowano|Atokano", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("[Ff]oliação", token.lemma) and regex("O", token.deps):
            token.deps = "B=ESTRUTURA_FÍSICA"

        # TATI
        # 08/09/2022

        if regex("B=UNIDADE_CRONO|B=UNIDADE_LITO", token.deps) and regex("gerador", token.head_token.lemma):
            token.head_token.deps = "B=ELEMENTO_PETRO"

        # MCLARA 29/09/2022

        #GÁS leva de dúvidas de agosto (08/22) - fluidodaterra_o

        if regex("nobre|carbônico", token.lemma) and regex("gás", token.head_token.lemma) and regex("B=FLUIDODATERRA_i", token.head_token.deps):
            token.deps = "I=FLUIDODATERRA_o"
            token.head_token.deps = "B=FLUIDODATERRA_o"
            
        #GÁS leva de dúvidas de julho (07/22) - fluidodaterra_o

        if regex("superaquecer", token.lemma) and regex("gás", token.head_token.lemma) and regex("B=FLUIDODATERRA_i", token.head_token.deps):
            token.head_token.deps = "B=FLUIDODATERRA_o"

        if regex("óleo", token.lemma) and regex("diesel", token.next_token.lemma) and regex("B=FLUIDODATERRA_i", token.deps):
            token.deps = "B=FLUIDO"
            token.next_token.deps = "I=FLUIDO"

        # MCLARA 07/10/2022

        if regex("M\’", token.word) and regex("Vone", token.next_token.word) and regex("B=BACIA", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Plataforma", token.word) and regex("de", token.next_token.word) and regex("Natal", token.next_token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"

        if regex("Andar", token.word) and regex("B=UNIDADE_CRONO", token.deps) and regex("Dom", token.next_token.word) and regex("João", token.next_token.next_token.word) and regex("O", token.next_token.next_token.deps):
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"         

        if regex("Oligo\-Mioceno", token.word) and regex("B=CAMPO", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Plataforma", token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"

        # MCLARA 10/10/2022

        if regex("Af\,", token.word) and regex("B=UNIDADE_LITO", token.deps) and regex("Permiano", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("grupo", token.lemma) and regex("B=UNIDADE_LITO", token.deps) and regex("I", token.next_token.word):
            token.deps = "O"
            
        if regex("Terreno", token.word) and regex("Paranaguá", token.next_token.word) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Botucatu/", token.word) and regex("Pirambóia", token.next_token.word) and regex("I=UNIDADE_LITO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_LITO"

        # MCLARA 18/10/2022

        if regex("Albiano|Barremiano|Turoniano|Neocretáceo", token.word) and regex("\–|\/", token.next_token.word) and regex("Turoniano|Aptiano|Maastrichtiano|Santoniano|Cenozóico", token.next_token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.next_token.deps):
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "O"

        if regex("Campaniano", token.word) and regex("–", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "O"

        if regex("Coniaciano", token.word) and regex("Neocampaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deprel = "conj"
            token.next_token.deps = "B=UNIDADE_CRONO"

        if regex("Recente", token.word) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"

        if regex("Coniaciano/", token.word) and regex("Santoniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.lemma = "Coniaciano"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Mesozóicas", token.word) and regex("\-Cenozóicas", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.lemma = "Cenozóicas"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Neo\-albiano", token.word) and regex("\-Cenomaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.lemma = "Cenomaniano"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("neocomiana/", token.word) and regex("barremiana", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("neocomiana/", token.word) and regex("eobarremiana", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Neojurássico", token.word) and regex("\-Eocretáceo", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.lemma = "Eocretáceo"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Oligoceno", token.word) and regex("\-Mioceno", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.lemma = "Mioceno"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Pleistoceno\/", token.word) and regex("Holoceno", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.lemma = "Pleistoceno"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("santoniana\-coniaciana\/", token.word) and regex("turoniana", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Santoniano", token.word) and regex("\-Campaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.lemma = "Campaniano"
            token.next_token.deps = "B=UNIDADE_CRONO"

        if regex("Coniaciano\/", token.word) and regex("Santoniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.lemma = "Coniaciano"
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Coniaciano", token.word) and regex("Neocampaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Cretáceo", token.word) and regex("Marinho", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "O"
            
        if regex("Cretáceo", token.word) and regex("pós\-", token.next_token.word) and regex("Aptiano", token.next_token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Mesozóicas", token.word) and regex("\-Cenozóicas", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.lemma = "Cenozóicas"
            
        if regex("Neo\-albiano", token.word) and regex("\-Cenomaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.lemma = "Cenomaniano"
            
        if regex("Neo\-eoceno\/", token.word) and regex("Oligoceno\/", token.next_token.word) and regex("Eomioceno", token.next_token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.lemma = "Neo-eoceno"
            token.next_token.lemma = "Oligoceno"
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Santoniano", token.word) and regex("\-Campaniano", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.lemma = "Campaniano"

        if regex("Discordância", token.word) and regex("de", token.next_token.word) and regex("Propagação", token.next_token.next_token.word) and regex("de", token.next_token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.next_token.word) and regex("Rifte", token.next_token.next_token.next_token.next_token.next_token.word) and regex("I=ESTRUTURA_FÍSICA", token.next_token.deps):
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.next_token.deps = "O"
            
        if regex("Discordância", token.word) and regex("pré-Ubarana", token.next_token.word) and regex("I=ESTRUTURA_FÍSICA", token.next_token.deps):
            token.next_token.deps = "O"
            
        if regex("Pai", token.word) and regex("Vitório", token.next_token.word) and regex("Falha", token.head_token.word) and regex("I=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"

        #REVISÃO CAMPO

        if regex("Rio", token.word) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Serra", token.next_token.next_token.next_token.word) and regex("Inferior|Médio", token.next_token.next_token.next_token.next_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        #ESTRUTURA_FÍSICA

        if regex("fraturas", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("tipo", token.next_token.next_token.next_token.word) and regex("\»", token.next_token.next_token.next_token.next_token.lemma) and regex("R|T", token.next_token.next_token.next_token.next_token.next_token.word) and regex("\»", token.next_token.next_token.next_token.next_token.next_token.next_token.lemma) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"
            
        if regex("fraturas", token.word) and regex("de", token.next_token.word) and regex("o", token.next_token.next_token.word) and regex("Tipo", token.next_token.next_token.next_token.word) and regex("I|II", token.next_token.next_token.next_token.next_token.word) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.next_token.next_token.next_token.next_token.deps = "I=ESTRUTURA_FÍSICA"

        # TATI 4/11/22

        if regex("anidrita", token.lemma) and regex("I=ROCHA", token.deps):
            token.deps = "B=ROCHA"

        if regex("folhelho", token.lemma) and regex("I=ROCHA", token.deps):
            token.deps = "B=ROCHA"

        if regex("siltito", token.lemma) and regex("I=ROCHA", token.deps):
            token.deps = "B=ROCHA"

        # MCLARA 8/11/22

        if regex("Falha", token.lemma) and regex("flat:name", token.next_token.deprel) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.next_token.deps = "O"

        #unidade crono - 07/11/22

        if regex("carbonifera/", token.word) and regex("cambriana", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
                
        if regex("Berriasiano|Alagoas|Buracica", token.lemma) and regex("Rio", token.head_token.lemma) and regex("de", token.head_token.next_token.lemma) and regex("o", token.head_token.next_token.next_token.lemma) and regex("Serra", token.head_token.next_token.next_token.next_token.lemma) and regex("B=CAMPO", token.head_token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.head_token.deps = "B=UNIDADE_CRONO"
            token.head_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                
        if regex("Rio", token.word) and regex("de", token.next_token.word) and regex("a", token.next_token.next_token.word) and regex("Serra", token.next_token.next_token.next_token.word) and regex("Médio", token.next_token.next_token.next_token.next_token.word):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
                
        if regex("permiana/", token.word) and regex("carbonifera", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
                
        #bacia - 07/11/22

        if regex("Santos/Campos/", token.word) and regex("Espírito", token.next_token.word) and regex("Santo", token.next_token.next_token.word) and regex("I=BACIA", token.next_token.deps):
            token.next_token.deps = "B=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
                
        #campo mourão não é campo

        if regex("Campo", token.word) and regex("Mourão", token.next_token.word) and regex("B=CAMPO", token.deps) and regex("Zonas", token.head_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
                
        #campo de Catu - Catu é uni lito

        if regex("campo", token.word) and regex("de", token.next_token.word) and regex("Catu", token.next_token.next_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "B=UNIDADE_LITO"

        if regex("Camboriú", token.word) and regex("Formação", token.head_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"

        #regras para Catu - 22/03/2023

        if regex("oleo-duto", token.word) and regex(",", token.next_token.word) and regex("de", token.next_token.next_token.word) and regex("Catu", token.next_token.next_token.next_token.word):
            token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
            
        if regex("de", token.word) and regex("o", token.next_token.word) and regex("tipo", token.next_token.next_token.word) and regex("Carmópolis", token.next_token.next_token.next_token.word) and regex(",", token.next_token.next_token.next_token.next_token.word) and regex("Catu", token.next_token.next_token.next_token.next_token.next_token.word) and regex("ou", token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("D.", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word) and regex("João", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=UNIDADE_LITO"
            token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"

        # MCLARA
        # unidade_crono 28/11/2022

        if regex("Alagoas", token.lemma) and regex("pré\-Alagoas", token.next_token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Aratu", token.lemma) and regex("O", token.deps) and regex("Rio", token.head_token.word) and regex(".*=UNIDADE_CRONO", token.head_token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Buracica", token.lemma) and regex("Rio", token.head_token.lemma) and regex("de", token.head_token.next_token.lemma) and regex("o", token.head_token.next_token.next_token.lemma) and regex("Serra", token.head_token.next_token.next_token.next_token.lemma) and regex("B=CAMPO", token.head_token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.head_token.deps = "B=UNIDADE_CRONO"
            token.head_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Dom", token.lemma) and regex("João", token.next_token.lemma) and regex("estágio", token.head_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("Almirante", token.lemma) and regex("sistema", token.head_token.lemma) and regex("B=UNIDADE_CRONO", token.head_token.deps):
            token.head_token.deps = "O"
            
        if regex("Alagoas", token.lemma) and regex("Aptiano|durante|Cronoestratigrafia|neocomianos", token.previous_token.previous_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Alagoas", token.lemma) and regex("terminando|cronoestratigráfico|Ma|final", token.previous_token.previous_token.previous_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Buracica", token.lemma) and regex("seção|Meso\-Rio", token.head_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Alagoas", token.lemma) and regex("pós\-|tempo", token.previous_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"

        if regex("Alagoas", token.lemma) and regex("Rio", token.head_token.lemma) and regex("de", token.head_token.next_token.lemma) and regex("o", token.head_token.next_token.next_token.lemma) and regex("Serra", token.head_token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.head_token.deps = "B=UNIDADE_CRONO"
            token.head_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        if regex("Jiquiá", token.lemma) and regex("Superior", token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Berriasiano", token.lemma) and regex("Rio", token.head_token.lemma) and regex("de", token.head_token.next_token.lemma) and regex("o", token.head_token.next_token.next_token.lemma) and regex("Serra", token.head_token.next_token.next_token.next_token.lemma) and regex("B=CAMPO", token.head_token.deps):
            token.head_token.deps = "B=UNIDADE_CRONO"
            token.head_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            token.head_token.next_token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        #unidade_lito 28/11/2022

        if regex("Muribeca|Calumbi", token.lemma) and regex("O", token.deps) and regex("Piaçabuçu", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Piaçabuçu|Urucutuca|Pirarucu", token.lemma) and regex("O", token.deps) and regex("Bacia|Espírito|Foz", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"

        #bacia 28/11/2022

        if regex("Foz", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Amazonas", token.next_token.next_token.next_token.lemma) and regex("Espírito", token.head_token.lemma) and regex("Santo", token.head_token.next_token.lemma) and regex("Urucutuca", token.head_token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            token.head_token.deps = "B=BACIA"
            token.head_token.next_token.deps = "I=BACIA"
            
        if regex("Camamu-Almada", token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"

        if regex("Jequitinhonha", token.lemma) and regex("Espírito", token.head_token.lemma) and regex("Santo", token.head_token.next_token.lemma) and regex("O", token.head_token.deps):
            token.head_token.deps = "B=BACIA"
            token.head_token.next_token.deps = "I=BACIA"

        #campo 28/11/2022

        if regex("Rio", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Ovos", token.next_token.next_token.next_token.lemma) and regex("O", token.deps) and regex("Dom", token.head_token.lemma):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.deps = "I=CAMPO"
            token.next_token.next_token.next_token.deps = "I=CAMPO"
            
        if regex("Dom", token.lemma) and regex("João", token.next_token.lemma) and regex("campos", token.head_token.word) and regex("O", token.deps):
            token.deps = "B=CAMPO"
            token.next_token.deps = "I=CAMPO"
        
        # MCLARA
        #campo - ubarana 01/12/2022

        if regex("Ubarana", token.lemma) and regex("[Zz]ona", token.head_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            
        if regex("Ubarana", token.lemma) and regex("[Cc]anyon|[Cc]anyons", token.head_token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"

        # MCLARA
        #bacia - 10/12/2022

        if regex("Barreirinhas|Alagoas", token.lemma) and regex("trabalhos", token.head_token.word) and regex("os", token.head_token.previous_token.word) and regex("em", token.head_token.next_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Sergipe/Alagoas|sub-bacia", token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"

            
        if regex("Maranhão", token.lemma) and regex("Pará", token.head_token.lemma) and regex("bacia", token.head_token.head_token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.head_token.deps = "B=BACIA"
            
        if regex("Bacias", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Amazonas", token.next_token.next_token.next_token.lemma) and regex("I=UNIDADE_CRONO", token.deps):
            token.deps = "B=BACIA"
            token.next_token.deps = "I=BACIA"
            token.next_token.next_token.deps = "I=BACIA"
            token.next_token.next_token.next_token.deps = "I=BACIA"
            
        if regex("Sergipe-Alagoas", token.lemma) and regex("Recôncavo-Tucano", token.head_token.lemma) and regex("aparecera", token.head_token.head_token.word) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.head_token.deps = "B=BACIA"
            
        if regex("Espirito", token.lemma) and regex("B=BACIA", token.deps) and regex("Campos", token.head_token.lemma) and regex("O", token.head_token.deps):
            token.head_token.deps = "B=BACIA"
            
        if regex("Gabão", token.lemma) and regex("O", token.deps) and regex("M\’", token.head_token.lemma) and regex(".*=UNIDADE_LITO", token.head_token.deps):
            token.deps = "B=BACIA"

        if regex("Maranhão", token.lemma) and regex("área", token.head_token.lemma) and regex("poço", token.head_token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            
        if regex("Pará", token.lemma) and regex("B=POÇO", token.head_token.deps) and regex("O", token.deps) and regex("Maranhão", token.head_token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Congo", token.lemma) and regex("Gabão", token.head_token.lemma) and regex("Cocobeach", token.head_token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.head_token.deps = "B=BACIA"
            
        if regex("Jacuípe", token.lemma) and regex("Alagoas", token.head_token.lemma) and regex("até", token.previous_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            
        if regex("Almada", token.lemma) and regex("[Cc]anyon", token.head_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            
        if regex("Pernambuco-Paraíba", token.lemma) and regex("O", token.deps) and regex("segmento", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Piauí", token.lemma) and regex("O", token.deps) and regex("Ceará", token.head_token.lemma) and regex("bacia", token.head_token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("o", token.lemma) and regex("Amazonas", token.next_token.lemma) and regex("ser", token.next_token.next_token.lemma) and regex("gigantesco", token.next_token.next_token.next_token.lemma) and regex("B=BACIA", token.next_token.deps):
            token.next_token.deps = "O"
            
        if regex("Recôncavo-Tucano-Jatobá", token.lemma) and regex("O", token.deps) and regex("Riftes", token.previous_token.lemma) and regex("sistema", token.previous_token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Sistema", token.lemma) and regex("de", token.next_token.lemma) and regex("Riftes", token.next_token.next_token.lemma) and regex("Recôncavo", token.next_token.next_token.next_token.lemma) and regex("Tucano", token.next_token.next_token.next_token.next_token.next_token.lemma) and regex("Jatobá", token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.next_token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
            token.next_token.next_token.next_token.next_token.next_token.next_token.next_token.deps = "B=BACIA"
            
        if regex("Sergipe-Alagoas", token.lemma) and regex("O", token.deps) and not regex("S\.", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Santos", token.lemma) and regex("Sul", token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            
        if regex("Alagoas/Sergipe", token.lemma) and regex("O", token.deps) and regex("subgrupo", token.head_token.lemma):
            token.deps = "B=BACIA"
            
        if regex("Jatobá", token.lemma) and regex("Tucano", token.head_token.lemma) and regex("B=BACIA", token.head_token.deps) and regex("O", token.deps):
            token.deps = "B=BACIA"
            
        if regex("Maranhão", token.lemma) and regex("Médio", token.head_token.lemma) and regex("Amazonas", token.head_token.next_token.lemma) and regex("B=BACIA", token.head_token.next_token.deps) and regex("O", token.deps):
            token.deps = "B=BACIA"
            
        if regex("Tucano", token.lemma) and regex("Jatobá", token.next_token.next_token.lemma) and regex("Recôncavo", token.previous_token.previous_token.lemma) and regex("sistema", token.previous_token.previous_token.previous_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            token.next_token.next_token.deps = "B=BACIA"
            token.previous_token.previous_token.deps = "B=BACIA"
            
        if regex("bacia", token.lemma) and regex("marginal", token.next_token.lemma) and regex("brasileiro", token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=BACIA"
            
        #estrutura_física - 10/12/2022

        if regex("N30E", token.lemma) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"
            
        if regex("Salvador", token.lemma) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"
            
        if regex("discordância", token.lemma) and regex("O", token.deps) and regex("falha", token.head_token.lemma):
            token.deps = "B=ESTRUTURA_FÍSICA"
            
        #rocha - 10/12/2022

        if regex("[Gg]ouge|[Rr]ocha", token.lemma) and regex("de", token.next_token.lemma) and regex("falha", token.next_token.next_token.lemma) and regex("O", token.next_token.next_token.deps):
            token.deps = "B=ROCHA"
            token.next_token.deps = "I=ROCHA"
            token.next_token.next_token.deps = "I=ROCHA"
            
        #unidade_crono - 10/12/2022

        if regex("Cenozóico|Cenozóicos|Kunguriano|Lutetiano|Bendian|Lampasan|Derryan|Morrowano|Atokano|Morrowano/Atokano|Morrowan|Pré\-Cambriana|Oligoceno|Maestrichtiano|Valanginiano|Mesoalbiano|Permiano|Cenomaniano|Maastrichtiano|cenozóico|Turoniano|Santoniano|meso-zóico", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Cretácio|Terciário", token.lemma) and regex("T", token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("de", token.lemma) and regex("o", token.next_token.lemma) and regex("Amazônia", token.next_token.next_token.lemma) and regex(".*=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            
        if regex("Bahia", token.lemma) and regex("série", token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.lemma) and regex("B=UNIDADE_CRONO", token.previous_token.previous_token.previous_token.previous_token.previous_token.previous_token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Eoturoniano", token.lemma) and regex("inicial", token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("idade", token.lemma) and regex("neocomiana|neosinemuriana|pré-aptiana|cambro-ordoviciana|eo-mesoalbiana|eopermiana|pré-Aratu|terciária", token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("idade", token.lemma) and regex("pós-", token.next_token.word) and regex("Campaniano", token.next_token.next_token.word) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Plioceno", token.lemma) and regex("Jiquia", token.head_token.lemma) and regex("Superior", token.head_token.next_token.lemma) and regex("O", token.head_token.deps):
            token.head_token.deps = "B=UNIDADE_CRONO"
            token.head_token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("Médio", token.lemma) and regex("Pensilvaniano", token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Protero-zóico|Terciário", token.lemma) and regex("Médio|Inicial|Superior", token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            token.next_token.deps = "I=UNIDADE_CRONO"
            
        if regex("o|período", token.lemma) and regex("Terciário", token.next_token.lemma) and regex("O", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("Terciário", token.lemma) and regex("Formação", token.head_token.lemma) and regex("Barreiras", token.head_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_CRONO"
            
        if regex("Atokan|Desmoinesian|Missourian|Virgilian", token.lemma) and regex("O", token.deps) and not regex("Formation", token.next_token.word):
            token.deps = "B=UNIDADE_CRONO"
            
        #unidade_lito - 10/12/2022

        if regex("Cabo", token.lemma) and regex("Carvoeiro", token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Cocobeach", token.lemma) and regex("inferior", token.next_token.word) and regex("grupo", token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Formação", token.lemma) and regex("Sergi", token.next_token.lemma) and regex("O", token.next_token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            
        if regex("Maria", token.lemma) and regex("Farinha", token.next_token.lemma) and regex("Gramame", token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.head_token.deps = "B=UNIDADE_LITO"
            
        if regex("Lemede", token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Mcg", token.lemma) and regex("O", token.deps) and regex("membro", token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Mcup", token.lemma) and regex("O", token.deps) and regex("membro", token.head_token.head_token.lemma):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Sergi", token.lemma) and regex("salientar", token.head_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            
        if regex("Vale", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("fonte", token.next_token.next_token.next_token.lemma) and regex("O", token.deps):
            token.deps = "B=UNIDADE_LITO"
            token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.deps = "I=UNIDADE_LITO"
            token.next_token.next_token.next_token.lemma = "Fontes"

        # ELVIS 14/12/2022
        # PÓS PLANILHA DE GRAFIAS ALTERNATIVAS QUE PATRÍCIA RETORNOU
        if token.lemma == "magma" and token.deps == "B=NÃOCONSOLID":
            token.deps = "B=ROCHA"

        # TATI 16/12/2022

        if regex("B=CAMPO.*", token.deps) and regex("flat:name|nmod", token.deprel) and regex("de", token.previous_token.previous_token.lemma) and regex("o|a", token.previous_token.lemma) and regex("campo|Campo", token.head_token.lemma):
            token.deps = "I=CAMPO"
            token.previous_token.previous_token.deps = "I=CAMPO"
            token.previous_token.deps = "I=CAMPO"

        if regex("B=POÇO", token.deps) and regex("1-", token.next_token.lemma) and regex("RJS-587", token.next_token.next_token.lemma):
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"

        if regex("B=POÇO_T", token.deps) and regex("1-", token.next_token.lemma) and regex("RJS-587", token.next_token.next_token.lemma):
            token.next_token.deps = "B=POÇO"
            token.next_token.next_token.deps = "I=POÇO"

        # MCLARA
        #campo - 13/12/2022

        if regex("São", token.lemma) and regex("Mateus", token.next_token.lemma) and regex("B=CAMPO", token.deps) and regex("Forte", token.head_token.lemma) and regex("Região", token.head_token.head_token.lemma):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Redonda", token.lemma) and regex("B=CAMPO", token.deps) and regex("Resende-Volta", token.head_token.lemma) and regex("Gráben", token.head_token.head_token.lemma):
            token.deps = "O"
            
        #estrutura_física - 13/12/2022

        if regex("Guaiaquil", token.lemma) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"

        # MCLARA 23/12/2022

        #unidade_crono - 23/12/2022

        if regex("[Ss]istema", token.lemma) and regex(".*=UNIDADE_CRONO", token.deps):
            token.deps = "O"

        # MCLARA E TATI 20/01/23
        #unidade_crono - 16/01/2023 (planilha de novas entidades)
        if regex("neocomiana/", token.word) and regex("barremiana|eobarremiana", token.next_token.word) and regex("I=UNIDADE_CRONO", token.next_token.deps):
            token.next_token.deps = "B=UNIDADE_CRONO"
            
        if regex("N’Dombo|Bahia|Fusulinella", token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            
        if regex("[Ii]dade|Idades|[Ss]érie|Séries", token.lemma) and regex("Rb-Sr|Ar/Ar|K/Ar|Potássio|[cC]ocobeach|Fusiella|Recôncavo", token.next_token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Siluriano|Pré-cambriano|Carbonifero|Carbonífero|Cretáceo|Daniano|neocretácea|Oligoceno|Quaternário|Tortoniano", token.lemma) and regex("Superior|Inferior|Médio|inferior", token.next_token.word) and regex("B=UNIDADE_CRONO", token.deps):
            token.next_token.deps = "O"
            
        if regex("idade", token.lemma) and regex("Permiano|Westphaliana", token.next_token.lemma) and regex("Inferior|Superior", token.next_token.next_token.word) and regex("B=UNIDADE_CRONO", token.deps):
            token.next_token.next_token.deps = "O"
            
        if regex("[sS]érie", token.lemma) and regex("de", token.next_token.lemma) and regex("o", token.next_token.next_token.lemma) and regex("Recôncavo", token.next_token.next_token.next_token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            
        if regex("série", token.lemma) and regex("de", token.next_token.lemma) and regex("M’Vone", token.next_token.next_token.lemma) and regex("B=UNIDADE_CRONO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            
        #unidade_lito - 16/01/2023 (planilha de novas entidades)

        if regex("Formação", token.lemma) and regex("Macaé", token.next_token.lemma) and regex("Inferior|Superior", token.next_token.next_token.word) and regex("B=UNIDADE_LITO", token.deps):
            token.next_token.next_token.deps = "O"
            
        if regex("Membro", token.lemma) and regex("Triunfo\-", token.next_token.lemma) and regex("PUNCT", token.next_token.next_token.upos) and regex("inferior", token.next_token.next_token.next_token.word) and regex("PUNCT", token.next_token.next_token.next_token.next_token.upos) and regex("B=UNIDADE_LITO", token.deps):
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
            
        if regex("Formação", token.lemma) and regex("Abadia", token.next_token.lemma) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        #bacia - 16/01/2023 (planilha de entidades novas)

        if regex("Bacia|Rio", token.lemma) and regex("Chaco-Paraná|Ribeira", token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Bacia", token.lemma) and regex("de", token.next_token.lemma) and regex("Iguape", token.next_token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            
        if regex("Bacia", token.lemma) and regex("Sergi", token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("bacia", token.lemma) and regex("hidrográfico", token.next_token.lemma) and regex("B=BACIA", token.deps):
            token.deps = "O"
            
        #campo - 16/01/2023 (planilha das novas entidades)

        if regex("Fazenda", token.lemma) and regex("Olho|Maria|Caritá|Rivadávia", token.next_token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("Jaraqui|Jutaí", token.lemma) and regex("B=CAMPO", token.deps):
            token.deps = "O"

            
        #estrutura_física - 16/01/2023 (planilha das novas entidades)

        if regex("interlaminação", token.lemma) and regex("wavy", token.head_token.lemma) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"
            token.head_token.deps = "B=ESTRUTURA_FÍSICA"
            
        #rocha - 16/01/2023 (planilha das novas entidades)

        if regex("[lL]amito|[Mm]arga|[Tt]ufo", token.lemma) and regex("calcífero|cinza|calcário|vulcânico", token.next_token.lemma) and regex("I=ROCHA", token.next_token.deps):
            token.next_token.deps = "O"
            
        #poço - 16/01/2023 (planilha de novas entidades)

        if regex("4SPS", token.word) and regex("0035", token.next_token.word) and regex("SP", token.next_token.next_token.word) and regex("B=POÇO", token.deps):
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"
            
        if regex("poço", token.lemma) and regex("Rosário", token.next_token.lemma) and regex("de", token.next_token.next_token.lemma) and regex("o", token.next_token.next_token.next_token.lemma) and regex("Catete", token.next_token.next_token.next_token.next_token.lemma) and regex("B=POÇO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.deps = "O"
            token.next_token.next_token.next_token.next_token.deps = "O"
            
        if regex("poço", token.lemma) and regex("São", token.next_token.lemma) and regex("José", token.next_token.next_token.lemma) and regex("B=POÇO", token.deps):
            token.deps = "O"
            token.next_token.deps = "O"
            token.next_token.next_token.deps = "O"
            
        if regex("I=POÇO", token.deps) and regex("1SPS", token.word) and regex("0034", token.next_token.word) and regex("SP", token.next_token.next_token.word):
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"

        # MCLARA 22/02/2023
        #estrutura_física - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("but", token.word) and regex("B=ESTRUTURA_FÍSICA", token.deps):
            token.deps = "O"
            
        #poço - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("poço", token.word) and regex("B=POÇO", token.deps) and regex("1-FCL-1-ES..", token.next_token.word):
            token.lemma = "1-FCL-1-ES"
            
        if regex("poço", token.word) and regex("1-", token.next_token.word) and regex("RJS-7", token.next_token.next_token.word) and regex("B=POÇO", token.deps):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"
            
        if regex("poço", token.word) and regex("3-", token.next_token.word) and regex("RJS-621", token.next_token.next_token.word) and regex("B=POÇO", token.deps):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"
            
        if regex("poço", token.word) and regex("1-", token.next_token.word) and regex("MAS-20|CES-112|RJS-297", token.next_token.next_token.word) and regex("B=POÇO", token.deps):
            token.deps = "B=POÇO"
            token.next_token.deps = "I=POÇO"
            token.next_token.next_token.deps = "I=POÇO"

        #unidade_lito - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("gr\.", token.word) and regex("B\.|C\.", token.next_token.word) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"
            
        if regex("Terciários", token.word) and regex("B=UNIDADE_LITO", token.deps):
            token.deps = "O"
            
        #unidade_crono - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("idades", token.word) and regex("B=UNIDADE_CRONO", token.deps) and regex("TF", token.next_token.word):
            token.deps = "O"
            token.next_token.deps = "O"
            
        if regex("séries", token.word) and regex("B=UNIDADE_CRONO", token.deps) and regex("O", token.next_token.deps):
            token.deps = "O"
            
        #campo - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("neo-Rio", token.word) and regex("B=CAMPO", token.deps):
            token.deps = "O"
            
        #nãoconsolid - MClara 15/02/2023 (revisão via anotação de URI)

        if regex("silte/", token.word) and regex("argila", token.next_token.word) and regex("B=NÃOCONSOLID", token.deps):
            token.next_token.deps = "B=NÃOCONSOLID"

        # MCLARA 26/04/2023
        if regex("Grupo", token.word) and regex("Dom", token.next_token.word) and regex("João", token.next_token.next_token.word) and regex("\(", token.next_token.next_token.next_token.word) and regex("Andar", token.next_token.next_token.next_token.next_token.word) and regex("\)", token.next_token.next_token.next_token.next_token.next_token.word):
            token.next_token.deps = "B=UNIDADE_CRONO"
            token.next_token.next_token.deps = "I=UNIDADE_CRONO"

        # MCLARA correções de EVENTO_PETRO, inclusão de etiqueta ELEMENTO_PETRO a pedido da Patrícia
        # 04/07/2023
         
        if regex("extrusivo|intrusivo", token.lemma) and regex("vulcânico|vulcânica", token.next_token.lemma):
            token.deps = "O"
            token.next_token.deps = "B=ROCHA"
            
        if regex("B=EVENTO_PETRO", token.deps) and regex("rocha", token.lemma) and regex("gerador|reservatório", token.next_token.lemma):
            token.deps = "B=ELEMENTO_PETRO"
            token.next_token.deps = "I=ELEMENTO_PETRO"
            
        if regex("B=EVENTO_PETRO", token.deps) and regex("trapa|selo", token.lemma):
            token.deps = "B=ELEMENTO_PETRO"

        if regex("B=EVENTO_PETRO", token.deps) and regex("[Gg]erador", token.lemma):
            token.deps = "B=ELEMENTO_PETRO"
            

    # ANCHOR (6) limpeza final
    # ANCHOR limpar I cujo anterior é diferente
    for t, token in enumerate(sentence.tokens):
        previous_token = t-1 if not '-' in sentence.tokens[t-1].id else t-2
        if t and token.deps.startswith("I=") and no_iob(sentence.tokens[previous_token].deps) != no_iob(token.deps):
            token.deps = "O"

    # ANCHOR limpar B=X|I=X
    for token in sentence.tokens:
        deps = no_iob(token.deps).split("|")
        if len(deps) > 1 and len(set(deps)) == 1:
            token.deps = "I={}".format(no_iob(deps[0]))

    # ANCHOR limpar "B=X" "B=X"
    for token in sentence.tokens:
        if token.deps == token.next_token.deps and token.deps.startswith("B=") and not token.word[-1] in ["/"]:
            token.next_token.deps = to_i(token.deps)

    # ANCHOR limpar de|o|,|e|em|(|)|a cujo próximo é O
    for token in reversed(sentence.tokens):
        if regex("de|o|,|e|em|\(|\)|a", token.lemma) and token.deps != "O" and token.next_token.deps.split("/")[0] != token.deps.split("/")[0]:
            token.deps = "O"

    # ANCHOR limpar /conj, /barra e /flat:name cujo head perdeu sema
    for token in sentence.tokens:
        if regex("conj|flat:name", token.special_log) and token.head_token.deps == "O":
            token.deps = "O"
        if regex("conj", token.special_log) and token.head_token.deps != token.deps:
            token.deps = to_b(token.head_token.deps)
        if regex("flat:name", token.special_log) and token.head_token.deps != token.deps:
            token.deps = to_i(token.head_token.deps)
        if regex("barra", token.special_log) and token.previous_token.deps == "O":
            token.deps = "O"

    # ANCHOR limpar tags inutilizadas
    for token in sentence.tokens:
        semas = [x for x in token.deps.split('|') if x in "_O" or no_iob(x) in available_tags]
        token.deps = "|".join(semas)
        if not token.deps:
            token.deps = "O"

    # ANCHOR special log
    for token in sentence.tokens:
        if token.special_log:
            if not test_sent_id:
                sintagma = None
                if token.special_log == "conj":
                    sintagma = "{} e {}\t{}".format(token.head_token.word, token.word, no_iob(token.deps))
                elif token.special_log in "barra flat:name".split():
                    if no_iob(token.next_token.deps) != no_iob(token.deps):
                        sintagma = token.head_token.word
                        if token.special_log == "flat:name":
                            for _token in sentence.tokens:
                                if _token.deprel == "flat:name" and _token.dephead == token.dephead and _token.deps == to_i(_token.head_token.deps):
                                    sintagma += " {}".format(_token.word)
                            sintagma += "\t{}".format(no_iob(token.deps))
                        if token.special_log == "barra":
                            sintagma = "{} / {}\t{}".format(token.previous_token.previous_token.word, token.word, no_iob(token.deps))
                elif token.special_log == "trigger":
                    sintagma = "{}{}{}\t{}".format(token._trigger, " de " if token.previous_token.word != token._trigger else " ", token.word, no_iob(token.deps))
                if sintagma:
                    with open("rules-new_{}.txt".format(token.special_log), "a") as f:
                        f.write(sintagma + "\n")
            if keep_special_log or test_sent_id:
                token.deps = token.deps + "/{}".format(token.special_log)
    # TODO tirar rio da serra da listas de flat:name. pq a correção I=X B=X não entrou pra special_log?

with open("rules-log.txt" if not test_sent_id else "rules-log_test.txt", "a") as f:
    f.write("{} rules were applied".format(len(rules)))

if not test_sent_id:
    with open("rules-conj_not_tagged.txt", "w") as f:
        f.write('5 deprel = "conj" and deps != head_token.deps and sent_id = "{}"'.format("|".join(map(lambda x: x[0], conj_not_tagged))))

if not test_sent_id:
    corpus.save(output)
    print("Saved to \"{}\", \"{}\", \"{}\"".format(output, "rules-big_flatnames.txt", "rules-conj_not_tagged.txt", "rules-log.txt"))
else:
    print(corpus.sentences[test_sent_id].to_str())

print("took: {}s or {}min".format(time.time() - t1, (time.time() - t1)/60))

# GRAPH
#%%
import matplotlib.pyplot as plt
from collections import defaultdict
import json
import csv

corpus = estrutura_ud.Corpus()
corpus.load("rules.conllu")
dados = defaultdict(int)
for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        if "B=" in token.deps:
            sema = token.deps.split("B=")[1].split("|")[0].replace("B=", "")
            dados[sema] += 1

# Ordenar os dados pelo valor
dados_ordenados = sorted(dados.items(), key=lambda x: x[1], reverse=True)

# Separar as chaves e os valores ordenados
chaves_ordenadas = [item[0] for item in dados_ordenados]
valores_ordenados = [item[1] for item in dados_ordenados]

# Criar o gráfico de barras
plt.bar(range(len(dados)), valores_ordenados)
plt.xticks(range(len(dados)), chaves_ordenadas, rotation=90)
plt.xlabel('Classes')
plt.ylabel('Número de Entidades')
plt.title('Número de Entidades por Classe')

# Adicionar o valor de cada barra acima dela
for i, v in enumerate(valores_ordenados):
    plt.text(i, v, str(v), ha='center', va='bottom')

# Exibir o gráfico
save_figure = "rules-results-figure.png"
save_csv = "rules-results.csv"
plt.tight_layout()
plt.savefig(save_figure, dpi=300)

# Abrir o arquivo CSV no modo de escrita
with open(save_csv, "w", newline="") as arquivo_csv:
    writer = csv.writer(arquivo_csv)

    # Escrever o cabeçalho do CSV
    writer.writerow(["Classe", "Entidades"])

    # Escrever os dados do dicionário no CSV
    for palavra, valor in dados_ordenados:
        writer.writerow([palavra, valor])

print("Saved to %s" % save_figure)
print("Saved to %s" % save_csv)

# %%
