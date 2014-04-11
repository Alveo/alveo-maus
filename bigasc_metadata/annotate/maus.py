'''
Send audio to MAUS for forced alignment

Created on Oct 31, 2012

@author: steve
'''

import urllib, urllib2
import MultipartPostHandler
import os, sys
import subprocess
from StringIO import StringIO
import configmanager
configmanager.configinit()
from rdflib import Graph, Literal, URIRef
import convert
from convert.namespaces import *
from data import COMPONENT_MAP
from tempfile import NamedTemporaryFile

OUTPUT_DIR = configmanager.get_config('OUTPUT_DIR')

LEXICON = os.path.join(os.path.dirname(__file__), "AUSTALK.lex")

class MausException(Exception):
    pass

def maus_boolean(value):
    """Turn a Python boolean value into a
    'true' or 'false for MAUS"""
    
    if value:
        return 'true'
    else:
        return 'false'

def maus(wavfile, text, language='aus', canonly=False, minpauselen=5, 
         startword=0, endword=999999, mausshift=10, insprob=0.0,
         inskantextgrid=True, insorttextgrid=True, usetrn=False, outformat='TextGrid',
         lexicon=None):
    """Send the given wavfile to MAUS for forced alignment
    text is the orthographic transcription
    
    returns the text of the textgrid returned by MAUS
    raises MausException if there was an error, the exception
    contains any error text returned by the MAUS web service
    
>>> txt = maus("test/bassinette-sample-16.wav", "bassinette")
>>> txt.find('xmax')
62
>>> txt.find('b{s@net')
896
>>> txt = maus("test/bassinette-sample-16.wav", "not in the lexicon")
Traceback (most recent call last):
MausException: Can't generate phonetic transcription for text 'not in the lexicon'

# a bad request, send a text file
>>> maus("annotate/maus.py", "bassinette")
Traceback (most recent call last):
MausException: Internal Server Error

# another bad request, an unknown language
>>> maus("test/bassinette-sample-16.wav", "bassinette", language='unknown')
Traceback (most recent call last):
MausException: Internal Server Error

#maus("test/bassinette-sample-16.wav", "bassinette", outformat="EMU")
#something
    """
    
    if lexicon is None:
        lex = load_lexicon()
    else:
        lex = load_lexicon(lexicon)
    phb = text_phb(text, lex)
    
    if phb == None:
        truncated_text = (text[:100] + '...') if len(text) > 100 else text
        raise MausException("Can't generate phonetic transcription for text '%s'" % truncated_text)

    params = dict((('LANGUAGE', language),
                   ('CANONLY', maus_boolean(canonly)),
                   ('MINPAUSLEN', str(minpauselen)),
                   ('STARTWORD', str(startword)),
                   ('ENDWORD', str(endword)),
                   ('MAUSSHIFT', str(mausshift)),
                   ('INSPROB', str(insprob)),
                   ('SIGNAL', wavfile),
                   ('BPF', StringIO(phb)),
                   ('OUTFORMAT', str(outformat)),
                   ('USETRN', maus_boolean(usetrn)),
                   ('INSKANTEXTGRID', maus_boolean(inskantextgrid)),
                   ('MAUSSHIFT', str(mausshift)),
                   ('INSORTTEXTGRID', maus_boolean(insorttextgrid)),
                ))
    
    if configmanager.get_config("MAUS_LOCAL", "no") == "yes":
        params['SIGNAL'] = wavfile
        h = NamedTemporaryFile(prefix='bpf', delete=False) 
        h.write(phb)
        h.close()
        params['BPF'] = h.name
        
        outfile = NamedTemporaryFile(prefix='textgrid', delete=False)
        outfile.close()
        
        params['OUT'] = outfile.name
        
        maus_program = configmanager.get_config("MAUS_PROGRAM")

        maus_cmd = [maus_program]
        for key in params.keys():
            maus_cmd.append("%s=%s" % (key, params[key]))
        #print " ".join(maus_cmd)
        
        try:
            # send err output to nowhere
            devnull = open(os.devnull, "w")
            process =  subprocess.Popen(maus_cmd, stdout=devnull, stderr=devnull)
    
            while process.poll() == None:
                pass
        except:
            pass
     
        os.unlink(h.name)
        
        if os.path.exists(outfile.name):
            # grab the result
            h = open(outfile.name)
            result = h.read()
            h.close()
            
            os.unlink(outfile.name)
        else:
            result = "Error Calling MAUS"
        
    else:
        # for the web call we open the wav file
        params['SIGNAL'] = open(wavfile)
        params['BPF'] = StringIO(phb)
        
        handler = MultipartPostHandler.MultipartPostHandler(debuglevel=0)
        opener = urllib2.build_opener(handler)
        
        MAUS_URL = configmanager.get_config("MAUS_URL")
        try:
            response = opener.open(MAUS_URL, params)
        except urllib2.HTTPError as e:
            errormessage = e.read()
            raise MausException(e.msg)
        
        result = response.read()
    
    if result.startswith('File type = "ooTextFile"'):
        # everything was ok
        return result
    else:
        # some kind of error
        raise MausException(result)


def load_lexicon(lex=None):
    """Load the lexicon from AUSTALK.lex and return 
    a dictionary with words as keys
    
>>> lex = load_lexicon()
>>> lex['actually']
'{ktS@li:'
>>> lex['zoo']
'z}:'
    """

    if lex is None:
        lex = LEXICON

    h = open(lex)
    lines = h.readlines()
    h.close()
    
    result = dict()
    for line in lines:
        words = line.split()
        if len(words) > 2:
            #print "Too many fields:", line
            continue
        ort = words[0]
        phn = words[1]
        result[ort] = phn
        
    return result
    
    
    
def text_phb(text, lex):
    """Generate a PHB format orthographic transcript
    corresponding to the given text. Text is split 
    on whitespace into words.  
    
    PHB formatted text is returned unless some of the
    words are not in the lexicon, in which case return None
    and print out messages 
    
>>> lex = load_lexicon()
>>> print text_phb('before', lex)
ORT: 0 before
KAN: 0 b@fo:
>>> print text_phb('before zombie', lex)
ORT: 0 before
ORT: 1 zombie
KAN: 0 b@fo:
KAN: 1 zOmbi:
>>> print text_phb('Before, zombie.', lex)
ORT: 0 before
ORT: 1 zombie
KAN: 0 b@fo:
KAN: 1 zOmbi:
>>> print text_phb("Who'll pour Rosas?.", lex)
ORT: 0 who'll
ORT: 1 pour
ORT: 2 rosas
KAN: 0 h}:l
KAN: 1 po:
KAN: 2 r\@}z@z
>>> print text_phb('hello world', lex)
Not in lexicon: 'hello'
Not in lexicon: 'world'
None
    """
    import re
    
    words = [x.lower() for x in re.split(r'[\s.,!?"\-]', text) if x != '']
    error = False
    ort = []
    kan = []
    n = 0
    for word in words:
        if lex.has_key(word):
            phon = lex[word] 
            ort.append("ORT: %d %s" % (n, word))
            kan.append("KAN: %d %s" % (n, phon))
        else:
            print "Not in lexicon: '%s'"  % word
            error = True
                        
        n += 1
    
    result = "\n".join(ort) + "\n" + "\n".join(kan)
    
    if error:
        return None
    
    return result

# list of component ids that we can run MAUS over because they are read
MAUSABLE_COMPONENTS = ['digits', 'words-1', 'words-2', 'words-3', 
                       'words-1-2', 'words-2-2', 'words-2-3', 
                       'sentences', 'sentences-e']


import ingest
import re
from convert.session import item_prompt
from convert.filepaths import item_file_uri

def item_details(mediafile):
    """Return the prompt text and media file URL for this item
    Return a dictionary with keys 'media', 'item_uri' and 'prompt', 
     if no details can be found, return None
     
>>> d = item_details('1_1119_2_16_049-ch6-speaker16.wav')
>>> sorted(d.keys())
['basename', 'item_uri', 'prompt']
>>> d['item_uri']
rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_1119_2_16_049')
>>> d['prompt']
'My mother gets cross when they say "yeah" instead of "yes".'
>>> d['basename']
'1_1119_2_16_049'
>>> print item_details('not a good basename')
None
>>> d = item_details('4_488_2_5_002-ch6-speaker16.wav')
>>> d['prompt']
'nine four two oh'
>>> d = item_details('4_1368_1_5_012-ch6-speaker16.wav')
>>> d['prompt']
'oh four two nine'
>>> item_details('2_1122_1_2_054-ch6-speaker16.wav')['prompt']
'harl'
>>> p = item_details('2_1122_1_2_142-ch6-speaker16.wav')['prompt']
>>> p
'pure'
>>> item_details('3_1202_3_14_073-ch6-speaker16.wav')['prompt']
'hode'
     """
    

    
    try:
        basename = convert.item_file_basename(mediafile)
        result = {'prompt': item_prompt(basename),
                  'item_uri': generate_item_uri(basename),
                  'basename': basename,
                  } 
        
        return result
    except:
        return None


def make_bpf_generator(server, outputdir):
        
    def bpf_item(site, spkr, session, component, item_path):
        """Procedure for use with map_session to generate a BPF 
        annotation file for input to MAUS"""
        
        
        if not component in MAUSABLE_COMPONENTS:
            return
        
        basename = os.path.basename(item_path)
        (name, ext) = os.path.splitext(basename)
        outpath = convert.item_file_path(name + ".bpf", "BPF")
        outfile = os.path.join(outputdir, outpath)
        
        lex = load_lexicon()        
        
        if not os.path.exists(os.path.dirname(outfile)):
            os.makedirs(os.path.dirname(outfile))
        
        details = item_details(basename)
        if details != None:

            phb = text_phb(details['prompt'], lex)

            if phb != None:
                sys.stdout.write('.')
                sys.stdout.flush()
                
                h = open(outfile, 'w')
                h.write(phb)
                h.close()
            else:
                print "Problem with", basename
    
    return bpf_item


def make_maus_processor(server, outputdir):
        
    def maus_item(site, spkr, session, component, item_path):
        """Procedure for use with map_session to send the audio data
        for one item to MAUS and store the resulting annotation 
        files"""
        
        
        if not component in MAUSABLE_COMPONENTS:
            return
        
        basename = os.path.basename(item_path)
        (name, ext) = os.path.splitext(basename)
        outpath = convert.item_file_path(name + ".TextGrid", "MAUS")
        outfile = os.path.join(outputdir, outpath)
        
        if not os.path.exists(os.path.dirname(outfile)):
            os.makedirs(os.path.dirname(outfile))
        
        details = item_details(basename)
        if details != None:    
            
            try:
                annotation = maus(item_path, details['prompt'])
                
                sys.stdout.write('.')
                sys.stdout.flush()
                
                h = open(outfile, 'w')
                h.write(annotation)
                h.close()
                
                graph = maus_metadata(details['item_uri'], outpath)
                
                server.output_graph(graph, convert.item_file_path(details['basename']+"-m", "metadata"))
                
            except MausException as e:
                print "ERROR", basename, e
        else:
            print "Item has no media/prompt: ", basename
    
    return maus_item
    
    
def maus_metadata(item_uri, mausfile):
    """Generate metadata for the output of MAUS"""
    
    maus_uri = DATA_NS[mausfile]
    graph = Graph()    
    convert.generate_file_metadata(graph, mausfile, "MAUS")
    
    graph.add((URIRef(item_uri), NS['has_annotation'], maus_uri))
    graph.add((maus_uri, RDF.type, NS.AnnotationFile))
    graph.add((maus_uri, NS['origin'], Literal("MAUS")))
    
    return graph



def url_to_path(media):
    """Convert a media URL to a path on the local
    file system"""
    
    root = "/var/syndisk/published"

    (ignore, tmp) = urllib.splittype(media)
    (ignore, path) = urllib.splithost(tmp)
    
    return root + path
    
    
    
    



if __name__=='__main__':
        
    import doctest
    doctest.testmod()
