#!/usr/bin/python2.7
# mets2iiif.py by Tanya Gray Jones [tanya.gray@bodleian.ox.ac.uk]
# This is a transformation script for METS to IIIF API Manifest version 2.0

import imp

factory = imp.load_source('factory', '../factory.py')

from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import libxml2, sys
import os

from lxml import etree
from io import StringIO, BytesIO

execfile('../in2iiif.py')


def main():
    mets = Mets2iiif()  # create an object that is an instance of Mets2iiif class
    factory = mets.factory()  # create ManifestFactory factory
    manifest = mets.manifest(factory)  # define manifest
    sequence = mets.sequence(manifest)  # define sequence
    mets.canvas(sequence)  # define canvases, annotations and images
    mets.outputManifest(manifest)  # write to file


class Mets2iiif(In2iiif):
    """Transforms METS to IIIF using ManifestFactory and in2iiif."""

    def __init__(self, **kwargs):
        """Constructor - sets global variables using command-line arguments and config file."""
        self.parseArguments()  # parse command line arguments and add to global variables
        self.parseConfig()  # parse config file and add generic vars to global variables
        self._parseConfigMetadata()  # parse config file and add mets specific metadata settings to global variables

    def _parseConfigMetadata(self):
        """Read config file and extracts metadata properties to global variables."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables
        config = ConfigParser.ConfigParser()  # config file parser

        try:
            config.read(arg.config)  # read configuration file defined in command line arguments
            metadataProperties = config.options('metadata')  # get metadata section of config file

            # iterate through each metadata property defined in the section and assign value to global variable with name constructed from prefix 'metadata' plus name of metadata property
            for property in metadataProperties:
                arg['metadata_' + str(property)] = config.get('metadata', property)
                arg['metadata'] = arg.metadata + '|' + str(
                    property)  # also append name of metadata property to a global variable called "metadata"

        except Exception as e:
            print("A problem was encountered reading the configuration file specified:", e)
            sys.exit(0)

    def factory(self):
        """Initalizes manifest factory and set properties"""
        factory = ManifestFactory()  # instance of ManifestFactory
        self.setFactoryProperties(factory)  # set properties of ManifestFactory using global variables
        return factory

    def manifest(self, factory):
        """Initializes manifest and sets manifest properties"""

        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        # set properties of manifest
        manifest = factory.manifest(ident=arg.manifest_id, label=arg.manifest_label)

        self.setManifestProperties(manifest)  # set ManifestFactory manifest properties using global vars
        self._setMetadata(manifest)  # set ManifestFactory manifest metadata block using global vars

        return manifest

    def _setMetadata(self, manifest):
        """Sets metadata block of manifest."""
        arg = GlobalConfig()  # global variables
        metadata = arg.metadata  # get a string representation of a list of metadata properties from global variables
        properties = metadata.split('|')  # create array from string
        dictMetadata = {}  # create dictionary to hold values retrieved from mets file
        doc = ""

        try:
            file = open(arg.input, 'r')  # read mets file
        except IOError as e:
            print("Problem encountered with opening the METS file", e, arg.input)
            sys.exit(1);
        try:
            doc = etree.parse(file)
        except Exception as e:
            print("Problem encountered with parsing the METS file", e)
        # file.close()

        # iterate through array of metadata properties defined in the config file - extract values from the METS file using xpath
        for property in properties:
            if property != '':
                value = ""
                language = ""
                script = ""
                dictMetadata[property] = ''

                xpath = arg['metadata_' + property]  # get xpath for property from global variables

                if xpath != "":

                    result = doc.xpath(xpath, namespaces={'goobi': 'http://meta.goobi.org/v1.5.1/',
                                                          'mets': 'http://www.loc.gov/METS/',
                                                          "mods": "http://www.loc.gov/mods/v3"})  # use xpath to extract corresponding string or node values from the mets file

                    for item in result:  # iterate through items in list returned - either string value or element
                        if type(item) == str:
                            # string value - supports there being only one string value due to concat xpath statement
                            dictMetadata[property] = item
                        else:
                            # t'is an element
                            value = item.text  # get string value
                            language = item.xpath('@xml:lang')  # check if language attribute exists

                            if len(language) > 0:
                                lang = language[0]
                                scriptQuery = item.xpath("@script")  # check if script attribute exists
                                script = scriptQuery[0]

                                if script != '':  # if script attribute exists append value to language
                                    lang += '-' + script

                                existingValues = dictMetadata[property]  # get existing dictionary value for property

                                if len(existingValues) == 0:
                                    dictMetadata[
                                        property] = []  # if dictionary entry does not exist then create list value

                                dict = {'@value': value, '@language': lang}
                                dictMetadata[property].append(dict)  # update dictionary

                            else:
                                existingValue = dictMetadata[
                                    property]  # if no language attribute exists then use different construct for property value
                                if existingValue != '':
                                    existingValue += ';'  # add delimiter if concatenating values

                                dictMetadata[property] = existingValue + value

        # set metadata block for manifest if values have been extracted from the METS file
        if bool(dictMetadata):
            manifest.set_metadata(dictMetadata)

    def sequence(self, manifest):
        """Defines sequence for the manifest."""
        # assumption is that there is one sequence per manifest
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables
        sequence = manifest.sequence()
        if arg.sequence_id != "":  # if sequence_id defined in global variables use this
            sequence.id = arg.sequence_id % (arg.manifest_id, arg.sequence_name)
        if arg.sequence_label != "":  # if seqeunce label defined in global variables use this
            sequence.label = arg.sequence_label

        return sequence

    def outputManifest(self, manifest):
        """Write IIIF manifest to file."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        if arg.compact == 'True':  # should json output be compact?
            data = manifest.toString()
        else:
            data = manifest.toString(compact=False)

        try:
            fh = file(arg.output, 'w')
            fh.write(data)
            fh.close()
        except Exception as e:
            print('Problem writing manifest to file', e)
            sys.exit(0)

    def canvas(self, sequence):
        """Define canvases for manifest using METS file structMap."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        if (arg.image_src == 'directory') and (
            os.path.isdir(arg.image_location) == True):  # canvases and images defined using files in image directory
            image_directory_location = arg.image_location  # image location is specified by directory path in image_location command line parameter
            counter = 0

            # iterate through image files in the directory
            for file in sorted(os.listdir(image_directory_location)):
                counter += 1
                image_location = image_directory_location + os.sep + file  # determine file path for image
                canvas_id = arg.canvas_id + "-" + str(counter)  # use canvas id prefix defined in config
                canvas_label = self._canvas_label(counter, file)  # use canvas label prefix defined in config
                canvas = sequence.canvas(ident=canvas_id, label=canvas_label)  # canvas
                annotation = canvas.annotation()
                annotation.id = arg.annotation_uri % (arg.manifest_id, canvas_id)  # set id property for annotation
                self._image(canvas, annotation, counter, image_location)

        elif (arg.image_src == 'file') and (
            os.path.isdir(arg.image_location) == False):  # canvas and image defined using single file specified
            image_location = arg.image_location  # image location is specified by file path in image_location command line parameter
            canvas_id = arg.canvas_id + "-1"  # use canvas id prefix defined in config
            canvas_label = self._canvas_label(1, ntpath.basename(
                image_location))  # use canvas label prefix defined in config
            canvas = sequence.canvas(ident=canvas_id, label=canvas_label)  # canvas
            annotation = canvas.annotation()
            annotation.id = arg.annotation_uri % (arg.manifest_id, canvas_id)  # set id property for annotation
            self._image(canvas, annotation, 1, image_location)

        else:
            structMap = self._getMetsFileStructMap()  # canvases and images defined in mets file - read METS file structMap
            counter = 0  # counter for canvas label and id

            for item in structMap:  # create canvases using structMap
                counter += 1

                if item.attrib['ID']:
                    canvas_id = item.attrib['ID']  # set canvas id to id attribute
                else:
                    canvas_id = arg.canvas_id + "-" + str(
                        counter)  # or if not present, use canvas id prefix defined in config

                if item.attrib['ORDERLABEL']:
                    canvas_label = item.attrib['ORDERLABEL']  # set canvas label to orderlabel attribute
                else:
                    canvas_label = self._canvas_label(
                        counter)  # or if not present, use canvas label prefix defined in config

                canvas = sequence.canvas(ident=canvas_id, label=canvas_label)  # canvas
                annotation = self._annotation(canvas, canvas_id)  # annotation
                image_location = self._getImageLocation(canvas_id)
                self._image(canvas, annotation, counter, image_location)

    def _canvas_label(self, counter, filename):

        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        if ((arg.canvas_label_regex != '') and (filename != '')):
            # use regex with filename to determine canvas label
            regex = re.compile(arg.canvas_label_regex)
            matchObj = re.match(regex, filename)
            canvas_label = matchObj.group()
            if canvas_label == '':
                print(
                'Problem with canvas label regular expression in config file - creating canvas label with label_prefix',
                arg.canvas_label_regex, filename)
                canvas_label = arg.canvas_label_prefix + " " + str(counter)

        else:
            canvas_label = arg.canvas_label_prefix + " " + str(counter)

        # canvas requires label - error if label not
        if canvas_label == '':
            print('Canvas requires a label', arg.input)
            sys.exit(0)

        return canvas_label

    def _annotation(self, canvas, canvas_id):
        """Define annotation for canvas."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables
        annotation = canvas.annotation()

        if ((arg.annotation_id_path != "") and (arg.annotation_uri != "")):
            try:
                file = open(arg.input, 'r')  # open mets file for reading
                doc = etree.parse(file)  # read file into etree for xpath queries
            except:
                print('Unable to open mets file ', arg.input)
                sys.exit(0)

            try:  # construct annotation id from base path and xpath defined in the config file
                annotation_id_path = (arg.annotation_id_path % canvas_id)
                annotation_id_list = doc.xpath(annotation_id_path, namespaces={'mets': 'http://www.loc.gov/METS/',
                                                                               'xlink': 'http://www.w3.org/1999/xlink'})
                annotation.id = arg.annotation_uri % (
                arg.manifest_id, annotation_id_list[0])  # set id property for annotation
            except:
                print('Problem with annotation id xpath ', annotation_id_path)
                sys.exit(0)
        return annotation

    def _image(self, canvas, annotation, counter, image_location):
        """Define image for annotation."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        image = annotation.image("p%s" % counter, iiif=True)  # image - assumption - one image per canvas

        self.setImageProperties(image, image_location)
        self.setCanvasProperties(canvas, image)

    def _getImageLocation(self, canvas_id):
        """Determine image location."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables

        try:  # image location specified in mets file
            file = open(arg.input, 'r')  # open mets file for reading
            doc = etree.parse(file)  # read file into etree for xpath queries
        except:
            print('Unable to open mets file ', arg.input)
            sys.exit(0)

        xpath = "//mets:structMap[@TYPE='PHYSICAL']/mets:div/mets:div[@ID='%s']/mets:fptr[position()=1]/@FILEID" % canvas_id  # determine file id
        file_id = doc.xpath(xpath, namespaces={'mets': 'http://www.loc.gov/METS/'})[0]

        try:  # determine image location from mets file using image_location_path defined in config file and file_id parameter
            xpath = arg.image_location_path % file_id  # determine image location
            image_location = \
            doc.xpath(xpath, namespaces={'xlink': 'http://www.w3.org/1999/xlink', 'mets': 'http://www.loc.gov/METS/'})[
                0]
        except:
            print(
            'Problem with determination of image location from METS file - check that the image location_path parameter is correct in your configuration file.')
            sys.exit(0)

        if image_location == '':
            print('Unable to determine image file location from METS file')
            sys.exit(0)

        if os.path.isabs(
                image_location) is False:  # if image location is relative then get mets file location from input parameter and append
            image_location = os.path.join(arg.image_location, os.path.basename(image_location))

        return image_location

    def _getMetsFileStructMap(self):
        """Gets the structMap section of a METS file."""
        arg = GlobalConfig()  # instance of GlobalConfig to hold global variables
        try:
            file = open(arg.input, 'r')  # open mets file for reading
            doc = etree.parse(file)  # read file into etree for xpath queries
            file.close()  # close mets file
        except Exception as e:
            print("Error when opening or parsing METS file:", e)
            sys.exit(0)

        xpath = "//mets:structMap[@TYPE='PHYSICAL']/mets:div/mets:div"
        xml = doc.xpath(xpath, namespaces={'mets': 'http://www.loc.gov/METS/'})

        return xml


if __name__ == "__main__":
    main()
