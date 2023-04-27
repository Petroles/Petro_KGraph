import sys
import os
import threading
import argparse
import time

def main(args):
    num_gpus_per_node = 4
    nodes = args.nodes.split(',')
    num_nodes = len(nodes)
    master_add = nodes[0]
    master_port = 9977
    process = num_nodes*num_gpus_per_node
    world_size = num_nodes*num_gpus_per_node
    python_args = [('--data_dir','./result_docs_select'),\
               ('--bert_model','neuralmind/bert-base-portuguese-cased'),\
                ('--train_batch_size',64),\
                ('--task_name','ner'),\
                ('--output_dir','./result_docs_select/multiclass_bert_model'),\
                ('--max_seq_length',256),\
                ('--do_train',''),\
                ('--num_train_epoch',10000),\
                ('--do_eval',''),\
                ('--num_ealy_stoping_epochs',30),\
                ('--warmup_proportion',0.1),\
                ('--local_rank',0),\
                ('--world_size',world_size),\
                ('--master_add',master_add),\
                ('--master_port',master_port),\
                ('--process',process)]

    python_args = ' '.join(['{} {}'.format(narg,varg) for narg,varg in python_args])
    
    aux = 0
    threads = []
    for node in nodes:
        for gpu_id in range(num_gpus_per_node):
            rank = gpu_id + aux
            singularity_command = f"SINGULARITYENV_CUDA_VISIBLE_DEVICES={gpu_id} singularity run -B {args.shared_folders} --nv {args.sif_file_path} "

            # mudar para o meu comandao python
            python_command =f'cd {args.project_home} ; nvidia-smi ; HOME={args.project_home} python run_ner_multiclass.py {python_args}'
            
            rank_python_command = python_command + f' --rank {rank} --cuda_device {gpu_id}'
            
            node_command = singularity_command + f"bash -c \"{rank_python_command}\""

            command = f"ssh {node} 'ulimit -u 10000 ; {node_command}'"
            
            def thread_function(command):
                os.system(command)
                
            thread = threading.Thread(target=thread_function, args=(command,))

            thread.start()

            threads.append(thread)

            time.sleep(5)
            
        aux += num_gpus_per_node
   
    for thread in threads:
        thread.join()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Model definition options
    parser.add_argument('--nodes', type=str, default='sdumont8090,sdumont8091')
    parser.add_argument('--shared_folders', type=str, default='/scratch/parceirosbr/bigoilict/share')
    parser.add_argument('--sif_file_path', type=str, required=True)
    parser.add_argument('--project_home', type=str,  default='/scratch/parceirosbr/bigoilict/share/BigOil/NER')
    #parser.add_argument('--master_add', type=str)
    #parser.add_argument('--master_port', type=str, default="9999")
    
    
    args = parser.parse_args()
    
    main(args)