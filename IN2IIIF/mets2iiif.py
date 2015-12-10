from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import libxml2, sys


from lxml import etree
from io import StringIO, BytesIO

execfile('in2iiif.py')


class Mets2iiif(In2iiif):
    
     def __init__(self, **kwargs):
         
         arg = GlobalConfig()
         
         self.parseArguments()   
         self.parseConfig()
         self.parseConfigMetadata()
         
        # factory
         fac = ManifestFactory()
         self.setFactoryProperties(fac)
        
        # manifest
         manifest = fac.manifest(
                                 ident=arg.manifest_id, 
                                 label= arg.manifest_label
                                 )
         self.setManifestProperties(manifest)
         self.setMetadata(manifest)
         
        # sequence
        # assumption - 1 sequence
         seq = manifest.sequence()
         if arg.sequence_id != "":
             seq.id = arg.sequence_id
         if arg.sequence_label != "":
            seq.label = arg.sequence_label
              
         file = open(arg.input, 'r') # open mets file for reading
         doc = etree.parse(file) # read file into etree for xpath queries
         file.close() # close mets file
         
         xpathOrderedList = "//mets:structMap/mets:div/mets:div"
         orderedList = doc.xpath(xpathOrderedList, namespaces={'mets': 'http://www.loc.gov/METS/'})
         
         p = 0 # counter for canvas label and id
         
        # canvases
        
         for canvas in orderedList: # Create a canvas with uri slug of page-1, and label of Page 1
            p += 1
           
            if canvas.attrib['ID']:
                canvas_id = canvas.attrib['ID']
            else:
                canvas_id = arg.canvas_id +"-"+str(p) # use canvas id prefix defined in config
            
            if canvas.attrib['ORDERLABEL']:
                 canvas_label = canvas.attrib['ORDERLABEL']
            else:
                canvas_label = arg.canvas_label+" " + str(p) # use canvas label prefix defined in config
        
            # determine whether to get images from local directory or via mets 
            # use arg image_src directory mets_file and image_dir 
            
            if arg.image_src == 'directory':
                # image information is from images in directory specified by image_dir
                imageLocation = arg.image_dir
            else:
                # image information derived from mets file    
                # get item id to retrieve file name
                itemId = canvas.xpath('mets:fptr[1]/@FILEID', namespaces={'mets': 'http://www.loc.gov/METS/'})
                xpathImageLocation = "//mets:fileSec//mets:file[@ID='" + itemId[0] +"']/mets:FLocat/@xlink:href"
                imageLocation = doc.xpath(xpathImageLocation, namespaces={'mets': 'http://www.loc.gov/METS/', 'xlink':'http://www.w3.org/1999/xlink'})
                imageLocation = imageLocation[0]
            
            cvs = seq.canvas(ident = canvas_id, label = canvas_label)
        
            # annotation
            # assumption - 1 image per canvas
            anno = cvs.annotation()
            if arg.annotation_id != "":
                anno.id = arg.annotation_id + canvas_id
        
            # image
            img = anno.image("p%s" % p, iiif=True)
        
            self.setImageProperties(img, imageLocation)
            self.setCanvasProperties(cvs, img)
        
        # should json output be compact?
         if arg.compact == 'True':
             manifest.toFile()
         else:
             manifest.toFile(compact=False)

    
    
     def parseConfigMetadata(self):
         
         arg = GlobalConfig()
         config = ConfigParser.ConfigParser() # config file parser
         config.read(arg.config) # read configuration file defined in command line arguments
         
         metadataProperties = config.options('metadata')
         
         for property in metadataProperties:    
             arg['metadata_'+ str(property)] = config.get('metadata', property)
             arg['metadata'] = arg.metadata + '|' + str(property)
         
         
     def setMetadata(self, manifest):
         
         arg = GlobalConfig()
         metadata = arg.metadata
         properties = metadata.split('|')
         dictMetadata = {}
        
        # read mets file
        
         file = open(arg.input, 'r')
         doc = etree.parse(file)
         #file.close()

         for property in properties:
             label = property
             if label != '':
                 key = 'metadata_' + property
                 xpath = arg[key]  
                 
                 if xpath != "":
                     
                     result = doc.xpath(xpath , namespaces={'mets': 'http://www.loc.gov/METS/', "mods": "http://www.loc.gov/mods/v3"})
                     
                     if result:
                         if type(result) == str:
                            value = result.strip()
                         else:
                             value = result[0].strip() 
                         if value != "":     
                            dictMetadata[label] = value
            
                
          
                 
         manifest.set_metadata(dictMetadata)


In2iiif()
Mets2iiif()   