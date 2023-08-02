import sys
from tqdm import tqdm
import os
import re
import datetime
import stanza
from stanza import Pipeline
from stanza.utils.conll import CoNLL
from utils.stanza_utils import list_to_conllu_text, text_preprocessing, portuguese_sentenciation,sentenciation_stanza
from stanza.models.common import doc
import itertools
import numpy as np

tokenization_pattern = r'''al\.|[.,;:"“”'?():_`]|\w*(?:[^;"“”'?():_`\s]*\w+)+[%º°?']?|[\S]'''

def spans(txt, tokens):
    offset = 0
    all_spans = []
    for token in tokens:
        offset = txt.find(token, offset)
        all_spans.append((token, offset, offset + len(token)))
        offset += len(token)
    return all_spans

def get_mwts(token_sentence, tokens_by_id):
    mwts = []
    for i in range(len(token_sentence)):
        token = token_sentence[i]
        if isinstance(token['id'], tuple):
            id_start = token['id'][0]
            id_end = token['id'][1]+1
            ids = range(id_start,id_end)
            mwts.append((token['text'] , [tokens_by_id[idx] for idx in ids]))
    return mwts

def merge_stanza_token_sentences(stanza_token_sentences):
    offset=0
    for i in range(len(stanza_token_sentences)):
        for j in range(len(stanza_token_sentences[i])):
            if 'head' in stanza_token_sentences[i][j]:
                stanza_token_sentences[i][j]['head']=int(stanza_token_sentences[i][j]['head'])+offset
                
            if  isinstance(stanza_token_sentences[i][j]['id'], tuple):
                ids = stanza_token_sentences[i][j]['id']
                #stanza_token_sentences[i][j]['id'] = '-'.join([str(int(id)+offset) for id in ids])
                stanza_token_sentences[i][j]['id'] = tuple(list(int(id)+offset for id in ids))
            else:
                stanza_token_sentences[i][j]['id'] = int(stanza_token_sentences[i][j]['id']) + offset

        offset=int(stanza_token_sentences[i][-1]['id'])
    stanza_token_sentences = list(itertools.chain.from_iterable(stanza_token_sentences))
    return stanza_token_sentences

def get_stanza_2_tagged(stanza_token_sentence, tagged_sentence):
    filtered_stanza_token_sentence = []
    skip_tokens_id = []
    for token in stanza_token_sentence:
        if token['id'] in skip_tokens_id:
            continue
        if isinstance(token['id'], tuple):#'-' in token['id']:
            id_start = token['id'][0]
            id_end = token['id'][1]+1
            skip_tokens_id =[idx for idx in range(id_start,id_end)]#.split('-')
        filtered_stanza_token_sentence.append(token)

    for i,token in enumerate(filtered_stanza_token_sentence):
        filtered_stanza_token_sentence[i]['start']=int(token['misc'].split('|')[0][11:])

    for i,token in enumerate(tagged_sentence):
        tagged_sentence[i]['start']=int(token['misc'].split('|')[0][11:])

    stanza_2_tagged = {}
    stanza_2_tagged[0]=0
    for ftoken in filtered_stanza_token_sentence:
        compare=[]
        for i,ttoken in enumerate(tagged_sentence):
            ftext = set(ftoken['text'])
            ttext =set(ttoken['text'])
            if min(len(ftext-ttext),len(ttext-ftext))==0:
                compare.append((i, abs(ftoken['start'] - ttoken['start'])))
        if len(compare)==0:
            continue
            
        idx = min(compare, key=lambda x:x[1])[0]
        
        if isinstance(ftoken['id'],int):
            ids = [ftoken['id']]
        else:
            id_start = ftoken['id'][0]
            id_end = ftoken['id'][1]+1
            ids = range(id_start, id_end)
            
        for f_id in ids:#.split('-')
            stanza_2_tagged[f_id] = tagged_sentence[idx]['id']
    
    return stanza_2_tagged


def conllu_process_file(input_path, input_filename, tag_nlp, nlp_sentece):
    print("loading file: {}".format(input_path))
    #input_path='data/{}.txt'.format(input_filename)
    try:
        infile = open(input_path, encoding='utf-16')
        text = infile.read()
        print('first')
    except:
        try:
            infile = open(input_path, encoding='utf-16')
            text = infile.read()
            print('second')
        except Exception as e:
            infile = open(input_path, encoding='latin-1')
            text = infile.read()
            print('thrid')
            print(e)

    #text = text.replace('<title>','')
    #print('*'*500)
    #text = infile.read().decode('utf-16', errors='replace')
    #if text == "" or text is None:
    #    text = infile.read().decode('utf-32', errors='ignore')
    #print('text',text)
    preprocessed_text = text_preprocessing(text)
    #print('preprocessed_text',preprocessed_text)
    #sentences = portuguese_sentenciation(preprocessed_text)
    #tok_nlp = Pipeline(lang='pt', tokenize_pretokenized=False, use_gpu=False)#processors='tokenize,mwt', 
    #tag_nlp = Pipeline(lang='pt', tokenize_pretokenized=True, use_gpu=False)#processors='tokenize,pos,lemma,depparse',

    sentences = sentenciation_stanza(preprocessed_text, nlp=nlp_sentece)

    #new_document=[]
    #raw_texts=[]
    #phrases = []
    #for phrase,rphrase in tqdm(list(sentences)):
        #if not phrase.strip()=='':
            #phrases.append(rphrase)
            #stanza_sentence = tok_nlp(phrase)
            #stanza_token_sentences2 = stanza_sentence.to_dict()
            #stanza_token_sentence = merge_stanza_token_sentences(stanza_token_sentences2)
            #tokens_by_id = {token['id']:token for token in stanza_token_sentence}
            #mwt_cases = get_mwts(stanza_token_sentence, tokens_by_id)
            #sentence = re.findall(tokenization_pattern, phrase)
            #tagged_sentences = tag_nlp([sentence])     
            #tagged_sentences = tagged_sentences.to_dict()
            #tagged_sentence = tagged_sentences[0]
            #assert len(tagged_sentence)==len(sentence)

            #sentence = spans(rphrase,sentence)

            #stanza_2_tagged = get_stanza_2_tagged(stanza_token_sentence, tagged_sentence)

            #max_str = sentence[-1][-1]
            #raw_text =" "*max_str
            #sent = []
            #ant2new = {}
            #ant2new[0]=0
            #token_id=1
            #for (token,start_char,end_char),tagged_token in zip(sentence,tagged_sentence):
                #idx=tagged_token['id']
                #ant2new[idx]=token_id
                #tagged_token.pop('key',None)
                #tagged_token.pop('misc',None)
                #tagged_token.pop('id',None)
                #tagged_token.pop('text',None)

                #if not len(mwt_cases)==0:
                    #mwt_token_key = mwt_cases[0][0]
                    #mwt_tokens = mwt_cases[0][1]

                    #if token == mwt_token_key:
                        #token_id0 = token_id
                        #token_id = token_id + len(mwt_tokens)-1
                        #token_information = {doc.ID: (token_id0, token_id), doc.TEXT: token, \
                                     #doc.MISC: f'start_char={start_char}|end_char={end_char}'}
                        #token_information = {**token_information, **tagged_token}
                        #sent.append(token_information)
                        #print(mwt_tokens)
                        #for i,c in enumerate(mwt_tokens):
                            #print('c:',c)
                            #try:
                                #c.pop('id')
                            #except: 
                                #print('except:',c)
                                #raise
                            #print(stanza_2_tagged)
                            #print(c)
                            #c['head'] = stanza_2_tagged[c['head']]
                            #token_information = {doc.ID: token_id0 + i}
                            #sent.append({**token_information, **c})
                        #mwt_cases = mwt_cases[1:]
                    #else:
                        #token_information = {doc.ID: token_id, doc.TEXT: token, \
                                 #doc.MISC: f'start_char={start_char}|end_char={end_char}'}
                        #token_information = {**token_information, **tagged_token}
                        #sent.append(token_information)

                #else:
                    #token_information = {doc.ID: token_id, doc.TEXT: token, \
                                 #doc.MISC: f'start_char={start_char}|end_char={end_char}'}
                    #token_information = {**token_information, **tagged_token}
                    #sent.append(token_information)

                #token_id+=1

                #raw_text = raw_text[:start_char] + token + raw_text[end_char:]
            #raw_texts.append(raw_text)
            #print(ant2new)
            #for i in range(len(sent)):
                #new_head = ant2new[sent[i]['head']]
                #sent[i]['head'] = int(new_head)

            #new_document.append(sent)
    #raw_texts='\n\n'.join(raw_texts)
    #phrases_str = '\n\n'.join(phrases)
    #new_document=doc.Document(new_document, phrases_str)
    phrases = []
    for phrase,rphrase in tqdm(list(sentences)):
        if not phrase.strip()=='':
            phrases.append(rphrase)
            #try:
                #print(rphrase.encode('latin-1', 'ignore'))
            #except:
                #pass
    new_document = tag_nlp(phrases)
    segmented_text = new_document.to_dict()
    conllu = CoNLL.convert_dict(segmented_text)
    output = list_to_conllu_text(input_filename, conllu, phrases)  
    return output

def stanza_inference(input_file, output_folder, processing_mode, tag_nlp, nlp_sentece, verbose=True):
    #stanza.download('pt')
    output_name = os.path.basename(input_file).replace(".txt", "")
    if processing_mode == "conllu":
        outfile = output_name + "_stanza.conllu"
    else:
        outfile = "{}_{}_{}.txt".format(output_name, "stanza", processing_mode)

    #nlp = Pipeline(lang='pt', processors='tokenize,pos,lemma,mwt', tokenize_pretokenized=True, use_gpu=False)
    # Colocar mwt na lista de processors quando quiser multi-word tokenization
    if verbose:
        sys.stderr.write("Starting to process text in file {0} at {1}\n".format(input_file, str(datetime.datetime.now())))
    
    
    output = conllu_process_file(input_file, output_name, tag_nlp, nlp_sentece)

    # print somente para analisar se as palavras foram separadas corretamente. Caso sim, devem aparecer o token e,
    # em words, suas possíveis contrações.
    #for sentence in doc.sentences:
    #    for token in sentence.tokens:
    #        print(f'token: {token.text}\twords: {", ".join([word.text for word in token.words])}')

    if verbose:
        print("========= Processed sentences: =========")
        print(output)
        sys.stderr.write("... processing completed at {0}\n".format(str(datetime.datetime.now())))

    # Salva o arquivo conllu
    file = open(os.path.join(output_folder, outfile), "w", encoding='utf-8')
    file.write(output)
    file.close()
