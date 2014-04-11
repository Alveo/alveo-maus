'''
Created on Sep 18, 2012

@author: Steve Cassidy

Namespace declarations for use in RDF generation
'''

from rdflib import Namespace

# for properties and classes specific to Austalk
AUSTALK = Namespace(u"http://ns.austalk.edu.au/")

# for elements of the protocol
PROTOCOL_NS = Namespace(u"http://id.austalk.edu.au/protocol/")

# for media files
DATA_NS = Namespace(u"http://data.austalk.edu.au/")

# for all entities (items, participants etc)
ID_NS = Namespace(u"http://id.austalk.edu.au/")

# Define namespaces
RDF = Namespace(u"http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
DC = Namespace(u"http://purl.org/dc/terms/")
FOAF = Namespace(u"http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace(u"http://schemas.talis.com/2005/address/schema#")
OLAC = Namespace(u"http://www.language-archives.org/OLAC/1.1/")
GRAF = Namespace("http://www.xces.org/ns/GrAF/1.0/")
RDFS = Namespace(u"http://www.w3.org/2000/01/rdf-schema#")
DBP = Namespace("http://dbpedia.org/ontology/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#") # for lat and long
ISO639 = Namespace("http://downlode.org/rdf/iso-639/languages#")
ISO639SCHEMA = Namespace("http://downlode.org/rdf/iso-639/schema#")


AUSNC = Namespace(u"http://ns.ausnc.org.au/schemas/ausnc_md_model/")

# this hack finds all of the namespaces defined above and 
# puts them into a dictionary that we can use in bind_graph
import sys
NameSpaces = dict()
namespaces = [n for n in sys.modules[__name__].__dict__.keys() if n.isupper()]
for ns in namespaces:
    NameSpaces[ns.lower()] = eval(ns)

def bind_graph(graph):
    
    for ns in NameSpaces.keys():
        graph.bind(ns, NameSpaces[ns]) 

    return graph

# for backwards compatibility but we don't want it above
NS = AUSTALK

# a URI for the corpus as a whole
CORPUS_URI = AUSTALK.corpus

SESSION_URI_TEMPLATE = "session/%s"
COMPONENT_URI_TEMPLATE = "component/%s"
ITEM_URI_TEMPLATE = "item/%s_%s"


DATA_URI_TEMPLATE = "%(site)s/%(speaker)s/%(session)s/%(componentName)s/%(filename)s"
# for current data location
#DATA_URI_TEMPLATE = "%(site)s/Spkr%(colour)s_%(animal)s/Spkr%(colour)s_%(animal)s_Session%(session)s/Session%(session)s_%(component)s/%(filename)s"


def generate_component_uri(colour_id, animal_id, session, component):
    """Return the URI for the component identified by these ids"""
    
    return ID_NS['component/%s_%s_%s_%s' % (colour_id, animal_id, session, component)]

def generate_session_uri(colour_id, animal_id, session):
    """Return the URI for the session identified by these ids"""
    
    return ID_NS['session/%s_%s_%s' % (colour_id, animal_id, session)]

def generate_item_uri(basename):
    
    return ID_NS["item/" + basename]
