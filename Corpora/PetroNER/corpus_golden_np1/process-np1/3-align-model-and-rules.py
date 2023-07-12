import sys
import json
from collections import defaultdict
import httpimport
with httpimport.github_repo('alvelvis', 'ACDC-UD', ref='master'): import estrutura_ud # type: ignore

files = {'model': "np1-ner-model-fixed.conllu", 'rules': "np1-ner-rules.conllu", 'golden': "np1-ner-golden.conllu"}
save_to = "log-3-align-{}.txt".format("_".join([x.replace(".conllu", "") for x in files.values()]))

orig_stdout = sys.stdout
f = open(save_to, "w")
sys.stdout = f
print(str(files.items()) + "\n")

corpora = {'model': 0, 'rules': 0, 'golden': 0}
ner_tokens = {'model': defaultdict(set), 'rules': defaultdict(set), 'golden': defaultdict(set)}

hits = {
'n_ne': {'model': defaultdict(int), 'rules': defaultdict(int), 'golden': defaultdict(int)},
'precision': {'model': defaultdict(int), 'rules': defaultdict(int)},
'recall': {'model': defaultdict(int), 'rules': defaultdict(int)},
'f1': {'model': defaultdict(int), 'rules': defaultdict(int)},
'tp': {'model': defaultdict(int), 'rules': defaultdict(int)},
'tp_correct': {'model': defaultdict(int), 'rules': defaultdict(int)},
'tp_incorrect': {'model': defaultdict(int), 'rules': defaultdict(int)},
'fn': {'model': defaultdict(int), 'rules': defaultdict(int)},
#'tn': {'model': defaultdict(int), 'rules': defaultdict(int)},
'fp': {'model': defaultdict(int), 'rules': defaultdict(int)},
}

for corpus in corpora:
    corpora[corpus] = estrutura_ud.Corpus(recursivo=True)
    corpora[corpus].load(files[corpus])
    print("{} n_sent: {}".format(corpus, len(corpora[corpus].sentences)))
    print("{} n_tokens: {}".format(corpus, sum([len(list(filter(lambda y: not '-' in y.id, x.tokens))) for x in corpora[corpus].sentences.values()])))
    print("{} n_ne: {}".format(corpus, sum([len(list(filter(lambda y: not '-' in y.id and "B=" in y.deps, x.tokens))) for x in corpora[corpus].sentences.values()])))
    for sent_id, sentence in corpora[corpus].sentences.items():
        for t, token in enumerate(sentence.tokens):
            if '-' in token.id:
                continue
            if "B=" in token.deps: # CONSIDERANDO SÓ B=
                sema = token.deps.replace("B=", "")
                token_set = (sent_id, t)
                #if not '_total' in ner_tokens[corpus]: ner_tokens[corpus]['_total'] = set()
                #if not sema in ner_tokens[corpus]: ner_tokens[corpus][sema] = set()
                hits['n_ne'][corpus]['_total'] += 1
                hits['n_ne'][corpus][sema] += 1
                ner_tokens[corpus]['_total'].add(token_set)
                ner_tokens[corpus][sema].add(token_set)

# INTERSECTION
intersection_same = 0
intersection_different = 0

for token in (ner_tokens['model']['_total'] | ner_tokens['rules']['_total']):
    token_model = corpora['model'].sentences[token[0]].tokens[token[1]]
    token_rules = corpora['rules'].sentences[token[0]].tokens[token[1]]
    if token in ner_tokens['model']['_total'] and token in ner_tokens['rules']['_total']:
        if token_rules.deps == token_model.deps:
            intersection_same += 1
        else:
            intersection_different += 1

print("intersection same ne (both identified and classified the same way): %s" % intersection_same)
print("intersection different ne (both identified but classified in different ways): %s" % intersection_different)

# CONSTRUIR DIAGRAMA DE VENN DE INTERSEÇÃO DO MODELO E REGRAS
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

# Define the sizes and labels
regras_items = hits['n_ne']['rules']['_total']
modelo_items = hits['n_ne']['model']['_total']
intersection_items = intersection_same + intersection_different
regras_unique_items = hits['n_ne']['rules']['_total'] - intersection_items
modelo_unique_items = hits['n_ne']['model']['_total'] - intersection_items
same_class_items = intersection_same
different_class_items = intersection_different

# Calculate percentages
regras_percentage = (regras_unique_items / regras_items) * 100
modelo_percentage = (modelo_unique_items / modelo_items) * 100

# Create the Venn diagram
venn = venn2(subsets=(regras_items - intersection_items, modelo_items - intersection_items, intersection_items),
             set_labels=('regras\n(entidades: {})'.format(regras_items),
                         'modelo\n(entidades: {})'.format(modelo_items)))

# Set the subset labels
venn.get_label_by_id('10').set_text('{:.2f}%\n({})'.format(regras_percentage, regras_unique_items))
venn.get_label_by_id('01').set_text('{:.2f}%\n({})'.format(modelo_percentage, modelo_unique_items))
venn.get_label_by_id('11').set_text('{}\n{} {}\n{} {}'.format(intersection_items,
                                                              same_class_items,
                                                              'mesma classif.',
                                                              different_class_items,
                                                              'classif. diferente'))

# Set the title
plt.title("")

# Show the plot
plt.show()

# HIT RATE (CONSIDERANDO SÓ OS TOKENS DE NER_TOKENS)
for ne in ner_tokens['golden']:
    for token in ner_tokens['golden'][ne]:
        tokens = {'model': 0, 'rules': 0, 'golden': 0}
        for corpus in "model,rules,golden".split(","):
            tokens[corpus] = corpora[corpus].sentences[token[0]].tokens[token[1]]    
        for corpus in "rules,model".split(","):
            if token in ner_tokens[corpus][ne]:
                hits['tp'][corpus][ne] += 1
                if tokens[corpus].deps == tokens['golden'].deps:
                    hits['tp_correct'][corpus][ne] += 1
                else:
                    hits['tp_incorrect'][corpus][ne] += 1
            else:
                hits['fn'][corpus][ne] += 1

for corpus in 'model,rules'.split(","):
    for ne in ner_tokens[corpus]:
        for token in ner_tokens[corpus][ne]:
            if token not in ner_tokens['golden'][ne]:
                hits['fp'][corpus][ne] += 1
        p_denominator = hits['tp'][corpus][ne] + hits['fp'][corpus][ne]
        r_denominator = hits['tp'][corpus][ne] + hits['fn'][corpus][ne]
        hits['precision'][corpus][ne] = hits['tp_correct'][corpus][ne] / p_denominator if p_denominator else 0
        hits['recall'][corpus][ne] = hits['tp_correct'][corpus][ne] / r_denominator if r_denominator else 0
        f_denominator = hits['precision'][corpus][ne] + hits['recall'][corpus][ne]
        hits['f1'][corpus][ne] = 2 * hits['precision'][corpus][ne] * hits['recall'][corpus][ne] / f_denominator if f_denominator else 0

print("{}".format(json.dumps(hits, indent=4, ensure_ascii=False)))

# CONSTRUIR GRÁFICO DE ACERTOS
import matplotlib.pyplot as plt

# Dados de exemplo
classes = sorted(set(list(hits['f1']["model"].keys()) + list(hits['f1']["rules"].keys())))
f1_anotador = [hits['f1']['rules'].get(x, 0) for x in classes]
f1_modelo = [hits['f1']['model'].get(x, 0) for x in classes]

# Configuração do gráfico de barras
bar_width = 0.35
index = range(len(classes))

# Plotar os dados do anotador com base em regras
plt.bar(index, f1_anotador, bar_width, label='Anotador com base em regras')

# Plotar os dados do modelo estatístico
plt.bar([i + bar_width for i in index], f1_modelo, bar_width, label='Modelo estatístico')

# Configurações adicionais do gráfico
plt.xticks([i + bar_width/2 for i in index], classes, rotation=45)

# Adicionar a porcentagem dentro de cada barra (vertical)
for i, v in enumerate(f1_anotador):
    plt.text(i, v/2, f'{v*100:.1f}%', color='white', ha='center', va='center', fontweight='bold', rotation='vertical')
    plt.text(i + bar_width, f1_modelo[i]/2, f'{f1_modelo[i]*100:.1f}%', color='white', ha='center', va='center', fontweight='bold', rotation='vertical')

# Remover legenda "Classes de entidades"
plt.xlabel('')

# Remover título do gráfico
plt.title('')

# Mover a legenda para o topo do gráfico
plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), fancybox=True, shadow=True, ncol=2)

# Ajustar o espaço para evitar conflito com a última barra
plt.subplots_adjust(bottom=0.25)

# Exibir o gráfico
plt.tight_layout()
plt.show()

# FECHAR CÓDIGO
f.close()
sys.stdout = orig_stdout
print("saved to: %s" % save_to)

exit()