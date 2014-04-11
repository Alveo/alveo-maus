
from sesameupload import SesameServer
from convert.ra_maptask import RAMapTask
import convert
from data import map_session
import os, sys


      
def ingest_session_map(server, sessiondir, csvdata, errorlog):
    """Given a base directory for a session, upload the metadata
    for the session to the server"""

    mapper = convert.ItemMapper(errorlog)
    
    def process_item(site, spkr, session, component, item_path):
        """upload metadata for a single item"""
        
        try:
            graph = mapper.item_rdf(item_path+".xml", csvdata)
            server.output_graph(graph, convert.item_file_path(item_path, "metadata"))
        except Exception as ex:
            errorlog.write("Problem with item: %s\n\t%s\n" % (item_path, ex))
            
    result = [x for x in map_session(sessiondir, process_item)]
    return result

def ingest_protocol(server):
    """Generate RDF for the protocol and upload it 
    to the server (an instance of SesameServer)"""
    
    assert(isinstance(server, SesameServer))

    graph = convert.session_metadata()
    
    print "Generated", len(graph), "triples for sessions"
    server.output_graph(graph, 'metadata/protocol/sessions')
    
    graph = convert.component_metadata()
    
    print "Generated", len(graph), "triples for components"
    server.output_graph(graph, 'metadata/protocol/components')
        
    graph = convert.item_metadata()
    
    print "Generated", len(graph), "triples for items"
    server.output_graph(graph, 'metadata/protocol/items')
        

def ingest_participants(server):
    """Generate RDF for all participants and upload it 
    to the server (an instance of SesameServer)"""
    
    assert(isinstance(server, SesameServer))

    participants = convert.get_participant_list()
    print "Processing", len(participants), "participants"
    
    convert.reset_site_mapping()
    
    maptask = RAMapTask()
    (spkr, mapname) = maptask.read_all()
    
    for p in participants:
        
        if spkr.has_key(p):
            csvdata = spkr[p]
        else:
            csvdata = None
        
        p_info = convert.get_participant(p)
        graph = convert.participant_rdf(p_info, csvdata)
    
        print "Generated", len(graph), "triples for participant", p
        server.output_graph(graph, os.path.join('metadata', 'participants', p))

        