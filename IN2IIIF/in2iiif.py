#!/usr/bin/python2.7
# in2iiif.py by Tanya Gray Jones [tanya.gray@bodleian.ox.ac.uk]
# This is a transformation script for various formats to IIIF API Manifest version 2.0

from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import os.path
import sys
import re
import ntpath


def main(): pass

class One:
    """One class (Borg design pattern) making class attributes global."""
    
    _shared_state = {} # Attribute dictionary

    def __init__(self):
        self.__dict__ = self._shared_state # Make it an attribute dictionary
              
        
class GlobalConfig(One): # inherits from the One class
     """GlobalConfig class shares all its attributes among its various instances."""
     # GlobalConfig objects are an object-oriented form of global variables
     
     def __init__(self, **kwargs):
         One.__init__(self)
         # Update the attribute dictionary by inserting new key-value pair(s) defined in argument
         self._shared_state.update(kwargs)
     
     def __setitem__(self, key, value):
         # Update the attribute dictionary by inserting a new key-value pair or updating value of existing key-value pair
         self._shared_state[key] = value
         
     def __getitem__(self, key):
         # Returns a value in the dictionary using a key, or None if key not found
         value = self._shared_state.get(key, None)  
         return value   
         
     def __str__(self):
         # Returns the attribute dictionary for printing
         return str(self._shared_state)
    
             
class In2iiif():
    """Base class for transformation of various formats to IIIF."""
    def __init__(self, **kwargs):
         
         arg = GlobalConfig() # instantiate GlobalConfig class to hold global variables
            
    def setFactoryProperties(self, fac):
         """Sets the ManifestFactory Factory properties."""
         arg = GlobalConfig() # instantiate GlobalConfig class to hold global variables
         
         # set attributes for ManifestFactory instance
         try:
             fac.set_base_metadata_uri(arg.manifest_uri + arg.manifest_id) # Where the resources live on the web
             fac.set_base_metadata_dir(arg.manifest_base_metadata_dir) # Where the resources live on disk
             fac.set_base_image_uri(arg.manifest_base_image_uri) # Default Image API information
             fac.set_iiif_image_info(arg.manifest_iiif_image_info_version,arg.manifest_iiif_image_info_compliance) # Version, ComplianceLevel
             fac.set_debug(arg.debug)         
         except Exception as inst:
             print("Problem encountered setting factory properties: " , inst)
             print("You need to ensure the following parameters are set correctly in the configuration file: base_metadata_dir, base_image_uri, iiif_image_info_version, iiif_image_info_compliance, debug.")
    
    def setManifestProperties(self, manifest):
         """Sets the ManifestFactory Manifest's properties."""
         # instance of global variables
         arg = GlobalConfig()
         # set ManifestFactory manifest description and viewing direction using global variables
         manifest.description = arg.manifest_description
         manifest.viewingDirection = arg.manifest_viewingDirection
        
    def setCanvasProperties(self, cvs, img):
         """Sets the ManifestFactory Canvas properties."""
         cvs.height = img.height
         cvs.width = img.width
    
    def setImageProperties(self, img, imagefile):
         """Sets the ManifestFactory Image properties."""   
         if os.path.isfile(imagefile) == True: # if path provided is to a file then set height width properties using file specified
             img.set_hw_from_file(imagefile) 
         else:
             print('The image file does not exist: ' + imagefile )
             sys.exit(0)    
             
         
         
         # OR if you have a IIIF service:
         #  img.set_hw_from_iiif()
    
    def parseConfig(self):
         """Parses configuration file and adds values to GlobalConfig attribute dictionary"""
         
         arg = GlobalConfig() # instance of GlobalConfig        
         config = ConfigParser.ConfigParser() # instance of config file parser
         
         # check that base_metadata_dir is a valid directory on system, otherwise generate error with meaningful message - causes @context error message in factory otherwise
            
         try:
             config.read(arg.config) # read configuration file defined in command line arguments   
         except IOError as e:
             print('An error occurred - Cannot read configuration file: ', e)
             sys.exit(0)
             
         try:
             if (os.path.isdir(config.get('manifest','base_metadata_dir')) == False):
                raise Exception('An error occurred - Please correct the base_metadata_dir parameter in the config file to a valid directory')
         except Exception as e:
             print(e)
             sys.exit(0)   
         
         try:
             

             # pass values to instance of GlobalConfig as arguments, that will add them to dictionary
             GlobalConfig(   
                    manifest_uri = config.get('manifest','uri'),
                    manifest_id = config.get('manifest','id'),
                    manifest_base_metadata_dir = config.get('manifest','base_metadata_dir'),
                    manifest_base_image_uri = config.get('manifest','base_image_uri'),
                    manifest_iiif_image_info_version = config.get('manifest','iiif_image_info_version'),
                    manifest_iiif_image_info_compliance = config.get('manifest','iiif_image_info_compliance'),
                    debug = config.get('manifest','debug'),
                    manifest_label = config.get('manifest','label'),
                    manifest_description = config.get('manifest','description'),
                    manifest_viewingDirection = config.get('manifest','viewingDirection'),
                    sequence_id = config.get('sequence','id'),
                    sequence_name = config.get('sequence','name'),
                    sequence_label = config.get('sequence','label'),
                    
                    canvas_id = config.get('canvas','id'),
                    canvas_label_prefix = config.get('canvas','label_prefix'),
                    canvas_label_regex = config.get('canvas','label_regex'),
                    annotation_uri = config.get('annotation','uri'),
                    annotation_id_path = config.get('annotation', 'id_path'),
                    image_location_path = config.get('image', 'location_path'),
                    metadata = '')

         except Exception as e:
             print('Error when adding values from the configuration file to the global dictionary: ', e)
             sys.exit(0)     
             
         
                             
        
    def parseArguments(self):
         """Parses command line arguments and adds values to GlobalConfig attribute dictionary"""
         
         parser = argparse.ArgumentParser() # instance of command line argument parser

         #POSITIONAL/REQUIRED ARGUMENTS
         parser.add_argument("--config", help="configuration file", required="True")
         parser.add_argument("--input",  help="input source file", required="True")  
         parser.add_argument("--output", help="output destination file" , required="True")
         parser.add_argument("--image_src",  help="image source: image_file | image_directory | mets_file", required="True")

         #OPTIONAL ARGUMENTS
         
         # eg /home/dmt/Documents/IIIF_Ingest/images/
         parser.add_argument("--image_location", help="file path of single image file or image directory, if image_src = image_directory or image_file")
         parser.add_argument("--compact", help="Should json be compact form or human-readable: Compact | Normal", required="True")

         # convert argument strings to objects and assign them as attributes
         # https://docs.python.org/2/library/argparse.html#the-parse-args-method
         try:
             arguments = parser.parse_args()
         except Exception as e:
             print('Problem encountered with reading command line arguments: ', e)
             sys.exit(0)
          
        
         # Add command line arguments to the global dictionary using GlobalConfig
         try:
             GlobalConfig(config = arguments.config )
             GlobalConfig(input = arguments.input)
             GlobalConfig(output = arguments.output)
             GlobalConfig(image_src = arguments.image_src )
             GlobalConfig(image_location = arguments.image_location )
             GlobalConfig(compact = arguments.compact)
 
         except Exception as e:
             print('Problem encountered with adding command line arguments to global variables: ', e)
             sys.exit(0)    
 
        


if __name__ == "__main__": main()

  
