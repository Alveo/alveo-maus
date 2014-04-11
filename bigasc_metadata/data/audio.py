'''
Resampling audio files

Created on Oct 31, 2012

@author: steve
'''

import sys, os, time, signal, shutil
import subprocess
from convert.namespaces import *
from convert import parse_media_filename

from rdflib import Literal

SOX_PROGRAM = ''
for d in ['/usr/bin/', '/usr/local/bin']:
    if os.path.exists(os.path.join(d, 'sox')):
        SOX_PROGRAM = os.path.join(d, 'sox')
        break
if SOX_PROGRAM == '':
    print "Can't find sox executable"

    
## generate a component map, do this only once and we'll use it below
from convert.session import component_map
COMPONENT_MAP = component_map()

def resample(sourcefile, targetfile):
    """Generate a 16 bit, 16kHz version of this audio file
    
    return the name of the new file or None if something went wrong
    
>>> fn = "../test/1_1121_1_12_001-ch6-speaker.wav"
>>> fn16 = resample(fn)
>>> fn16
'../test/1_1121_1_12_001-ch6-speaker16.wav'
>>> os.path.exists(fn16)
True
>>> os.unlink(fn16)
>>> fn16a = resample(fn, '/tmp')
>>> fn16a
'/tmp/1_1121_1_12_001-ch6-speaker16.wav'
>>> os.unlink(fn16a)
    """
    
    (indir, filename) = os.path.split(sourcefile)
 
    outdir = os.path.dirname(targetfile)
    # make sure outdir exists
    try:
        os.makedirs(outdir)
    except:
        pass
    
    # convert to 16kHz/16 bit and normalise amplitude to -3db
    soxcmd = [SOX_PROGRAM, sourcefile, "-b16", targetfile, "rate", "-I", "16k", "gain", "-n", "-3" ] 
    
    #print " ".join(soxcmd) 

    # send err output to nowhere
    devnull = open(os.devnull, "w")
    process =  subprocess.Popen(soxcmd, stdout=devnull, stderr=devnull)

    while process.poll() == None:
        pass
 
    
    if os.path.exists(targetfile):
        return targetfile
    else:
        return None


if __name__=='__main__':
        
        import doctest
        doctest.testmod()
        
    
