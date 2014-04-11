import csv

from collections import namedtuple
import os

from session import blackbox_path

import sys
sys.path.append(blackbox_path) 
from recorder.animals import animalIdMap
from recorder.Domain import colourIdMap

## names for site RA spreadsheet exports
CSVDIR = os.path.join(os.path.dirname(__file__), "../ra-spreadsheets")
ALLSITES = ['ANU', 'Bathurst', 'Townsville', 'UC', 'USYD', 'UTAS', 'UWA', 'Armidale', 'UNSW', 'FLIN']

KEYMAP = {'ID Number': 'ID',
        'Gender': 'Gender',
        'DOB': 'DOB',
        'Suburb': 'Suburb',
        'Postcode': 'Postcode',
        'State': 'State',
        'Closest Site': 'ClosestSite',
        'Age Group': 'AgeGroup',
        'Est. SES': 'SES',
        'Session 1 *': 'Session1',
        'Session 2 *': 'Session2',
        'Session 3 *': 'Session3',
        'Comments': 'Comments',
        'NOTES': 'NOTES',
        'First Name': 'FirstName',
        'Last Name': 'LastName',
        'Phone': 'Phone',
        'Email': 'Email',
        }



class RAMapTask:

    CONST_IG = "Information Giver"


    ## ----------
    ## code to map colour/animal names uses the blackbox module
    ## 
    def animal_to_id (self, animal):
        """ Reverse lookup from animal name to animal id 
>>> maptask = RAMapTask()
>>> maptask.animal_to_id(u'Australian Reed-Warbler')
123
>>> maptask.animal_to_id(u'australian reed-warbler')
123
        """
        
        for key, value in animalIdMap.iteritems():
            # remove all spaces and dashes and fold to lower case for comparison
            value = value.lower().replace(' ', '').replace('-', '')
            animal = animal.lower().replace(' ', '').replace('-', '')
            
            if value == animal:
                return key

        return None

    def id_to_animal (self, id):
        """ Forward lookup from colour id to colour name 
>>> maptask = RAMapTask()
>>> maptask.id_to_animal(123)
u'Australian Reed-Warbler'
        """
        
        return animalIdMap[id] if id in animalIdMap else None
    
    
    def colour_to_id (self, colour):
        """ Reverse lookup from colour name to colour id 
>>> maptask = RAMapTask()
>>> maptask.colour_to_id(u'Red')
3
>>> maptask.colour_to_id(u'red')
3
"""
        
        for key, value in colourIdMap.iteritems():
            if value.lower() == colour.lower():
                return key

        return None


    def id_to_colour (self, id):
        """ Forward lookup from colour id to colour name 
>>> maptask = RAMapTask()
>>> maptask.id_to_colour(3)
u'Red'
        """
        
        return colourIdMap[id] if id in colourIdMap else None

    ## end of code using the blackbox module
    ##-------------

    def parse_maptask (self, source, report = False):
        """ This function parses a map task CSV document as provided by the RA's. 
>>> maptask = RAMapTask ()
>>> results = maptask.parse_maptask ("ra-spreadsheets/ANU-MapTask.csv")
>>> len (results)
48
>>> sorted(results['4_864'].items())
[('date', '18/01/12'), ('map', 'MapA-Colour'), ('partner', '2_1178'), ('role', 'Information Giver')]
>>> sorted(results['2_1178'].items())
[('date', '18/01/12'), ('map', 'MapB-Architecture'), ('partner', '4_864'), ('role', 'Information Follower')]
        """
        results = {}
        
        # these 'speakers' occur in the sample section, we ignore them
        nonspeakers = ["", "black snake", "yellow tail", "green wombat", "red spider", "blue lizard", "red wombat",
                       "green spider", "yellow wombat"]
        
        if (os.path.exists (source)):
            file_handle = csv.reader (open (source, 'rU'))

            for values in file_handle:
                s1 = values[1].strip()
                s2 = values[2].strip()
                 
                if s1 in nonspeakers or s2 in nonspeakers:
                    continue
                
                if not values[0].strip() in ["", "Date"]:
                    # Identify the speakers then build the list for IG and IF
                    speaker1 = self.identify_speaker (s1)
                    speaker2 = self.identify_speaker (s2)
                    task1map = values[3].strip()
                    task2map = values[4].strip()
                    date = values[0].strip()
                    
                    if speaker1["id"] is None or speaker2["id"] is None:
                        if report:
                            if speaker1["id"] is None:
                                print "Problem in %s with speaker 1 '%s'" % (source, values[1].strip ())
                            if speaker2["id"] is None:
                                print "Problem in %s with speaker 2 '%s'" % (source, values[2].strip ())
                    else:
                        results[speaker1["id"]] = {'partner': speaker2["id"], 'map': task1map, 'date': date, 'role': 'Information Giver'}
                        results[speaker2["id"]] = {'partner': speaker1["id"], 'map': task2map, 'date': date, 'role': 'Information Follower'}
                        
        return results


    def parse_speaker (self, source, report = False):
        """ RA's have also recorded speaker meta data in their spreadsheets. This function parsers that meta
        data, and allows us to add it to the map task meta.

>>> maptask = RAMapTask ()
>>> meta_fields = maptask.parse_speaker ("ra-spreadsheets/FLIN-Speaker.csv", True)
>>> len(meta_fields)
109
>>> meta_fields = maptask.parse_speaker ("ra-spreadsheets/ANU-Speaker.csv", True)
>>> len (meta_fields)
48
>>> sorted(meta_fields['2_1151'].items())
[('AgeGroup', '>50'), ('ClosestSite', ''), ('Comments', ''), ('DOB', '21/06/1948'), ('Gender', 'M'), ('ID', 'Green Pygmy Sperm Whale'), ('Postcode', '2903'), ('SES', 'Prof-M'), ('Session1', '4/01/12'), ('Session2', '11/01/12'), ('Session3', '23/01/12'), ('State', 'ACT'), ('Suburb', 'Wanniassa')]
>>> meta_fields = maptask.parse_speaker ("ra-spreadsheets/USYD-Speaker.csv", True)
        """
        results = {}

        if (os.path.exists (source)):
            file_handle = csv.reader (open (source, 'rU'))
            headers = []
            
            for values in file_handle:
                if not values[0].strip () in ["", "BigASC Participant Sheet", "Location", "ID Number"]:
                    # Identify the speaker first
                    speaker = self.identify_speaker (values[0].strip ())
                    
                    if not speaker["id"] is None:
                        results[speaker["id"]] = self.extract_speaker_meta (values, headers)
                    else:
                        if report:
                            print "Problem in %s with speaker '%s'" % (source, values[0].strip ())
                else:
                    if values[0].strip() == 'ID Number':
                        headers = values
        else:
            print "SPEAKER FILE MISSING: ", source

        return results


    def identify_speaker (self, speaker):
        """ This translates the name from the source data into values we understand. 

>>> maptask = RAMapTask ()
>>> maptask.identify_speaker ("Gold Australasian Grebe")
{'colour': '1', 'participant': 'Gold - Australasian Grebe', 'id': '1_107', 'animal': '107'}
>>> maptask.identify_speaker ("Pink Australasian Grebe")
{'colour': None, 'participant': None, 'id': None, 'animal': '107'}
>>> maptask.identify_speaker ("Gold - Australian Sea Lion")
{'colour': '1', 'participant': 'Gold - Australian Sea Lion', 'id': '1_1119', 'animal': '1119'}

# USYD do this
>>> maptask.identify_speaker("Red-White-bellied Cuckoo-shrike (3-875)")
{'colour': '3', 'participant': 'Red - White-bellied Cuckoo-shrike', 'id': '3_875', 'animal': '875'}


        """
        # first we need to strip down the words, then we assume that the first word is
        # the colour which we translate and then the remainder is the animal. Unknown
        # colours and animals must result in a warning of some sort
        import re
        
        pattern = "([A-Za-z]+)[ -]+([a-zA-Z- ']+)(\s*\([0-9-]+\))?"
        
        m = re.match(pattern, speaker)
        if not m == None:
            (colour, animal, ignore) = m.groups()
            colour = colour.strip()
            animal = animal.strip()
        else:
            print "Malformed id: '%s'" % (speaker,)
            return {'id': None}
        
        colour_id = self.colour_to_id (colour)
        animal_id = self.animal_to_id (animal)
            
        if colour_id is None or animal_id is None: 
            return {"id" : None, 
                    "colour" : None if colour_id is None else str (colour_id), 
                    "animal" : None if animal_id is None else str (animal_id),
                    "participant" : None}
        else:
            return {"id" : str (colour_id) + '_' + str (animal_id),
                    "colour" : str (colour_id),
                    "animal" : str (animal_id),
                    "participant" : colour + ' - ' + animal}


    def extract_speaker_meta (self, source, keys):
        """ This function extracts the meta data for the participant from the speaker csv document."""

        results = {}
        
        for index in range (len (source)):
            if KEYMAP.has_key(keys[index]):
                results[KEYMAP[keys[index]]] = source[index].strip ()
            
        if results.has_key('SES') and results['SES'] != '' and results['SES'].find('rof') < 0:
            print "Bad SES value: ", results['SES']
            
        return results
    
    
    def read_all(self, report=True):
        """Read all speaker and maptask data from CSV files
        
>>> maptask = RAMapTask()
>>> (s, m) = maptask.read_all()
>>> len(s.keys())
538
>>> len(m.keys())
486
>>> sorted(s['3_166'].items())
[('AgeGroup', '>50'), ('ClosestSite', 'Charles Sturt University'), ('Comments', ''), ('DOB', '12/10/39'), ('Email', ''), ('FirstName', ''), ('Gender', 'F'), ('ID', 'Red Black Breasted Buzzard'), ('LastName', ''), ('Phone', ''), ('Postcode', '2795'), ('SES', 'Prof-F'), ('Session1', '22/07/11'), ('Session2', '1/08/11'), ('Session3', '15/11/11'), ('State', 'NSW'), ('Suburb', 'Kelso')]
        """
        
        spkr = dict()
        maptask = dict()
        
        for site in ALLSITES:

            mapcsv = os.path.join(CSVDIR, site+"-MapTask.csv")
            spkrcsv = os.path.join(CSVDIR, site+"-Speaker.csv")

            spkr.update(self.parse_speaker(spkrcsv, report))
            maptask.update(self.parse_maptask(mapcsv, report))
            
        return (spkr, maptask)
        
        

if __name__=='__main__':
    
    
    import doctest
    doctest.testmod()


