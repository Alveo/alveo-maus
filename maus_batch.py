import os
import pdb

def load_lexicon(lexdirpath):
    lex = {}


    files = [fp for fp in os.listdir(lexdirpath) if 
             os.path.isfile(os.path.join(lexdirpath, fp)) 
             and not fp.startswith('.')]
             


    pdb.set_trace()
    for fp in files:
        with open(os.path.join(lexdirpath, fp)) as f:
            for line in f:
                lex[line.split()[0]] = line.split()[1]

    return lex


    
