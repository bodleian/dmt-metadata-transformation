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


Setup
=====

git clone https://gitlab.bodleian.ox.ac.uk/dmt/MetadataTransformation.git 
cd IN2IIIF
pip install -r requirements.txt



Usage
=====
The in2iiif.py file is not called directly, but must be imported by another python file that is concerned with a specific format transformation, e.g. METS.

Mets2iiif
---------
Mets2iiif.py is a file that transforms METS/MODS to IIIF presentation manifest. Mets2iiif.py imports in2iiif.py. 




```bash
usage: mets2iiif.py [-h] --config CONFIG --output OUTPUT --input INPUT --image_src IMAGE_SRC
                    [--image_dir IMAGE_DIR] [--compact COMPACT]
```

Example

```bash
python mets2iiif.py --config example/mets.cfg --input example/METS/12.xml --image_src directory --image_dir example/book.jpg --compact False --output example/manifest.json

```

Tei2iiif
--------
Tei2iiif.py is a file that transforms TEI to IIIF presentation manifest. Tei2iiif.py imports in2iiif.py

```bash
usage: tei2iiif.py [-h] --config CONFIG --input INPUT --output OUTPUT --image_src IMAGE_SRC [--image_dir IMAGE_DIR] --compact COMPACT
```

Example

```bash
python tei2iiif.py --config example/tei.cfg --input example/tei.xml --image_src directory --image_dir example/images/ --compact False --output example/manifest.json

```





Configuration options
=====================

Command line
------------
```
--config
configuration file - location of configuration file
--input
input source file - location of input file to be transformed
--image_src
image source - directory or mets_file
--image_dir
location of image directory (if source folder used)
--compact
should json be compact or human-readable
--output
location of output file

```
Configuration file 
------------------

The configuration file can/will contain options that are specific to a particular format transformation. 

The variables defined in the configuration file are copied to the IIIF manifest output, or used to determine the values, using XPath for instance, from the input file. 

METS
An example configuration file for METS is shown below, divided into the following sections:
 * manifest
 * sequence
 * canvas
 * annotation
 * metadata

Manifest
  
 * uri - Where the resources live on the web
 * id - identifier for manifest
 
 * base_metadata_dir -  Where the resources live on disk
 
 * base_image_uri - Default Image API information
 * iiif_image_info_version
 * iiif_image_info_compliance
 
 * debug - whether to show debug messages in ManifestFactory - options: warn,error,error_on_warning
 
 
 * label - human-readable label for manifest
 * description - description of manifest
 * viewingDirection - viewing direction of image

Sequence

 * name 
 * id - sequence id
 * label - sequence label

Canvas

 * id - canvas id
 * label - canvas label

Annotation
 * uri
 * id_path - annotation id

Image 
 * location_path

Metadata

The metadata section contains xpath values that allow values to be extracted from the input file for a default set of Dublin Core properties:
 * contributor
 * coverage
 * creator
 * date
 * description
 * format
 * identifier
 * language
 * publisher
 * relation
 * rights
 * source
 * subject
 * title
 * type


```
[manifest]
# Where the resources live on the web
uri:					http://www.example.org/path/to/object/
id: 					manifest
 
# Where the resources live on disk
base_metadata_dir: 		/home/dmt/Documents/IIIF_Ingest/METS/ 

# Default Image API information
base_image_uri: 		http://www.example.org/path/to/image/api/ 
iiif_image_info_version:2.0
iiif_image_info_compliance:2

# options: warn,error,error_on_warning
debug: 					warn 

label: 					Example Manifest
description:			This is a longer description of the manifest
viewingDirection:		left-to-right

[sequence]
name:					SequenceName
id:						http://www.example.org/path/to/object/sequence/normal
label:					sequence label

[canvas]
id:						page
label:					Page 

[annotation]
uri:					scheme://host/prefix/%s/annotation/%s/info.json
id_path:				/mets:mets/mets:structMap[@TYPE='PHYSICAL']//mets:div[@ID='%s']/@CONTENTIDS


[metadata]
contributor:	//mods:mods/mods:name[@mods:role='contributor']/mods:displayForm
coverage:		concat(//mods:mods/mods:subject/mods:temporal,' ', //mods:mods/mods:subject/mods:geographic)
creator:		//mods:mods/mods:name[@mods:role='creator']/mods:displayForm
date:			//mods:mods/mods:originInfo/mods:dateCreated
description:	//mods:mods/mods:note
format:			concat(//mods:mods/mods:physicalDescription/mods:form,' ', //mods:mods/mods:physicalDescription/mods:extent, ' ',  //mods:mods/mods:physicalDescription/mods:extent/@unit, ' ', //mods:mods/mods:physicalDescription/mods:note)
identifier:		//mods:mods/mods:identifier
language:		//mods:mods/mods:language/mods:languageTerm
publisher:		//mods:mods/mods:originInfo/mods:publisher
relation:		//mods:mods/mods:relatedItem/@displayLabel
rights:			//mods:mods/mods:accessCondition
source:
subject:		//mods:mods/mods:subject/mods:topic
title:			//mods:mods/mods:titleInfo/mods:title
type:			//mods:mods/mods:typeOfResource


```
