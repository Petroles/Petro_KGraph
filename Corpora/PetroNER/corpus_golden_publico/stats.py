import sys
import os
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore

folder = "tagged"

if os.path.isdir(folder):
    files = {}
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not name.endswith(".conllu"):
            continue
        with open(path) as f:
            text = f.read()
        files[name.rsplit(".conllu", 1)[0]] = text
    print(files.keys())

elif os.path.isfile(folder):
    files = {}
    with open(folder) as f:
        text = f.read()
    corpus = estrutura_ud.Corpus()
    corpus.load(folder)
    for sent_id, sentence in corpus.sentences.items():
        name = sent_id.rsplit("-", 1)[0]
        if not name in files:
            files[name] = []
        files[name].append(sentence.to_str())
    for name in files:
        files[name] = "\n\n".join(files[name])
    print(files.keys())

else:
    raise Exception("not a folder nor a file: {}".format(folder))

stats = {x: {'sentences': 0, 'tokens': 0, 'types': [], 'tags': {}, 'NE': 0} for x in files}
all_tags = {}

for n, name in enumerate(files):
    print(n+1, "/", len(files), name)
    corpus = estrutura_ud.Corpus()
    corpus.build(files[name])
    for sentence in corpus.sentences.values():
        stats[name]['sentences'] += 1
        for token in sentence.tokens:
            if '-' in token.id:
                continue
            stats[name]['tokens'] += 1
            stats[name]['types'].append(token.lemma)
            if "B=" in token.deps:
                ne = [x.split("|")[0] for x in token.deps.split("B=") if x]
                stats[name]['NE'] += len(ne)
                for ent in ne:
                    if not ent in all_tags:
                        all_tags[ent] = {'count': 0, 'files': []}
                    all_tags[ent]['count'] += 1
                    all_tags[ent]['files'].append(name)
                    if not ent in stats[name]['tags']:
                        stats[name]['tags'][ent] = 0
                    stats[name]['tags'][ent] += 1
    stats[name]['types'] = len(set(stats[name]['types']))

tags_stats = "Tag;NE;FILES"
for tag in all_tags:
    all_tags[tag]['files'] = len(set(all_tags[tag]['files']))
with open("tags_stats.csv", "w+") as f:
    print(tags_stats, file=f)
    for tag in sorted(all_tags, reverse=True, key=lambda x: (all_tags[x]['count'], all_tags[x]['files'])):
        print("{};{};{}".format(tag, all_tags[tag]['count'], all_tags[tag]['files']), file=f)

files_stats = "File;%NE;NE;TTR;SENT;TOKENS;TAGS"
for name in stats:
    stats[name]['%NE'] = stats[name]['NE'] / stats[name]['tokens']
    stats[name]['TTR'] = stats[name]['types'] / stats[name]['tokens']
with open("files_stats.csv", "w+") as f:
    print(files_stats, file=f)
    for name in sorted(stats, reverse=True, key=lambda x: (stats[x]['%NE'], stats[x]['NE'], stats[x]['TTR'])):
        print("{};{};{};{};{};{};{}".format(
            name,
            stats[name]['%NE'],
            stats[name]['NE'],
            stats[name]['TTR'],
            stats[name]['sentences'],
            stats[name]['tokens'],
            ", ".join(["{}: {}".format(x, stats[name]['tags'][x]) for x in sorted(stats[name]['tags'], reverse=True, key=lambda x: stats[name]['tags'][x])]),
        ), file=f)

lexicons = {}
if os.path.isdir("tagset"):
    with open("tagset_stats.csv", "w+") as f:
        for filename in os.listdir("tagset"):
            if filename.endswith(".txt"):
                with open(os.path.join("tagset/{}".format(filename))) as l:
                    lexicons[os.path.splitext(filename)[0]] = [x for x in l.read().splitlines() if x.strip() and not x.strip().startswith("#")]
        print("NE;#", file=f)
        for lexicon in sorted(lexicons, key=lambda x: -len(lexicons[x])):
            print("{};{}".format(lexicon, len(lexicons[lexicon])), file=f)
            

print(">> files_stats.csv")
print(">> tags_stats.csv")
print(">> tagset_stats.csv")