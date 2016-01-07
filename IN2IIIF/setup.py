import os
import sys

from setuptools import setup



setup(
    name = 'in2iiif',
    version = '0.0.1',
    author = 'Tanya Gray Jones',
    author_email = 'tanya.gray@bodleian.ox.ac.uk',
    description = 'Script to transform METS to IIIF Presentation Manifest v2.0',
    packages=['in2iiif','tests']
    
)
