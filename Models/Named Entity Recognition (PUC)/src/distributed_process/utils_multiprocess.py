from __future__ import absolute_import, division, print_function

import argparse
import json
import logging
import os
import random
import pandas as pd

import numpy as np
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from transformers import (WEIGHTS_NAME, AdamW, BertConfig,
                                  BertForTokenClassification, BertTokenizer,
                                  get_linear_schedule_with_warmup)
from torch import nn
from torch.utils.data import (DataLoader, RandomSampler, SequentialSampler,
                              TensorDataset)
from torch.utils.data.distributed import DistributedSampler
from tqdm import tqdm, trange

from seqeval.metrics import classification_report
from seqeval.scheme import IOB2

class InputExample(object):

    def __init__(self, guid, text_a, text_b=None, label=None):

        self.guid = guid
        self.text_a = text_a
        self.text_b = text_b
        self.label = label

class InputFeatures(object):

    def __init__(self, input_ids, input_mask, segment_ids, label_id, valid_ids=None, label_mask=None):
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_id = label_id
        self.valid_ids = valid_ids
        self.label_mask = label_mask

def alter_tokens(tokens):
    cont_tokens = len(tokens)
    if cont_tokens > 20:
        num_idx_choice = random.randint(1,3)
        aux = False
    elif cont_tokens > 5:
        num_idx_choice = random.randint(1,2)
        aux = False
    else:
        aux = True    
    if aux:
        return tokens
    
    else:
        list_idx = list(np.arange(len(tokens)))
        random.shuffle(list_idx)

        for i in range(num_idx_choice):
            tokens[list_idx[i]] = '[UNK]'

        return tokens

def get_vocab(tokenizer):
    vocab = [token for idx,token in enumerate(tokenizer.vocab) if idx > 103]
    return vocab

def alter_tokens_ten_percent(tokens, vocab):
    if len(tokens) < 5:
        return tokens
    try:
        list_idx = list(np.arange(len(tokens)))
        random.shuffle(list_idx)
        cont_idx = int(len(list_idx)*0.1)

        for idx, index in enumerate(list_idx[:int(len(list_idx)*0.1)]):
            if idx >= int(cont_idx/2):
                tokens[index] = '[UNK]'
            else:
                tokens[index] = vocab[random.randint(0,len(vocab))]
        return tokens
    except:
        return tokens

def convert_examples_to_features_2(args):

    ex_index, example, label_list, max_seq_length, tokenizer = args
    label_map = {label : i for i, label in enumerate(label_list,1)}

   
    vocab = get_vocab(tokenizer)
    
    
    textlist = example.text_a.split(' ')
    labellist = example.label
    tokens = []
    labels = []
    valid = []
    label_mask = []
    for i, word in enumerate(textlist):
        token = tokenizer.tokenize(word)

        tokens.extend(token)
        label_1 = labellist[i]
        for m in range(len(token)):
            if m == 0:
                labels.append(label_1)
                valid.append(1)
                label_mask.append(1)
            else:
                valid.append(0)

    tokens = alter_tokens_ten_percent(tokens, vocab)
    #return label_1,tokens

    if len(tokens) >= max_seq_length - 1:
        tokens = tokens[0:(max_seq_length - 2)]
        labels = labels[0:(max_seq_length - 2)]
        valid = valid[0:(max_seq_length - 2)]
        label_mask = label_mask[0:(max_seq_length - 2)]
    ntokens = []
    segment_ids = []
    label_ids = []
    ntokens.append("[CLS]")
    segment_ids.append(0)
    valid.insert(0,1)
    label_mask.insert(0,1)
    label_ids.append(label_map["[CLS]"])
    for i, token in enumerate(tokens):
        ntokens.append(token)
        segment_ids.append(0)
        if len(labels) > i:
            label_ids.append(label_map[labels[i]])
    ntokens.append("[SEP]")
    segment_ids.append(0)
    valid.append(1)
    label_mask.append(1)
    label_ids.append(label_map["[SEP]"])
    input_ids = tokenizer.convert_tokens_to_ids(ntokens)    # Acho que a alteração deve começar antes daqui (mas como converter palavras em tokens nan)
    input_mask = [1] * len(input_ids)
    label_mask = [1] * len(label_ids)
    while len(input_ids) < max_seq_length:
        input_ids.append(0)
        input_mask.append(0)
        segment_ids.append(0)
        label_ids.append(0)
        valid.append(1)
        label_mask.append(0)
    while len(label_ids) < max_seq_length:
        label_ids.append(0)
        label_mask.append(0)
    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length
    assert len(label_ids) == max_seq_length
    assert len(valid) == max_seq_length
    assert len(label_mask) == max_seq_length


    """if ex_index < 5:
        logger.info("*** Example ***")
        logger.info("guid: %s" % (example.guid))
        logger.info("tokens: %s" % " ".join(
                [str(x) for x in tokens]))
        logger.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
        logger.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
        logger.info(
                "segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
#             logger.info("label: %s (id = %d)" % (example.label, label_ids))
"""
    features = InputFeatures(input_ids=input_ids, input_mask=input_mask, segment_ids=segment_ids, label_id=label_ids, valid_ids=valid, label_mask=label_mask)
    
    return features
