'''
Created on Sep 25, 2012

@author: steve

upload protocol metadata to the server

'''

import sys
import ingest

import configmanager
configmanager.configinit()

if __name__ == '__main__':
    
    server_url = configmanager.get_config("SESAME_SERVER")
    
    server = ingest.SesameServer(server_url)
    
    if len(sys.argv) != 1:
        print "Usage upload_protocol.py"
    
    ingest.ingest_protocol(server)