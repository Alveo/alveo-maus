import os
import subprocess
import tempfile 
import StringIO
import re

import yaml

from pyhcsvlab import hcsvlab

class MausError(Exception):
    """ Raised when MAUS does not execute successfully """
    pass

    
class IncompleteLexiconError(Exception):
    """ Raised when an attempt is made to gennerate a phonetic
        transcription for a word that is not present in the lexicon
        
        
    """
    pass

    
def load_lexicon(lexdirpath=None):
    """ Load all files in the specified directory as a lexicon dictionary.
        Each line of each file is split by whitespace, then the last delimited
        element is treated as the phonetic representation, while the rest are 
        joined with spaces, converted to lowercase, then recorded as the 
        orthographic representation
        
        @type lexdirpath: C{String}
        @param lexdirpath: the directory to search for lexicon files. If not
        specified, this will default to the value in the config file.
            
        @rtype: C{Dict}
        @returns: the combined lexicon, as a dictionary
       
       
    """
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
    """ Load the config file as a dictionary
    
        @rtype: C{Dict}
        @returns: the content of the C{config.yaml} file, as a dictionary
        
    
    """
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'config.yaml')

    f = open(filename, 'r')
    c = yaml.safe_load(f.read())
    f.close()

    return c


    
def __df(param, default_value):
    """ Return the given parameter, or, if the parameter is None,
        return the given default value
        
    @param param: the parameter in question
    @param default value: the defauly value
    
    @returns: the paramater or its default value
    
    
    """
    if param is None:
        return default_value
    return param
    
    
def maus_bool(value):
    """ Format a boolean value for passing to MAUS as an argument
    
    @type value: C{Boolean}
    @param value: the boolean value to format
    
    @rtype: C{String}
    @returns: 'true' if the value is True, 'false' if false
    
    
    """
    if value: return 'true'
    return 'false'
    
    
def call_maus(wav_file, bpf, language=None, canonly=None, minpauslen=None,
              startword=None, endword=None, mausshift=None, insprob=None,
              inskantextgrid=None, insorttextgrid=None, usetrn=None,
              outformat=None):
    """ Call the MAUS program with the specified arguments. All optional
    parameters correspond to MAUS command-line parameters, and their values,
    if not explictly set, will be taken from the C{config.yaml} configuration
    file.
    
    @type wav_file: C{String}
    @param wav_file: path to the WAV file to process
    @type bpf: C{String}
    @param: transcription of the recording in BPF format
    
    @rtype: C{String}
    @returns: the MAUS-generated annotation, if successful
    
    @raises MausError: if the alignment was not successful
    
    
    """
    
    conf = config()
    pm = conf['maus_params']

    params = {
        'LANGUAGE': __df(language, 'LANGUAGE']),
        'CANONLY': maus_bool(__df(canonly, p['CANONLY'])),
        'MINPAUSLEN': str(__df(minpauslen, p['MINPAUSLEN'])),
        'STARTWORD': str(__df(startword, p['STARTWORD'])),
        'ENDWORD': str(__df(endword, p['ENDWORD'])),
        'MAUSSHIFT': str(__df(mausshift, p['MAUSSHIFT'])),
        'INSPROB': str(__df(insprob, p['INSPROB'])),
        'SIGNAL': wav_file,
        'BPF': StringIO.StringIO(bpf),
        'OUTFORMAT': str(__df(outformat, p['OUTFORMAT'])),
        'USETRN': maus_bool(__df(usetrn, p['USETRN'])),
        'INSKANTEXTGRID': maus_bool(__df(inskantextgrid, p['INSKANTEXTGRID'])),
        'MAUSSHIFT': str(__df(mausshift, p['MAUSSHIFT'])),
        'INSORTTEXTGRID': maus_bool(__df(insorttextgrid, p['INSORTTEXTGRID'])),
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

    
def build_bpf(ortho_trans, lex=None):
    """ Given an orthographic transcript, generate a BPF-format phonetic
        transcription for passing to MAUS, using the specified lexicon.
        
        @type ortho_trans: C{String}
        @param ortho_trans: the (space-separated) orthographic transcript 
        @type lex: C{Dict}
        @param lex: the lexicon to use; if unspecified, the lexicon specified
        in the configuration file will be loaded and used
        
        @rtype: C{String}
        @returns: the BPF-formatted transcript
        
        @raises IncompleteLexiconError: if there is a word appearing in the 
        orthographic transcript that is not covered by the lexicon
        
        
    """
    if lex is None: lex = load_lexicon()
    
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
    """ Given a WAV recording and its transcript, produce an
    annotation using MAUS, using the lexicon and MAUS parameters
    specified in the C{config.yaml} configuration file.
    
    @type wav_file: C{String}
    @param wav_file: the path to the WAV file containing the recording
    @type ortho_trans: C{String}
    @param ortho_trans: the (space-separated) orthographic transcript
    
    @rtype: C{String}
    @returns: the annotation as output by MAUS
    
    @raises IncompleteLexiconError: if there is a word appearing in the 
        orthographic transcript that is not covered by the lexicon 
    @raises MausError: if the alignment was not successful
    
    
    """
    lex = load_lexicon()
    bpf = build_bpf(ortho_trans, lex)
    return call_maus(wav_file, bpf)
    

def annotate_item(item, prompt):
    """ Given a pyhcsvlab Item object for which each document is a recording
    with identical orthographic transcript, produce an annotation for each
    of its recordings, using the lexicon and MAUS parameters
    specified in the C{config.yaml} configuration file.
    
    @type item: L{hcsvlab.Item}
    @param item: the Item object to annotate
    @type prompt: C{String}
    @param prompt: the common orthographic transcript of the item's documents
    
    @rtype: C{String}
    @returns: the annotation as output by MAUS
    
    @raises IncompleteLexiconError: if there is a word appearing in the 
        orthographic transcript that is not covered by the lexicon 
    @raises MausError: if the alignment was not successful
    
    
    """
    annotations = []
    for doc in item.get_documents():
        docfile = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        docfile.write(doc.get_content())
        docfile.close()
        annotations.append(annotate_wav(docfile.name, prompt))
        os.unlink(docfile.name)
        
    return annotations

     
