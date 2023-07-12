import pandas
import os
import re
import sys
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore
print(os.listdir())

save_to = {"log": "log-1-filter.txt", "np1-raw": "np1-raw.conllu", "np1-ner-model": "np1-ner-model.conllu", "np1-ner-model-fixed": "np1-ner-model-fixed.conllu"}
f = open(save_to['log'], "w")
sys.stdout = f

to_set = lambda x: set([y.split("results\\")[1] if '\\' in y else y for y in x if isinstance(y, str) and '.csv' in y])
n_tokens_in_conllu = lambda x: sum([len([z for z in y.splitlines() if z.count("\t") == 9 and not '-' in z.split("\t")[0]]) for y in x])

def get_features(doc):
    print("docs", len(doc))
    print("sentences", sum([len(x) for _, x in doc.items()]))
    print("tokens", sum([n_tokens_in_conllu(x) for _, x in doc.items()]))

docs_fabio = to_set(pandas.read_excel("fabio.xlsx")['Unnamed: 0'])
docs_patricia = to_set(pandas.read_excel("patricia.xlsx", "Planilha2")['Documento'])
inferred_docs = docs_fabio | docs_patricia
print(len(inferred_docs), 'inferred docs from fabio and patricia')

# all sentences
all_docs = {}
folder_1 = "../ner_conllu_novo"
for folder_2 in os.listdir(folder_1):
    path = os.path.join(folder_1, folder_2)
    for doc in os.listdir(path):
        doc = doc.rsplit(".", 1)[0]#.replace("_stanza", "")
        path = os.path.join(folder_1, folder_2, doc) + ".conllu" #+ "_stanza.conllu")
        with open(path) as f:
            if doc in all_docs:
                print("already in all_docs: %s" % doc)
            all_docs[doc] = f.read().strip().split("\n\n")
print("\nall_docs:")
get_features(all_docs)

filters = {
    'space_character': r'# text = .*?( \S){4}',
    'english': r'# text = .*\b(the|and|of)\b',
    'many_special_characters': "[^\sa-zA-Z,]",
    'not_ending_punctuation': r'# text = .*[^\.\?\!]\n'
    }
filter_files = {}
for filter_name in filters:
    filter_files[filter_name] = open("filter-%s.txt" % filter_name, "w+")

# filter sentences
all_sentences = {}
filtered_sent_ids = []
filtered_docs = ["05125DBC4CDB1E89E054002128300A66"]
for doc, sentences in all_docs.items():
    for i, sentence in enumerate(sentences[:]):
        if not '# sent_id = ' in sentence:
            continue
        sentence = sentence.splitlines()
        for l, line in enumerate(sentence):
            if line.startswith('# text = '):
                sentence[l] = sentence[l].strip() # NECESSÁRIO POIS O CONLLU ESTÁ COM ESPAÇO NO FINAL DOS TEXT
        sentence = "\n".join(sentence)
        sentences[i] = sentence[:]
        sent_id = sentence.split("# sent_id = ")[1].split("\n")[0]
        text = sentence.split("# text = ")[1].split("\n")[0]
        all_sentences[sent_id] = sentence
        if doc in filtered_docs:
            filtered_sent_ids.append(sent_id)
        for filter_name, regex in filters.items():
            found_regex = None
            if filter_name == "many_special_characters":
                regex_output = re.findall(regex, text)
                if len(regex_output) > (len(text) * 0.3):
                    found_regex = [text]
            else:
                found_regex = re.search(regex, sentence, flags=re.IGNORECASE)
            if found_regex:
                filter_files[filter_name].write("regex: " + found_regex[0] + "\n") #  + sentence + "\n\n"
                filtered_sent_ids.append(sent_id)

for filter_name in filters:
    filter_files[filter_name].close()

filtered_docs = {}
for doc, sentences in all_docs.items():
    for i, sentence in enumerate(sentences):
        if not '# text = ' in sentence:
            continue
        sent_id = sentence.split("# sent_id = ")[1].split("\n")[0]
        if not sent_id in filtered_sent_ids:
            if not doc in filtered_docs:
                filtered_docs[doc] = []
            filtered_docs[doc].append(sentence)
print("\nfiltered_docs:")
get_features(filtered_docs)

# from spreadsheets
sentences_from_spreadsheets = []
filtered_docs_from_spreadsheets = {}
for doc in inferred_docs:
    doc = doc.replace(".csv", "")
    if not doc in filtered_docs:
        print("doc not in filtered_docs: %s" % doc)
        continue
    sentences = filtered_docs[doc]
    for i, sentence in enumerate(sentences):
        if not '# text = ' in sentence:
            continue
        sent_id = sentence.split("# sent_id = ")[1].split("\n")[0]
        sentences_from_spreadsheets.append(sent_id)
        if not doc in filtered_docs_from_spreadsheets:
            filtered_docs_from_spreadsheets[doc] = []
        filtered_docs_from_spreadsheets[doc].append(sentence)
print("\nfrom spreadsheets:")
get_features(filtered_docs_from_spreadsheets)

with open(save_to['np1-ner-model'], "w") as f:
    f.write("\n\n".join([all_sentences[x] for x in all_sentences if x not in filtered_sent_ids and x in sentences_from_spreadsheets]))
print("Saved to %s" % save_to['np1-ner-model'])

# correções porque o arquivo gerado pelo modelo da evelyn coloca O nas contrações, quando deveria ser _
corpus = estrutura_ud.Corpus()
corpus.load(save_to['np1-ner-model'])
for sentence in corpus.sentences.values():
    for t, token in enumerate(sentence.tokens):
        if '-' in token.id:
            token.deps = "_"
corpus.save(save_to['np1-ner-model-fixed'])
print("Saved to %s" % save_to['np1-ner-model-fixed'])

for sentence in corpus.sentences.values():
    for t, token in enumerate(sentence.tokens):
        if '-' in token.id:
            continue
        token.deps = "O"
corpus.save("np1-raw.conllu")
print("Saved to %s" % save_to['np1-raw'])

f.close()
print("Saved to %s" % save_to['log'])
# %%
