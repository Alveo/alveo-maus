'''
Created on Sep 14, 2012

@author: steve

Convert metadata from the Blackbox Recorder software to RDF
 This metadata describes the sessions and components recorded

'''
# find the path to the blackbox project
# hacketty hack hack hoo
import os
bbpaths = ['/Users/steve/projects/eclipse-workspace/blackbox-gui/src',
           '/home/steve/workspace/SSCP-GUI/src',
           '/Users/steve/Workspace/SSCP-GUI/src']

for p in bbpaths:
    if os.path.exists(p):
        blackbox_path = p
        break

import sys
sys.path.append(blackbox_path)
from recorder import Persistence

from rdflib import Namespace, Graph, Literal, URIRef

from namespaces import *
import re


### classes
CLASS_SESSION = NS.Session
CLASS_COMPONENT = NS.Component
CLASS_ITEM = NS.Item


def make_graph():
    """Return a suitably prepared graph"""
    
    graph = Graph(identifier=NS['graph/protocol'])
    graph.bind('austalk', NS)
    graph.bind('dc', DC)
    graph.bind('protocol', PROTOCOL_NS)
    
    return graph

# define this here because we want to access Persistance
def component_map():
    """Return a dictionary to map between component numbers
    and the short names we use in media URLs"""
    
    component_map = dict()
    
    for comp in Persistence.Component.GetInstances():
        component_map[comp.GetId()] = comp.GetShortName()

    return component_map


def session_metadata():
    """Return a dictionary containing all of the metadata
    from the session and component descriptions"""
    
    graph = make_graph()
    
    # generate a list of session numbers and descriptors
    for session in Persistence.Session.GetInstances():
        id = PROTOCOL_NS[SESSION_URI_TEMPLATE % session.GetId()]
        
        graph.add((id, NS.id, Literal(session.GetId())))
        
        name = session.GetName()
        if name == "Session 3.1" or name == "Session 3.2":
            name = "Session 3"
        
        graph.add((id, NS.name, Literal(name)))
        graph.add((id, RDF.type, CLASS_SESSION))
        
        for comp in session.getComponents():
            cid = PROTOCOL_NS[COMPONENT_URI_TEMPLATE % comp.GetId()]
            graph.add((cid, DC.isPartOf, id))
    return graph


def component_metadata():
    """Return a dictionary of metadata for each component"""
    
    graph = make_graph()
    
    
    for comp in Persistence.Component.GetInstances():
        cid = PROTOCOL_NS[COMPONENT_URI_TEMPLATE % comp.GetId()]
        
        graph.add((cid, NS.id, Literal(comp.GetId())))
        graph.add((cid, NS.name, Literal(comp.GetName())))
        graph.add((cid, NS.shortname, Literal(comp.GetShortName())))
        
        for item in comp.getItems():
            iid = PROTOCOL_NS[ITEM_URI_TEMPLATE % (comp.GetId(), item.GetId())]
            graph.add((iid, DC.isPartOf, cid))
            graph.add((iid, RDF.type, CLASS_ITEM))
            
        # add type info
        graph.add((cid, RDF.type, CLASS_COMPONENT))
        
    return graph

def item_metadata():
    """Return a dictionary of metadata for each item"""
    
    graph = make_graph()

    for comp in Persistence.Component.GetInstances():
        for item in comp.getItems():
            iid = PROTOCOL_NS[ITEM_URI_TEMPLATE % (comp.GetId(), item.GetId())]
            graph.add((iid, NS.id, Literal(item.GetId())))
            graph.add((iid, NS.prompt, Literal(clean_prompt(item.GetPrompt()))))
            
    return graph
            
            
def clean_prompt(prompt):
    """Clean up a prompt value from the metadata
    to make it more like what was shown on screen"""
    
    
    # if the prompt contains 'sounds like' then we want just the first word
    m = re.match('([a-z ]+).*sounds like.*', prompt)
    if m:
        prompt = m.group(1).replace(' ', '')
        
    # super special case
    if prompt == 'p ure':
        prompt = 'pure'
        
    # digit prompts include two parts '0123:zero one two three'
    m = re.match('[0-9o]+\s*:(.*)', prompt)
    if m:
        prompt = m.group(1)
    
    prompt = prompt.strip()   

    return prompt
            
            
def item_prompt(basename):
    """Return the prompt for an item given an item file basename"""
    
    # should use parse_item_filename but that would give us a circular import    
    
    m = re.match(r'^((\d*)_(\d*)_(\d*)_(\d*)_(\d*))', basename)
    
    if m:
        component = int(m.group(5))
        item = int(m.group(6))

        return clean_prompt(Persistence.ItemPrompt(component, item))
    else:
        raise Exception("Can't parse item basename %s" % basename)
    
            
if __name__=='__main__':
    
    graph = session_metadata()

    print "Graph has ", len(graph), "statements"
    s = graph.serialize(format='turtle')
    print s
