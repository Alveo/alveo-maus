"""
Resample the audio for a site/session/speaker and
save a copy in a new location
"""
import os, glob

import ingest 
from data import site_sessions, map_session, resample
from rdflib import Graph
import convert

import configmanager
configmanager.configinit()

## generate a component map, do this only once and we'll use it below
from convert.session import component_map
COMPONENT_MAP = component_map()

def make_processor(sessiondir, outdir, server):
    """Return a function to generate output to the given dir"""
     
    
    def process_item(site, spkr, session, component, item_path):
        """Process a single item - convert the audio 
        and write out to the new location
        take care to get all -n* files if present
        return a list of metadata triples that
        describe the new audio files and link
        them to the items.
        Return a count of the number of audio files processed
        """
        
        n = 0
        
        graph = Graph()
        versions = convert.item_file_versions(item_path)
        basename = convert.item_file_basename(item_path)
        
        # we want to grab the maptask channel if this is a maptask component
        getmaptask = component in ['8', '10']
        
        for base in versions['good'].keys(): 
                
            for fn in versions['good'][base]:
                
                # only worry about ch6-speaker
                # unless this is a maptask when we want ch1-maptask as well
                
                if fn.find('ch6-speaker') >= 0 or (getmaptask and fn.find('ch1-maptask') >= 0):
                
                    newname = convert.change_item_file_basename(os.path.basename(fn), base) 
                    newname = newname.replace('ch6-speaker', 'ch6-speaker16')
                    newname = newname.replace('ch1-maptask', 'ch1-maptask16')
                    path = convert.item_file_path(newname, "downsampled")
                    
                    # generate metadata
                    convert.generate_file_metadata(graph, path, "downsampled")
                    
                    # skip generating the downsampled file if it's already there
                    if not os.path.exists(os.path.join(outdir, path)):
                        resample(fn, os.path.join(outdir, path))
                        n += 1

        # output metadata
        server.output_graph(graph, convert.item_file_path(basename+"-ds", "metadata"))
    
        # in the case when we don't have versionselect info we want to write the 
        # data somewhere so that someone can look at it
        if versions.has_key('versioninfo') and versions['versioninfo'] == 'missing':

            print "Unknown versions: ", basename
            bgraph = Graph()
            # for rejected files we still downsample but this time to the rejected directory
            for fn in convert.item_files(item_path):
                
                # only worry about ch6-speaker or ch1-maptask if we're in a maptask
                if fn.find('ch6-speaker') >= 0 or (getmaptask and fn.find('ch1-maptask') >= 0):
                     
                    newname = fn.replace('ch6-speaker', 'ch6-speaker16')
                    newname = fn.replace('ch1-maptask', 'ch1-maptask16')
                    
                    path = convert.item_file_path(newname, "versionselect")
                    
                    # generate metadata
                    convert.generate_file_metadata(bgraph, path, "versionselect")
                    
                    # skip generating the downsampled file if it's already there
                    if not os.path.exists(os.path.join(outdir, path)):
                        resample(fn, os.path.join(outdir, path))
                    
            
            # output metadata if any
            server.output_graph(bgraph, convert.item_file_path(basename+"-ds", "versionselect-meta"))
            
        return n
    
    return process_item
    

if __name__=='__main__':
    
    import sys 
    
    if len(sys.argv) > 1:
        print "Usage: resample_audio.py <limit>?"
        exit()

    datadir = configmanager.get_config('DATA_DIR')
    outdir =  configmanager.get_config('OUTPUT_DIR')

    if len(sys.argv) == 2:
        limit = int(sys.argv[1])
    else:
        limit = 1000000
    
    server_url = configmanager.get_config("SESAME_SERVER")
    server = ingest.SesameServer(server_url)

    for d in os.listdir(datadir):
        
        sitedir = os.path.join(datadir, d)
        
        if os.path.isdir(sitedir):
            for session in site_sessions(sitedir):
                if configmanager.get_config('SHOW_PROGRESS', '') == 'yes':
                    print "Session: ", session
                
                files = [m for m in map_session(session, make_processor(sitedir, outdir, server))]
                
                if configmanager.get_config('SHOW_PROGRESS', '') == 'yes':
                    print sum(files)
                
                limit -= 1
                if limit <= 0:
                    print "Stopping after hitting limit"
                    exit()  
            
