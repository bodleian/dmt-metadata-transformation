#!/usr/bin/python2.7
# mets2iiif.py by Tanya Gray Jones [tanya.gray@bodleian.ox.ac.uk]
# This is a transformation script for METS to IIIF API Manifest version 2.0

from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import libxml2, sys


from lxml import etree
from io import StringIO, BytesIO

execfile('in2iiif.py')

def main():
    
    transformer = Mets2iiif()   # create an object that is an instance of Mets2iiif class
    
    factory = transformer.factory() # create ManifestFactory factory
     
    manifest = transformer.manifest(factory) # define manifest
         
    sequence = transformer.sequence(manifest) # define sequence
         
    structMap = transformer.getMetsFileStructMap()  # read METS file structMap
         
    transformer.canvas(sequence, structMap) # define canvases, annotations and images
         
    transformer.outputManifest(manifest) # write to file


class Mets2iiif(In2iiif):
     """Transforms METS to IIIF using ManifestFactory and in2iiif.""" 
     
     def __init__(self, **kwargs):
         """Constructor - sets global variables using command-line arguments and config file."""
         
         self.parseArguments()   # parse command line arguments and add to global variables
         self.parseConfig()      # parse config file and add to global variables
         self._parseConfigMetadata() # parse config file and add metadata settings to global variables
                 
             
     def _parseConfigMetadata(self):
         """Reads config file and extracts metadata properties to global variables."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         config = ConfigParser.ConfigParser() # config file parser
         
         try:
             config.read(arg.config) # read configuration file defined in command line arguments
             metadataProperties = config.options('metadata') # get metadata section of config file
         
             # iterate through each metadata property defined in the section and assign value to global variable with name constructed from prefix 'metadata' plus name of metadata property
             for property in metadataProperties:    
                 arg['metadata_'+ str(property)] = config.get('metadata', property)
                 arg['metadata'] = arg.metadata + '|' + str(property) # also append name of metadata property to a global variable called "metadata"
             
         except Exception as e:
             print("A problem was encountered reading the configuration file specified:", e)
             sys.exit(0)
         
               
     def factory(self):
         """Initalizes manifest factory and set properties"""
         
         factory = ManifestFactory() # instance of ManifestFactory
         
         self.setFactoryProperties(factory) # set properties of ManifestFactory using global variables
          
         return factory    
             
             
     def manifest(self, factory):    
         """Initializes manifest and sets manifest properties"""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         # set properties of manifest
         manifest = factory.manifest( ident=arg.manifest_id, label= arg.manifest_label)
         
         self.setManifestProperties(manifest) # set ManifestFactory manifest properties using global vars
         self._setMetadata(manifest) # set ManifestFactory manifest metadata block using global vars
               
         return manifest      
               
     def _setMetadata(self, manifest):
         """Sets metadata block of manifest."""
         
         arg = GlobalConfig() # global variables
         
         metadata = arg.metadata # get a string representation of a list of metadata properties from global variables
         properties = metadata.split('|') # create array from string
         dictMetadata = {} # create dictionary to hold values retrieved from mets file
        
         doc= ""
         
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
             if property != '':
                 value  = ""
                 language = ""
                 script = ""
                 dictMetadata[property] = ''
                 
                 xpath = arg['metadata_' + property]  # get xpath for property
                 if xpath != "":
                     # use xpath to extract corresponding string or node values from the mets file
                     result = doc.xpath(xpath , namespaces={'mets': 'http://www.loc.gov/METS/', "mods": "http://www.loc.gov/mods/v3"})
                     
                     # iterate through items in list returned - either string value or element
                     for item in result:

                         if type(item) == str: 
                             # string value
                             # support there being only one string value as result of concat xpath statement 
                             dictMetadata[property] = item
                         else:
                             # 'element
                                 
                             value = item.text # get string value
            
                             # check if language attribute exists
                             language = item.xpath('@xml:lang')
                             if len(language) > 0:
                                     lang = language[0]
                                     # check if script attribute exists
                                     scriptQuery = item.xpath("@script")
                                     script = scriptQuery[0]
                                     # if script attribute exists append value to language
                                     if script != '':
                                         lang += '-' + script
                                     
                                     # get existing dictionary value for property
                                     existingValues = dictMetadata[property]
                                     if len(existingValues) == 0:
                                         # if dictionary entry does not exist then create list value
                                        dictMetadata[property] = []
                                         
                                     dict = {'@value': value, '@language': lang}
                                     # update dictionary
                                     dictMetadata[property].append(dict) 
                                 
                             else:
                                 # if no language attribute exists then use different construct for property value
                                     existingValue = dictMetadata[property]
                                     # add delimiter if concatenating values
                                     if existingValue != '':
                                         existingValue += ';'
                                     # update dictionary     
                                     dictMetadata[property] = existingValue + value 
                                      
            
         # set metadata block for manifest if values have been extracted from the METS file
         if bool(dictMetadata):
             manifest.set_metadata(dictMetadata)      
          
          
     def sequence(self, manifest):
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


     def canvas(self, sequence, structMap):
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
            annotation = self._annotation(canvas, canvas_id)
            
            self._image(canvas, annotation, item, counter)
            
  
     def _annotation(self, canvas, canvas_id):
         """Define annotation for canvas."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
                  
         annotation = canvas.annotation()
        
         if arg.annotation_id != "":
             annotation.id = arg.annotation_id + canvas_id
         return annotation        
     
     
     def _image(self, canvas, annotation, item, counter):    
         """Define image for annotation."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
            
         image_location = self._getImageLocation(item)
         
         # image - assumption - one image per canvas
         image = annotation.image("p%s" % counter, iiif=True)
        
         self.setImageProperties(image, image_location)
        
         self.setCanvasProperties(canvas, image)
        
                 
     def _getImageLocation(self, item):
         """Determine image location."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         # determine whether to get images from local directory or via mets 
         # use arg image_src directory mets_file and image_dir 
            
         if arg.image_src == 'directory':
                # image information is from images in directory specified by image_dir
               image_location = arg.image_dir
         else:
                # image information derived from mets file           
                # get item id to retrieve file name
                
                try:
                    file = open(arg.input, 'r') # open mets file for reading
                    doc = etree.parse(file) # read file into etree for xpath queries
                except:
                    print('Unable to open mets file', + arg.input)
                    sys.exit(0)
                
                try:    
                    item_id = item.xpath('mets:fptr[1]/@FILEID', namespaces={'mets': 'http://www.loc.gov/METS/'})
                    xpathImageLocation = "//mets:fileSec//mets:file[@ID='" + item_id[0] +"']/mets:FLocat/@xlink:href"
                    image_location = doc.xpath(xpathImageLocation, namespaces={'mets': 'http://www.loc.gov/METS/', 'xlink':'http://www.w3.org/1999/xlink'})
                    image_location = image_location[0]
                    return image_location    
                except:
                    print('Unable to determine image location from mets file')
                    sys.exit(0)


     def getMetsFileStructMap(self):
         """Gets the structMap section of a METS file."""
         
         arg = GlobalConfig() # instance of GlobalConfig to hold global variables
         
         try:
             file = open(arg.input, 'r') # open mets file for reading
             doc = etree.parse(file) # read file into etree for xpath queries
             file.close() # close mets file
         except Exception as e:
             print("Error when opening or parsing METS file:", e)
             sys.exit(0)
             
         xpath = "//mets:structMap/mets:div/mets:div"
         xml = doc.xpath(xpath, namespaces={'mets': 'http://www.loc.gov/METS/'})
         
         return xml


     

if __name__ == "__main__": main()


