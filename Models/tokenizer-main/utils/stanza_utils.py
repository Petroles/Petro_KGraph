import re
import stanza

pattern = r'''((?<!\d)+[.](?=[\s]*[A-Z])|[\s\.]*[\n\r]+[\s]*(?=[A-Z]))'''

def list_to_conllu_text(document_filename: str, conllu_list: list, phrases: list):
    value_list = []
    for s,(sentence,text) in enumerate(zip(conllu_list, phrases)):
        #text = " ".join([token[1] for token in sentence if '-' not in token[0]])
        sent_id = str(s+1)
        content = "\n".join(["\t".join(token[:]) for token in sentence])
        value_list.append("# sent_id = {}-{}\n# text = {}\n{}".format(document_filename, sent_id, text, content))
    return "\n\n".join(value_list)

def portuguese_sentenciation(text):
    #pattern = r'''([.](?=[\s]+[A-Z])|[\s\.]*[\n\r]+[\s]*(?=[A-Z]))'''
    original_values = re.split(pattern, text)
    values = ['{} {}'.format(f1,f2) for f1,f2 in zip(original_values[::2],original_values[1::2])]
    real_values = ['{}{}'.format(f1,f2) for f1,f2 in zip(original_values[::2],original_values[1::2])]
    for value,rvalue in zip(values,real_values):
        value = recursive_space_removal(value)
        rvalue = recursive_space_removal(rvalue)
        yield value, rvalue

def sentenciation_stanza(text, nlp):   
    started_ordinal = re.compile('^[0-9][.][\s][A-Z]')
    #nlp = stanza.Pipeline(lang='pt', processors='tokenize')
    text_by_block = []
    for ii,i in enumerate(text.split('<title>')):
        lista = i.split('\n')   
        for i in range(len(lista)):            
            texto = lista[i]
            if texto.replace('.','').replace(',','').isnumeric():
                lista[i]=''
            if len(re.findall(started_ordinal, texto))>0:
                lista[i] = texto.replace(re.findall(started_ordinal, texto)[0],
                                         re.findall(started_ordinal, texto)[0].replace('. ','. - '))        
        while ('' in lista) or (' ' in lista):
            if '' in lista :
                lista.remove('')
            if ' ' in lista :
                lista.remove(' ')

        text_by_block.append(lista)
    for text_ in text_by_block:
        #print(text_)
        if len(text_) == 0:
            continue
        sents = []
        title = text_[-1]
        text_ = text_[:-1]
        if len(text_)>0:
            text_ = '\n'.join(text_)
            doc = nlp(text_)            
            for sentence in doc.sentences:
                sents.append(sentence.text)
        sents.append(title)
        sent_c = []

        for ind,sent in enumerate(sents):
            if sent[-1]==';' or sent[-1]==':' or (len(sents)!=(ind+1) and sents[ind+1].startswith('“')) or (len(sents)!=(ind+1) and sents[ind+1].startswith('('))  or (len(sents)!=(ind+1) and sents[ind+1].startswith('•')) or (len(sents)!=(ind+1) and sents[ind+1].startswith('')) or (len(sents)!=(ind+1) and sents[ind+1].startswith('μ')):
                sent_c.append(sent)
                continue
            else:
                sent_c.append(sent)
                sent = ' '.join(sent_c)
                
                if sent[-2:]==' .':
                    values = sent
                    real_values = sent
                elif sent[-1:]=='.':
                    values = sent + ' .'
                    real_values = sent + '.'
                else:
                    values = sent
                    real_values = sent
                sent_c = []
                yield values,real_values



"""
def sentenciation(text):
    paragraph_pattern = r'''[\s\.]*[\n\r]+[\s]*'''
    phrase_pattern = r'''(?=[^\s])[.](?=[\s]+[A-Z])'''
    paragraphs = re.split(paragraph_pattern, text)
    sentences = []
    for i, paragraph in enumerate(paragraphs):
        phrases = re.split(phrase_pattern, paragraph)
        if paragraph in [""]:
            continue
        if len(paragraph.split(" ")) <= 2:
            sentences.append(paragraph)
            continue
        for value in phrases:
            value = recursive_space_removal(value)
            value = value.replace("\n", "").replace("\r", "")
            if value in [""]:
                continue
            if value[-1] not in [".", ":"]:
                value += "."
            sentences.append(value)
    return sentences
"""
def recursive_space_removal(value):
    try:
        if value[0] == " ":
            value = value[1:]
            return recursive_space_removal(value)
        else:
            return value.replace("\n", "").replace("\r", "")
    except IndexError:
        return value.replace("\n", "").replace("\r", "")

def text_preprocessing(text):
    # TEXTBAR PREPROCESSING
    text = text.replace(" / ", "##SPACE-BAR-SPACE##")
    text = text.replace(" \ ", "##SPACE-LBAR-SPACE##")
    text = text.replace("/ ", "/")
    text = text.replace(r"\ ", "\\")
    text = text.replace(" /", "/")
    text = text.replace(r" \\", "\\")
    text = text.replace("##SPACE-BAR-SPACE##", r" / ")
    text = text.replace("##SPACE-LBAR-SPACE##", r" \ ")
    return text

def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return True
