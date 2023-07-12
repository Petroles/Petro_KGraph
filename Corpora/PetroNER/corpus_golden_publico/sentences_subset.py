import sys
import os
import estrutura_ud

if len(sys.argv) < 3:
    print("python3 sentences_subset.py file.conllu \"SENT_ID1|SENT_ID2|SENT_ID3...\"")
    sys.exit()

sentences = sys.argv[2].split("|")
conllu = sys.argv[1]
if not os.path.isfile(conllu):
    raise Exception("{} not found!".format(conllu))
with open(conllu) as f:
    corpus = [x for x in f.read().split("\n\n") if any("# sent_id = {}\n".format(y) in x for y in sentences)]

print(len(corpus))
with open("conllu/subset.conllu", "w") as f:
    f.write("\n\n".join(corpus) + "\n")
