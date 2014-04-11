"""Some query operations on the metadata store"""


PREFIXES = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dc: <http://purl.org/dc/terms/>
PREFIX ausnc: <http://ns.ausnc.org.au/schemas/ausnc_md_model/>
PREFIX olac: <http://www.language-archives.org/OLAC/1.1/>
PREFIX ice: <http://ns.ausnc.org.au/schemas/ice/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX graf: <http://www.xces.org/ns/GrAF/1.0/>
PREFIX austalk: <http://ns.austalk.edu.au/>
PREFIX protocol: <http://id.austalk.edu.au/protocol/>
PREFIX austalkd: <http://data.austalk.edu.au/>

"""


def media_query(server, qterms, channel='ch6-speaker'):
    """query for items with some properties
    and return a list of media file urls
    
    qterms is a list of query terms that will restrict
    the items returned, the variable ?obj will refer to
    the AusNCObject instance they qualify
    
    channel is the name of the channel to be returned, default ch6-speaker
    
    returns a list of media file urls
    """
    
    q = PREFIXES + """select ?media where {
 ?obj rdf:type ausnc:AusNCObject .
 %(qterms)s
 ?obj austalk:media ?media .
 ?media austalk:version 1 .
 ?media austalk:channel "%(channel)s" .
} order by ?media"""

    q = q % {'qterms': qterms, 'channel': channel}
    
    result = server.query(q)
    
    items = []
    for row in result['results']['bindings']:
        items.append(row['media']['value'])
        
    return items
            


    