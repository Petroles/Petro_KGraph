import os
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore
try:
    import stanza
except Exception:
    os.system("pip3 install stanza")
    import stanza
#stanza.download('pt')
nlp = stanza.Pipeline('pt')
import unicodedata
import time
import sys
import pandas as pd

APAGAR_ENTIDADES = True
EXPANDIR_ESCRITAS_ALTERNATIVAS = "--expand" in sys.argv
print(">>>>> Expanding entities from escritas alternativas: %s" % EXPANDIR_ESCRITAS_ALTERNATIVAS)
script_folder = os.path.dirname(os.path.abspath(__file__))
tagset_folder = os.path.join(script_folder, "tagset")
conllu_folder = (sys.argv[1:] or (os.path.join(script_folder, "conllu"),))[0]
tagged_folder = os.path.join(script_folder, "tagged")
sys.path.append(os.path.abspath(os.path.join(script_folder, "../uri")))
t1 = time.time()
split_grafia = lambda x: [x.strip() for x in x.replace("; ", ";").replace("\n", ";").split(";")] if isinstance(x, str) else []

print("Reading files from: %s" % conllu_folder)

# Checking folders exist
for folder in [tagset_folder, conllu_folder]:
    if not os.path.isdir(folder) and not os.path.isfile(folder):
        os.mkdir(folder)
        print("Creating: %s" % folder)

if not all(os.path.isdir(x) or os.path.isfile(x) for x in [tagset_folder, conllu_folder]):
    raise Exception("Folder not found.")

col_sema = 8
files = {}
tags = {}
lemmas = {
    'ums': 'ums',
    'santos': 'santos',
    'estai': 'estai',
    'veio': 'veio',
    'campos': 'campos'
}

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def stanza_lemmatize(string):
    doc = nlp(string)
    return " ".join([token['lemma'] for sentence in doc.to_dict() for token in sentence if 'lemma' in token])

def count_tokens(string):
    return {
        'tokens': len(list(filter(lambda x: len(x.split("\t")) == 10 and not '-' in x.split("\t")[0], string.splitlines()))),
        'sentences': len([x for x in string.split("\n\n") if x.strip()]),
        'types': {x.split("\t")[1] for x in filter(lambda x: len(x.split("\t")) == 10, string.splitlines())},
        }

def tag_sentence(sentence, entity, tag):
    tokens = list(filter(lambda x: isinstance(x, list) and not '-' in x[0], sentence))
    metadata = list(filter(lambda x: isinstance(x, str), sentence))
    mwt = {l: line for l, line in enumerate(sentence) if isinstance(line, list) and '-' in line[0]}
    ngram_span = len(entity)
    for t, token in enumerate(tokens):
        if t + ngram_span > len(tokens):
            break
        ngram_word = [remove_accents(tokens[t+i][1].lower()) for i in range(ngram_span)]
        ngram_lemma = [remove_accents(tokens[t+i][2].lower()) for i in range(ngram_span)]
        if any(x == entity for x in [ngram_word, ngram_lemma]):
            if entity[0] == "campos" and tokens[t][1][0] != "C":
                continue
            for i in range(ngram_span):
                tokens[t+i][col_sema] = "|".join(sorted(set([x for x in tokens[t+i][col_sema].split("|") if x != "O"] + ["{}={}".format("I" if i else "B", tag)])))
    sentence = metadata + tokens
    for line in mwt:
        sentence.insert(line, mwt[line])
    return sentence

def count_tags(text):
    frequency = []
    for token in filter(lambda x: len(x.split("\t")) == 10 and not '-' in x.split("\t")[0] and "B=" in x.split("\t")[col_sema], text.splitlines()):
        frequency.extend([x.replace("B=", "") for x in token.split("\t")[col_sema].split("|") if x.startswith("B=")])
    return frequency

def apply_rules(text):
    corpus = estrutura_ud.Corpus()
    corpus.build(text)
    for sentence in corpus.sentences.values():
        for token in sentence.tokens:
            pass
    return corpus.to_str()

# Build tagset lexicon
for file in os.listdir(tagset_folder):
    if file.lower().endswith(".txt"):
        tag = file.upper().split(".TXT")[0].replace("_", ":").replace(" ", "_")
        with open("{}/{}".format(tagset_folder, file)) as f:
            text = f.read().replace("; ", "\n").replace(";", "\n").replace("\t", "\n")
        tags[tag] = set([x.lower().replace("_", " ").replace(".", ". ").replace("  ", " ").strip() for x in text.splitlines() if not x.strip().startswith("#") and x.strip()])

if EXPANDIR_ESCRITAS_ALTERNATIVAS:
    tags['ESTRUTURA_FÍSICA'] = set()
    tags['TEXTURA'] = set()
    tags['EVENTO_PETRO'] = set()
    tags['TIPO_POROSIDADE'] = set()
    tags['POÇO_Q'] = set()
    tags['POÇO_R'] = set()
    tags['POÇO_T'] = set()
    escritas_alternativas = ["../Entidades novas.xlsx", "../Grafias alternativas.xlsx"]

    for spreadsheet in escritas_alternativas:
        file_path = os.path.join(script_folder, os.path.abspath(spreadsheet))
        alternativas_dict = pd.read_excel(file_path, sheet_name=None, header=1 if "novas" in spreadsheet else 0)
        tabs = alternativas_dict.keys()
        
        for tab in tabs:
            sheet = alternativas_dict[tab].to_dict()
            for i in sheet["ESCRITAS ALTERNATIVAS"]:
                escritas_alternativas = split_grafia(sheet['ESCRITAS ALTERNATIVAS'][i])
                palavra = split_grafia(sheet['PALAVRA'])
                sema = tab
                tags[sema].update(escritas_alternativas + palavra)

# Load conllu files and gather initial statistics
for file in (os.listdir(conllu_folder) if os.path.isdir(conllu_folder) else [conllu_folder]):
    if file.lower().endswith(".conllu"):
        with open("{}/{}".format(conllu_folder, file) if os.path.isdir(conllu_folder) else conllu_folder) as f:
            text = f.read()
        sentences = [x.splitlines() for x in text.split("\n\n") if x.strip()]
        for s, sentence in enumerate(sentences):
            for l, line in enumerate(sentence):
                if len(line.split("\t")) == 10:
                    sentences[s][l] = line.split("\t")
                    if not '-' in line.split("\t")[0]:
                        if sentences[s][l][col_sema] == "_":
                            sentences[s][l][col_sema] = "O"
                        if APAGAR_ENTIDADES:
                            sentences[s][l][col_sema] = "O"
                    else:
                        sentences[s][l][col_sema] = "_"
        files[file] = {'text': text, 'tagged': sentences, 'tags_frequency': []}
        files[file].update(count_tokens(files[file]['text']))

# Tag each file
for f, file in enumerate(files):
    print("tagging: {}".format(file))
    text_normalized = remove_accents(files[file]['text'].lower())
    for t, tag in enumerate(tags):
        print(tag)
        filtered_entities = list(filter(lambda x: any(y in text_normalized for y in [z for z in remove_accents(x.lower()).split() if z not in "de o a".split()]), tags[tag]))
        n_entities = len(filtered_entities)
        for e, entity in enumerate(filtered_entities):
            if not entity in lemmas:
                # TESTAR POÇO
                lemmas[entity] = stanza_lemmatize(entity) if tag not in "POÇO".split() else entity
            if not e%20:
                print("{}/{} - {}/{} - {} / {} {}: {} - {} {}".format(f+1, len(files), t+1, len(tags), e+1, len(tags[tag]), n_entities, entity, lemmas[entity], "-- skip lemma" if lemmas[entity] == entity else ""))
            for ngram in [entity, lemmas[entity] if lemmas[entity] != entity else ""]:
                if ngram:
                    for s, sentence in enumerate(files[file]['tagged']):
                        files[file]['tagged'][s] = tag_sentence(sentence, [remove_accents(x) for x in ngram.split(" ")], tag)    
                        # barra / slash => testar
                        if tag not in "POÇO".split():
                            files[file]['tagged'][s] = tag_sentence(sentence, [remove_accents(x) + "/" for x in ngram.split(" ")], tag)
                            files[file]['tagged'][s] = tag_sentence(sentence, [remove_accents(x) + "-" for x in ngram.split(" ")], tag)
                            files[file]['tagged'][s] = tag_sentence(sentence, ["/" + remove_accents(x) for x in ngram.split(" ")], tag)
                            files[file]['tagged'][s] = tag_sentence(sentence, ["-" + remove_accents(x) for x in ngram.split(" ")], tag)
    files[file]['output'] = files[file]['tagged'][:]
    for s, sentence in enumerate(files[file]['tagged']):
        for t, token in enumerate(sentence):
            if isinstance(token, list):
                files[file]['output'][s][t] = "\t".join(files[file]['output'][s][t])
        files[file]['output'][s] = "\n".join(files[file]['output'][s])
    files[file]['output'] = "\n\n".join(files[file]['output'])
    files[file]['output'] = apply_rules(files[file]['output'])
    files[file]['tags_frequency'].extend(count_tags(files[file]['output']))

# Save tagged files
if not os.path.isdir(tagged_folder):
    os.mkdir(tagged_folder)
for n, file in enumerate(files):
    save_to = os.path.join(tagged_folder, os.path.split(file)[1])
    with open(save_to, "w") as f:
        f.write(files[file]['output'])
        print("Saved to: %s" % save_to)
#os.system("meld --diff {}/{} tagged/{}".format(conllu_folder, file, file))

print("took: {}s".format(time.time() - t1))