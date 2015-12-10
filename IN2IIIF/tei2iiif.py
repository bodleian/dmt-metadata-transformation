from factory import ManifestFactory
import ConfigParser
import ast
import argparse

 
execfile('in2iiif.py')
In2iiif()
  
class Tei2iiif(In2iiif):
     def __init__(self, **kwargs):
         
         arg = GlobalConfig()
         
         self.parseArguments()   
         self.parseConfig()
        # factory
         fac = ManifestFactory()
         self.setFactoryProperties(fac)
        
        # manifest
         manifest = fac.manifest(ident=arg.manifest_id, label= arg.manifest_label)
         self.setManifestProperties(manifest)
         
         # tei metadata parsing here
         manifest.set_metadata(
            {'label' : {'en':"Date", 'fr':'Date'}, 
             'value': {'en':'15th Century', 'fr': 'Quinzieme Siecle'}
            })
         
        # sequence
         seq = manifest.sequence()  # unlabeled, anonymous sequence
         seq.id = arg.sequence_id
        
        # canvas
         for p in range(1): # Create a canvas with uri slug of page-1, and label of Page 1
            
            cvs = seq.canvas(ident=arg.canvas_id+"-"+str(p), label=arg.canvas_label+" "+str(p))
        
            # annotation
            anno = cvs.annotation()
            anno.id = arg.annotation_id
        
            # Add Image: http://www.example.org/path/to/image/api/p1/full/full/0/native.jpg
            img = anno.image("p%s" % p, iiif=True)
        
            self.setImageProperties(img, p)
            self.setCanvasProperties(cvs, img)
        
         manifest.toFile(compact=False)



Tets2iiif()   