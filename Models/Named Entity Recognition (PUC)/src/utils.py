import pandas as pd
import os
from collections import defaultdict
from glob import glob
import pandas as pd
import numpy as np
import stanza
import torch
import json
import os



def get_entities():
    geocrono = pd.read_csv('./data/unidades_cronoestratigrafica.csv',index_col=0)
    geocrono = list(set(geocrono['CRONOESTRATIGRFIA (ROCHA)'].to_list()))
    
    campo = pd.read_csv('./data/campo.csv',index_col=0)
    campo = list(set(campo['CAMPO'].to_list()))
    
    bacia = pd.read_csv('./data/bacia.csv',index_col=0)
    bacia = list(set(bacia['BACIA'].to_list()))
    
    litologia = pd.read_csv('./data/litologia.csv',index_col=0)
    litologia = list(set(litologia['LITOLOGIA'].to_list()))
    
    label2list = {'uniCRONO':geocrono,'CAMP':campo,'BAC':bacia,'LIT':litologia}
    return label2list

def transform_sent(new_text):
    new_text = new_text.replace('ç','c')
    new_text = new_text.replace('ã','a')
    new_text = new_text.replace('ç','c')
    new_text = new_text.replace('ã','a')
    new_text= new_text.replace('õ','o')
    new_text= new_text.replace('Ã','A')
    new_text= new_text.replace('Õ','o')
    new_text= new_text.replace('Ç','C')
    new_text= new_text.replace('ê','e')
    new_text= new_text.replace('Ê','E')
    new_text= new_text.replace('É','E')
    new_text= new_text.replace('é','e')
    new_text= new_text.replace('Í','I')
    new_text= new_text.replace('í','i')        
    new_text= new_text.replace('Ó','O')
    new_text= new_text.replace('ó','o')
    new_text= new_text.replace('Ô','O')
    new_text= new_text.replace('ô','o')
    new_text= new_text.replace('Â','A')
    new_text= new_text.replace('â','a')
    new_text= new_text.replace('Ú','U')
    new_text= new_text.replace('ú','u')
    new_text= new_text.replace('á','a')
    new_text= new_text.replace('Á','A')
    return new_text.lower()


def get_anotation(list_words,tokens):
    labels = np.array(['O']*len(tokens))
    if list_words == '':
        return '_'.join(labels)

    list_words = list_words.split(',')
    for word in list_words:
        word_part = word.split(' ')
        for idx, token in enumerate(tokens):
            if len(word_part) == 1:
                if word_part[0] == token:
                    labels[idx] = 'B'
            else:
                if idx >= (len(tokens) - len(word_part) + 1):
                    continue
                if word == ' '.join(tokens[idx:idx+len(word_part)]):
                    labels[idx] = 'B'
                    labels[idx+1:idx+len(word_part)] = 'I'
                
    return '_'.join(labels)

def annotation(args):
    doc_path,label2list = args
    name = doc_path.split('/')[-1][:-4]
    if os.path.exists(os.path.join('./post_tag_docs_3/annotation/',f'{name}.csv')):
        return (doc_path,'ok')
    else:
        df = pd.read_csv(doc_path,index_col=0)
        df_sent = pd.DataFrame([], columns=['sent','sent_transform','uniCRONO', 'CAMP', 'BAC', 'LIT']) 
        df_new = pd.DataFrame([], columns=list(df.columns.to_list() + list(label2list.keys())))
        sents = df.groupby(['sent'])

        aux_ = {}            
        for key in sents.groups.keys():
            grp = sents.get_group(key)
            grp['text'] = grp['text'].fillna(' ') 
            sent = ' '.join(grp['text'].to_list()).lower()
            #sent = ' '.join(sents.get_group(key)['text'].to_list()).lower()
            sent_t = transform_sent(sent)
            teste = defaultdict(str)
            aux = []
            for ner_entity, ner_list in label2list.items():
                for word in ner_list:
                    word_ = transform_sent(word)
                    if f' {word_} ' in sent_t:
                        aux.append([word, ner_entity])
                        teste[ner_entity] += f'{word}|'

            if aux != []:
                aux_.update({key:aux})


            dicio = {'sent':sent,\
                     'sent_transform':sent_t}
            dicio.update(teste)
            df_sent = df_sent.append(dicio,ignore_index=True)

        df_sent = df_sent.fillna('')

        for col in label2list.keys():
            df_sent[f'{col}_label'] = df_sent.apply(lambda x: get_anotation(x[col], x['sent_transform']), axis=1)

        for key in sents.groups.keys():
            grupo = sents.get_group(key)
            for col in label2list.keys():
                grupo[col] = df_sent.loc[key][f'{col}_label'].split('|')

            df_new = df_new.append(grupo,ignore_index=True)
        df_new.to_csv(os.path.join('./post_tag_docs_3/annotation/',f'{name}.csv'))
        return (doc_path,'ok')

    
def pos_neg_identification(uniCRONO, BAC, LIT, CAMP):
    if uniCRONO != 'O' or BAC  != 'O' or LIT != 'O' or CAMP != 'O':
        return 'pos'
    else:
        return 'neg'

def entity_identification(list_label):
    if 'B' in list_label:
        return 1
    else:
        return 0

def ajust_data(args):
    file, label2list = args
    
    df_pos = pd.DataFrame([],columns=['text','text_transform','doc','words','upos','uniCRONO','BAC','LIT','CAMP','uniCRONO_lab','BAC_lab','LIT_lab','CAMP_lab'])
    df_neg = pd.DataFrame([],columns=['text','doc'])
    
    df = pd.read_csv(file,index_col=0)
    df['valid'] = df.apply(lambda x: pos_neg_identification(x['uniCRONO'], x['BAC'],x['LIT'],x['CAMP']), axis=1)
    df = df.fillna('_')
    
    grp_sent = df.groupby(['sent'])
    aux = df[df['valid']!='neg']
    
    if aux.shape[0] > 0:
        grp_aux = aux.groupby(['sent'])
        sents_pos = grp_aux.groups.keys() 
        for key in grp_aux.groups.keys():
            dict_aux = {'text':' '.join(grp_sent.get_group(key)['text'].to_list()),\
                        'text_transform':transform_sent(' '.join(grp_sent.get_group(key)['text'].to_list())),\
                        'doc':grp_sent.get_group(key)['doc'].unique()[0],\
                        'words':'|'.join(grp_aux.get_group(key)['text'].to_list()),\
                        'upos':'|'.join(grp_aux.get_group(key)['upos'].to_list())}

            for key_ner in label2list.keys():
                dict_aux[key_ner] = entity_identification(grp_aux.get_group(key)[key_ner].to_list())
                dict_aux[f'{key_ner}_lab'] = '|'.join(grp_sent.get_group(key)[key_ner].to_list())

            df_pos = df_pos.append(dict_aux,ignore_index=True)
    else:
        sents_pos =[]
          
    for key_sent in grp_sent.groups.keys():
        if key_sent not in sents_pos:
            dict_aux = {'text':' '.join(grp_sent.get_group(key_sent)['text'].to_list()),\
                        'doc':grp_sent.get_group(key_sent)['doc'].unique()[0]}
            df_neg = df_neg.append(dict_aux,ignore_index=True)

    return (df_pos,df_neg)

def get_post_tag(args):
    sentence, idx, doc_path = args
    df = pd.DataFrame([],columns=['id','text','upos','start_char','end_char','sent'])
    for token in sentence.tokens:
        dicio = token.to_dict()[0]
        dicio.update({'sent':idx, 'doc':doc_path})
        df = df.append(dicio,ignore_index=True)
    
    return df

def ajust_dataframe(args):
    grp, label2list = args
    
    df_sent = pd.DataFrame([], columns=['sent','sent_transform','uniCRONO', 'CAMP', 'BAC', 'LIT'])
    doc = list(grp['doc'].unique())[0]
    upos = '|'.join(grp['upos'].to_list())
    sent = ' '.join(grp['text'].to_list())
    sent_t = transform_sent(sent)
    teste = defaultdict(str)
    teste['upos'] = upos
    
    for ner_entity, ner_list in label2list.items():
        for word in ner_list:
            word_ = transform_sent(word)
            if f' {word_} ' in sent_t:
                teste[ner_entity] += f'{word}|'

    dicio = {'sent':sent,\
             'sent_transform':sent_t,\
             'doc':doc}
    dicio.update(teste)
    
    return df_sent.append(dicio,ignore_index=True)





# ==================================== Train Models ======================================
import pandas as pd
from keras.preprocessing.sequence import pad_sequences
from collections import defaultdict, Counter
from itertools import chain
import numpy as np

def readcsv(filename):

    data = pd.read_csv(filename,sep='\t')
    agg_func = lambda s: [(w, t) for w,t in zip(s['0'].values.tolist(),
                                                        s['1'].values.tolist())]
    data = data.groupby("sentence").apply(agg_func)
       
    return data

class Vocab:
    def __init__(self,
                 special_tokens=tuple()):
        self.special_tokens = special_tokens
        self._t2i = defaultdict(lambda: 0)
        self._i2t = []
        
    def fit(self, tokens):
        count = 0
        self.freqs = Counter(chain(*tokens))
        for special_token in self.special_tokens:
            self._t2i[special_token] = count
            self._i2t.append(special_token)
            count += 1
        for token, freq in self.freqs.most_common():
            if token not in self._t2i:
                self._t2i[token] = count
                self._i2t.append(token)
                count += 1

    def __call__(self, batch, **kwargs):
        indices_batch = []
        for tokens in batch:
            indices = []
            for token in tokens:
                indices.append(self[token])
            indices_batch.append(indices)
        return indices_batch

    def __getitem__(self, key):
        if isinstance(key, (int, np.integer)):
            return self._i2t[key]
        elif isinstance(key, str):
            return self._t2i[key]
        else:
            raise NotImplementedError("not implemented for type `{}`".format(type(key)))
    
    def __len__(self):
        return len(self._i2t)

class NerDatasetReader:
    def read(self, data_path):
        data_parts = ['train', 'valid', 'test']
        extension = '.csv'
        dataset = {}
        for data_part in data_parts:
            file_path = data_path + data_part + extension
            dataset[data_part] = self.read_file(str(file_path))
        return dataset
            
    def read_file(self, file_path):
        data = pd.read_csv(file_path,sep='\t')
        agg_func = lambda s: [(w, t) for w,t in zip(s['0'].values.tolist(),
                                                        s['1'].values.tolist())]
        data = data.groupby("sentence").apply(agg_func)
    
        samples = []
        tags=[]
        tokens=[]
   
        for content in data:
            if len(tokens)!=0:
                samples.append((tokens,tags))
                tokens=[]
                tags=[]
            else:
                tokens.extend([token[0] for token in content ])
                tags.extend([tag[1] for tag in content ])

        
        return samples

def padding(sentences, labels, max_len, padding='post'):
    padded_sentences = pad_sequences(sentences, max_len, padding='post')
    padded_labels = pad_sequences(labels, max_len, padding='post')
    return padded_sentences, padded_labels

def idx_to_label(predictions, correct, idx2Label): 
    label_pred = []    
    for sentence in predictions:
        for i in sentence:
            label_pred.append([idx2Label[elem] for elem in i ])

    label_correct = []  
    if correct != None:
        for sentence in correct:
            for i in sentence:
                label_correct.append([idx2Label[elem] for elem in i ]) 
        
    return label_correct, label_pred
