'''
Created on Sep 14, 2012

@author: steve
'''
import unittest
import item, geonames
from rdflib import URIRef

class Test(unittest.TestCase):


    def test_read_metadata(self):
        
        mdfile = "../test/1_1121_1_12_001.xml"
        
        md = item.read_metadata(mdfile)
        
        #for key in md.keys():
           # print key, ":", md[key]
        
        self.assertEqual(md['componentName'], "Words Session 1")
        self.assertEqual(md['timestamp'], "Mon Jul 18 16:48:43 2011")
        self.assertEqual(len(md['files'].keys()), 5)
        self.assertEqual(md['files']['1_1121_1_12_001-ch1-maptask.wav']['checksum'], '3a1ac90a5a3940ac1cb9046d5546b574')
        

class TestGeonames(unittest.TestCase):
    
    
    def test_placename_info(self):
        
        places = [
                  ("Toowoomba", "Qld", "Australia", 2146268, 'Toowoomba', 'Australia', 'AU'),
                  ("toowoomba", "qld", "australia", 2146268, 'Toowoomba', 'Australia', 'AU'),  # case insensitive
                  ("Brisbane", "QLD", "Australia", 2174003, 'Brisbane', 'Australia', 'AU'),  # a captial city
                  ("Bright", "Vic", "Australia", 2174041, 'Bright', 'Australia', 'AU'), # first match not PPL
                  ]
        
        g = geonames.GeoNames()
        
        for place in places:
            info = g.placename_info(place[0], place[1], place[2])

            self.assertEqual(info['geoname'], place[3])
            self.assertEqual(info['placename'], place[4])
            self.assertEqual(info['countryname'], place[5])
            self.assertEqual(info['countrycode'], place[6])
        
        
        # test one placename_uri
        place = places[1]
        uri = g.placename_uri(place[0], place[1], place[2])
        self.assertEqual(uri, URIRef(u'http://sws.geonames.org/' + str(place[3])))
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.test_read_metadata']
    unittest.main()