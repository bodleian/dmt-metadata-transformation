


# Introduction

IN2IIIF is a python application that converts a number of data formats to a manifest file conforming to the IIIF Manifest Presentation API 2.0 specification (http://iiif.io/api/presentation/2.0/).

IN2IIIF is intended to be used from the command line.

IN2IIIF supports the conversion of two data formats:
* METS (http://www.loc.gov/standards/mets/), and
* TEI P5 (http://www.tei-c.org/Guidelines/P5/)


# Quick start

- install IN2IIIF
- decide what format you are converting from, and where to get the image(s) data
- use the script that corresponds to the format you are converting, e.g. mets2iiif.py for METS, tei2iiif.py for TEI
- modify the configuration file for the script that you will be using to extract the correct attributes from the input files - you can modify one of the example configuration files provided in the example folders
- consider what values are needed for the command line parameters, and run the script with the defined parameters

# Installation

Download a copy of IN2IIF using git, go into the IN2IIIF directory and install the python dependencies using pip:

```
git clone git@github.com:bodleian/dmt-metadata-transformation.git
cd IN2IIIF
pip install -r requirements.txt
```

### Python 2.7 only

IN2IIIF uses a python module (ManifestFactory) and this requires that Python version 2.7 is available.

## Dependencies

The use of IN2IIIF has a number of dependencies relating to the use of third-party python packages and modules.

- **ManifestFactory**: IN2IIIF makes use of the ManifestFactory python module to generate the IIIF presentation manifest. This was available at https://github.com/IIIF/presentation-api/tree/master/implementations/manifest-factory, but it appears to have disappeared...
- **Pillow**: Pillow is a python package that incorporates the Python Image Library. https://pypi.python.org/pypi/Pillow
- **lxml**: lxml is a python library for XML and HTML processing. http://lxml.de/

### libxml2

When installing the dependencies, you may encounter an error saying it can't find libxml. If so, follow these instructions to install libxml on Mac OSX or Linux system:

- Download libxml binary (http://xmlsoft.org/sources/libxml2-2.9.3.tar.gz), or "curl -O http://xmlsoft.org/sources/libxml2-2.9.3.tar.gz"
- tar xvzf libxml2-2.9.3.tar.gz
- cd libxml2-2.9.3
- ./configure --with-python=~/MetadataTransformation/lib/python2.7/
-- (replace —with-python path with usr/bin/python if not using a virtualenv)
- make
- sudo make install

# Usage


## Conversion of METS files

Use the mets2iiif.py file in the mets2iiif directory to convert METS files to IIIF.

The key pieces of information in a IIIF manifest are the location and file names of the images being listed, the size of the images, and their labels.

There are three options available for generating image locations, labels and sizes when converting METS files to IIIF:
* From information specified in the METS file
* From information gathered from a single image file
* From information gathered from a directory of image files

The command line parameters you use depends on the type of conversion you want to achieve.
```
usage: mets2iiif.py [-h] --config CONFIG --input INPUT --output OUTPUT --image_src IMAGE_SRC [--image_location IMAGE_LOCATION]
 --compact COMPACT
```


### Image location and label specified in the METS file

The image location and label are defined in the structMap section of the METS file. The image location will be used to retrieve an image and determine its dimensions; information that will be added to the IIIF manifest file.
Example
```
python mets2iiif.py --config example/mets2.cfg --input ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/local_flocatMets.xml --image_src mets_file  --image_location ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/images/MSOppenheimAdd871_1452598088645_jpg/  --compact False --output example/manifest.json
```

### Image location and label specified with a single image file

The image location is defined as a single file location in the command line parameters. The image label and image properties will be determined from the file, together with the use of an optional regular expression defined in the mets2iiif configuration file.
Example
```
python mets2iiif.py --config example/mets2.cfg --input ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/local_flocatMets.xml --image_src file  --image_location ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/images/MSOppenheimAdd871_1452598088645_jpg/oulis2015-bxx-0010-0.jpg  --compact False --output example/manifest.json
```

### Image location specified as a file directory containing the image files

In this case the IIIF manifest does not include any image information from the METS file such as location and labels. Instead it determines image properties from the images and can generate labels using a combination of a regular expression defined in the mets2iiif configuration file and the image file name.
Example
```
python mets2iiif.py --config example/mets2.cfg --input ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/local_flocatMets.xml --image_src directory  --image_location ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/images/MSOppenheimAdd871_1452598088645_jpg/  --compact False --output example/manifest.json
```
## Conversion of TEI files

Use the tei2iiif.py file in the tei2iiif directory to convert TEI files to IIIF.
```
usage: tei2iiif.py [-h] --config CONFIG --input INPUT --output OUTPUT --image_src IMAGE_SRC [--image_location IMAGE_LOCATION] --compact COMPACT
```


### Image location and label specified with a single image file

The image location is defined as a single file location in the command line parameters. The image label and image properties will be determined from the file, together with the use of an optional regular expression defined in the tei2iiif configuration file.
Example
```
python tei2iiif.py --config example/tei.cfg --input example/tei.xml --image_src file  --image_location ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/images/MSOppenheimAdd871_1452598088645_jpg/oulis2015-bxx-0010-0.jpg  --compact False --output example/manifest.json
```
### Image location specified as a file directory containing the image files

In this case the IIIF manifest does not include any image information from the TEI file such as location and labels. Instead it determines image properties from the images and can generate labels using a combination of a regular expression defined in the tei2iiif configuration file and the image file name.
Example
```
python tei2iiif.py --config example/tei.cfg --input example/tei.xml --image_src directory  --image_location ~/apps/MetadataTransformation/samples/MSOppenheimAdd871/images/MSOppenheimAdd871_1452598088645_jpg/  --compact False --output example/manifest.json
```






# Configuration options
The script is configured using both command line parameters and a configuration file. This section describes the parameters that can be set on the command line and in the configuration file.

## Command line
The following parameters are set on the command line.

|  Command   |  Operation  |
| ---------- | ----------- |
|  --config  | Specifies the location of configuration file |
| --input    | Specifies the location of the input file to be transformed to IIIF |
| --image_src  | Specifies the source of the image file(s) that are used in the conversion process. A controlled vocabulary is used, with the following options: <ul><li>directory - images are located in a directory specified by the image_location parameter</li><li>file - a single image is used with its location specified by the image_location parameter</li><li>mets_file - the location of the image(s) is defined in the METS file</li></ul> |
|  --image_location  | Specifies the location of an image or directory of images -  required if the image_src parameter value is "directory" or "file" |
|  --compact  | Specifies the style of the IIIF manifest JSON. A controlled vocabulary is used with two options: <ul><li>compact</li><li>human-readable</li></ul>  |
|  --output  | Specifies the location of the IIIF manifest file that is output from the conversion process |


## Configuration file

The configuration file specified in the command line parameter contains parameters that are specific to the format being transformed.

The parameters defined in the configuration file are inserted into the IIIF manifest output, or else used to extract values from the input file, for inclusion in the IIIF manifest file.

An example configuration file for METS is shown below, divided into the following sections:
 * manifest
 * sequence
 * canvas
 * annotation
 * metadata

 #### Example METS configuration file
 Also see the example mets.cfg file in the example directory associated with the mets2iiif.py script.

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
 label_regex:                            [a-zA-Z0-9-]*

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

The tables below specify the attributes and valid values for the configuration file.

### Manifest

|  Attribute  |  Value |
| ----------- | -------- |
|  uri        |  Where the resources live on the web  |
|  id         |  Identifier for manifest  |
|  base_metadata_dir  | Where the resources live on disk  |
|  base_image_uri  |  Default Image API information
|  iiif_image_info_version  |  |
|  iiif_image_info_compliance  |  |
|  debug  |  whether to show debug messages in ManifestFactory - options: <ul><li>warn</li><li>error</li> <li>error_on_warning</li></ul>  |
|  label  |  human-readable label for manifest  |
|  description  |  description of manifest  |
|  viewingDirection  |  viewing direction of image  |


### Sequence

|  Attribute  |  Value |
| ----------- | -------- |
|  name  |  |
|  id  |  sequence id  |
|  label  |  sequence label  |

### Canvas

|  Attribute  |  Value |
| ----------- | -------- |
|  id  |  Canvas id  |
|  label_prefix  |  Canvas label  |
|  label_regex  |  <p>Regular expression to extract canvas label from the image file name(s).</p><p>The following regular expression will create a label from the image file name, it will only extract the leading characters that include alphabetical characters (case-insensitive) and a hyphen.</p><p>[a-zA-Z0-9\-]*</p><p>As a consequence the file suffix will not be included in the matched string, as the regular expression does not include a period.</p><p>To learn more about regular expressions, go to http://regexone.com/ .</p>

### Annnotation

|  Attribute  |  Value |
| ----------- | -------- |
| uri |  |
| id_path |  annotation id  |
|

### Metadata

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
