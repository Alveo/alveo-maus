"""
  Copy some of the files over to the new directory structure
  

"""

import convert
import shutil
import sys
from rdflib import Graph

def make_copy_processor(server, outdir, what):
    

    def process_item(site, spkr, session, component, item_path):
        """upload metadata for a single item"""
        

        if True:    
            # copy the files 
            versions = convert.item_file_versions(item_path)
            basename = convert.item_file_basename(item_path)
            
            graph = Graph()
            for base in versions['good'].keys(): 
                
                for fn in versions['good'][base]:
                    
                    props = convert.parse_media_filename(fn)
                    if props.has_key('type') and props['type'].lower() == what.lower():
                        newname = convert.change_item_file_basename(os.path.basename(fn), base)            
                        path = convert.item_file_path(newname, what.lower())
                        
                        #print "COPY:", os.path.basename(fn), path
                        
                        convert.generate_file_metadata(graph, path, what.lower())
                        
                        path = os.path.join(outdir, path)
                        
                        if not os.path.exists(os.path.dirname(path)):
                            os.makedirs(os.path.dirname(path))
                        
                        # copy if not already present
                        if not os.path.exists(path):
                            shutil.copy(fn, path)
                        
                        
            # output metadata for all files
            server.output_graph(graph, convert.item_file_path(basename+"-files", "metadata"))
        
            for fn in versions['rejected']:
                
                props = convert.parse_media_filename(fn)
                if props.has_key('type') and props['type'] == what:
                    path = convert.item_file_path(fn, os.path.join('rejected', what))
                    #print "REJECT:", os.path.basename(fn), path
                    path = os.path.join(outdir, path)
                    
                    if not os.path.exists(os.path.dirname(path)):
                        os.makedirs(os.path.dirname(path))
                        
                    shutil.copy(fn, path)
        try:
            pass
        except Exception as ex:
            sys.stderr.write("Problem with item: %s\n\t%s\n" % (item_path, ex))
            
    return process_item


if __name__=='__main__':
    
    import sys
    import os
    from data import site_sessions, map_session
    import configmanager
    import ingest
    
    if len(sys.argv) not in [2,3]:
        print "Usage: copy_files.py audio|video <limit>?"
        exit()  
        
    datadir = configmanager.get_config("DATA_DIR")
    outdir = configmanager.get_config("OUTPUT_DIR")
    what = sys.argv[1]
    if len(sys.argv) == 3:
        limit = int(sys.argv[2])
    else:
        limit = 10000000
    
    server_url = configmanager.get_config("SESAME_SERVER")
    server = ingest.SesameServer(server_url) 

    for d in os.listdir(datadir):
        
        sitedir = os.path.join(datadir, d)
        
        if os.path.isdir(sitedir):
            for session in site_sessions(sitedir):
                print "Session: ", session
                
                result = [i for i in map_session(session, make_copy_processor(server, outdir, what))]
            
                limit -= 1
                if limit <= 0:
                    print "Stopping after hitting limit"
                    exit()  
        
