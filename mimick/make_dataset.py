'''
Creates dataset for trained-embeddings prediction by character Bi-LSTM.
Inputs:
- A pre-trained embedding dictionary that is to be emulated by character model
- An optional set of downstream-task vocab words, those of which not present in the
    pre-trained embeddings will be output by the character model
    (only important for sanity statistics following model training)
'''
from __future__ import division
from _collections import defaultdict
import codecs
import argparse
import cPickle
import collections
import numpy as np

from util import charseq

__author__ = "Yuval Pinter, 2017"

POLYGLOT_UNK = unicode("<UNK>")
W2V_UNK = unicode("UNK")
PADDING_CHAR = "<*>"

Instance = collections.namedtuple("Instance", ["chars", "word_emb"])

def read_text_embs(files):
    words = []
    embs = []
    for filename in files:
        with codecs.open(filename, "r", "utf-8") as f:
            for line in f:
                split = line.split()
                if len(split) > 2:
                    words.append(split[0])
                    embs.append(np.array([float(s) for s in split[1:]]))
    return words, embs

def charseq(word, c2i):
    chars = []
    for c in word:
        if c not in c2i:
            c2i[c] = len(c2i)
        chars.append(c2i[c])
    return chars

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--vectors", required=True, nargs="*", dest="vectors", help="Pickle file(s) from which to get target word vectors")
parser.add_argument("--w2v-format", dest="w2v_format", action="store_true", help="Vector file is in textual w2v format")
parser.add_argument("--vocab", required=True, nargs="*", dest="vocab", help="File(s) containing words for unlabeled test set")
parser.add_argument("--output", required=True, dest="output", help="Output filename (.pkl)")

    options = parser.parse_args()

    c2i = {}
    training_instances = []
    test_instances = []


# Read in the output vocab
vocab = set()
for filename in options.vocab:
    with codecs.open(filename, "r", "utf-8") as f:
        vocab.update(set([ line.strip() for line in f ]))

    # read embeddings file
    if options.w2v_format:
        words, embs = read_text_embs(options.vectors)
    else:
        words, embs = cPickle.load(open(options.vectors, "r"))
    dim = len(embs[0])
    word_to_ix = {w : i for (i,w) in enumerate(words)}

    in_vocab = 0
    for word, emb in zip(words, embs):
        if word == POLYGLOT_UNK or word == W2V_UNK: continue
        if word in vocab:
            in_vocab += 1
        training_instances.append(Instance(charseq(word, c2i), emb))
    training_char_count = len(c2i)
    print "Total in Embeddings vocabulary:", len(words)
    print "Training set character count: ", training_char_count

    # Test
    if len(vocab) > 0:
        total = len(vocab)
        for v in vocab:
            if v not in words:
                test_instances.append(Instance(charseq(v, c2i), np.array([0.0] * dim)))
        print "Total Number of output words:", total
        print "Total in Training Vocabulary:", in_vocab
        print "Percentage in-vocab:", in_vocab / total
        print "Total character count: ", len(c2i)

    c2i[PADDING_CHAR] = len(c2i)

    # populate output
    output = {}
    output["c2i"] = c2i
    output["training_instances"] = training_instances
    output["test_instances"] = test_instances

    # write output
    with open(options.output, "w") as outfile:
        cPickle.dump(output, outfile)
