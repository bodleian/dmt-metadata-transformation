from factory import ManifestFactory
import ConfigParser
import ast
import argparse

  

class One:
    _shared_state = {} # attribute dictionary

    def __init__(self):
        self.__dict__ = self._shared_state
        
        
class GlobalConfig(One): # inherits from the GlobalConfig class
    # this class shares all its attributes among its various instances  
     def __init__(self, **kwargs):
         One.__init__(self)
         self._shared_state.update(kwargs)
     
     def __setitem__(self, key, value):
         self._shared_state[key] = value
         
     def __getitem__(self, key):
         value = self._shared_state[key]  
         return value   
         
     def __str__(self):
         return str(self._shared_state)
    
             
class In2iiif():
    
    def __init__(self, **kwargs):
            
         arg = GlobalConfig()
            

    def setFactoryProperties(self, fac):
         arg = GlobalConfig()
         fac.set_base_metadata_uri(arg.manifest_base_metadata_uri) # Where the resources live on the web
         fac.set_base_metadata_dir(arg.manifest_base_metadata_dir) # Where the resources live on disk
        
         fac.set_base_image_uri(arg.manifest_base_image_uri) # Default Image API information
         fac.set_iiif_image_info(arg.manifest_iiif_image_info_version,arg.manifest_iiif_image_info_compliance) # Version, ComplianceLevel
        
         fac.set_debug(arg.debug) 
    
    def setManifestProperties(self, manifest):
         arg = GlobalConfig()
         manifest.description = arg.manifest_description
         manifest.viewingDirection = arg.manifest_viewingDirection
        
    def setCanvasProperties(self, cvs, img):
            cvs.height = img.height
            cvs.width = img.width
    
    def setImageProperties(self, img, imagefile):
            
            img.set_hw_from_file(imagefile) 
            # OR if you have a IIIF service:
            #  img.set_hw_from_iiif()
    
    def parseConfig(self):
        
         arg = GlobalConfig() 
               
         config = ConfigParser.ConfigParser() # config file parser
         config.read(arg.config) # read configuration file defined in command line arguments
         
         GlobalConfig(   
                manifest_base_metadata_uri = config.get('manifest','base_metadata_uri'),
                manifest_base_metadata_dir = config.get('manifest','base_metadata_dir'),
                manifest_base_image_uri = config.get('manifest','base_image_uri'),
                manifest_iiif_image_info_version = config.get('manifest','iiif_image_info_version'),
                manifest_iiif_image_info_compliance = config.get('manifest','iiif_image_info_compliance'),
                debug = config.get('manifest','debug'),
                manifest_id = config.get('manifest','id'),
                manifest_label = config.get('manifest','label'),
                manifest_description = config.get('manifest','description'),
                manifest_viewingDirection = config.get('manifest','viewingDirection'),
                sequence_id = config.get('sequence','id'),
                sequence_label = config.get('sequence','label'),
                canvas_id = config.get('canvas','id'),
                canvas_label = config.get('canvas','label'),
                annotation_id = config.get('annotation','id'),
                metadata = '')
                          
        
    def parseArguments(self):
        
         parser = argparse.ArgumentParser() # command line argument parser

         #positional arguments
         parser.add_argument("config", help="configuration file")
         parser.add_argument("input", help="input source file")
         # manifest factory doesen't appear to allow output file location to be specified
       #  parser.add_argument("output",
       #              help="output destination file")
         parser.add_argument("image_src", help="image source: directory | mets_file")

         #optional arguments
         parser.add_argument("--image_dir", help="location of image directory (if source folder used for images")
# eg /home/dmt/Documents/IIIF_Ingest/images/

         parser.add_argument("--compact", help="Should json be compact form or human-readable: Compact | Normal")

         arg = parser.parse_args()
         
         GlobalConfig(config = arg.config )
         GlobalConfig(input = arg.input)
        # GlobalConfig(output = arg.output )
         GlobalConfig(image_src = arg.image_src )
         GlobalConfig(image_dir = arg.image_dir )
         GlobalConfig(compact = arg.compact)
  
