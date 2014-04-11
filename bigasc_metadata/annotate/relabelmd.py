'''Code for relabelling the Mitchell & Delbridge data
which has ESPS format label files that are offset by an
unknown amount.
'''

PROMPTS = {
           's1': 'beat boot say so high how',
           's2': "let's pick a good spot near the water and pass the morning surfing and relaxing in the sun",
           's3': 'the plane flew down low over the runway then increased speed and circled the aerodrome a second time',
           }


import os
from maus import maus


def label_file(wavfile, outdir=None):
    """Given the name of a wav file, feed it to MAUS and
    return the name of the TextGrid created in outdir"""

    print "Label", wavfile
    basename, ext = os.path.splitext(os.path.basename(wavfile))

    if outdir==None:
        outdir = os.path.dirname(wavfile)

    # last one or two chars of basename give us the prompt
    key = basename[-2:]
    if PROMPTS.has_key(key):
        prompt = PROMPTS[key]
        textgrid = maus(wavfile, prompt, outformat='TextGrid')

        h = open(os.path.join(outdir, basename+".TextGrid"), 'w')
        h.write(textgrid)
        h.close()

def label_dir(dirname):
    """generate textgrids for all wav files found under dirname
    recursing into subdirectories if needed"""
    
    
    for f in os.listdir(dirname):
        path = os.path.join(dirname, f)
        if os.path.isdir(path):
            label_dir(path)
        elif path.endswith('.wav'):
            label_file(path)




if __name__=='__main__':
    import sys

    if len(sys.argv) != 2:
        print "Usage: relabelmd.py <dirname>\n   Label all wav files under dirname"
        exit()

    dirname = sys.argv[1]

    tg = label_dir(dirname)