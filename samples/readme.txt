MSOppenheimAdd871

Contains images in jp2 and jpeg format.

There are three METS files:

i) goobi_internalMETS.xml

This is Goobi's internal format. It's not standard METS. This is what gets turned into standard METS by Goobi during the export process. This can be ignored for the purpose of testing just now, although it might be a useful exercise at some point to try creating a version of the METS to IIIF config file that uses the internal Goobi XPaths.

ii) local_flocatMETS.xml

Exported METS. File references in the xlink hrefs in the flocats have been changed to local relative paths. 

This file should be suitable for testing the METS to IIIF transformation reading the files locally, i.e. with --image_src mets_file

iii) http_flocatMETS.xml

This is how the METS is actually stored on Databank. All of the xlink hrefs are to Databank datasets.

This file should be suitable for testing the METS to IIIF transformation reading the files locally, i.e. with --image_src mets_\
file

Matt McGrattan can provide a login to use with basic HTTP authentication so these files can be read via HTTP. By default these files are embargoed and can't be downloaded by unauthenticated users.

---

The images subfolders can also be used for testing with the --image_src directory option.

