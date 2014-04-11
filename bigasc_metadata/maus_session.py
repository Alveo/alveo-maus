
if __name__=='__main__':
    
    import sys
    import os
    from annotate.maus import make_maus_processor, make_bpf_generator
    from data import site_sessions, map_session
    from data.map import pub_site_speakers, pub_map_session
    import configmanager
    import ingest
    
    if len(sys.argv) not in [2,3]:
        print "Usage: maus_session.py maus|bpf <speakerlist>?"
        exit()  
        
    datadir = configmanager.get_config("DATA_DIR")
    
    outdir = configmanager.get_config("OUTPUT_DIR")
    # our input data is the downsampled version of the data which is in the output
    # directory
    datadir = os.path.join(outdir, "downsampled")
    
    what = sys.argv[1]
    if len(sys.argv) == 3:
        speakerfn = sys.argv[2]
        h = open(speakerfn)
        speakers = h.readlines()
        speakers = [s.strip() for s in speakers]
        h.close()
        
        for s in speakers:
            print "SPKR: ", s
    else:
        speakers = None
    
    server_url = configmanager.get_config("SESAME_SERVER")
    server = ingest.SesameServer(server_url) 

    for d in os.listdir(datadir):
        
        sitedir = os.path.join(datadir, d)
        print "SITE: ", sitedir
        if os.path.isdir(sitedir):
            for speaker in os.listdir(sitedir):
                print "Speaker: ", speaker
                
                # if speaker is in our list
                if speakers == None or speaker in speakers:
                
                
                    spkrdir = os.path.join(sitedir, speaker)
                    for session in os.listdir(spkrdir):
                        print "Session: ", session
                        sessiondir = os.path.join(spkrdir, session)
                        if what == 'maus':
                            result = [i for i in pub_map_session(sessiondir, make_maus_processor(server, outdir), '*ch6-speaker16.wav')]
                        else:
                            result = [i for i in pub_map_session(sessiondir, make_bpf_generator(server, outdir), '*ch6-speaker16.wav')]
                        print ""
                        
                else:
                    print "Ignoring speaker", speaker
