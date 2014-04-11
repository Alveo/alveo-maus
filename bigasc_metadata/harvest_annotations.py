'''
Created on Jul 19, 2013

@author: steve

gather together annotation files into an appropriate directory structure

'''

import configmanager
configmanager.configinit()
from convert.namespaces import *
from convert.item import parse_item_filename
from convert.participant import participant_uri, item_site_name
from convert.session import component_map
import ingest
from convert.filepaths import item_file_path, item_file_uri, item_file_basename
from rdflib import Graph, URIRef, Literal

import hashlib
import os
import shutil


def newest_file(files):
    """Given a list of filenames, return the one
    corresponding to the newest file"""
    
    newest = files[0]
    newest_s = os.stat(newest).st_mtime
    for f in files[1:]:
        s = os.stat(f).st_mtime
        if s > newest_s:
            newest = f
            newest_s = s
            
    return newest

def process_results(server, basenames, outdir, origin, format):
    """Given a dictionary of basenames and the files associated with them, 
     find the most recent file for each basename and copy it to it's 
     intended location. Also write a metadata file for each item."""
    
    for basename in sorted(basenames.keys()):

        source = newest_file(basenames[basename]) 
        source_basename = os.path.basename(source)

        # need to tidy up the name because of extensions like '.TextGrid 2'
        (b, e) = os.path.splitext(source_basename)
        dest_basename = b + "." + format
        
        graph = ann_metadata(dest_basename, origin, format)
        server.output_graph(graph, item_file_path(basename+"-"+origin, os.path.join("annotation", "metadata")))

        path = item_file_path(dest_basename, os.path.join("annotation", origin))
        copy_file(source, os.path.join(outdir, path))
        
        

def copy_file(src, dest):
    """Copy src to dest but make sure that the directories in dest exist"""
    
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    
    shutil.copy(src, dest)
    
    
def ann_metadata(annfile, origin, format):
    
    ann_uri = item_file_uri(annfile, os.path.join("annotation", origin))
    basename = item_file_basename(annfile)
    item_uri = generate_item_uri(basename)
    
    graph = Graph()
    graph.add((URIRef(item_uri), NS['has_annotation'], ann_uri))
    graph.add((ann_uri, RDF.type, NS.AnnotationFile))
    graph.add((ann_uri, NS['origin'], Literal(origin)))
    graph.add((ann_uri, NS['format'], Literal(format)))
    
    return graph

if __name__ == '__main__':
    
    import sys, os
    
    if len(sys.argv) != 4:
        print "Usage: harvest_annotations.py <input dir> <ext> <origin>"
        print "  <ext> is file extension without the period (eg. TextGrid, trs)"
        print "  <origin> is a string descriptor of the origin of the annotation eg. 'Manual'"
        exit()
    
    dirname = sys.argv[1]
    ext = sys.argv[2] 
    origin = sys.argv[3]
    
    outdir = configmanager.get_config("OUTPUT_DIR")
    server_url = configmanager.get_config("SESAME_SERVER")
    server = ingest.SesameServer(server_url)

    for dirpath, dirnames, filenames in os.walk(dirname):
        # find all files associated with each basename in this directory
        # store them in a dictionary with the basename as a key
        results = dict()
        for fn in filenames:
            # ignore files containing 'Copy', there are only a few and they are not different
            if fn.find("Copy") >= 0:
                continue
            
            if fn.endswith(ext):
                try:
                    # guard against wierd filenames
                    basename = item_file_basename(fn)
                    fullpath = os.path.join(dirpath, fn)
                    
                    # ignore basenames with added spaces - 
                    if fullpath.find(' ') >= 0:
                        print "Ignoring due to spaces:", fn
                        continue
                    
                    if results.has_key(basename):
                        results[basename].append(fullpath)
                    else:
                        results[basename] = [fullpath]
                except:
                    pass
                    
        process_results(server, results, outdir, origin, ext)
                    

            
            
            
                
                
                
