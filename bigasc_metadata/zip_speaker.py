"""
Resample the audio for a site/session/speaker and
save a copy in a new location
"""
import os, glob

import ingest 
from data import site_sessions, map_session, resample
from rdflib import Graph
import convert
import zipfile

import configmanager
configmanager.configinit()

if __name__=='__main__':
    
    import sys 
    
    if len(sys.argv) < 2:
        print "Usage: zip_speaker.py <spkrid> <comp> <comp> <comp>"
        print "    where <comp> is a component name, if none give, then all components will be included"
        exit()

    datadir = configmanager.get_config('DATA_DIR')
    outdir =  configmanager.get_config('OUTPUT_DIR')

    spkrid = sys.argv[1]
    if len(sys.argv) > 2:
        components = sys.argv[2:]
    else:
        components = []
        
    # should be from the command line...
    include_maus = False
    
    outfile = spkrid + ".zip"
    zfile = zipfile.ZipFile(outfile, 'w')
    
    audiodir = os.path.join(outdir, 'downsampled')
    mausdir = os.path.join(outdir, 'MAUS')
    
    for site in os.listdir(audiodir):
        
        sitedir = os.path.join(audiodir, site)
        print sitedir
        if os.path.isdir(sitedir):
            for sdir in os.listdir(sitedir):
                if sdir == spkrid:
                    speakerdir = os.path.join(sitedir, sdir)
                    #print speakerdir
                    for sessiondir in os.listdir(speakerdir):
                        #print sessiondir
                        for cdir in os.listdir(os.path.join(speakerdir, sessiondir)):
                            #print cdir
                            if components != [] and cdir in components:
                                compdir = os.path.join(speakerdir, sessiondir, cdir)
                                for item in os.listdir(compdir):
                                    
                                    # add the audio file to the zip file
                                    (base, ext) = os.path.splitext(item)
                                    audioname = base + ".wav"
                                    audiopath = os.path.join(site, sdir, sessiondir, cdir, audioname)
                                    audiofile = os.path.join(audiodir, audiopath)
                                    
                                    zfile.write(audiofile, audiopath)
                                    
                                    if include_maus:
                                        mauspath = os.path.join(site, sdir, sessiondir, cdir, item)
                                        mausfile = os.path.join(mausdir, mauspath)
                                        if sys.path.exists(mausfile):
                                            zfile.write(mausfile, mauspath)
                                            
                                            
                                                                                
    zfile.close()
    



