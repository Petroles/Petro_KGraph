import sys
import estrutura_ud

if len(sys.argv) < 3:
    print("python3 diff.py new_file old_file")
    exit()

corpus_new = estrutura_ud.Corpus()
corpus_old = estrutura_ud.Corpus()
corpus_new.load(sys.argv[1])
corpus_old.load(sys.argv[2])

sema = lambda x: x.split("=")[1] if '=' in x else x
diffs = {}
for sentid, sentence in corpus_new.sentences.items():
    if sentid in corpus_old.sentences:
        if len(corpus_old.sentences[sentid].tokens) == len(corpus_new.sentences[sentid].tokens):
            for t, token in enumerate(sentence.tokens):
                if token.deps != corpus_old.sentences[sentid].tokens[t].deps:
                    before = corpus_old.sentences[sentid].tokens[t].deps
                    after = token.deps
                    what_changed = "{} -> {}".format(before, after)
                    if not what_changed in diffs:
                        diffs[what_changed] = []
                    diffs[what_changed].append({
                        'sentid': sentid, 't': t, 'before': before, 'after': after,
                        'text': " ".join(["{}{}{}".format("<b>" if i == t else "", x.word, "</b>" if i == t else "") for i, x in enumerate(sentence.tokens) if not '-' in x.id]),
                        'annotation': sentence.to_str()
                        })

blocks = {}
for sema in diffs:
    blocks[sema] = ""
    for e, entry in enumerate(diffs[sema]):
        blocks[sema] += '''
        <div style='cursor:pointer' class='entry'>{}/{} - {} - {}<br>
                        \n{}<pre class='annotation' style='padding:10px; background-color:lightgray; display:none'>{}</pre>
                        </div><hr>\n
                        '''.format(e+1, len(diffs[sema]), entry['sentid'], sema, entry['text'], entry['annotation'])

html = '''
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
Diff: {tokens} tokens<br>
<div class="buttons" style="margin:20px">{links}</div>
<div>
    {blocks}
</div>
<script>
    $('.links').click(function(){{
        $('.blocks').hide()
        $('[id="' + $(this).text() + '"]').show()
    }})
    $('.entry').click(function(){{
        $('.annotation').hide()
        $(this).find('.annotation').show()
    }})
</script>
'''.format(
    tokens = sum([len(diffs[x]) for x in diffs]),
    links = "<br>".join("<a href='#' class='links' style='text-decoration:none; cursor:pointer; color:blue'>{}</a> ({})".format(y, len(diffs[y])) for y in sorted(diffs, key=lambda x: -len(diffs[x]))),
    blocks = "\n".join(["<div style='display:none' class='blocks' id='{}'>{}</div>".format(x, blocks[x]) for x in diffs])
    )

with open("diff.html", "w") as f:
    f.write(html)
print("Saved to diff.html")