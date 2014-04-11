'''
Created on Oct 2, 2012

@author: steve
'''

if __name__ == '__main__':
    from query import media_query
    from ingest import SesameServer
    server_url = "http://115.146.94.199/openrdf-sesame/repositories/bigasc" 
    
    server = SesameServer(server_url)
    
    qterms = """
 ?obj olac:speaker ?spkr .
 ?spkr foaf:gender "male" .
 ?obj dc:isPartOf ?rc .
 ?rc austalk:prototype ?comp .
 ?comp austalk:shortname "digits" .
    """
    
    items = media_query(server, qterms)
    
    import json
    
    request = {'media': items,
                 'name':  'male_digits',
                 }
    
    request_j = json.dumps(request, indent=True)
    print request_j
    