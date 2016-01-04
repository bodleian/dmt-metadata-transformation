Introduction
============
IN2IIF is a python application that converts various formats to IIIF Manifest Presentation API v2.0.


Dependencies
============

ManifestFactory
---------------
https://github.com/IIIF/presentation-api/tree/master/implementations/manifest-factory 

IN2IIIF makes use of the ManifestFactory python library to generate the IIIF presentation manifest 

Python 2.7
----------
Use of ManifestFactory requires the use of python version 2.7

ImageMagick or Python Image Library
-----------------------------------
Use of ManifestFactory requires the use of ImageMagick or Python Image Library if image dimensions are to be determined programmatically.





Usage
=====
The in2iiif.py file is not called directly, but must be imported by another python file that is concerned with a specific format transformation, e.g. METS.

Mets2iiif
---------

```bash
usage: mets2iiif.py [-h] --config CONFIG --input INPUT --image_src IMAGE_SRC
                    [--image_dir IMAGE_DIR] [--compact COMPACT]
```

Example

```bash
python mets2iiif.py 
--config mets.cfg 
--input /home/dmt/Documents/IIIF_Ingest/METS/input/12.xml 
--image_src directory 
--image_dir /home/dmt/Documents/IIIF_Ingest/images/book.jpg 
--compact False
```


