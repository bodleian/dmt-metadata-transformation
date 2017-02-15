#!/usr/bin/python2.7

import in2iiif
import unittest

from factory import ManifestFactory
import ConfigParser
import ast
import argparse
import os.path
import sys


class TestIn2iiif(unittest.TestCase):
    def setUp(self):
        self.nums = list(range(11))
        self.dict = {"one": "1", "two": "2"}

    def testGlobalConfigSetGetItem(self):
        # testing GlobalConfig

        print "\ntesting GlobalConfig setitem and getitem:"
        g = in2iiif.GlobalConfig()
        g.__setitem__("key", "value")
        value = g.__getitem__("key")
        self.assertEqual(value, "value")

    def testGlobalConfigInit(self):

        print "\nteesting GlobalConfig init:"
        g = in2iiif.GlobalConfig(
                    manifest_base_metadata_uri = "a",
                    manifest_base_metadata_dir = "b",
                    manifest_base_image_uri = "c",

                    )

        a = g.__getitem__("manifest_base_metadata_uri")
        self.assertEqual(a, "a")




if __name__ == "__main__": unittest.main()
