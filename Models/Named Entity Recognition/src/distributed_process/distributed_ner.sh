#!/bin/bash

CONFIG_FILE=$1

#'bash distributed_detectron.sh config_1.json'
#bash distributed_detectron.sh config_2.json
#bash distributed_detectron.sh config_3.json
#bash distributed_detectron.sh config_4.json

sbatch --export=CONFIG_FILE=$CONFIG_FILE distributed_ner.srm