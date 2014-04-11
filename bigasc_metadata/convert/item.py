'''
Created on Sep 14, 2012

@author: steve

Convert item level metadata to RDF
'''
from xml.etree import ElementTree
from rdflib import Literal
import os, urllib2, re

import map
from namespaces import *
from session import component_map, clean_prompt, item_prompt
from participant import participant_uri

from participant import item_site_name
from filepaths import parse_item_filename, parse_media_filename, item_file_uri, item_file_basename


def generate_file_metadata(graph, filename, dirname=None):
    """Generate metadata records for a single media file
    associated with an item, given the filename. dirname if supplied
    is the new directory that this file is to be stored in, eg. audio, downsampled.
    This is used to generate the file uri in the description.

>>> from rdflib import Graph
>>> graph = Graph()
>>> md = generate_file_metadata(graph, "test/items/1_178_2_16_001-ch6-speaker.wav")
>>> len(md)
6
    """
    
    basename = item_file_basename(filename)
    item_uri = generate_item_uri(basename)
    m_uri = item_file_uri(filename, dirname)
    properties = parse_media_filename(filename)
    
    graph.add((item_uri, AUSNC.document, m_uri))
    # add file properties
    graph.add((m_uri, RDF.type, FOAF.Document))
    graph.add((m_uri, DC['format'], Literal(properties['mimetype'])))
    graph.add((m_uri, DC.type, Literal(properties['type'])))
    
    for prop in ['version', 'checksum', 'channel', 'sequence']:
        if properties.has_key(prop):
            graph.add((m_uri, NS[prop], Literal(properties[prop])))
            
    # add identifier field which is just the filename
    graph.add((m_uri, DC.identifier, Literal(os.path.basename(filename))))

    return graph



class ItemMapper:
    
    def __init__(self, errorlog=None):
        """Initialise an item mapper"""
        
        if errorlog == None:
            self.errorlog = sys.stderr
        else:
            self.errorlog = errorlog
        self.init_map()
        self.component_map = component_map()

    def error(self, message):
        """Log an error"""
        self.errorlog.write(message + "\n")
    
    
    def init_map(self):
        """Initialise the RDF map"""
        
        self.itemmap = map.FieldMapper()
        self.itemmap.add("path", ignore=True)
        self.itemmap.add('colour', ignore=True)
        self.itemmap.add('animal', ignore=True)
        self.itemmap.add('item', ignore=True) # will be replaced with a link to item
        self.itemmap.add('participant', ignore=True) # will replace with pointer to participant
        self.itemmap.add('component', mapper=self.map_component)
        self.itemmap.add('session', mapper=self.map_session)
        
        self.itemmap.add('timestamp', mapto=DC.created)
        
        self.itemmap.add('basename', mapto=DC.identifier)
    
        # TODO: deal with maptask properties
        self.itemmap.add('otherAnimal', ignore=True)
        self.itemmap.add('otherColour', ignore=True)
        self.itemmap.add('otherParticipant', ignore=True)
        self.itemmap.add('role', ignore=True)
        self.itemmap.add('map', ignore=True)

        #self.itemmap.add('files', mapper=self.map_files)
        self.itemmap.add('files', ignore=True)
        self.itemmap.add('componentName', ignore=True)
        

    def map_component(self, subj, prop, value):
        """Map the component field to point to the 
        appropriate component URI"""
        
        cid = PROTOCOL_NS[COMPONENT_URI_TEMPLATE % value]
        
        return [(subj, NS.component, cid)]
    
    def map_session(self, subj, prop, value):
        """Map the session field a value 1-3"""
        
        # fold 3/4
        if value == "4":
            value = "3"
    
        #sid = PROTOCOL_NS[SESSION_URI_TEMPLATE % value]
        
        return [(subj, NS.session, Literal(value))]

        
    COMPONENTS = {'spontaneous': [
                        "interview",
                        "calibration",
                        "maptask-1",
                        "maptask-2",
                        "yes-no-opening-2",
                        "yes-no-closing",
                        "yes-no-opening-1",
                        "yes-no-opening-3",
                        "conversation",
                        "re-told-story",
                              ],
                  'read': [
                        "words-3-2",
                        "words-2-2",
                        "story",
                        "digits",
                        "words-1-2",
                        "sentences",
                        "words-3",
                        "words-2",
                        "words-1",
                        "sentences-e",
                       ]
              }

        
    def item_generic_properties(self, graph, item_uri, component):
        """Generate the triples describing the 'genre' of this item"""
         
        # get the component short name, easier to work with
        component = self.component_map[int(component)]
        
        graph.add((item_uri, NS.componentName, Literal(component)))
        graph.add((item_uri, AUSNC.mode, AUSNC.spoken))
        
        # face_to_face, distance
        graph.add((item_uri, AUSNC.communication_context, AUSNC.face_to_face))
        
        #  individual, massed, small-group, unseen, mass-market, specialised
        graph.add((item_uri, AUSNC.audience, AUSNC.individual))
        
        # some components are read, others are interview or dialogue
        if component in self.COMPONENTS['read']:
            graph.add((item_uri, AUSNC.interactivity, AUSNC.read))
            graph.add((item_uri, AUSNC.speech_style, AUSNC.scripted))
        elif component == 'interview':
            graph.add((item_uri, AUSNC.interactivity, AUSNC.interview))
            graph.add((item_uri, AUSNC.speech_style, AUSNC.spontaneous))
        elif component == 're-told-story':
            graph.add((item_uri, AUSNC.interactivity, AUSNC.monologue))
            graph.add((item_uri, AUSNC.speech_style, AUSNC.spontaneous))
        else:
            graph.add((item_uri, AUSNC.interactivity, AUSNC.dialogue))
            graph.add((item_uri, AUSNC.speech_style, AUSNC.spontaneous))
        


 

        
    
    def item_rdf(self, xmlfile, csvdata=None):
        """Given the url of an item xml file, read the metadata and map
        to RDF, returning a graph
        
        If csvdata is present it should be the metadata extracted from the
        RA spreadsheet, we'll use it to fill in gaps in maptask data if present
    
    >>> import sys
    >>> sys.path.append("..")
    >>> from ingest import SesameServer
    >>> mdurl = "test/items/1_178_2_16_001.xml"
    >>> im = ItemMapper()
    >>> graph = im.item_rdf(mdurl)
    >>> [t for t in graph.subject_objects(NS.cameraSN0)]
    [(rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_178_2_16_001'), rdflib.term.Literal(u'11051192'))]
    
    >>> [t for t in graph.subject_objects(DC.created)]
    [(rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_178_2_16_001'), rdflib.term.Literal(u'Tue Feb 21 10:37:05 2012'))]
    
    # print graph.serialize(format='turtle') 
     
     # a maptask item with full metadata
    >>> mfile = "test/items/1_530_3_8_001.xml"
    >>> graph = im.item_rdf(mfile)
    >>> [t for t in graph.subject_objects(NS.information_follower)]
    [(rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_530_3_8_001'), rdflib.term.URIRef(u'http://id.austalk.edu.au/participant/4_172'))]
                
    # this one is a maptask item with no second speaker metadata
    >>> mfile = "test/items/1_619_4_10_001.xml"
    >>> from ra_maptask import RAMapTask
    >>> mt = RAMapTask()
    >>> (s, m) = mt.read_all()
    >>> graph2 = im.item_rdf(mfile, m)
    >>> [t for t in graph2.subject_objects(NS.information_giver)]
    [(rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_619_4_10_001'), rdflib.term.URIRef(u'http://id.austalk.edu.au/participant/1_69'))]
    
    # this one is too, via a URL
    >>> mdurl = "test/items/1_719_4_10_001.xml"
    >>> graph3 = im.item_rdf(mdurl, m)
    >>> [t for t in graph3.subject_objects(NS.information_giver)]
    [(rdflib.term.URIRef(u'http://id.austalk.edu.au/item/1_719_4_10_001'), rdflib.term.URIRef(u'http://id.austalk.edu.au/participant/2_114'))]
    
    >>> print graph3.serialize(format='turtle')   

    
        """
        
        md = self.read_metadata(xmlfile)
        
        # reset prompt from the session
        prompt = item_prompt(md['basename'])
        md['prompt'] = prompt
        
        # generate a URI for this component 
        component_uri = generate_component_uri(md['colour'], md['animal'], md['session'], md['component'])
        # the prototype is the component we're an example of
        component_prototype = PROTOCOL_NS[COMPONENT_URI_TEMPLATE % md['component']]

        # generate a URI for this session 
        session_uri = generate_session_uri(md['colour'], md['animal'], md['session'])
        # the prototype is the session we're an example of
        session_prototype = PROTOCOL_NS[SESSION_URI_TEMPLATE % md['session']]
        
        item_uri = generate_item_uri(md['basename'])
        
        # generate participant uri and use it to find the site name which we'll use
        # later in mapping file names to uris
        
        self.participant_uri = participant_uri(md['colour'], md['animal'])
        self.site_name = item_site_name(self.participant_uri)
        
        participant_id = "%(colour)s_%(animal)s" % md
        
        graph = self.itemmap.mapdict(item_uri, md, NS['graph/data'])
        
        # add link to the main participant
        graph.add((item_uri, OLAC.speaker, self.participant_uri))
        
        # details of other participant and speaker roles for maptask
        if 'Map' in md['componentName']:
            # check if metadata is present
            if md.has_key('otherColour') and md.has_key('otherAnimal'):
                other_participant_uri = participant_uri(md['otherColour'], md['otherAnimal'])
                if md.has_key('map'):
                    mapname = md['map']
                else:
                    mapname = None
                    
                if md.has_key('role'):
                    role=md['role']
                else:
                    role=None
                    
            elif csvdata != None and csvdata.has_key(participant_id): 
                other_participant_id = csvdata[participant_id]['partner']
                other_participant_uri = participant_uri('', '', other_participant_id)
                mapname = csvdata[participant_id]['map']
                role = csvdata[participant_id]['role']
            else:
                other_participant_uri = None
                mapname = None
                role = None
                
            if other_participant_uri != None:
                graph.add((item_uri, OLAC.speaker, other_participant_uri))
                
            if role != None:
                if role == 'Information Giver':
                    graph.add((item_uri, NS.information_giver, self.participant_uri))
                    graph.add((item_uri, NS.information_follower, other_participant_uri))
                elif role ==  'Information Follower':
                    graph.add((item_uri, NS.information_follower, self.participant_uri))
                    graph.add((item_uri, NS.information_giver, other_participant_uri))
            else:
                self.error("\tNo role for item: %s" % md['basename'])
                
            # generate a triple for the map, standardising the name
            maps = {'Map A - architecture': 'map/A-architecture',
                    'Map A - colour': 'map/A-colour', 
                    'Map B - architecture': 'map/B-architecture',
                    'Map B - colour': 'map/B-colour',
                    # these for cvsdata
                    'MapA-Architecture': 'map/A-architecture',
                    'MapA-Colour': 'map/A-colour', 
                    'MapB-Architecture': 'map/B-architecture',
                    'MapB-Colour': 'map/B-colour'
            }

            if maps.has_key(mapname):
                mapname = PROTOCOL_NS[maps[mapname]]
                graph.add((item_uri, NS.map, mapname))
            else:
                self.error("\tUnknown map name: %s in %s " % (mapname, md['basename']))

        graph.add((item_uri, RDF.type, AUSNC.AusNCObject))
        
        # add some standard metadata
        graph.add((item_uri, DC.title, Literal(md['basename'])))
        
        # part of the component, which has a prototype
        graph.add((component_uri, NS.prototype, component_prototype))
        graph.add((component_uri, RDF.type, NS.RecordedComponent))
        graph.add((item_uri, DC.isPartOf, component_uri))
        graph.add((component_uri, OLAC.speaker, self.participant_uri))
        # a redundant property to make web queries for speaker+session faster
        graph.add((component_uri, NS.session, Literal(md['session'])))
        
        # and part of the session
        graph.add((session_uri, NS.prototype, session_prototype))
        graph.add((session_uri, RDF.type, NS.RecordedSession))
        graph.add((component_uri, DC.isPartOf, session_uri))
        graph.add((session_uri, OLAC.speaker, self.participant_uri))
        graph.add((session_uri, NS.session, Literal(md['session'])))
        
        # add link to item prototype
        iid = PROTOCOL_NS[ITEM_URI_TEMPLATE % (md['component'], md['item'])]
        graph.add((item_uri, NS.prototype, iid))
        
        # add a link to the collection level record
        graph.add((item_uri, DC.isPartOf, CORPUS_URI))
        
        
        self.item_generic_properties(graph, item_uri, md['component'])
        
        
        # add some namespaces to make output prettier
        graph.bind('austalk', NS)
        graph.bind('olac', OLAC)
        graph.bind('ausnc', AUSNC)
        graph.bind('rdf', RDF)
        graph.bind('dc', DC)
        
        return graph

    
    
    def read_metadata(self, mdfile):
        """Read item metadata from the given file
        return a dictionary of values
    
    >>> import sys
    >>> sys.path.append("..")
    >>> mdurl = "test/items/1_178_2_16_001.xml"
    >>> im = ItemMapper()
    >>> mdfile = "test/items/1_1121_1_12_001.xml"
    >>> im.read_metadata(mdfile)
    {'files': {'1_1121_1_12_001-ch6-speaker.wav': {'checksum': 'e0012015d6babdce61cb553939d87792', 'basename': '1_1121_1_12_001', 'filename': '1_1121_1_12_001-ch6-speaker.wav', 'version': 1, 'type': 'audio', 'channel': 'ch6-speaker'}, '1_1121_1_12_001-ch1-maptask.wav': {'checksum': '3a1ac90a5a3940ac1cb9046d5546b574', 'basename': '1_1121_1_12_001', 'filename': '1_1121_1_12_001-ch1-maptask.wav', 'version': 1, 'type': 'audio', 'channel': 'ch1-maptask'}, '1_1121_1_12_001-ch4-c2Left.wav': {'checksum': 'db028ab9647fe0e04377f338451ed53a', 'basename': '1_1121_1_12_001', 'filename': '1_1121_1_12_001-ch4-c2Left.wav', 'version': 1, 'type': 'audio', 'channel': 'ch4-c2Left'}, '1_1121_1_12_001-camera-0-left.mp4': {'checksum': '6065f4a33f4008b592a1f6d178bea5fb', 'basename': '1_1121_1_12_001', 'filename': '1_1121_1_12_001-camera-0-left.mp4', 'version': 1, 'type': 'video', 'channel': 'camera-0-left'}, '1_1121_1_12_001-ch5-c2Right.wav': {'checksum': '630d4d53a57e9f5ae01c6d764d8f169a', 'basename': '1_1121_1_12_001', 'filename': '1_1121_1_12_001-ch5-c2Right.wav', 'version': 1, 'type': 'audio', 'channel': 'ch5-c2Right'}}, 'participant': "Gold-Blainville's Beaked Whale", 'cameraSN1': '10251399', 'cameraSN0': '10251399', 'componentName': 'Words Session 1', 'colour': '1', 'component': '12', 'item': '1', 'session': '1', 'animal': '1121', 'timestamp': 'Mon Jul 18 16:48:43 2011', 'prompt': 'slide2.jpg', 'path': '/tmp/tmph7F7_g', 'basename': '1_1121_1_12_001'}
    
    # an example of regenerated metadata, has no basename so we need to reconstruct it
    >>> mdfile = "test/items/1_178_4_12_001.xml"
    >>> md = im.read_metadata(mdfile)
    >>> md['basename']
    '1_178_4_12_001'
    
    # grab an example that has -n files
    >>> mdurl = "test/items/1_178_2_16_001.xml"
    >>> md = im.read_metadata(mdurl)
    >>> md['cameraSN1']
    '11072159'
    >>> md['files'].keys()
    ['1_178_2_16_001-ch5-c2Right.wav', '1_178_2_16_001-n-ch6-speaker.wav', '1_178_2_16_001-ch3-strobe.wav', '1_178_2_16_001-n-ch1-maptask.wav', '1_178_2_16_001-ch4-c2Left.wav', '1_178_2_16_001-ch1-maptask.wav', '1_178_2_16_001-camera-0-left.mp4', '1_178_2_16_001-camera-0-right.mp4', '1_178_2_16_001-ch6-speaker.wav', '1_178_2_16_001-n-ch4-c2Left.wav', '1_178_2_16_001-ch2-boundary.wav', '1_178_2_16_001-n-ch5-c2Right.wav', '1_178_2_16_001-n-camera-0-right.mp4', '1_178_2_16_001-n-ch2-boundary.wav', '1_178_2_16_001-n-camera-0-left.mp4', '1_178_2_16_001-n-ch3-strobe.wav']
    >>> md['files']['1_178_2_16_001-n-ch5-c2Right.wav']
    {'checksum': '2d5b13b05063a4b3b845672d1ca4eb91', 'basename': '1_178_2_16_001', 'filename': '1_178_2_16_001-n-ch5-c2Right.wav', 'version': 2, 'type': 'audio', 'channel': 'ch5-c2Right'}
    
        """
    
        result = dict()
        
        # parse the xml, might fail but we'll just pass on the exception 

        h = open(mdfile)
        xmltext = h.read()
        h.close()
        
        dirname = os.path.dirname(mdfile)
        
        root = ElementTree.fromstring(xmltext)
        
        if root is None:
            # no root element found  => corrupted xml
            # we got nothing
            return result
     
        result['files'] = dict()
        
        for node in root: 
            name = node.tag
            if name == "files":
                # we make a list of the filenames
                for ch in node.findall(".//file"):
                    filename = ch.text
                    # early versions were writing .xml files into the metadata, we don't
                    # want to know about that
                    # we also don't want to know about files that don't exist (eg. some .raw16 files
                    # are in the metadata but were removed
                
                    if not filename.endswith(".xml") and os.path.exists(os.path.join(dirname, filename)):
                        
                        # for each file we'll make a dictionary with it's properties
                        if not result['files'].has_key(filename):
                            result['files'][filename] = {'filename': filename}
                        
                        # we're ignoring the 'uploaded' attribute here
                        # since it's not really of interest 
                        
                        if ch.get('md5hash') is not None:
                            result['files'][filename]['checksum'] = ch.get('md5hash')
                        # add new properties for file type and channel
                        info = parse_media_filename(filename, self.errorlog)
                        for key in info.keys():
                            result['files'][filename][key] = info[key]
                        
    
    
            elif name == "checksums":
                # handle old style checksums in a separate element
                for ch in node.findall(".//md5hash"):
                    filename = ch.get('file')
                    if not result['files'].has_key(filename) and os.path.exists(os.path.join(dirname, filename)):
                        result['files'][filename] = {'filename': filename}
                    result["files"][filename]['checksum'] = ch.text
    
                        
            elif name == "uploaded": 
                pass
            else:
                result[name] = node.text
        
        # regenerated metadata has no basename
        if not result.has_key('basename'):
            result['item'] = int(result['item'])
            result['basename'] = "%(colour)s_%(animal)s_%(session)s_%(component)s_%(item)03d" % result
        
        return result
    

if __name__=='__main__':
        
        import doctest
        doctest.testmod()
        
        

        
          