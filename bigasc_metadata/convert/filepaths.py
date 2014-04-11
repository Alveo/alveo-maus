"""
  utilities for parsing item filenames and generating 
  the right paths for storing data
  
"""

import sys
import os
import re
import urllib2
import json

from session import component_map
from participant import item_site_name, participant_uri
from namespaces import DATA_URI_TEMPLATE, DATA_NS

import configmanager
configmanager.configinit()

def extension_mimetype(ext):
    """Return the mimetype for this extension"""
    
    extmap = {'wav': 'audio/wav',
              'mp4': 'video/mp4',
              'TextGrid': 'text/praat-textgrid', # http://www.isocat.org/rest/dc/2562
              }
    if extmap.has_key(ext):
        return extmap[ext]
    else:
        raise Exception("Unknown extension: '%s'" % ext)
    


def parse_media_filename(filename, errorlog=sys.stderr):
    """Extract the channel name, media type and -n status from a filename
    return a dictionary.


>>> parse_media_filename('1_178_1_2_150-ch1-maptask.wav')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'audio', 'channel': 'ch1-maptask'}
    
>>> parse_media_filename('1_178_1_2_150-n-ch1-maptask.wav')
{'basename': '1_178_1_2_150', 'version': 2, 'type': 'audio', 'channel': 'ch1-maptask'}
    
>>> parse_media_filename('1_178_1_2_150-n-n-ch1-maptask.wav')
{'basename': '1_178_1_2_150', 'version': 3, 'type': 'audio', 'channel': 'ch1-maptask'}

>>> parse_media_filename('1_178_1_2_150-n-n-n-n-n-ch1-maptask.wav')
{'basename': '1_178_1_2_150', 'version': 6, 'type': 'audio', 'channel': 'ch1-maptask'}

>>> parse_media_filename('1_178_1_2_150-camera-0-left.mp4')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'video', 'channel': 'camera-0-left'}

>>> parse_media_filename('1_178_2_16_001-camera-0-right.mp4')
{'basename': '1_178_2_16_001', 'version': 1, 'type': 'video', 'channel': 'camera-0-right'}

>>> parse_media_filename('1_1121_1_12_001-ch4-c2Left.wav')
{'basename': '1_1121_1_12_001', 'version': 1, 'type': 'audio', 'channel': 'ch4-c2Left'}

>>> parse_media_filename('1_1121_1_12_001-ch6-speaker-yes.wav')
{'basename': '1_1121_1_12_001', 'version': 1, 'type': 'audio', 'response': 'yes', 'channel': 'ch6-speaker'}

>>> parse_media_filename('1_178_1_2_150-camera-0-no-left.mp4')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'video', 'response': 'no', 'channel': 'camera-0-left'}

>>> parse_media_filename('1_178_1_2_150-n-n-camera-0-yes-left.mp4')
{'basename': '1_178_1_2_150', 'version': 3, 'type': 'video', 'response': 'yes', 'channel': 'camera-0-left'}

>>> parse_media_filename('1_178_1_2_150-ch6-speaker16.wav')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'audio', 'channel': 'ch6-speaker16'}

>>> parse_media_filename('1_178_1_2_150-ch6-speaker16.raw16')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'raw16', 'channel': 'ch6-speaker16'}

>>> parse_media_filename('1_178_1_2_150A-ch6-speaker16.wav')
{'basename': '1_178_1_2_150', 'version': 1, 'type': 'audio', 'channel': 'ch6-speaker16', 'sequence': 'A'}
    """
    
    basename = os.path.basename(filename)
    
    pattern_general = "([0-9_]+)([A-Z]?)-((n-)*)(ch[0-9]-[a-zA-Z0-9]+)(-(yes|no))?\.(.*)"
    
    pattern_video = "([0-9_]+)([A-Z]?)-((n-)*)((camera-[0-9])(-(yes|no))?(-left|-right))\.(.*)"
    
    m_gen = re.match(pattern_general, basename)
    m_vid = re.match(pattern_video, basename)
    
    if m_gen:
        (base, ab, alln, n, channel, ignore, yesno, ext) =  m_gen.groups() #@UnusedVariable
        #print "MATCH: ", (base, ab, alln, n, channel, ignore, yesno, ext )
        if ext == 'wav':
            tipe = 'Audio'
        else:
            tipe = ext
    elif m_vid:
        (base, ab, alln, n, ignore, camera, ignore, yesno, leftright, ext) = m_vid.groups()
        
        channel = camera + leftright
        if ext == 'mp4':
            tipe = 'Video'
        else:
            tipe = ext
    else:
        # unknown file pattern
        errorlog.write("filename doesn't match media pattern: %s\n" % basename)
        return dict()
    
    mimetype = extension_mimetype(ext)

    sequence = None
    if n == None:
        if ab == '':
            version = 1
        else:
            # this is a new ABC sequenced file
            sequence = ab
            version = 1
    else:
        version = len(alln)/2 + 1
    

    result = {'basename': base, 
              'channel': channel, 
              'type': tipe, 
              'mimetype': mimetype,
              'version': version}
    
    if sequence != None:
        result['sequence'] = sequence
        
    if yesno != None:
        result['response'] = yesno
        
    #print "PMF: ", filename, result
    return result
 
def parse_item_filename(filename, errorlog=sys.stderr):
    """Get the session, component and item ids
    from the file name, return a dictionary with keys 'session', 'component', 'item'
    
    >>> parse_item_filename('1_178_1_2_150.xml')
    {'basename': '1_178_1_2_150', 'component': '2', 'item': '150', 'session': '1', 'speaker': '1_178', 'animal': '178', 'colour': '1'}
    >>> parse_item_filename('../test/University_of_Tasmania,_Hobart/Spkr2_2/Spkr2_2_Session1/Session1_11/2_2_1_11_003')
    {'basename': '2_2_1_11_003', 'component': '11', 'item': '3', 'session': '1', 'speaker': '2_2', 'animal': '2', 'colour': '2'}
    """
    
    basename = os.path.basename(filename)
    result = dict()
    parse_it = re.compile(r'^((\d*)_(\d*)_(\d*)_(\d*)_(\d*))')
    match = parse_it.search(basename)
    if match:
        groups = match.groups() 
        result['basename'] = groups[0]
        result['colour'] = groups[1]
        result['animal'] = groups[2]
        result['speaker'] = groups[1]+"_"+groups[2]
        result['session']   = groups[3]
        result['component'] = groups[4]
        result['item']      = str(int(groups[5]))  # do this to trim leading zeros
    else:
        errorlog.write("'%s' doesn't match the filename pattern\n" % filename )
        
    return result

def item_file_uri(filename, dirname=None):
    """Given a filename for one of the files in an item, return a URI for
     this file on the data server
     
>>> item_file_uri('1_178_1_2_150-ch6-speaker16.wav')
rdflib.term.URIRef(u'http://data.austalk.edu.au/audio/ANU/1_178/1/words-1/1_178_1_2_150-ch6-speaker16.wav')

     """
    path = item_file_path(filename, dirname)
    
    return DATA_NS[path]

def item_file_path(filename, dirname=None):
    """Given a filename for one of the files in an item, return a path that we can 
    use to store it in the right place. This is a relative path, you still
    need to add OUTPUT_DIR to get an absolute path.
    
>>> item_file_path('1_178_1_2_150-ch6-speaker16.wav')
'audio/ANU/1_178/1/words-1/1_178_1_2_150-ch6-speaker16.wav'
>>> item_file_path('1_178_1_2_150A-ch6-speaker16.wav')
'audio/ANU/1_178/1/words-1/1_178_1_2_150A-ch6-speaker16.wav'
>>> item_file_path('1_178_1_2_150.nt', 'metadata')
'metadata/ANU/1_178/1/words-1/1_178_1_2_150.nt'
>>> item_file_path('/foo/bar/test/University_of_the_Sunshine_Coast,_Maroochydore/Spkr1_1216/Spkr1_1216_Session1/Session1_1/1_1216_1_1_001', 'metadata')
'metadata/USCM/1_1216/1/yes-no-opening-1/1_1216_1_1_001'
    """

    info = parse_item_filename(filename)
    info['filename'] = os.path.basename(filename)
            
    m = component_map()
    info['componentName'] = m[int(info['component'])]
    info['site'] = item_site_name(participant_uri(info['colour'], info['animal']))
    
    path = DATA_URI_TEMPLATE % info
    
    if dirname == None:
        
        # we modify the path based on the file type since we're splitting
        # audio and video data
        minfo = parse_media_filename(filename)
        if minfo.has_key('type'):
            dirname = minfo['type']
        else:
            dirname = ''
#            raise Exception("Can't work out directory name in item_file_path(%s)" % filename)
        
    path = os.path.join(dirname, path)
    
    return path

def item_file_basename(filename):
    """Given a filename for one of the files in an item, return the basename
    of the item
    
>>> item_file_basename('1_178_1_2_150-ch6-speaker16.wav')
'1_178_1_2_150'
>>> item_file_basename('2_267_1_2_001-ch6-speaker.TextGrid')
'2_267_1_2_001'
>>> item_file_basename('../test/University_of_Tasmania,_Hobart/Spkr2_2/Spkr2_2_Session1/Session1_11/2_2_1_11_003')
'2_2_1_11_003'

    """
    
    info = parse_item_filename(filename)
    return info['basename']

def versionselect():
    """Load versionselect data from the website (or a chached
    copy) and return the dictionary"""
    
    global VERSIONS
    
    try:
        return VERSIONS
    except:
        # VERSIONS not bound
        url = configmanager.get_config("VERSIONSELECT_URL")
        cache = configmanager.get_config("VERSIONSELECT_CACHE", "versionselect.json")
        
        if os.path.exists(cache):
            h = open(cache)
            json_text = h.read()
            h.close()
        else:
            h = urllib2.urlopen(url)
            json_text = h.read()
            h.close()
            # cache a copy
            h = open(cache, 'w')
            h.write(json_text)
            h.close()
        
        VERSIONS = json.loads(json_text)
        return VERSIONS

def item_file_versions(path):
    """Given the base path of an item, work out which
    the good and bad versions are.  The data comes from
    the versionselect application where there are more
    than one version of a recording for an item.
    
    Return
    
    {'rejected': [<list of rejected files>],
     'good': {'1_1216_1_4_001A': ['path/to/1_1216_1_4_001-n-camera-0-left.mp4', 'path/to/1_1216_1_4_001-n-camera-0-right.mp4'],
              '1_1216_1_4_001B': etc.,
              }
    }
    
    if there is no version info then add the key 'versioninfo' with the value 'missing'
    
>>> x = item_file_versions('test/University_of_the_Sunshine_Coast,_Maroochydore/Spkr1_1216/Spkr1_1216_Session1/Session1_11/1_1216_1_11_016')
>>> x['rejected']
[]
>>> x['good'].keys()
['1_1216_1_11_016']

# fake this a little
>>> versions = versionselect()
>>> versions['1_1216_1_4_001'] = [2]
>>> x = item_file_versions('test/University_of_the_Sunshine_Coast,_Maroochydore/Spkr1_1216/Spkr1_1216_Session1/Session1_4/1_1216_1_4_001')
>>> len(x['rejected'])
8
>>> x['good'].keys()
['1_1216_1_4_001']
>>> versions['1_1216_1_4_001'] = [1, 2]
>>> x = item_file_versions('test/University_of_the_Sunshine_Coast,_Maroochydore/Spkr1_1216/Spkr1_1216_Session1/Session1_4/1_1216_1_4_001')
>>> len(x['rejected'])
0
>>> x['good'].keys()
['1_1216_1_4_001A', '1_1216_1_4_001B']
>>> len(x['good']['1_1216_1_4_001A'])
8
    """
    
    versions = versionselect()
    
    basename = item_file_basename(path)
    all_files = item_files(path)
    
    # do we have more than one version
    fv = dict()
    for fn in all_files:
        props = parse_media_filename(fn)
        if props.has_key('version'):
            v = props['version']
            if fv.has_key(v):
                fv[v].append(fn)
            else:
                fv[v] = [fn]
        else:
            # filename is malformed - message already printed by parse_media_filename
            pass
    
    if len(fv) <= 1:
        # we only have one version (or zero if there is only an xml file for this item)
        return {'rejected': [], 'good': {basename: all_files}}
    
    # see if we have versionselect data for this item    
    if versions.has_key(basename):
        goodversions = versions[basename]
        goodfiles = dict()
        badfiles = []
        
        # a zero in goodversions means there's no good version
        if 0 in goodversions:
            print "No good version of ", basename
            return {'rejected': all_files, 'good': {}}
        
        N = 0
        for v in goodversions:
            if fv.has_key(v):
                files = fv[v]
                newbase = generate_new_item_basename(basename, N, len(goodversions))
                goodfiles[newbase] = files
                del fv[v]
                N += 1
            
        # now badfiles is the rest
        for v in fv.keys():
            badfiles.extend(fv[v])

        return {'rejected': badfiles, 'good': goodfiles}

    else:
        print "Duplicate recordings and no version info for ", basename
        return {'rejected': [], 'good': {}, 'versioninfo': 'missing'}
    
    
    
def generate_new_item_basename(basename, n, total):
    """Generate a basename for an item that might be 
    one of a number of good versions. n is the index
    of this version, total is the total number of good
    versions
    
>>> generate_new_item_basename('1_123_1_2_001', 0, 1)
'1_123_1_2_001'
>>> generate_new_item_basename('1_123_1_2_001', 0, 2)
'1_123_1_2_001A'
>>> generate_new_item_basename('1_123_1_2_001', 1, 2)
'1_123_1_2_001B'
    """

    if total == 1:
        return basename
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return basename+letters[n]


def change_item_file_basename(f, basename):
    """Change the basename of a file without changing any of the other
    parts

>>> change_item_file_basename('1_123_1_2_001-ch6-speaker.wav', '1_123_1_2_001')
'1_123_1_2_001-ch6-speaker.wav'
>>> change_item_file_basename('1_123_1_2_001-ch6-speaker.wav', '1_123_1_2_001A')
'1_123_1_2_001A-ch6-speaker.wav'
>>> change_item_file_basename('1_123_1_2_001-n-n-ch6-speaker.wav', '1_123_1_2_001A')
'1_123_1_2_001A-ch6-speaker.wav'
    """

    pattern = '^([0-9_]+(-n)*)(.*)$'
    m = re.match(pattern, f)
    if m:
        (obase, n, rest) = m.groups()
        return basename+rest
    else:
        raise Exception("filename '%s' doesn't match pattern in change_item_file_basename" % f)
    
    
    
    
        
def item_files(path):
    """Given the base path of an item, return a list
    of the files associated with that item - ie. all
    files starting with this prefix except the .xml
    metadata file.

>>> sorted(item_files('University_of_the_Sunshine_Coast,_Maroochydore/Spkr1_1216/Spkr1_1216_Session1/Session1_11/1_1216_1_11_003'))
[]
    """
    
    from glob import glob
    
    files = glob(path + '*')
    return [f for f in files if not f.endswith('.xml')]





## generate a component map, do this only once and we'll use it below

if __name__=='__main__':
        
    import doctest
    doctest.testmod()


    
        
        

