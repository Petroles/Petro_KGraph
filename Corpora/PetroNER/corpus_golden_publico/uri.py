import re

def append_to(original, s, delimiter="|"):
    original = original.split(delimiter)
    novosFeats = s.split(delimiter)
    novosFeats += [x for x in original if x != "_" and not any(y.split("=")[0] == x.split("=")[0] for y in novosFeats)]

    return delimiter.join(sorted(novosFeats))

def remove_uri(misc, uri_separated_by_comma):
    new_misc = misc[:]
    remove_tags = uri_separated_by_comma.split(",")    
    grafo = new_misc.split("grafo=")[1].split("|")[0].split(",")
    grafo = [x for x in grafo if x not in remove_tags]
    new_misc = append_to(new_misc, "grafo={}".format(",".join(grafo)))
    return new_misc

def regex(exp, col):
    return re.search(r'^(' + exp + r")$", col)

#convert_tags = lambda x: {'naoconsolid': 'nãoconsolid'}.get(x, x).replace(" ", "_")
split_grafia = lambda x: [x.strip() for x in x.replace("; ", ";").replace("\n", ";").split(";")] if isinstance(x, str) else []

import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore
import sys
import os
import pandas as pd
corpus_name = sys.argv[1]
script_folder = os.path.realpath(os.path.dirname(__file__))
uri_files = ["uri-finalização.xlsx", "uri-entidades-novas.xlsx", "uri-grafias-alternativas.xlsx"]
remove_from_log = "uri-casos_específicos_coordenação_e_descontínuos.txt;uri-entidades_novas_pos_uri.txt".split(";")
save_to = "uri.conllu"
log_planilhas_save_to = "uri_log_planilhas.txt"
log_save_to = "uri_log.txt"
prefix = "grafo="

for filename in list(remove_from_log):
    with open(os.path.join(script_folder, filename)) as f:
        remove_from_log.extend(f.read().strip().splitlines())
    remove_from_log.remove(filename)

corpus = estrutura_ud.Corpus(recursivo=True)
corpus.load(corpus_name)

uris = {}
descending_order = []
no_uri_in_sheet = []
log_planilhas = []

for uri_file in uri_files:
    file_path = os.path.join(script_folder, uri_file)
    uri_dict = pd.read_excel(file_path, sheet_name=None, header=1 if "novas" in uri_file else 0)
    tabs = uri_dict.keys()
    
    for tab in tabs:
        sheet = uri_dict[tab].to_dict()
        tag = tab
        for i in sheet["URI"]:
            if 'SEMA' in sheet:
                if not isinstance(sheet['SEMA'][i], str):
                    log_planilhas.append("No SEMA: %s" % sheet['PALAVRA'][i])
                    continue
                tag = sheet['SEMA'][i].split("B=")[1]
            if not tag in uris:
                uris[tag] = {}
            uri = sheet["URI"][i]
            lexico = sheet['PALAVRA'][i]
            lexico = [x for x in split_grafia(lexico)]
            if 'ESCRITAS ALTERNATIVAS' in sheet:
                escritas_alternativas = [x for x in split_grafia(sheet['ESCRITAS ALTERNATIVAS'][i])]
            else:
                log_planilhas.append("No 'ESCRITAS ALTERNATIVAS' in %s" % tab)
                escritas_alternativas = []
            if 'NOVAS ESCRITAS ALTERNATIVAS' in sheet:
                novas_escritas_alternativas = [x for x in split_grafia(sheet['NOVAS ESCRITAS ALTERNATIVAS'][i])]
            else:
                novas_escritas_alternativas = []
            grafias = lexico + escritas_alternativas + novas_escritas_alternativas
            if not grafias:
                continue
            if not isinstance(uri, str):
                log_planilhas.append("No URI in sheet: {}\t{}".format("; ".join(grafias), tab.upper()))
                no_uri_in_sheet.extend(grafias)
                continue
            if not uri.startswith("#"):
                log_planilhas.append("URI not allowed, skipped: {}\t{}\t{}".format(uri, "; ".join(grafias), "B=%s" % tag.upper()))
                continue
            for item in grafias:
                if not item.strip():
                    continue
                if not item in uris[tag]:
                    uris[tag][item] = []
                uris[tag][item].extend([x.strip() for x in set(uri.replace("|", ",").replace("; ", ",").replace(";", ",").replace("\n", ",").replace("/", ",").split(",")) if x not in uris[tag][item]])
                if not item + ";" + tag in descending_order:
                    descending_order.append(item + ";" + tag)
                else:
                    log_planilhas.append("Appears more than once: {} - {}".format(item, tag))

descending_order = list(sorted(descending_order, key=lambda x: (-len(x.split(";")[0]), x.lower().split(";")[0])))
# uris = {tag: {words: uri}}
# descending_order = [a, aa, aaa, aaa]

sentence_words = {}
for n, entidade in enumerate(descending_order):
    entidade_words = entidade.split(";")[0].split()
    tag = entidade.split(";")[1]
    length = len(entidade_words)
    print("[{}/{}]: {} - {}".format(n+1, len(descending_order), " ".join(entidade_words), tag))
    for sentid, sentence in corpus.sentences.items():
        if not sentid in sentence_words:
            sentence_words[sentid] = [x.word for x in sentence.tokens if not '-' in x.id]
        if any(x not in sentence_words[sentid] for x in entidade_words):
            continue
        for t, token in enumerate(sentence.tokens):
            if token.word != entidade_words[0] or token.deps.upper() != "B=%s" % tag.upper() or prefix in token.misc:
                continue
            ngram = []
            i = 0
            for _ in range(length):
                ngram.append(sentence.tokens[t+i].word)
                try:
                    i = i + (1 if not '-' in sentence.tokens[t+i+1].id else 2)
                except IndexError:
                    break
            if ngram == entidade_words:
                uri = ",".join(sorted(uris[tag][" ".join(ngram)]))
                token.misc = append_to(token.misc, "{}{}".format(prefix, uri))
                print("Found {}: {}".format(tag, uri))

# anotações específicas
for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        if '-' in token.id:
            continue
        try:
            # MCLARA 28/03/2023
            #2 de "membro cc 2"
            if regex("membros", token.word) and regex("CC", token.next_token.word) and regex("1", token.next_token.next_token.word) and regex("e", token.next_token.next_token.next_token.word) and regex("2", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.misc = append_to(token.next_token.next_token.next_token.next_token.misc, "grafo=#inter_membro_002")
                
            #superior de "oligoceno superior"
            if regex("Oligoceno", token.word) and regex("Inferior", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("o", token.next_token.next_token.next_token.word) and regex("Superior", token.next_token.next_token.next_token.next_token.word):
                token.next_token.next_token.next_token.next_token.misc = append_to(token.next_token.next_token.next_token.next_token.misc, "grafo=#Chattian")
                
            #contato/contatos de "contato abrupto"
            if regex("contato", token.word) and regex("basal|planar|superior", token.next_token.word) and regex("abrupto", token.next_token.next_token.word):
                token.misc = append_to(token.misc, "grafo=#TEFR_CD_TIPO_EST_FISICA_ROCHA_002")
                
            if regex("contatos", token.word) and regex("basal", token.next_token.word) and regex("e", token.next_token.next_token.word) and regex("superior", token.next_token.next_token.next_token.word) and regex("abruptos", token.next_token.next_token.next_token.next_token.word):
                token.misc = append_to(token.misc, "grafo=#TEFR_CD_TIPO_EST_FISICA_ROCHA_002")

            # pedidos da Patrícia sobre fluidos 03/07/2023
            if token.deps == "B=FLUIDO":
                token.misc = append_to(token.misc, "grafo=#generic_anthropogenic_fluid")
            if token.deps == "B=FLUIDODATERRA_o":
                token.misc = append_to(token.misc, "grafo=#generic_earth_fluid")
            if prefix in token.misc:
                token.misc = remove_uri(token.misc,"#fluid_origin,#fluid_composition")
        except Exception as e:
            log_planilhas.append("Error :::: %s" % e)

ne_without_uri = []
all_uris = []
log = []

for sentid, sentence in corpus.sentences.items():
    for t, token in enumerate(sentence.tokens):
        if '-' in token.id:
            continue
        if "B=" in token.deps and prefix in token.misc:
            all_uris.extend(token.misc.split("grafo=")[1].split("|")[0].split(","))
        if "B=" in token.deps and not prefix in token.misc:
            ngram = [token.word]
            for _t, _token in enumerate(sentence.tokens):
                if '-' in _token.id:
                    continue
                if _t > t:
                    if _token.deps == token.deps.replace("B=", "I="):
                        ngram.append(_token.word)
                    else:
                        break
            ne = " ".join(ngram) + "\t" + token.deps
            if not ne in ne_without_uri:
                ne_without_uri.append(ne)
                if not " ".join(ngram) in remove_from_log and not ne in remove_from_log:
                    log_planilhas.append("NE without URI: %s" % ne)
            # remover anotação
            log.append("NE removed: {} - {} -> O".format(" ".join(ngram), token.deps))
            token.deps = "O"

log_planilhas.extend(["NE without URI (not a case of no_uri_in_sheet): {}".format(x) for x in ne_without_uri if not x.split("\t")[0] in no_uri_in_sheet])

# checar URIs não existentes na planilha
import json
sheets_list = "uri_sheets-list.txt"
with open(os.path.join(script_folder, sheets_list), "w") as f:
    json.dump(uris, f, indent=4, ensure_ascii=False)

match_uri_sheets = set(descending_order).intersection(set(ne_without_uri))
print("[OK]: List of URIs in spreadsheet saved to %s" % sheets_list)
print("[Check]: Nº of NE without URI in corpus found in spreadsheets (uri_sheets-list.txt): {} -- {}".format(len(match_uri_sheets), str(match_uri_sheets)))

corpus.save(os.path.join(script_folder, save_to))
print("")
with open(os.path.join(script_folder, log_planilhas_save_to), "w") as f:
    f.write("\n".join(sorted(set(log_planilhas))))
with open(os.path.join(script_folder, log_save_to), "w") as f:
    f.write("\n".join(sorted(set(log))))
print("[OK]: Saved to %s" % save_to)
print("[OK]: log saved to %s" % log_planilhas_save_to)