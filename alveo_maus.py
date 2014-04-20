import os
import subprocess
import tempfile 
import StringIO
import re

import yaml

from pyhcsvlab import hcsvlab

class MausError(Exception):
    pass

    
class IncompleteLexiconError(Exception):
    pass

    
def load_lexicon(lexdirpath=None):
    lex = {}
    
    if lexdirpath is None:
        lexdirpath = config()['lexdirpath']

    files = [fp for fp in os.listdir(lexdirpath) if 
             os.path.isfile(os.path.join(lexdirpath, fp)) 
             and not fp.startswith('.')]

    for fp in files:
        with open(os.path.join(lexdirpath, fp)) as f:
            for line in f:
                spl = line.split()
                lex[(" ".join(spl[:-1])).lower()] = spl[-1]

    return lex


def config():
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'config.yaml')

    f = open(filename, 'r')
    c = yaml.safe_load(f.read())
    f.close()

    return c


def deft(param, param_name, default_params):
    if param is None:
        return default_params[param_name]
    
    
def maus_bool(value):
    if value: return 'true'
    return 'false'
    
    
def call_maus(wav_file, bpf, language=None, canonly=None, minpauslen=None,
              startword=None, endword=None, mausshift=None, insprob=None,
              inskantextgrid=None, insorttextgrid=None, usetrn=None,
              outformat=None):

    conf = config()
    pm = conf['maus_params']

    params = {
        'LANGUAGE': deft(language, 'LANGUAGE', pm),
        'CANONLY': maus_bool(deft(canonly, 'CANONLY', pm)),
        'MINPAUSLEN': str(deft(minpauslen, 'MINPAUSLEN', pm)),
        'STARTWORD': str(deft(startword, 'STARTWORD', pm)),
        'ENDWORD': str(deft(endword, 'ENDWORD', pm)),
        'MAUSSHIFT': str(deft(mausshift, 'MAUSSHIFT', pm)),
        'INSPROB': str(deft(insprob, 'INSPROB', pm)),
        'SIGNAL': wav_file,
        'BPF': StringIO.StringIO(bpf),
        'OUTFORMAT': str(deft(outformat, 'OUTFORMAT', pm)),
        'USETRN': maus_bool(deft(usetrn, 'USETRN', pm)),
        'INSKANTEXTGRID': maus_bool(deft(inskantextgrid, 'INSKANTEXTGRID', pm)),
        'MAUSSHIFT': str(deft(mausshift, 'MAUSSHIFT', pm)),
        'INSORTTEXTGRID': maus_bool(deft(insorttextgrid, 'INSORTTEXTGRID', pm)),
    }
    
    bpf_file = tempfile.NamedTemporaryFile(delete=False)
    bpf_file.write(bpf)
    bpf_file.close()
    params['BPF'] = bpf_file.name
    
    outfile = tempfile.NamedTemporaryFile(delete=False)
    outfile.close()
    params['OUT'] = outfile.name
    
    maus_cmd = [conf['maus_path']]
    for key in params.keys():
        maus_cmd.append("%s=%s" % (key, params[key]))
    
    devnull = open(os.devnull, "w")
    #this is where MAUS is actually invoked
    p = subprocess.Popen(maus_cmd, stdout=subprocess.PIPE)
    out, err = p.communicate()

    os.unlink(bpf_file.name)
   
    try:
        output = open(outfile.name).read()
        os.unlink(outfile.name)
        if output: return output #return iff there's some data to return
    except IOError: #output file doesn't exist, something went wrong
        pass
    #if nothing went wrong, we should have returned already
    raise MausError((out, err))

    
def build_bpf(ortho_trans, lex):
    spl = re.compile(r'[\s.,!?"\-]')
    words = [w.lower() for w in spl.split(ortho_trans) if w]
    ort = []
    kan = []
    
    for n, word in enumerate(words):
        try:
            ort.append("ORT: %d %s" % (n, word))
            kan.append("KAN: %d %s" % (n, lex[word]))
        except KeyError:
            raise IncompleteLexiconError("'" + word +
                                         "' not present in lexicon")
    
    nl = "\n"
    return nl.join(ort) + nl + nl.join(kan)
    
    
def annotate_wav(wav_file, ortho_trans):
    lex = load_lexicon()
    bpf = build_bpf(ortho_trans, lex)
    return call_maus(wav_file, bpf)
    

def annotate_item(item, prompt):
    annotations = []
    for doc in item.get_documents():
        docfile = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        docfile.write(doc.get_content())
        docfile.close()
        annotations.append(annotate_wav(docfile.name, prompt))
        os.unlink(docfile.name)
        
    return annotations
    
   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
     
