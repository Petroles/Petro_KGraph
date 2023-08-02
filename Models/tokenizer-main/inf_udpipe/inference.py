import sys
import os
import datetime
import ufal.udpipe
import re

from utils.udpipe_filters import preprocessing, postprocessing

script_path = os.path.dirname(os.path.realpath(__file__))
truecaser_script_dir = os.path.join(script_path, "dependencies", "truecaser")
sys.path.insert(1, truecaser_script_dir)

class Model:
    def __init__(self, path):
        """Load given model."""
        self.model = ufal.udpipe.Model.load(path)
        if not self.model:
            raise Exception("Cannot load UDPipe model from file '%s'" % path)

    def tokenize(self, text):
        """Tokenize the text and return list of ufal.udpipe.Sentence-s."""
        tokenizer = self.model.newTokenizer(self.model.DEFAULT)
        if not tokenizer:
            raise Exception("The model does not have a tokenizer")
        return self._read(text, tokenizer)

    def read(self, text, format):
        """Load text in the given format (conllu|horizontal|vertical) and return list of ufal.udpipe.Sentence-s."""
        input_format = ufal.udpipe.InputFormat.newInputFormat(format)
        if not input_format:
            raise Exception("Cannot create input format '%s'" % format)
        return self._read(text, input_format)

    def _read(self, text, input_format):
        input_format.setText(text)
        error = ufal.udpipe.ProcessingError()
        sentences = []

        sentence = ufal.udpipe.Sentence()
        while input_format.nextSentence(sentence, error):
            sentences.append(sentence)
            sentence = ufal.udpipe.Sentence()
        if error.occurred():
            raise Exception(error.message)

        return sentences

    def tag(self, sentence):
        """Tag the given ufal.udpipe.Sentence (inplace)."""
        self.model.tag(sentence, self.model.DEFAULT)

    def parse(self, sentence):
        """Parse the given ufal.udpipe.Sentence (inplace)."""
        self.model.parse(sentence, self.model.DEFAULT)

    def write(self, sentences, format):
        """Write given ufal.udpipe.Sentence-s in the required format (conllu|horizontal|vertical)."""

        output_format = ufal.udpipe.OutputFormat.newOutputFormat(format)
        output = ''
        for sentence in sentences:
            output += output_format.writeSentence(sentence)
        output += output_format.finishDocument()

        return output


def udpipe_inference(input_file: str, output_folder:str,  processing_mode: str = "conllu", verbose: bool = True):
    output_name = os.path.basename(input_file).replace(".txt", "")
    if processing_mode == "conllu":
        outfile = output_name + "_udpipe.conllu"
    else:
        outfile = "{}_{}_{}.txt".format(output_name, "udpipe", processing_mode)
    sys.stderr.write(
        "Starting to process text in file {0} at {1}\n".format(input_file, str(datetime.datetime.now())))
    file = open(input_file, "rb")
    text = file.read().decode('utf-8')
    if verbose:
        print("============= Raw text: =============")
        print(text)
    text, dict_of_encodings = preprocessing(text)
    model_file = os.path.join(os.getcwd(), "models", "portuguese-bosque-ud-2.4-190531.udpipe")
    model = Model(model_file)
    sentences = model.tokenize(text)

    for s in sentences:
        model.tag(s)
        model.parse(s)
    conllu = model.write(sentences, processing_mode)
    conllu = postprocessing(conllu, dict_of_encodings)
    vertical = model.write(sentences, "vertical")
    vertical = postprocessing(vertical, dict_of_encodings)
    horizontal = model.write(sentences, "horizontal")
    horizontal = postprocessing(horizontal, dict_of_encodings)
    if verbose:
        print("========= Processed sentences: =========")
        print(conllu)
        sys.stderr.write("... processing completed at {0}\n".format(str(datetime.datetime.now())))
    open(outfile, "w", encoding='utf-8').write(conllu)
    open(os.path.join(output_folder, "{}_udpipe_tokens.txt".format(output_name)), "w", encoding='utf-8').write(vertical)
    open(os.path.join(output_folder, "{}_udpipe_sents.txt".format(output_name)), "w", encoding='utf-8').write(horizontal)

