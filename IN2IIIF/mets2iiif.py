from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import libxml2, sys


from lxml import etree
from io import StringIO, BytesIO

execfile('in2iiif.py')


class Mets2iiif(In2iiif):
     """Transforms METS to IIIF using ManifestFactory and in2iiif.""" 
     
     def __init__(self, **kwargs):
         """Gets attributes from command line and config file and creates IIIF manifest using ManifestFactory."""
          
         self.initSettings() # read config file and command line args and add to global vars
       
         factory = self.initFactory() # create ManifestFactory factory
         
         manifest = self.initManifest(factory) # define manifest
         
         sequence = self.initSequence(manifest) # define sequence
         
         structMap = self.getMetsFileStructMap()  # read METS file structMap
         
         self.initCanvas(sequence, structMap) # define canvases, annotations and images
         
         self.outputManifest(manifest) # write to file
          
          
     def initSettings(self):
         """Reads command line arguments and config file and adds to global variables"""
         
         self.parseArguments()   # parse command line arguments and add to global variables
        
         self.parseConfig()      # parse config file and add to global variables
         
         self.parseConfigMetadata() # parse config file and add metadata settings to global variables
             
               
     def initFactory(self):
         """Initalizes manifest factory and set properties"""
         factory = ManifestFactory() # instance of ManifestFactory
         
         self.setFactoryProperties(factory) # set properties of ManifestFactory using global variables
          
         return factory    
             
             
     def initManifest(self, factory):    
         """Initializes manifest and sets manifest properties"""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         # set properties of manifest
         manifest = factory.manifest( ident=arg.manifest_id, label= arg.manifest_label)
         
         self.setManifestProperties(manifest) # set ManifestFactory manifest properties using global vars
         self.setMetadata(manifest) # set ManifestFactory manifest metadata block using global vars
               
         return manifest      
               
     def setMetadata(self, manifest):
         """Sets metadata block of manifest."""
         
         arg = GlobalConfig() # global variables
         
         metadata = arg.metadata # get a string representation of a list of metadata properties from global variables
         properties = metadata.split('|') # create array from string
         dictMetadata = {} # create dictionary to hold values retrieved from mets file
        
         try:
             file = open(arg.input, 'r')   # read mets file
         except IOError as e:
             print("Problem encountered with opening the METS file", e)
         
         try:        
             doc = etree.parse(file)
         except Exception as e:
             print("Problem encountered with parsing the METS file", e)    
         #file.close()

         # iterate through array of metadata properties defined in the config file
         # extract values from the METS file using xpath
         for property in properties:
             label = property
             if label != '':
                 key = 'metadata_' + property
                 xpath = arg[key]  # get xpath for property
                 
                 if xpath != "":
                     # use xpath to extract corresponding value from the mets file
                     result = doc.xpath(xpath , namespaces={'mets': 'http://www.loc.gov/METS/', "mods": "http://www.loc.gov/mods/v3"})
                     
                     if result:
                         if type(result) == str:
                            value = result.strip()
                         else:
                             value = result[0].strip() 
                         if value != "":     
                            dictMetadata[label] = value
            
         # set metadata block for manifest if values have been extracted from the METS file
         if bool(dictMetadata):
             manifest.set_metadata(dictMetadata)      
          
          
     def initSequence(self, manifest):
         """Defines sequence for the manifest."""
         
        # assumption is that there is one sequence per manifest
        
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
        
         sequence = manifest.sequence()
         
         # if sequence_id defined in global variables use this
         if arg.sequence_id != "":
             sequence.id = arg.sequence_id
         # if seqeunce label defined in global variables use this    
         if arg.sequence_label != "":
            sequence.label = arg.sequence_label     
         
         return sequence   


     def outputManifest(self, manifest):
         """Write IIIF manifest to file."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         # should json output be compact?
         if arg.compact == 'True':
             manifest.toFile()
         else:
             manifest.toFile(compact=False)


     def initCanvas(self, sequence, structMap):
         """Define canvases for manifest using METS file structMap."""
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         counter = 0 # counter for canvas label and id
         
        # create canvases using structMap
         for item in structMap: 
            counter += 1
           
            if item.attrib['ID']:
                canvas_id = item.attrib['ID'] # set canvas id to id attribute
            else:
                canvas_id = arg.canvas_id +"-" + str(counter) # or if not present, use canvas id prefix defined in config
            
            if item.attrib['ORDERLABEL']:
                 canvas_label = item.attrib['ORDERLABEL'] # set canvas lablel to orderlabel attribute
            else:
                canvas_label = arg.canvas_label+" " + str(counter) # or if not present, use canvas label prefix defined in config
        
            # canvas
            canvas = sequence.canvas(ident = canvas_id, label = canvas_label)
            
            # annotation
            annotation = self.initAnnotation(canvas, canvas_id)
            
            self.initImage(canvas, annotation, item, counter)
            
            
            
        
        
     def initAnnotation(self, canvas, canvas_id):
         """Define annotation for canvas."""
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         # annotation
         
         annotation = canvas.annotation()
        
         if arg.annotation_id != "":
             annotation.id = arg.annotation_id + canvas_id

         return annotation        
     
     
     def initImage(self, canvas, annotation, item, counter):    
         """Define image for annotation."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
            
         image_location = self.getImageLocation(item)
         
         # image - assumption - one image per canvas
         image = annotation.image("p%s" % counter, iiif=True)
        
        
         self.setImageProperties(image, image_location)
        
         self.setCanvasProperties(canvas, image)
        
                 
     def getImageLocation(self, item):
         """Determine image location."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         image_location = ""
         
         # determine whether to get images from local directory or via mets 
            # use arg image_src directory mets_file and image_dir 
            
         if arg.image_src == 'directory':
                # image information is from images in directory specified by image_dir
               image_location = arg.image_dir
         else:
                # image information derived from mets file           
                # get item id to retrieve file name
                item_id = item.xpath('mets:fptr[1]/@FILEID', namespaces={'mets': 'http://www.loc.gov/METS/'})
                xpathImageLocation = "//mets:fileSec//mets:file[@ID='" + item_id[0] +"']/mets:FLocat/@xlink:href"
                image_location = doc.xpath(xpathImageLocation, namespaces={'mets': 'http://www.loc.gov/METS/', 'xlink':'http://www.w3.org/1999/xlink'})
                image_location = image_location[0]
                
         return image_location        


     def getMetsFileStructMap(self):
         """Gets the structMap section of a METS file."""
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         file = open(arg.input, 'r') # open mets file for reading
         doc = etree.parse(file) # read file into etree for xpath queries
         file.close() # close mets file
         
         xpath = "//mets:structMap/mets:div/mets:div"
         xml = doc.xpath(xpath, namespaces={'mets': 'http://www.loc.gov/METS/'})
         
         return xml
         
        
        
        

    

    
     
     
     
    
    
     def parseConfigMetadata(self):
         """"""
         arg = GlobalConfig()
         config = ConfigParser.ConfigParser() # config file parser
         config.read(arg.config) # read configuration file defined in command line arguments
         
         metadataProperties = config.options('metadata')
         
         for property in metadataProperties:    
             arg['metadata_'+ str(property)] = config.get('metadata', property)
             arg['metadata'] = arg.metadata + '|' + str(property)
         
         
    


In2iiif() # create a new instance of In2iiif class
Mets2iiif()   # create a new instance of Mets2iiif class