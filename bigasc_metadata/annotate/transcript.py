"""
Tools for running AusTalk transcripts through MAUS
"""

import maus
import xml.etree.ElementTree as ET
import string

def flatten_transcript(transcript):
    """Take an AusTalk transcript file and produce just the text content"""

    tree = ET.parse(transcript)
    root = tree.getroot()

    text = ''

    for episode in root:
        if episode.tag != 'Episode': continue
        for section in episode:
            if section.tag != 'Section': continue
            for turn in section:
                if turn.tag != 'Turn': continue
                for part in turn:
                    text += part.tail
    
    text = text.translate(string.maketrans("",""), string.punctuation)

    return ' '.join(text.split())


def align_transcript_MAUS(recording, transcript, lexicon):
    """Run an AusTalk recording through MAUS"""

    return maus.maus(recording,\
                     flatten_transcript(transcript),\
                     lexicon=lexicon)
