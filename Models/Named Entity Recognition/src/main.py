#!/usr/bin/env python
# coding: utf-8

# Remove warnings in jupyter
import warnings
warnings.filterwarnings("ignore")

from multiprocessing import Pool
from utils import get_post_tag
from utils import *
from tqdm import tqdm
from glob import glob
import pandas as pd
import numpy as np
import argparse
import stanza
#import torch
import json
import os
import logging


#device = "cuda" if torch.cuda.is_available() else "cpu"
#if device == 'cuda':
    # Selecionando GPU ou GPUs que serão utilizadas (0, 1, 2 ou 3)
#    os.environ["CUDA_VISIBLE_DEVICES"]= "0,1,2,3"


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


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Annotation initial dataset')
    parser.add_argument('--number_of_chunks', '-n', help='', type=int, required=False, default=1)
    parser.add_argument('--chunk_id', '-c', help='', type=int, required=False, default=0)  
    args = parser.parse_args()


    #list_paths = sorted(glob('./docs/*.txt'))
    #PATH='/nethome/projetos30/busca_semantica/_Geologica_snapshot_2021-05/extracoes/'
    #result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(PATH) for f in filenames if os.path.splitext(f)[1] == '.txt']
    #list_paths = [file for file in result if len(file.split('/')[-1][:-4])==64]
    
    
    PATHS=['/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/comunicadostecnicos_output_gpu/batch_1/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/comunicadostecnicos_output_gpu/batch_2/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/comunicadostecnicos_output_gpu/batch_3/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/comunicadostecnicos_output_gpu/batch_4/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/relatoriostecnicos_output_gpu/batch_1/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/relatoriostecnicos_output_gpu/batch_2/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/relatoriostecnicos_output_gpu/batch_3/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/relatoriostecnicos_output_gpu/batch_4/',
           '/nethome/recpinfo/busca_semantica/buscaict/BigOil/output_tornado/comunicadostecnicos_output_gpu_pt2/'
          ]
    list_paths = []
    for PATH in PATHS:
        list_paths += [os.path.join(PATH,filenames) for filenames in os.listdir(PATH) if os.path.splitext(filenames)[1] == '.txt' and len(os.path.splitext(filenames)[0]) == 6]
    
    label2list = get_entities()

    nlp = stanza.Pipeline('pt',processors='tokenize,pos',use_gpu=True)


    if args.number_of_chunks > 1:
        number_of_chunks_per_node = (len(list_paths)+args.number_of_chunks-1)//args.number_of_chunks
        start_index = (args.chunk_id)*number_of_chunks_per_node
        end_index = (args.chunk_id + 1)* number_of_chunks_per_node
        list_paths = list_paths[start_index:end_index]


    for doc_path in list_paths:

        try:
            with open(doc_path,'r',encoding='utf-16') as f:
                text = f.read()
        except:
            continue

        name = doc_path.split('/')[-1][:-4]
        if os.path.exists(os.path.join('./result_post_tag_pt/',f'{name}_.csv')) and os.path.exists(os.path.join('./result_post_tag_pt/annotation/',f'{name}_.csv')):
            print('This file already exist ',os.path.join('./result_post_tag_pt/',f'{name}_.csv'))
            continue
        try:
            
            text = nlp(text)

            list_args = [(sentence,idx,doc_path) for idx, sentence in enumerate(text.sentences)]
            with Pool(processes=50) as p:
                data = list(tqdm(p.map(get_post_tag,list_args),total=len(list_args),desc=f'Get sentences information'))

            df = pd.concat(data) 
            df.to_csv(os.path.join('./result_post_tag_pt/',f'{name}_.csv'))

            df['text'] = df.apply(lambda x: (x['end_char']-x['start_char'])*' ' if x['text'] is np.nan else x['text'], axis=1)
            df['upos'] = df['upos'].fillna('_')

            sents = df.groupby(['sent'])

            list_args = [(sents.get_group(key), label2list) for key in sents.groups.keys()]
            with Pool(processes=50) as p:
                data = list(tqdm(p.map(ajust_dataframe,list_args),total=len(list_args),desc=f'Ajust dataframe'))

            df_new = pd.concat(data)
            df_new = df_new.reset_index(drop=True)
            df_new = df_new.fillna('')    
            df_new.to_csv(os.path.join('./result_post_tag_pt/annotation/',f'{name}_.csv'))

            new_path = os.path.join('./result_post_tag_pt/',f'{name}_.csv')
            logging.info(f'End process {new_path}')
        except:
            new_path = os.path.join('./result_post_tag_pt/',f'{name}_.csv')
            print(os.path.join('./result_post_tag_pt/',f'{name}_.csv'))

