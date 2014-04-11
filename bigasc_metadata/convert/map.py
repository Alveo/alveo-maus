"""Mapping property names and values for metadata and annotation ingest"""


from rdflib import Namespace, Graph, Literal, BNode, URIRef
from namespaces import NS


def toRDFName(value):
    """
     convert a given value to a legal RDF property name suitable
     for appending to a namespace URI
    """
    
    return str(value)
    
def dictmapper(dictionary):
    """Return a function to map property values
    via a dictionary lookup in the given dictionary"""
    
    def fn(subj, prop, val):
        if dictionary.has_key(val):
            return ((subj, prop, dictionary[val]),)
        else:
            return ((subj, prop, Literal(val)),)
        
    return fn

def dictionary_blank_mapper(bnprop, bnmap):
    """Return a mapper for use with a 
    value that is expected to be a dictionary, map
    to a blank node with properties and values from
    the dictionary
    bnprop - the property name to link to the blank node
    bnmap - a FieldMapper to use on the dictionary keys"""
    
    import hashlib
    
    def mapper(subj, prop, value):

        result = []
        # make a repeatable node id
        hash = hashlib.sha1(bnprop+prop+str(value)).hexdigest()
        bnode = URIRef(subj+"#"+hash)
        
        #  link in the bnode
        result.append((subj, bnprop, bnode))
        # map the properties given the bnode map
        for key in value.keys():
            for triple in bnmap.map(bnode, key, value[key]):
                result.append(triple)
        return result
    
    return mapper



class FieldMapper:
    """Class representing a mapping of field names and values"""
    
    def __init__(self, copy_if_unknown=True):
        """Create a Field Mapper 
        if copy_if_unknown is True, unknown properties will be copied
        to the output with a suitable namespace, if false, they will
        be ignored
        """
        self.copy_if_unknown = copy_if_unknown
        self.simpleMap = dict() # a dict of simple key to key mappings
         
        
    def __call__(self, key, value):
        """Callable interface to map a single property/value pair"""
        
        return self.map(key, value)
        
        
    def add(self, key, mapto=None, ignore=False, mapper=None):
        """Add a mapping to the mapper.  
        key is the key that triggers this mapping
        mapto is a simple RDF property, if present this will be the output property
        ignore - if True, this property will be ignored, no output
        mapper - another mapper object that will be used to map properties
           in the value of this property - ie. for when the value is a nested
           property list (like speaker info)  OR mapper is a function(property, value) that
           returns a (property, RDFValue) pair where property is a valid RDF property and
           RDFvalue is either a Literal or Resource value.
        transform - a function that transforms the (key, value) pair"""
            
            
        # clean up the property name before we store it
        key = toRDFName(key)
    
        if ignore:
            self.simpleMap[key] = 'IGNORE'  
        elif mapto:
            self.simpleMap[key] = mapto
        elif mapper:
            self.simpleMap[key] = mapper
    
    def get_mapper(self, key):
        """Return a mapper function to map this key"""
    
        
        if self.simpleMap.has_key(key): 
            if self.simpleMap[key] == 'IGNORE':
                # always map to empty
                return lambda a, b, c: []
            
            elif isinstance(self.simpleMap[key], URIRef):        
                # value is unchanged
                prop = self.simpleMap[key]
                return lambda a, b, c: [(a, prop, Literal(c))]
            
            elif callable(type(self.simpleMap[key])):
                
                return self.simpleMap[key]
        elif self.copy_if_unknown:
            # just use this property and the unchanged value
            prop = NS[key]
            return lambda a, b, c: [(a, prop, Literal(c))]
        
        else: 
            # always map to empty
            return lambda a, b, c: []
    
    def map(self, subj, key, value):
        """Return a sequence of triples (subj, property, mappedvalue) which is the mapping
        for the given (subj key value) triple
        Returns the empty list in the case when no mapping can be made"""
        
        # clean up the property name before we start converting
        key = toRDFName(key) 
        
        mapper = self.get_mapper(key)
        
        # ignore terms with empty values
        if isinstance(value, (str, unicode)) and value.strip() == "": 
            return []
        
        # if value is a list, map each element of the list
        elif isinstance(value, (list, tuple)):
            result = []
            for v in value:
                for triple in self.map(subj, key, v): 
                    result.append(triple)
            return result
        else:
        
            return mapper(subj, key, value)
        
    
    def mapdict(self, uri, metadata, context=None):
        '''
        This function takes one metadata dictionary as extracted by the ingest
        module in this package, and returns a rdflib Graph instance.
        '''
        
        if context != None:
            graph = Graph(identifier=context)
        else:
            graph = Graph()
        
        for key in metadata.keys():
            # convert and add the property/value  
            for triple in self.map(uri, key, metadata[key]) :
                graph.add(triple)
        
        return graph
    
