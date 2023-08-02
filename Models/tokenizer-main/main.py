from inf_stanza.inference import stanza_inference
import os
import argparse
import stanza
from stanza import Pipeline

# mode_help = "training mode{}. Options are:" \
#             "\n - conllu: saves in .conllu model." \
#             "\n - vertical: saves tokens in .txt file." \
#             "\n - horizontal: saves sentences in .txt file."

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Tokenization Process for multiple thesis')
    parser.add_argument('--idir', '-i', help='Path to thesis .txt files.', type=str, required=True)
    parser.add_argument('--odir', '-o', help='Path to outfolder .conllu files.', type=str, required=True)
    # parser.add_argument('--processing_type', '-m', help=mode_help, type=str, default='Abstract',
    #                     required=False)

    args = parser.parse_args()
    input_folder = args.idir
    output_folder = args.odir

    if not os.path.exists(input_folder):
        print("Input path ({}) does not exist.".format(input_folder))

    if not os.path.exists(output_folder):
        print("Output path ({}) does not exist.".format(output_folder))

    if os.path.isfile(input_folder):
        input_folder = os.path.basename(input_folder)
        
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)

    #tok_nlp = Pipeline(lang='pt', tokenize_pretokenized=False, use_gpu=True)#processors='tokenize,mwt', 
    tag_nlp = Pipeline(lang='pt', tokenize_pretokenized=False, tokenize_no_ssplit=True, use_gpu=True, depparse_model_path="./models/pt_bosquepetrolestodooeg_parser.pt")#processors='tokenize,pos,lemma,depparse',
    nlp_sentece = stanza.Pipeline(lang='pt', processors='tokenize')
    for input_file in os.listdir(input_folder):
        output_name = os.path.basename(input_file).replace(".txt", "")
        outfile = output_name + "_stanza.conllu"
        output_file = os.path.join(output_folder, outfile)
        if not os.path.exists(output_file):
            stanza_inference(os.path.join(input_folder, input_file), output_folder, processing_mode='conllu', tag_nlp=tag_nlp, nlp_sentece=nlp_sentece, verbose=False)
        # udpipe_inference(os.path.join(input_folder, input_file), output_folder, verbose=False)

