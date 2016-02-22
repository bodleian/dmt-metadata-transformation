#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
        METS IIIF Create

        By Tanya Gray Jones
        29/01/2016

        Takes a METS document and creates a IIIF Presentation Version 2.0 Manifest from it

        Command line:
            needs: config, output, input, image_src, image_dir, compact

        Relies on steps:
            None

        Example run :
            In Goobi:
                /gscripts/bdlss/step_mets_iiif_convert.py config={config} output={output} input={input} image_src={image_src} image_dir={image_dir} compact={compact}

            From command line:
                sudo -u tomcat6 ./step_mets_iiif_convert.py --config mets.cfg --input /home/dmt/Do
cuments/IIIF_Ingest/METS/input/12.xml --output /home/dmt/Documents/IIIF_Ingest/METS/manifest.json --ima
ge_src directory --image_dir /home/dmt/Documents/IIIF_Ingest/images/book.jpg --compact False

python step_mets_iiif_create.py --config /home/dmt/apps/goobi-bdlss/bdlss/scripts/bdlss/in2iiif/mets2iiif/mets.cfg --input /home/dmt/Documents/IIIF_Ingest/METS/input/12.xml --output /home/dmt/Documents/IIIF_Ingest/METS/manifest.json --image_src directory --image_dir /home/dmt/Documents/IIIF_Ingest/images/book.jpg --compact False

'''
    
from goobi.goobi_step import Step
from in2iiif.mets2iiif import mets2iiif

#execfile('./in2iiif/mets2iiif/mets2iiif.py')


class Step_Mets_IIIF_Create( Step ) :


    def setup( s ):
    
        s.name = "METS IIIF Create"
        
        s.config_main_section = "IIIF_create"
      
        s.essential_commandlines = {
            # Use with self.command_line.NAME
            "config":   Step.type_file,
            "input":    Step.type_file,
            "output":   Step.type_file,
            "image_src":Step.type_string,
            "image_dir":Step.type_file,
            "compact":  Step.type_string
            
        }
    
    def step( s ):
    
        """
            Uses Manifest Factory together with configuration file and image to create IIIF manifest
            
            Try using, debug, auto_complete, detach and report_problem on commandline
        """
    
        error = None
        
        #config = self.command_line.config
        #input = self.command_line.input
        #output = self.command_line.output
        #image_src = self.command_line.image_src
        #image_dir = self.command_line.image_dir
        #compact = self.command_line.compact
        
        
        mets = Mets2iiif()   # create an object that is an instance of Mets2iiif class
    
        factory = mets.factory() # create ManifestFactory factory
     
        manifest = mets.manifest(factory) # define manifest
         
        sequence = mets.sequence(manifest) # define sequence
         
        structMap = mets.getMetsFileStructMap()  # read METS file structMap
         
        mets.canvas(sequence, structMap) # define canvases, annotations and images
         
        mets.outputManifest(manifest) # write to file
        
        return error


        
if __name__ == '__main__' :

    import config_ini
    Step_Mets_IIIF_Create( config_ini.file ).begin()









