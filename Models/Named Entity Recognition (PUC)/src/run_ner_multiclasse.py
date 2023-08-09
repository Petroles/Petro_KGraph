# !/usr/bin/env python
# -*- coding:utf-8 -*-

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

from multiprocessing import Pool
from utils_multiprocess import convert_examples_to_features_2
from tqdm import tqdm

logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = logging.INFO)
logger = logging.getLogger(__name__)

class Ner(BertForTokenClassification):

    def forward(self, input_ids, token_type_ids=None, attention_mask=None, labels=None,valid_ids=None,attention_mask_label=None):
        sequence_output = self.bert(input_ids, token_type_ids, attention_mask,head_mask=None)[0]
        batch_size,max_len,feat_dim = sequence_output.shape
        valid_output = torch.zeros(batch_size,max_len,feat_dim,dtype=torch.float32,device='cuda')

        for i in range(batch_size):
            jj = -1
            for j in range(max_len):
                    if valid_ids[i][j].item() == 1:
                        jj += 1
                        valid_output[i][jj] = sequence_output[i][j]
        sequence_output = self.dropout(valid_output)
        logits = self.classifier(sequence_output)

        if labels is not None:
            loss_fct = nn.CrossEntropyLoss(ignore_index=0)
            # Only keep active parts of the loss
            #attention_mask_label = None
            if attention_mask_label is not None:
                active_loss = attention_mask_label.view(-1) == 1
                active_logits = logits.view(-1, self.num_labels)[active_loss]
                active_labels = labels.view(-1)[active_loss]
                loss = loss_fct(active_logits, active_labels)
            else:
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            return loss
        else:
            return logits


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

def readfile(filename):

    dataset=[]
    data = pd.read_csv(filename,sep='\t').fillna(method="ffill")
    agg_func = lambda s: [(w, t) for w,t in zip(s['0'].values.tolist(),
                                                        s['1'].values.tolist())]
    for i in data.groupby("sentence").apply(agg_func).tolist():
        dataset.append(i)
    index=[]
    sentence = []
    label = []
    return dataset

class DataProcessor(object):

    @classmethod
    def _read_tsv(cls, input_file, quotechar=None):
        return readfile(input_file)


class NerProcessor(DataProcessor):
    def get_train_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "train.csv")), "train")

    def get_dev_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "valid.csv")), "dev")

    def get_test_examples(self, data_dir):
        return self._create_examples(
            self._read_tsv(os.path.join(data_dir, "test.csv")), "test")

    def get_labels(self, list_classes):
        #return ["O", "B-BAC", "I-BAC", "B-CAMP", "I-CAMP", "B-uniCRONO", "I-uniCRONO", "B-LIT", "I-LIT", "[CLS]", "[SEP]"]
        classes = ["O"]
        new_classes = []
        for i in list_classes:
            new_classes.extend(["B="+i, "I="+i])
        classes.extend(new_classes)
        classes.extend(["[CLS]", "[SEP]"])
        print("classes ", classes)
        return classes

    def _create_examples(self,lines,set_type):
        examples = []
        for i, line in enumerate(lines):
            guid = "%s-%s" % (set_type, i)
            text_a = '$#7#$'.join([l[0] for l in line])
            text_b = None
            label = [l[1] for l in line]
            examples.append(InputExample(guid=guid,text_a=text_a,text_b=text_b,label=label))
        return examples

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

def get_text_label_later_del(textlist, labellist):
    text, label = textlist.copy(), labellist.copy()
    
    list_del = list(np.arange(len(textlist)))
    random.shuffle(list_del,random=random.random)
    
    if len(textlist) > 30:
        cont = random.randint(1,3)
    elif len(textlist) < 5:
        return textlist, labellist
    else:
        cont = random.randint(1,2)
    
    list_del = list_del[:cont]
    list_del.sort()
    for i in range(cont):
        text.pop(list_del[i]-i)
        label.pop(list_del[i]-i)
    
    return text, label
    
def convert_examples_to_features(examples, label_list, max_seq_length, tokenizer):

    label_map = {label : i for i, label in enumerate(label_list,1)}

    features = []    
    vocab = get_vocab(tokenizer)
    list_del = list(np.arange(len(examples)))
    random.shuffle(list_del,random=random.random)
    list_del = list_del[:int(len(list_del)*0.1)]
    
    for (ex_index,example) in enumerate(examples):
        
        textlist = example.text_a.split(' ')
        labellist = example.label
        
        if ex_index in list_del:
            textlist, labellist = get_text_label_later_del(textlist, labellist)
        
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
        features.append(
                InputFeatures(input_ids=input_ids,
                              input_mask=input_mask,
                              segment_ids=segment_ids,
                              label_id=label_ids,
                              valid_ids=valid,
                              label_mask=label_mask))
    return features
def main():
    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--data_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="The input data dir. Should contain the .tsv files (or other data files) for the task.")
    parser.add_argument("--bert_model", default=None, type=str, required=True,
                        help="Bert pre-trained model selected in the list: neuralmind/bert-base-portuguese-cased,                 "
                             "neuralmind/bert-large-portuguese-cased.")
    parser.add_argument("--task_name",
                        default=None,
                        type=str,
                        required=True,
                        help="The name of the task to train.")
    parser.add_argument("--output_dir",
                        default=None,
                        type=str,
                        required=True,
                        help="The output directory where the model predictions and checkpoints will be written.")

    ## Other parameters
    parser.add_argument("--cache_dir",
                        default="",
                        type=str,
                        help="Where do you want to store the pre-trained models downloaded")
    parser.add_argument("--max_seq_length",
                        default=128,
                        type=int,
                        help="The maximum total input sequence length after WordPiece tokenization. \n"
                             "Sequences longer than this will be truncated, and sequences shorter \n"
                             "than this will be padded.")
    parser.add_argument("--do_train",
                        action='store_true',
                        help="Whether to run training.")
    parser.add_argument("--do_eval",
                        action='store_true',
                        help="Whether to run eval or not.")
    parser.add_argument("--eval_on",
                        default="dev",
                        help="Whether to run eval on the dev set or test set.")
    parser.add_argument("--train_batch_size",
                        default=32,
                        type=int,
                        help="Total batch size for training.")
    parser.add_argument("--eval_batch_size",
                        default=8,
                        type=int,
                        help="Total batch size for eval.")
    parser.add_argument("--learning_rate",
                        default=5e-5,
                        type=float,
                        help="The initial learning rate for Adam.")
    parser.add_argument("--num_train_epochs",
                        default=3.0,
                        type=float,
                        help="Total number of training epochs to perform.")
    parser.add_argument("--warmup_proportion",
                        default=0.1,
                        type=float,
                        help="Proportion of training to perform linear learning rate warmup for. "
                             "E.g., 0.1 = 10%% of training.")
    parser.add_argument("--weight_decay", default=0.01, type=float,
                        help="Weight deay if we apply some.")
    parser.add_argument("--adam_epsilon", default=1e-8, type=float,
                        help="Epsilon for Adam optimizer.")
    parser.add_argument("--max_grad_norm", default=1.0, type=float,
                        help="Max gradient norm.")
    parser.add_argument("--no_cuda",
                        action='store_true',
                        help="Whether not to use CUDA when available")
    parser.add_argument("--local_rank",
                        type=int,
                        default=-1,
                        help="local_rank for distributed training on gpus")
    parser.add_argument('--seed',
                        type=int,
                        default=42,
                        help="random seed for initialization")
    parser.add_argument('--gradient_accumulation_steps',
                        type=int,
                        default=1,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument('--num_ealy_stoping_epochs',
                        type=int,
                        default=5,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument('--classes', 
                        default=["BAC", "CAMP", "uniCRONO", "LIT"],#["BAC", "CAMP", "uniCRONO", "ROCHA", "NCONSOLID"],
                        nargs='+',
                        required=False)


    args = parser.parse_args()

    processors = {"ner":NerProcessor}

    if args.local_rank == -1 or args.no_cuda:
        device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
        print('device:', device)       
        n_gpu = torch.cuda.device_count()
    else:
        torch.cuda.set_device(args.local_rank)
        device = torch.device("cuda", args.local_rank)
        n_gpu = 1
        # Initializes the distributed backend which will take care of sychronizing nodes/GPUs
        torch.distributed.init_processcat_group(backend='nccl')
    logger.info("device: {} n_gpu: {}, distributed training: {}".format(
        device, n_gpu, bool(args.local_rank != -1)))

    if args.gradient_accumulation_steps < 1:
        raise ValueError("Invalid gradient_accumulation_steps parameter: {}, should be >= 1".format(
                            args.gradient_accumulation_steps))

    args.train_batch_size = args.train_batch_size // args.gradient_accumulation_steps

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if not args.do_train and not args.do_eval:
        raise ValueError("At least one of `do_train` or `do_eval` must be True.")

    if os.path.exists(args.output_dir) and os.listdir(args.output_dir) and args.do_train:
        raise ValueError("Output directory ({}) already exists and is not empty.".format(args.output_dir))
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    task_name = args.task_name.lower()

    if task_name not in processors:
        raise ValueError("Task not found: %s" % (task_name))

    processor = processors[task_name]()
    label_list = processor.get_labels(args.classes)
    num_labels = len(label_list) + 1

    tokenizer = BertTokenizer.from_pretrained(args.bert_model)

    train_examples = None
    num_train_optimization_steps = 0
    if args.do_train:
        train_examples = processor.get_train_examples(args.data_dir)
        num_train_optimization_steps = int(
            len(train_examples) / args.train_batch_size / args.gradient_accumulation_steps) * args.num_train_epochs
        if args.local_rank != -1:
            num_train_optimization_steps = num_train_optimization_steps // torch.distributed.get_world_size()
            
    if args.local_rank not in [-1, 0]:
        torch.distributed.barrier() 
        
    config = BertConfig.from_pretrained(args.bert_model, num_labels=num_labels, finetuning_task=args.task_name)
    model = Ner.from_pretrained(args.bert_model,
              from_tf = False,
              config = config)
    #model.to(device)
    if args.local_rank == 0:
        torch.distributed.barrier() 

    param_optimizer = list(model.named_parameters())
    no_decay = ['bias','LayerNorm.weight']
    optimizer_grouped_parameters = [
        {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)], 'weight_decay': args.weight_decay},
        {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
        ]
    warmup_steps = int(args.warmup_proportion * num_train_optimization_steps)
    optimizer = AdamW(optimizer_grouped_parameters, lr=args.learning_rate, eps=args.adam_epsilon)

    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=num_train_optimization_steps
    )

    if n_gpu > 1:
        model = torch.nn.DataParallel(model)

    if args.local_rank != -1:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[args.local_rank],
                                                          output_device=args.local_rank,
                                                          find_unused_parameters=True)

    global_step = 0
    nb_tr_steps = 0
    tr_loss = 0
    label_map = {i : label for i, label in enumerate(label_list,1)}
    if args.do_train:
        
        list_args = [(idx, example, label_list, args.max_seq_length, tokenizer) for idx, example in enumerate(train_examples)]
        with Pool(processes=112) as p:
            train_features = list(tqdm(p.imap_unordered(convert_examples_to_features_2,list_args),total=len(list_args)))

        #train_features = convert_examples_to_features(
        #    train_examples, label_list, args.max_seq_length, tokenizer)
        
        logger.info("***** Running training *****")
        logger.info("  Num examples = %d", len(train_examples))
        logger.info("  Batch size = %d", args.train_batch_size)
        logger.info("  Num steps = %d", num_train_optimization_steps)
        all_input_ids = torch.tensor([f.input_ids for f in train_features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in train_features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in train_features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_id for f in train_features], dtype=torch.long)
        all_valid_ids = torch.tensor([f.valid_ids for f in train_features], dtype=torch.long)
        all_lmask_ids = torch.tensor([f.label_mask for f in train_features], dtype=torch.long)
        train_data = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_label_ids,all_valid_ids,all_lmask_ids)
        if args.local_rank == -1:
            train_sampler = RandomSampler(train_data)
        else:
            train_sampler = DistributedSampler(train_data)
        train_dataloader = DataLoader(train_data, sampler=train_sampler, batch_size=args.train_batch_size)

        model.train()
        model.to(device)
        min_loss = 1000000000000000000000000000000000000000000000000000000000000
        list_loss = []
        for _ in trange(int(args.num_train_epochs), desc="Epoch"):
            tr_loss = 0
            nb_tr_examples, nb_tr_steps = 0, 0
            for step, batch in enumerate(tqdm(train_dataloader, desc="Iteration")):
                batch = tuple(t.to(device) for t in batch)
                input_ids, input_mask, segment_ids, label_ids, valid_ids,l_mask = batch
                loss = model(input_ids, segment_ids, input_mask, label_ids,valid_ids,l_mask)
                if n_gpu > 1:
                    loss = loss.mean() # mean() to average on multi-gpu.
                if args.gradient_accumulation_steps > 1:
                    loss = loss / args.gradient_accumulation_steps

                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), args.max_grad_norm)
                
                tr_loss += loss.item()
                nb_tr_examples += input_ids.size(0)
                nb_tr_steps += 1
                if (step + 1) % args.gradient_accumulation_steps == 0:
                    optimizer.step()
                    scheduler.step()  # Update learning rate schedule
                    model.zero_grad()
                    global_step += 1
              
            
            if tr_loss < min_loss:
                min_loss = tr_loss
                # Save a trained model and the associated configuration
                model_to_save = model.module if hasattr(model, 'module') else model  # Only save the model it-self
                model_to_save.save_pretrained(args.output_dir)
                tokenizer.save_pretrained(args.output_dir)
                label_map = {i : label for i, label in enumerate(label_list,1)}
                model_config = {"bert_model":args.bert_model,"do_lower":False,"max_seq_length":args.max_seq_length,
                                "num_labels":len(label_list)+1,"label_map":label_map}
                json.dump(model_config,open(os.path.join(args.output_dir,"model_config.json"),"w"))
                print('Model saved!')
                # Load a trained model and config that you have fine-tuned
            
            if len(list_loss) >= args.num_ealy_stoping_epochs:
                cont_false = (tr_loss < np.array(list_loss[-args.num_ealy_stoping_epochs:])).tolist().count(False) 
                if cont_false > round(args.num_ealy_stoping_epochs*0.6):
                    print('Treinamento interrompido!')
                    break

            list_loss.append(tr_loss)
            #print(tr_loss)
            #print(list_loss)
            
    else:
        # Load a trained model and vocabulary that you have fine-tuned
        model = Ner.from_pretrained(args.output_dir)
        tokenizer = BertTokenizer.from_pretrained(args.output_dir)

    model.to(device)

    if args.do_eval and (args.local_rank == -1 or torch.distributed.get_rank() == 0):
        if args.eval_on == "dev":
            eval_examples = processor.get_dev_examples(args.data_dir)
        elif args.eval_on == "test":
            eval_examples = processor.get_test_examples(args.data_dir)
        else:
            raise ValueError("eval on dev or test set only")
        list_args = [(idx, example, label_list, args.max_seq_length, tokenizer) for idx, example in enumerate(eval_examples)]
        with Pool(processes=112) as p:
            eval_features = list(tqdm(p.imap_unordered(convert_examples_to_features_2,list_args),total=len(list_args)))
        
        #eval_features = convert_examples_to_features(eval_examples, label_list, args.max_seq_length, tokenizer)
        logger.info("***** Running evaluation *****")
        logger.info("  Num examples = %d", len(eval_examples))
        logger.info("  Batch size = %d", args.eval_batch_size)
        all_input_ids = torch.tensor([f.input_ids for f in eval_features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in eval_features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in eval_features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_id for f in eval_features], dtype=torch.long)
        all_valid_ids = torch.tensor([f.valid_ids for f in eval_features], dtype=torch.long)
        all_lmask_ids = torch.tensor([f.label_mask for f in eval_features], dtype=torch.long)
        eval_data = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_label_ids,all_valid_ids,all_lmask_ids)
        # Run prediction for full data
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=args.eval_batch_size)
        model.eval()
        eval_loss, eval_accuracy = 0, 0
        nb_eval_steps, nb_eval_examples = 0, 0
        y_true = []
        y_pred = []
        label_map = {i : label for i, label in enumerate(label_list,1)}
        print(label_map)
        len_label_map = len(label_map)
        print("[0,len_label_map-1, len_label_map] ", [0,len_label_map-1, len_label_map])
        for input_ids, input_mask, segment_ids, label_ids,valid_ids,l_mask in tqdm(eval_dataloader, desc="Evaluating"):
            input_ids = input_ids.to(device)
            input_mask = input_mask.to(device)
            segment_ids = segment_ids.to(device)
            valid_ids = valid_ids.to(device)
            label_ids = label_ids.to(device)
            l_mask = l_mask.to(device)

            with torch.no_grad():
                logits = model(input_ids, segment_ids, input_mask,valid_ids=valid_ids,attention_mask_label=l_mask)

            logits = torch.argmax(F.log_softmax(logits,dim=2),dim=2)
            logits = logits.detach().cpu().numpy()
            label_ids = label_ids.to('cpu').numpy()
            input_mask = input_mask.to('cpu').numpy()
                        
            for sentence in logits.tolist():
                y_pred.append([label_map[1] if int(elem) in [0,len_label_map-1, len_label_map] else label_map[elem] for elem in sentence])
                

            if label_ids.tolist() != None:
                for idx in label_ids.tolist():
                    y_true.append([ label_map[1] if int(elem) in [0,len_label_map-1, len_label_map] else label_map[elem] for elem in idx]) 
    
        #print(y_true)        
        y_true = [lista[1:-1] for lista in y_true]
        y_pred = [lista[1:-1] for lista in y_pred]

        # new_y_true, new_y_pred = [], []
        # for true, pred  in zip(y_true,y_pred):
        #     y, p = [], []
        #     for true_, pred_ in zip(true,pred):
        #         if true_ == '[CLS]':
        #             continue
        #         elif true_ == '[SEP]':
        #             new_y_true.append(y)
        #             new_y_pred.append(p)
        #             y, p = [], []
        #         else:
        #             y.append(true_)
        #             p.append(pred_)
        # y_true = new_y_true
        # y_pred = new_y_pred

        report = classification_report(y_true, y_pred, mode='strict', scheme=IOB2)
        #print(y_pred)
        
        logger.info("\n%s", report)
        output_eval_file = os.path.join(args.output_dir, "eval_results.txt")
        with open(output_eval_file, "w") as writer:
            logger.info("***** Eval results *****")
            logger.info("\n%s", report)
            writer.write(report)


if __name__ == "__main__":
    main()

