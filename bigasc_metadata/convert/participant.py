'''
Created on Sep 18, 2012

@author: Steve Cassidy

Convert meta-data about participants harvested from the web server database to RDF
'''
from rdflib import Literal
import urllib2
import json
import os

import map
from namespaces import *
import configmanager
configmanager.configinit()
PARTICIPANT_DETAIL = configmanager.get_config("PARTICIPANT_DETAIL", "FULL")

# file to write site mapping to in map_location
# used to speed up lookup of sites for items
SITE_MAPPING_FILE = "sitemap.dat"
SITE_MAP = None

def item_site_name(spkruri):
    """Given a speaker URI, return the short name of the
    the recording site for inclusion in the file path
    
>>> item_site_name("http://id.austalk.edu.au/participant/1_530")
'ANU'
>>> item_site_name("http://id.austalk.edu.au/participant/1_719")
'ANU'
 
    """

    global SITE_MAP
    
    if SITE_MAP == None:
        if not os.path.exists(SITE_MAPPING_FILE):
            raise Exception("ERROR: No site mapping file, run upload_participants first")
           
        
        h = open(SITE_MAPPING_FILE, 'r')
        lines = h.readlines()
        h.close()
        SITE_MAP = dict()
        
        for line in lines:
            (id, site) = line.split()
            SITE_MAP[id] = site 
        
  #  print "sitename for", spkruri,
    
    # it might be a URI object, coerce it to string
    spkruri = str(spkruri)
    
    if SITE_MAP.has_key(spkruri):
    #    print SITE_MAP[spkruri]
        return SITE_MAP[spkruri]
    else:
    #    print "UNKNOWN"
        return "UNKNOWN"

def reset_site_mapping():
    
    if os.path.exists(SITE_MAPPING_FILE):
        os.unlink(SITE_MAPPING_FILE)


def record_site_mapping(subj, site_id):
    """Record the mapping between a speaker and a site"""
    
    h = open(SITE_MAPPING_FILE, 'a')
    h.write("%s %s\n" % (subj, site_id))
    h.close()
    





#PARTICIPANT_URI = "https://echidna.science.mq.edu.au/forms/export/participants/"
PARTICIPANT_URI = "https://austalk.edu.au/forms/export/participants/"


# list exceptions to our site short name generator
SITE_SHORTNAMES = {
"UOCC": "UC",    # "University of Canberra"        "Canberra"
"UOTH": "UTAS", # "University of Tasmania"        "Hobart"
"ANUC":  "ANU",  # "Australian National University"        "Canberra"
"UOSS": "USYD", # "University of Sydney"  "Sydney"
"UOWAP": "UWA",   # "University of Western Australia"       "Perth"
"UOTSCM": "USCM", # "University of the Sunshine Coast"      "Maroochydore"
"UONEA": "UNE",   # "University of New England"     "Armidale"
"UONSWS": "UNSW", # "University of New South Wales" "Sydney"
"UOMM": "UMELBM", # "University of Melbourne"       "Melbourne"
"UOMC": "UMELBC", # "University of Melbourne"       "Castlemaine"
"UOQT": "UQT",  # "University of Queensland"      "Townsville"
"UOQB": "UQB",  # "University of Queensland"      "Townsville"
"FUA": "FLIN", 
}

from pycountry import languages
def map_language_name(subj, prop, value):
    """Value is a language name from the database, we map it 
    to a standard language name and return some triples"""
    
    name = value.strip().capitalize()
    
    # some common cases
    
    if name == "Australian":
        name = "English"
    elif name == "Dutch":
        name = "Dutch; Flemish"
    elif name in ['Mandarin', 'Cantonese']:
        name = "Chinese"
    elif name == 'Spanish':
        name = "Spanish; Castilian"
    elif name == "Greek":
        name = "Greek, Modern (1453-)"
    
    # try to get the language directly
    lang = None
    try:
        lang = languages.get(name=name)
    except KeyError:
        # try splitting the words
        name = name.replace('/', ' ')
        if name.find(' '):
            for name in name.split():
                try: 
                    lang = languages.get(name=name.strip().capitalize())
                    break
                except KeyError:
                    pass
    if lang == None or getattr(lang, 'alpha2', None) == None:
        print "No language found for '%s'" % name
        #h = open("unknown-languages.txt", "a")
        #h.write(name + " " + subj + "\n")
        #h.close()
        return [(subj, NS[prop], Literal(name))]
    else:
        code = getattr(lang, 'alpha2', None)
        languri = ISO639[code]
        return [(subj, NS[prop], languri),
                (languri, RDF.type, ISO639SCHEMA.Language),
                (languri, ISO639SCHEMA.alpha2, Literal(code)),
                (languri, ISO639SCHEMA.name, Literal(getattr(lang, 'name', name)))]
    


def get_participant_list():
    """Return a list of participant ids"""
    
    uri = PARTICIPANT_URI
    
    h = urllib2.urlopen(uri)
    data = h.read()
    h.close()
    
    result = json.loads(data)
    # we just want the 'id' field from each record
    result = [r['id'] for r in result]
    
    return result
    

def get_participant(id):
    """id is a numerical participant identifier (1_123),
    get the participant metadata from the server and 
    return as a dictionary
     
>>> p = get_participant('2_450') 
>>> p['animal']['id']
450
>>> p['colour']['id']
2
>>> p = get_participant('1_978') 
>>> p['animal']['id']
978
>>> p['colour']['id']
1
    """
    
    #print "get_participant", id
    
    uri = PARTICIPANT_URI + id
     
    
    h = urllib2.urlopen(uri)
    data = h.read()
    h.close()
     
    result = json.loads(data)
    #print "result", result['animal']
    
    return result


def get_participant_from_file(filename):
    """id is a numerical participant identifier (1_123),
    get the participant metadata from the given filename and 
    return as a dictionary (mainly for testing)
    
>>> part_file = "test/participant.json"
>>> p = get_participant_from_file(part_file) 
>>> p['animal']['id']
450
>>> p['colour']['id']
2
    
    """
    
    h = open(filename)
    data = h.read()
    h.close()
    
    result = json.loads(data)
    
    return result


def add_geolocation(p_uri, predicate, location, graph):
    """Location is a triple (town, state, country) or (suburb, postcode, country)
    which will be used to  
    find a geonames URI for the location and then add a location to the graph
    (p_uri, predicate, <location>)
    """
    
    from geonames import GeoNames
    
    g = GeoNames()
    
    info = g.placename_info(location[0], location[1], location[2])

    if info == None:
        return
    
    pob_uri = g.placename_uri(info)
    
    graph.add((p_uri, NS.birthPlace, pob_uri))
    graph.add((pob_uri, RDF.type, GEO.Feature))
    graph.add((pob_uri, GEO.lat, Literal(info['lat'])))
    graph.add((pob_uri, GEO.long, Literal(info['long'])))


 

def map_gender(subj, prop, value):
    """Map gender (M or F) to FOAF.gender (male or female)
>>> map_gender('foo', 'sex', 'M')
[('foo', rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/gender'), rdflib.term.Literal(u'male'))]
>>> map_gender('foo', 'sex', 'F')
[('foo', rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/gender'), rdflib.term.Literal(u'female'))]
>>> map_gender('foo', 'sex', 'U')
Unknown value for SEX: U
[('foo', rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/gender'), rdflib.term.Literal(u'U'))]

    """
    
    
    if value == "M":
        value = "male"
    elif value == "F":
        value = "female"
    else:
        print "Unknown value for SEX: %s" % value
        #raise Exception("Unknown value for SEX in ICE: %s" % value)
    
    return [(subj, FOAF.gender, Literal(value))]

def map_dob(subj, prop, value):
    """Map date of birth, only retain the year
>>> map_dob('foo', 'dob', '1992-01-21')
[('foo', rdflib.term.URIRef(u'http://dbpedia.org/ontology/birthYear'), rdflib.term.Literal(u'1992', datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#integer'))), ('foo', rdflib.term.URIRef(u'http://ns.austalk.edu.au/ageGroup'), rdflib.term.Literal(u'<30')), ('foo', rdflib.term.URIRef(u'http://xmlns.com/foaf/0.1/age'), rdflib.term.Literal(u'20', datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#integer')))]
"""
    
    (y, m, d) = value.split('-')
    # calculate age group relative to 2012
    age = 2012-int(y)
    if age < 30:
        ageGroup = "<30"
    elif age < 50:
        ageGroup = "30-49"
    else:
        ageGroup = ">50"
    
    return [(subj, DBP.birthYear, Literal(int(y))),
            (subj, NS.ageGroup, Literal(ageGroup)),
            (subj, FOAF.age, Literal(age))]


def map_ra(subj, prop, value):
    """Map the RA (Research Assistant) field to a 
    unique but anonymous identifier for the RA - the md5hash of their email address in lowercase

>>> ra_info = {u'username': u'steve', u'first_name': '', u'last_name': '', u'is_active': True, u'email': u'steve.cassidy@mq.edu.au', u'is_superuser': True, u'is_staff': True, u'last_login': u'2012-02-01 18:00:05', u'id': 1, u'date_joined': u'2011-06-24 15:20:35'}
>>> graph = map_ra('foo', 'RA', ra_info)
>>> len(graph)
2
>>> graph[0][2]
rdflib.term.URIRef(u'http://id.austalk.edu.au/453dd33bc7976708d8b64f94fb2e50e8')
"""
    import hashlib
    import time
    
    # add some salt so that we can't discover the identity if we know the email address or name
    # not really secure but better than nothing
    salt = "this is some salt"
    
    if value.has_key('email'):
        email = value['email'].lower()
        hash = hashlib.md5(salt+email).hexdigest()
    else:
        user = value['username'].lower()
        hash = hashlib.md5(salt+user).hexdigest()

    # make a person ID and record them as a foaf:Person
    return [(subj, OLAC.recorder, ID_NS[hash]),
            (ID_NS[hash], RDF.type, FOAF.Person)]
    

def map_location(subj, prop, value):
    """Map the location value to one of the defined site names

>>> loc = {u'city': u'Bathurst', u'state': u'NSW', u'name': u'Charles Sturt University', u'id': 4} 
>>> map_location('foo', 'location', loc)
[('foo', rdflib.term.URIRef(u'http://ns.austalk.edu.au/recording_site'), rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/CSUB')), (rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/CSUB'), rdflib.term.URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/RecordingSite')), (rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/CSUB'), rdflib.term.URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'), rdflib.term.Literal(u'CSUB')), (rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/CSUB'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/city'), rdflib.term.Literal(u'Bathurst')), (rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/CSUB'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/institution'), rdflib.term.Literal(u'Charles Sturt University'))]
>>> loc = {u'city': u"Maroochydore", u'state': u'QLD', u'name': u'University of the Sunshine Coast', u'id': 6} 
>>> for t in map_location('bar', 'location', loc):
...   print t
('bar', rdflib.term.URIRef(u'http://ns.austalk.edu.au/recording_site'), rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/USCM'))
(rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/USCM'), rdflib.term.URIRef(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/RecordingSite'))
(rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/USCM'), rdflib.term.URIRef(u'http://www.w3.org/2000/01/rdf-schema#label'), rdflib.term.Literal(u'USCM'))
(rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/USCM'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/city'), rdflib.term.Literal(u'Maroochydore'))
(rdflib.term.URIRef(u'http://id.austalk.edu.au/protocol/site/USCM'), rdflib.term.URIRef(u'http://ns.austalk.edu.au/institution'), rdflib.term.Literal(u'University of the Sunshine Coast'))
   """

    site_id = map_site_name(value['name'], value['city'])
    
    site_uri = PROTOCOL_NS["site/"+site_id]
    
    # for person-site mapping
    record_site_mapping(subj, site_id)
    
    return [(subj, NS.recording_site, site_uri),
            (site_uri, RDF.type, NS.RecordingSite),
            (site_uri, RDFS.label, Literal(site_id)),
            (site_uri, NS.city, Literal(value['city'])),
            (site_uri, NS.institution, Literal(value['name']))]

def map_site_name(name, city):
    """Given a site name and city, generate the short name that we're going to 
    use in future
    
>>> map_site_name("University of Queensland", "Brisbane")
'UQB'
>>> map_site_name("Univeristy of Tasmania", "Hobart")
'UTAS'
>>> map_site_name("University of Sydney", "Sydney")
'USYD'
    """
    
    # get initials of name
    inits = [w[0] for w in name.split()]
    # and first letter of city
    inits += city[0]
    inits = "".join(inits).upper()

    # pull in the exception if present
    if SITE_SHORTNAMES.has_key(inits):
        inits = SITE_SHORTNAMES[inits]
        
    return inits


def map_ratings(graph, p_md):
    """generate triples to record the ratings for 
    sessions and add them to the graph"""
    
    
    for rating in p_md['rating']:
        
        c_uri = generate_component_uri(p_md['colour']['id'], p_md['animal']['id'], rating['session'], rating['component'])
        graph.add((c_uri, NS.videorating, Literal(rating['video'])))
        graph.add((c_uri, NS.audiorating, Literal(rating['audio'])))
        graph.add((c_uri, NS.comment, Literal(rating['comment'])))



def generate_partmap():
    # a map for nested properties (education and professional history)
    submap = map.FieldMapper()
    submap.add('_state', ignore=True)
    submap.add("id", ignore=True)
    submap.add("name", mapper=map_language_name)
    
    
    if PARTICIPANT_DETAIL == "MINIMAL":
        partmap = map.FieldMapper(copy_if_unknown=False)
    else:    
        partmap = map.FieldMapper()
    
    
    partmap.add("dob", mapper=map_dob)
    partmap.add("_state", ignore=True)
    partmap.add("id", ignore=True)
    partmap.add("participant_id", ignore=True)
    partmap.add("colour", ignore=True)
    partmap.add("animal", ignore=True)
    partmap.add('rating', ignore=True)
    
    
    partmap.add('location', mapper=map_location)
    partmap.add("gender", mapper=map_gender)
    partmap.add('first_language', mapper=map_language_name)
    partmap.add('RA', mapper=map_ra)
    
    if PARTICIPANT_DETAIL in ["TRIM", "FULL"]:
    
        partmap.add('language_usage', mapper=map.dictionary_blank_mapper(NS.language_usage, submap))
        partmap.add('residence_history', mapper=map.dictionary_blank_mapper(NS.residential_history, submap))
        partmap.add('mother_first_language', mapper=map_language_name)
        partmap.add('father_first_language', mapper=map_language_name)
        
    else:
        
        partmap.add('language_usage', ignore=True)
        partmap.add('residence_history', ignore=True)  
        partmap.add('mother_first_language', ignore=True)
        partmap.add('father_first_language', ignore=True)
    
    if PARTICIPANT_DETAIL == "TRIM":
        ## the following are ignored because they potentially expose too much
        ## personal detail on the site
        partmap.add('profession_history', ignore=True) 
        partmap.add('education_history', ignore=True)  
        partmap.add('religion', ignore=True)


    return partmap

def participant_uri(colour, animal, id=None):
    """Generate the URI for a participant given their colour and animal ids
    or their id (1_123), id overrides other args if provided"""
    
    if id == None:
        p_id = "participant/%s_%s" % (colour, animal)
    else:
        p_id = "participant/"+id
        
    return ID_NS[p_id]


def participant_rdf(part_md, csvdata=None):
    """part_md is a dictionary of participant metadata from 
    the web server, generate corresponding RDF, returning a 
    graph object
    
    If csvdata is present it should be a dictionary of speaker 
    properties read from the RA spreadsheets, it will be used
    to override and validate the metadata
    
>>> from ra_maptask import RAMapTask
>>> part_file = "test/participant.json"
>>> maptask = RAMapTask ()
>>> csvdata = maptask.parse_speaker ("ra-spreadsheets/ANU-Speaker.csv", True)
>>> p = get_participant('3_726')
>>> graph = participant_rdf(p, csvdata['3_726'])
>>> len(graph)
149
>>> PARTICIPANT_DETAIL = "TRIM"
>>> graph_trim = participant_rdf(p, csvdata['3_726'])
>>> len(graph_trim)
149
>>> PARTICIPANT_DETAIL = "MINIMAL"
>>> graph_min = participant_rdf(p, csvdata['3_726'])
>>> len(graph_min)
149
>>> p = get_participant('2_1165')
>>> graph = participant_rdf(p, csvdata['2_1165'])
>>> print graph_min.serialize(format='turtle')
    """
    
    p_id = "%s_%s" % (part_md['colour']['id'], part_md['animal']['id'])
    p_name = "%s - %s" % (part_md['colour']['name'], part_md['animal']['name'])
    
    partmap = generate_partmap()
    
    p_uri = participant_uri(part_md['colour']['id'], part_md['animal']['id'])
    graph = partmap.mapdict(p_uri, part_md, NS['graphs/participants'])
    
    graph.add((p_uri, RDF.type, FOAF.Person))
    graph.add((p_uri, NS.id, Literal(p_id)))
    graph.add((p_uri, NS.name, Literal(p_name)))
    
    
    if PARTICIPANT_DETAIL != "MINIMAL":
        birthLoc = (part_md['pob_town'], part_md['pob_state'], part_md['pob_country'])
        add_geolocation(p_uri, NS.birthPlace, birthLoc, graph)
         
    if part_md.has_key('rating'):
        map_ratings(graph, part_md)
        
        
    # check and update some values from csvdata
    if csvdata != None: 
        if csvdata.has_key('DOB'):
            try:
                (d, m, y) = csvdata['DOB'].split('/')
                if len(y) == 2:
                    if int(y) < 12:
                        refyr = "20"+y 
                    else:
                        refyr = "19"+y
                elif len(y) == 4:
                    refyr = y
                else:
                    print "Odd year:", y
                
                refage = 2012-int(refyr)
                
                ages = graph.objects(subject=p_uri, predicate=FOAF.age)
                for age in ages:
                    if  str(age) != str(refage):
                        print "\tDOBs differ for %s, '%s' changed to '%s'" % (p_id, age, refage)
                        
                        newtriples = map_dob(p_uri, 'dob', refyr+"-"+m+"-"+d)
                        
                        for tr in newtriples:
                            s, p, o = tr
                            graph.remove((s, p, None))
                            graph.add(tr)
                        
                        # modify the graph
                        #graph.remove((p_uri, FOAF.age, age))
                        #graph.add((p_uri, FOAF.age, Literal(refage)))
            except:
                print "Bad DOB for", p_id, ":", csvdata['DOB']
        else:
            print "No DOB"
           
        # SES status
        if csvdata.has_key('SES') and csvdata['SES'] != '':
            ses = csvdata['SES']
            if ses.lower().startswith('prof'):
                ses = Literal('Professional')
            elif ses.lower().startswith('nprof'):
                ses = Literal('Non Professional')
            else:
                print "Unknown SES category: ", ses
                ses = Literal('Unknown')
                
            graph.add((p_uri, NS.ses, ses))

        if csvdata.has_key('Comment'):
            graph.add((p_uri, NS.racomment, Literal(csvdata['Comment'])))
            
        if csvdata.has_key('NOTES'):
            graph.add((p_uri, NS.maptaskcomment, Literal(csvdata['NOTES'])))
        
        if PARTICIPANT_DETAIL != "MINIMAL" and csvdata.has_key('Suburb') and csvdata.has_key('Postcode'):
            graph.add((p_uri, NS.suburb, Literal(csvdata['Suburb'])))
            graph.add((p_uri, NS.postcode, Literal(csvdata['Postcode'])))
              
    bind_graph(graph)

    return graph


if __name__=='__main__':
            
    import doctest
    doctest.testmod()


        
        
