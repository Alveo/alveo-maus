'''

Map operations over Austalk session data

Created on Nov 6, 2012

@author: steve
'''

import re, os

def site_sessions(dirname):
    """
    Returns a sequence of sessions for the given
    site directory.  We look for speaker directories
    first then sessions within those.

>>> list(site_sessions('test/University_of_Tasmania,_Hobart/'))
['test/University_of_Tasmania,_Hobart/Spkr2_2/Spkr2_2_Session1']

    """
    for spkrdir in os.listdir(dirname):
        if os.path.isdir(os.path.join(dirname, spkrdir)):
            for sessiondir in os.listdir(os.path.join(dirname, spkrdir)):
                if parse_session_dir(sessiondir): 
                    yield(os.path.join(dirname, spkrdir, sessiondir))
    




def parse_site_dir(dirname):
    """Given a site directory name (University_of_Tasmania,_Hobart)
    return the new short site identifier that the new 
    website will use (UTAS)

>>> parse_site_dir("University_of_Tasmania,_Hobart")
'UTAS'
>>> parse_site_dir("University_of_Queensland,_Brisbane")
'UQB'
    """
    import sys
    sys.path.append('..')
    from convert import map_site_name
    
    (name, city) = dirname.replace('_', ' ').split(',') 
    return map_site_name(name.strip(), city.strip())


def parse_session_dir(dirname):
    """Return a pair (speakerid, sessionid) for this 
    session directory name or None if it doesn't match the pattern

>>> parse_session_dir("Spkr1_123_Session3")
('1_123', '3')
>>> parse_session_dir("Not a Session Dir")
>>> parse_session_dir("Spkr1_1_Session4")
('1_1', '4')
    """
    
    SESSION_DIR_PATTERN = "Spkr([1234]+_[0-9]+)_Session([0-4]+)"
    
    match = re.match(SESSION_DIR_PATTERN, dirname)
    if match:
        return match.groups()
    else:
        return None
        
def parse_component_dir(dirname):
    """Return a pair (sessionid, componentid) for this 
    component directory or None if it doesn't match the pattern

>>> parse_component_dir("Session2_22")
('2', '22')
>>> parse_component_dir("Doesn't match")
>>> parse_component_dir("Session1_2")
('1', '2')
    """

    match = re.match(r'^Session(\d*)_(\d*)$', dirname)
    if match:
        return match.groups()
    else:
        return None
    

def map_session(sessiondir, fn):
    """Call fn for every item in the given session
    fn is a callable that takes arguments:
    
    fn(site, spkr, session, component, item_path)
    
     - site is the site id (UTAS, UNSW, etc)
     - spkr is speaker id 1_123
     - session is session id [1, 2, 3, 4]
     - component is numerical component id
     - item_path is the base path to the item /home/foo/Spkr1_123/2/22/1_123_2_22
     
    return value is an iterator over the results of the individual
    function calls (calls are lazy via yield)
    
>>> paths = list(map_session('test/University_of_Tasmania,_Hobart/Spkr2_2/Spkr2_2_Session1', lambda a, b, c, d, e: e ))
>>> len(paths)
54
>>> paths[2]
'test/University_of_Tasmania,_Hobart/Spkr2_2/Spkr2_2_Session1/Session1_5/2_2_1_5_012'
    """

    # progressively split off directories
    (spath, sessdirname) = os.path.split(sessiondir)
    (spath, spkrdirname) = os.path.split(spath)
    (basepath, sitedirname) = os.path.split(spath)
    
    # get info from session directory name
    (spkrid, sessionid) = parse_session_dir(sessdirname)
    siteid = parse_site_dir(sitedirname)
    
    
    for cdir in os.listdir(sessiondir):
        if parse_component_dir(cdir) != None:
            (ss, componentid) = parse_component_dir(cdir)
            
            for ifile in os.listdir(os.path.join(sessiondir, cdir)):

                if ifile.endswith(".xml"):
                    (basename, ext) = os.path.splitext(os.path.basename(ifile))
                    path = os.path.join(sessiondir, cdir, basename)
                    
                    yield( fn(siteid, spkrid, sessionid, componentid, path) )



def pub_site_speakers(dirname):
    """
    Returns a sequence of speakers for the given
    site directory.  We look for speaker directories
    first then sessions within those.


    """
    for spkrdir in os.listdir(dirname):
        if os.path.isdir(os.path.join(dirname, spkrdir)):
            for sessiondir in os.listdir(os.path.join(dirname, spkrdir)): 
                yield(os.path.join(dirname, spkrdir, sessiondir))


from fnmatch import fnmatch 

def pub_map_session(sessiondir, fn, pattern):
    """Call fn for every item in the given session directory
    with the published directory structure.  
    
    Unlike map_session this maps over files rather than items. The
    pattern argument is a glob pattern that matches the files you
    want to see - typically this will be a channel name or extension.
    
    fn is a callable that takes arguments:
    
    fn(site, spkr, session, component, item_path)
    
     - site is the site id (UTAS, UNSW, etc)
     - spkr is speaker id 1_123
     - session is session id [1, 2, 3, 4]
     - component is the component name (words-1, sentences)
     - item_path is the base path to the item /home/foo/Spkr1_123/2/22/1_123_2_22
     
    return value is an iterator over the results of the individual
    function calls (calls are lazy via yield)
    
    """

    # progressively split off directories
    (spath, sessionid) = os.path.split(sessiondir)
    (spath, spkrid) = os.path.split(spath)
    (basepath, siteid) = os.path.split(spath)
    
    for component in os.listdir(sessiondir):
        
        for ifile in os.listdir(os.path.join(sessiondir, component)):

            if fnmatch(ifile, pattern):
                path = os.path.join(sessiondir, component, ifile)
                
                yield( fn(siteid, spkrid, sessionid, component, path) )

if __name__=='__main__':
        
        import doctest
        doctest.testmod()
    
    
    
    