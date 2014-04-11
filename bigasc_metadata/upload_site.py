'''
Created on Sep 25, 2012

@author: steve

upload metadata about some or all sessions for a site to the server

'''
import os
import ingest
from convert.ra_maptask import RAMapTask
from data import site_sessions


import configmanager
configmanager.configinit()
    
    

def process(datadir, limit, errorlog):
    
    server_url = configmanager.get_config("SESAME_SERVER") 
    server = ingest.SesameServer(server_url)
    # get RA spreadsheet data on maptasks
    maptask = RAMapTask()
    (spkr, map) = maptask.read_all()  
    
    for d in os.listdir(datadir):
        sitedir = os.path.join(datadir, d)
        if os.path.isdir(sitedir):
            for session in site_sessions(sitedir):
                print "Session: ", session
                try:
                    ingest.ingest_session_map(server, session, map, errorlog)
                except Exception as ex:
                    errorlog.write("\tProblem with session...%s\n" % ex)
                    
                limit += -1
                if limit <= 0:
                    print "Stopping after hitting limit"
                    return    
        
if __name__ == '__main__':
    
    import sys
     
    
    if len(sys.argv) > 2:
        print "Usage upload_site.py <limit>?"
        print " where <limit> gives the maximum number of sessions to upload"
        exit()

    datadir = configmanager.get_config('DATA_DIR')
    outdir =  configmanager.get_config('OUTPUT_DIR')

    if len(sys.argv) == 2:
        limit = int(sys.argv[1])
    else:
        limit = 1000000

    errorlog = open('item-errors.txt', 'w')

    process(datadir, limit, errorlog)
    
#    import cProfile
#    cProfile.run("process(server_url, limit)", "profile.dat")

