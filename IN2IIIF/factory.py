
import os, sys
import commands
import urllib2

try:
    import json
except:
    # 2.5
    import simplejson as json

try:
    # Only available in 2.7
    # This makes the code a bit messy, but eliminates the need
    # for the locally hacked ordered json encoder
    from collections import OrderedDict
except:
    # Backported...
    try:
        from ordereddict import OrderedDict
    except:
        print "You must: easy_install ordereddict"
        raise

try:
    from PIL import Image as pil_image
except:
    try:
        import Image as pil_image
    except:
        pil_image = None

try:
    from lxml import etree
except:
    etree = None

class PresentationError(Exception):
    resource = None

    def __init__(self, msg, resource=None):
        self.args = [msg]
        self.resource = resource

# Raised when an object (likely the factory) isn't configured properly for the current operation
class ConfigurationError(PresentationError):
    pass

# Base metadata exception
class MetadataError(PresentationError):
    pass

# Raised when an object is not in the right place for the structure, or the structure is empty
# and cannot be
class StructuralError(MetadataError):
    pass

# Raised when a requirement of the model is not met (eg property is missing)
class RequirementError(MetadataError):
    pass

# Raised when the data is invalid, either by content or type
class DataError(MetadataError):
    pass

MAN_VIEWINGHINTS = ['individuals', 'paged', 'continuous']
CVS_VIEWINGHINTS = ['non-paged']
RNG_VIEWINGHINTS = ['top', 'individuals', 'paged', 'continuous']
VIEWINGDIRS = ['left-to-right', 'right-to-left', 'top-to-bottom', 'bottom-to-top']

BAD_HTML_TAGS = ['script', 'style', 'object', 'form', 'input']
GOOD_HTML_TAGS = ['a', 'b', 'br', 'i', 'img', 'p', 'span']

KEY_ORDER = ["@context", "@id", "@type", "@value", "@language", "label", "value",
             "metadata", "description", "thumbnail", "attribution", "license", "logo",
             "format", "height", "width", "startCanvas",
             "viewingDirection", "viewingHint", 
             "profile", "seeAlso", "search", "formats", "qualities", "supports",
             "scale_factors", "scaleFactors", "tile_width", "tile_height", "tiles", "sizes",
             "within", "motivation", "stylesheet", "resource", 
             "on", "default", "item", "style", "full", "selector", "chars", "language", 
             "sequences", "structures", "canvases", "resources", "images", "otherContent" ] 

KEY_ORDER_HASH = dict([(KEY_ORDER[x],x) for x in range(len(KEY_ORDER))])

class ManifestFactory(object):
    metadata_base = ""
    metadata_dir = ""

    def __init__(self, version="2.0", mdbase="", imgbase="", mddir="", lang="en"):
        """ mdbase: (string) URI to which identities will be appended for metadata
        imgbase: (string) URI to which image identities will be appended for IIIF Image API
        mddir: (string) Directory where metadata files will be written
        lang: (string) Language code to use by default if multiple languages given"""

        if mdbase:
            self.set_base_metadata_uri(mdbase)
        if imgbase:
            self.set_base_image_uri(imgbase)

        if mddir:
            self.set_base_metadata_dir(mddir)

        self.default_lang = lang
        if self.default_lang != "en":
            self.add_lang = True
        else:
            self.add_lang = False

        self.presentation_api_version = version
        if version[0] == "2":
            self.context_uri = "http://iiif.io/api/presentation/2/context.json"
        elif version == "1.0" or version == "0.9":
            self.context_uri = "http://www.shared-canvas.org/ns/context.json"
        else:
            raise ConfigurationError("Unknown Presentation API Version: " + version )

        # Default Image API info
        self.default_image_api_version = "0"
        self.default_image_api_level = -1
        self.default_image_api_context = ""
        self.default_image_api_profile = ""
        self.default_image_api_uri = ""
        self.default_image_api_dir = ""
        self.image_auth_token = ""

        self.default_base_image_uri = ""
        self.default_base_image_dir = ""

        self.debug_level = "warn"
        self.log_stream = sys.stdout

        # Try to find ImageMagick's identify
        try:
            self.whichid = commands.getoutput('which identify')
        except:
            # No IM or not unix
            self.whichid = ""

    def set_debug_stream(self, strm):
        self.log_stream = strm

    def set_debug(self, typ):
        # error = squash warnings
        # warn = display warnings
        # error_on_warning = raise exception for a warning rather than continuing

        if typ in ['error', 'warn', 'error_on_warning']:
            self.debug_level = typ
        else:
            raise ConfigurationError("Only levels are 'error', 'warn' and 'error_on_warning'")

    def maybe_warn(self, msg):
        if self.debug_level == "warn":
            self.log_stream.write(msg + "\n")
            try:    
                self.log_stream.flush()
            except:
                pass
        elif self.debug_level == "error_on_warning":
            # We don't know the type, just raise a MetadataError
            raise MetadataError(msg)        

    def assert_base_metadata_uri(self):
        if not self.metadata_base:
            raise ConfigurationError("Metadata API Base URI is not set")

    def assert_base_image_uri(self):
        if not self.default_base_image_uri:
            raise ConfigurationError("IIIF Image API Base URI is not set")

    def set_base_metadata_dir(self, dir):
        if not os.path.exists(dir):
            raise ConfigurationError("Metadata API Base Directory does not exist")
        elif dir[-1] != "/":
            dir += "/"
        self.metadata_dir = dir

    def set_base_metadata_uri(self, uri):
        if not uri:
            raise ValueError("Must provide a URI to set the base URI to")
        elif uri[-1] != "/":
            uri += "/"
        self.metadata_base = uri

    def set_default_label_language(self, lang):
        self.default_lang = lang

    def set_base_image_dir(self, dr):
        if not dr:
            raise ValueError("Must provide a directory name to set the base directory to")            
        self.default_base_image_dir = dr


    def set_iiif_image_auth_token(self, token):
        self.image_auth_token = token

    def set_base_image_uri(self, uri):
        # No trailing / as that's what the base URI really is
        # Need to add it back all over the place though :(
        if not uri:
            raise ValueError("Must provide a URI to set the base URI to")    
        if uri[-1] == "/":
            uri = uri[:-1]
        self.default_base_image_uri = uri

    def set_iiif_image_info(self, version="2.0", lvl="1"):
        version = str(version)
        lvl = str(lvl)
        if not version in ['1.0', '1.1', '2.0']:
            raise ConfigurationError("Only versions 1.0, 1.1, 2.0 are known")
        if not lvl in ['0','1','2']:
            raise ConfigurationError("Level must be 0, 1 or 2")            
        self.default_image_api_version = version
        self.default_image_api_level = lvl
        if version == "1.0":
            self.default_image_api_profile = "http://library.stanford.edu/iiif/image-api/compliance.html#level" + lvl
            self.default_image_api_context = "http://library.stanford.edu/iiif/image-api/context.json"
        elif version == "1.1":
            self.default_image_api_profile = "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level" + lvl
            self.default_image_api_context = "http://library.stanford.edu/iiif/image-api/1.1/context.json"
        else:
            self.default_image_api_profile = "http://iiif.io/api/image/2/level%s.json" % lvl        
            self.default_image_api_context = "http://iiif.io/api/image/2/context.json"
    
    def set_iiif_image_conformance(self, version, lvl):
        return self.set_iiif_image_info(version, lvl)

    def collection(self, ident="collection", label="", mdhash={}):
        if not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return Collection(self, ident, label, mdhash)

    def manifest(self, ident="manifest", label="", mdhash={}):
        if not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return Manifest(self, ident, label, mdhash)

    def sequence(self,ident="", label="", mdhash={}):
        if ident and not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return Sequence(self, ident, label, mdhash)

    def canvas(self,ident="", label="", mdhash={}):
        if not ident:
            raise RequirementError("Canvases must have a real identity (Canvas['@id'] cannot be empty)")
        elif not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return Canvas(self, ident, label, mdhash)

    def annotation(self, ident="", label="", mdhash={}):
        if ident and not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return Annotation(self, ident, label=label)

    def annotationList(self, ident="", label="", mdhash={}):
        if not ident:
            raise RequirementError("AnnotationLists must have a real identity (AnnotationList['@id'] cannot be empty)")
        elif not ident.startswith('http'):
            self.assert_base_metadata_uri()
        return AnnotationList(self, ident, label, mdhash)

    def image(self, ident, label="", iiif=False, region='full', size='full'):
        if not ident:
            raise RequirementError("Images must have a real identity (Image['@id'] cannot be empty)")            
        return Image(self, ident, label, iiif, region, size)

    def audio(self, ident, label=""):
        if not ident:
            raise RequirementError("Audio must have a real identity (Audio['@id'] cannot be empty)")            
        return Audio(self, ident, label)        

    def choice(self, default, rest):
        return Choice(self, default, rest)

    def specificResource(self, full):
        return SpecificResource(self, full)

    def text(self, txt="", ident="", language="", format=""):
        if ident:
            return ExternalText(self, ident, language, format)
        else:
            # may be empty string
            return Text(self, txt, language, format)

    def range(self, ident="", label="", mdhash={}):
        return Range(self, ident, label, mdhash)

    def layer(self, ident="", label="", mdhash={}):
        return Layer(self, ident, label, mdhash)

    def service(self, ident="", label="", context="", profile=""):
        return Service(self, ident, label, context, profile)

### Note: id, type and context are always @(prop) in the output
### Cannot have type --> dc:type, for example 

class BaseMetadataObject(object):

    _properties = ['id', 'type', 'label', 'metadata', 'description', 'thumbnail',
        'attribution', 'license', 'logo', 'service', 'seeAlso', 'within', 'related',
        'viewingHint', 'viewingDirection']
    _extra_properties = []
    _integer_properties = []
    _structure_properties = {}
    _object_properties = ['thumbnail', 'license', 'logo', 'seeAlso', 'within', 'related', 'service']

    def __init__(self, factory, ident="", label="", mdhash={}, **kw):
        self._factory = factory
        if ident:
            if ident.startswith('http'):
                self.id = ident
            else:
                self.id = factory.metadata_base + self.__class__._uri_segment + ident
                if not self.id.endswith('.json'):
                    self.id += '.json'
        else:
            self.id = ""
        self.type = self.__class__._type
        self.label = ""
        if label:
            self.set_label(label)
        self.metadata = []
        if mdhash:
            self.set_metadata(mdhash)

        self.description = ""
        self.thumbnail = ""
        self.attribution = ""
        self.license = ""
        self.logo = ""
        self.service = ""
        self.seeAlso = ""
        self.within = ""
        self.related = ""

    def __setattr__(self, which, value):
        if which == 'context':
            raise DataError("Must not set context on non-Service, non-root objects")
        elif which[0] != "_" and not which in self._properties and not which in self._extra_properties and not which in self._structure_properties.keys():
            self.maybe_warn("Setting non-standard field '%s' on resource of type '%s'" % (which, self._type))
        elif which[0] != '_' and not type(value) in [str, unicode, list, dict] and not which in self._integer_properties and \
            not isinstance(value, BaseMetadataObject) and not isinstance(value, OrderedDict):
            # Raise Exception for standard prop set to non standard value
            # not perfect but stops the worst cases.                
            raise DataError("%s['%s'] does not accept a %s" % (self._type, which, type(value).__name__), self)                
        elif which in self._integer_properties and type(value) != int:
            raise DataError("%s['%s'] does not accept a %s, only an integer" % (self._type, which, type(value).__name__), self)
        elif value and which in self._object_properties and not self.test_object(value):
            raise DataError("%s['%s'] must have a URI or resource, got %s" % (self._type, which, repr(value)))

        if hasattr(self, which) and hasattr(self, 'set_%s' % which):
            fn = getattr(self, 'set_%s' % which)
            return fn(value)
        elif value and which in self._object_properties:
            self._set_magic_resource(which, value)
        else:
            object.__setattr__(self, which, value)

    def maybe_warn(self, msg):
        msg = "WARNING: " + msg
        self._factory.maybe_warn(msg)

    def test_object(self, data):
        # "http://..."
        # {"@id": "http://..."}
        # or list of above
        if type(data) in [str, unicode]:
            return data.startswith('http')
        elif type(data) == dict:
            return '@id' in data
        elif isinstance(data, BaseMetadataObject):
            return True
        elif type(data) == list:
            for d in data:
                if type(d) in [str, unicode] and not data.startswith('http'):
                    return False
                elif type(d) == dict and not '@id' in d:
                    return False
            return True
        else:
            print "expecing a resource, got: %r" % data
            return True


    def test_html(self, data):
        if etree:
            try:
                dom = etree.XML(data)
            except Exception, e:
                raise DataError("Invalid XHTML in '%s':  %s" % (data, e), self)
            for elm in dom.iter():
                if elm.tag in BAD_HTML_TAGS:
                    raise DataError("HTML vulnerability '%s' in '%s'" % (elm.tag, data), self)
                elif elm.tag in [etree.Comment, etree.ProcessingInstruction]:
                    raise DataError("HTML Comment vulnerability '%s'" % elm, self)
                elif elm.tag == 'a':
                    for x in elm.attrib.keys():
                        if x != "href":
                            raise DataError("Vulnerable attribute '%s' on a tag" % x, self)
                elif elm.tag == 'img':
                    for x in elm.attrib.keys():
                        if not x in ['src', 'alt']:
                            raise DataError("Vulnerable attribute '%s' on img tag" % x, self)
                else:
                    if elm.attrib:
                        raise DataError("Attributes not allowed on %s tag" % (elm.tag), self)
                    if not elm.tag in GOOD_HTML_TAGS:
                        self.maybe_warn("Risky HTML tag '%s' in '%s'" % (elm.tag, data))
                # Cannot keep CDATA sections separate from text when parsing in LXML :(        

    def langhash_to_jsonld(self, lh, html=True):
        # {"fr": "something in french", "en": "something in english", "de html" : "<span>German HTML</span>"}
        # --> [{"@value": "something in french", "@language": "fr"}, ...]
        l = []
        for (k,v) in lh.items():
            if 'html' in k or (v[0] == '<' and v[-1] == '>'):
                k = k.replace("html", '').strip()
                if not html:
                    raise DataError("Cannot have HTML in '%s', only plain text" % v, self)
                # process HTML here
                if v[0] != '<' or v[-1] != '>':
                    raise DataError("First and last characters of HTML value must be '<' and '>' respectively, in '%r'" % v, self)
                self.test_html(v)
                if k:
                    l.append(OrderedDict([("@value",v), ("@language",k)]))
                else:
                    l.append(v)        
            else:
                l.append(OrderedDict([("@value",v), ("@language",k)]))
        return l

    def set_metadata(self, mdhash):
        # In:  {label:value, label2:value2}
        # ... or:  {'label': langhash, 'value': langhash}
        # Set: {"label":label, "value":value}
        # Really add_metadata, as won't overwrite
        
        if type(mdhash) != dict:
            raise ValueError("set_metadata takes a dict()")

        # by reference, not value, so can modify in place without
        # triggering __setattr__ on the resource ;)
        md = self.metadata

        mdk = mdhash.keys() 
        mdk.sort()
        if mdk == ['label', 'value']:
            # Work around to allow multiple languages for label;
            # just have to set_metadata() one at a time
            k = mdhash['label']
            v = mdhash['value']
            if type(k) in [str, unicode] and self._factory.add_lang:
                k = self.langhash_to_jsonld({self._factory.default_lang : k})
            elif type(k) == dict:
                k = self.langhash_to_jsonld(k)
            if type(v) in [str, unicode] and self._factory.add_lang:
                v = self.langhash_to_jsonld({self._factory.default_lang : v})
            elif type(v) == dict:
                v = self.langhash_to_jsonld(v)
            md.append(OrderedDict([("label", k), ("value", v)]))

        else:
            for (k,v) in mdhash.items():
                if type(v) in [str, unicode] and self._factory.add_lang:
                    v = self.langhash_to_jsonld({self._factory.default_lang : v})
                elif type(v) == dict:
                    v = self.langhash_to_jsonld(v)
                md.append(OrderedDict([("label", k), ("value", v)]))

    def _set_magic(self, which, value, html=True):
        if type(value) in [str, unicode]:
            if self._factory.add_lang:
                value = self.langhash_to_jsonld({self._factory.default_lang : value}, html)
            elif value and value[0] == '<' and value[-1] == '>':
                self.test_html(value)
        elif type(value) == dict:
            # {"en:"Something",fr":"Quelque Chose"}
            value = self.langhash_to_jsonld(value, html)
        elif type(value) == list:
            # list of values
            nl = []
            for i in value:
                if type(i) in [str, unicode]:
                    if self._factory.add_lang:
                        nl.extend(self.langhash_to_jsonld({self._factory.default_lang : i}, html))
                    elif value and value[0] == '<' and value[-1] == '>':
                        self.test_html(i)
                        nl.append(i)
                elif type(i) == dict:
                    # {"en:"Something",fr":"Quelque Chose"}
                    nl.extend(self.langhash_to_jsonld(i, html))            
                else:
                    nl.append(i)
            value = nl
        object.__setattr__(self, which, value)

    def set_label(self, value):
        return self._set_magic('label', value, False)
    def set_description(self, value):
        return self._set_magic('description', value)
    def set_attribution(self, value):
        return self._set_magic('attribution', value)

    def _set_magic_resource(self, which, value):
        # allow: string/object/dict, and magically generate list thereof
        try:
            current = getattr(self, which)
        except:
            current = None
        if not current:
            object.__setattr__(self, which, value)
        elif type(current) == list:
            new = current.append(value)
            object.__setattr__(self, which, new)
        else:
            new = [current, value]
            object.__setattr__(self, which, new)

    def add_service(self, ident, label="", context="", profile=""):
        svc = self._factory.service(ident, label, context, profile)
        self.service = svc
        return svc

    def get_thumbnail(self, width=0, height=0, square=False):
        # Check self for thumbnail
        if this.thumbnail:
            # Check if we have a IIIF Service and want width/height/square
            # XXX Finish Me
            if type(this.thumbnail) == list:
                pass
            return this.thumbnail
        else: 
            return None

    def toJSON(self, top=False):
        d = self.__dict__.copy()
        if d.has_key('id') and d['id']:
            d['@id'] = d['id']
            del d['id']
        d['@type'] = d['type']
        del d['type']
        for (k, v) in d.items():
            if not v or k[0] == "_":
                del d[k]
        if d.has_key('context'):
            d['@context'] = d['context']
            del d['context']
        for e in self._required:
            if not d.has_key(e):
                if self._structure_properties.has_key(e):
                    raise StructuralError("Resource type '%s' requires '%s' to be set" % (self._type, e), self)
                else:
                    raise RequirementError("Resource type '%s' requires '%s' to be set" % (self._type, e), self)
        debug = self._factory.debug_level
        if debug.find("warn") > -1:
            for e in self._warn:
                if not d.has_key(e):
                    msg = "Resource type '%s' should have '%s' set" % (self._type, e)
                    self.maybe_warn(msg)
        if top:
            d['@context'] = self._factory.context_uri

        # Enumerations
        if d.has_key('viewingHint'):
            if hasattr(self, '_viewing_hints'):
                if not d['viewingHint'] in self._viewing_hints:
                    msg = "'%s' not a known viewing hint for type '%s': %s" % (d['viewingHint'], self._type, ' '.join(self._viewing_hints))
                    self.maybe_warn(msg)
            else:
                msg = "Resource type '%s' does not have any known viewingHints; '%s' given" % (self._type, d['viewingHint'])
                self.maybe_warn(msg)

        if d.has_key('viewingDirection'):
            if hasattr(self, '_viewing_directions'):
                if not d['viewingDirection'] in self._viewing_directions:
                    msg = "'%s' not a known viewing direction for type '%s': %s" % (d['viewingDirection'], self._type, ' '.join(self._viewing_directions))
                    raise DataError(msg, self)
            else:
                msg = "Resource type '%s' does not have any known viewingDirections; '%s' given" % (self._type, d['viewingDirection'])
                self.maybe_warn(msg)

        # Recurse into structures, maybe minimally
        for (p,sinfo) in self._structure_properties.items():
            if d.has_key(p):
                if type(d[p]) == list:
                    newl = []
                    for s in d[p]:
                        minimalOveride = self._should_be_minimal(s)
                        done = self._single_toJSON(s, sinfo, p, minimalOveride)
                        newl.append(done)
                    d[p] = newl
                else:
                    if sinfo.get('list', False):
                        raise StructuralError("%s['%s'] must be a list, got %r" % (self._type, p, d[p]), self)
                    d[p] = self._single_toJSON(d[p], sinfo, p)

        return OrderedDict(sorted(d.items(), key=lambda x: KEY_ORDER_HASH.get(x[0], 1000)))

    def _should_be_minimal(self, what):
        return False

    def _single_toJSON(self, instance, sinfo, prop, minimalOveride=False):
        # duck typing. Bite me. 
        typ = sinfo.get('subclass', None)
        minimal = sinfo.get('minimal', False)
        if minimalOveride:
            minimal=True
        if type(instance) in [str, unicode]:
            # Just a URI
            return instance
        elif ( isinstance(instance, BaseMetadataObject) and typ == None ) or (typ != None and isinstance(instance, typ)):
            if minimal:
                return {'@id': instance.id, '@type': instance._type, 'label': instance.label}
            else:
                return instance.toJSON(False)
        elif type(instance) == dict and ( (instance.has_key('@type') and instance['@type'] == typ._type) or typ == None ):
            if minimal:
                return {'@id': instance['@id'], '@type':instance['@type'], 'label': instance['label']}
            else:
                return instance
        elif type(instance) == dict:
            raise StructuralError("%s['%s'] objects must be of type %s, got %s" % (self._type, prop, typ._type, instance.get('@type', None)), self)
        else:
            raise StructuralError("Saw unknown object in %s['%s']: %r" % (self._type, prop, instance), self)


    def _buildString(self, js, compact=True):
        if type(js) == dict:
            if compact:
                out = json.dumps(js, sort_keys=True, separators=(',',':'))
            else:
                out = json.dumps(js, sort_keys=True, indent=2)
        else:
            if compact:
                out = json.dumps(js, separators=(',',':'))
            else:
                out = json.dumps(js, indent=2)
        return out         

    def toString(self, compact=True):
        js = self.toJSON(top=True)
        return self._buildString(js, compact)

    def toFile(self, compact=True):
        mdd = self._factory.metadata_dir
        if not mdd:
            raise ConfigurationError("Metadata Directory on Factory must be set to write to file")

        js = self.toJSON(top=True)
        # Now calculate file path based on URI of top object
        # ... which is self for those of you following at home
        myid = js['@id']
        mdb = self._factory.metadata_base
        if not myid.startswith(mdb):
            raise ConfigurationError("The @id of that object is not the base URI in the Factory")
        fp = myid[len(mdb):]    
        bits = fp.split('/')
        if len(bits) > 1:
            mydir = os.path.join(mdd, '/'.join(bits[:-1]))        
            try:
                os.makedirs(mydir)
            except OSError, e:
                pass
        fh = file(os.path.join(mdd, fp), 'w')
        out = self._buildString(js, compact)
        fh.write(out)
        fh.close()
        return out


class ContentResource(BaseMetadataObject):

    def make_selection(self, selector, summarize=False):
        if summarize:
            full = OrderedDict([("@id",self.id), ("@type", self.type)])
            if self.label:
                full['label'] = self.label
        else:
            full = self

        sr = SpecificResource(self._factory, full)
        if type(selector) == str:
            selector = OrderedDict([("@type", "oa:FragmentSelector"), ("value", selector)])
        elif type(selector) == dict:
            selector = OrderedDict(sorted(selector.items(), key=lambda x: KEY_ORDER_HASH.get(x[0], 1000)))
        sr.selector = selector
        return sr

    def make_fragment(self, fragment):
        return self.id + "#" + fragment


class Collection(BaseMetadataObject):
    _type = "sc:Collection"
    _uri_segment = ""
    _required = ["@id", 'label']
    _warn = ["description"]
    collections = []
    manifests = []

    def __init__(self, *args, **kw):
        super(Collection, self).__init__(*args, **kw)
        self.collections = []
        self.manifests = []

    def add_collection(self, coll):
        self.collections.append(coll)

    def add_manifest(self, manifest):
        self.manifests.append(manifest)

    def collection(self, *args, **kw):
        coll = self._factory.collection(*args, **kw)
        self.add_collection(coll)
        return coll

    def manifest(self, *args, **kw):
        mn = self._factory.manifest(*args, **kw)
        self.add_manifest(mn)
        mn.within = self.id
        return mn


class Manifest(BaseMetadataObject):
    _type = "sc:Manifest"
    _uri_segment = ""
    _required = ["@id", "label", "sequences"]
    _warn = ["description"]
    _viewing_hints = MAN_VIEWINGHINTS
    _viewing_directions = VIEWINGDIRS

    sequences = []
    structures = []

    def __init__(self, *args, **kw):
        super(Manifest, self).__init__(*args, **kw)
        self.sequences = []
        self.structures = []

    def _should_be_minimal(self, what):
        if isinstance(what, Sequence) and self.sequences.index(what) > 0:
            return True
        return False

    def add_sequence(self, seq):
        # verify identity doesn't conflict with existing sequences
        if seq.id:
            for s in self.sequences:
                if s.id == seq.id:
                    raise DataError("Cannot have two Sequences with the same identity", self)

        # Label is only required if there is more than one sequence
        if self.sequences:
            seq._required.append("label")
            if len(self.sequences) == 1:
                self.sequences[0]._required.append("label")
        self.sequences.append(seq)

    def add_range(self, rng):
        # verify identity doesn't conflict with existing ranges
        if rng.id:
            for r in self.structures:
                if r.id == rng.id:
                    raise DataError("Cannot have two Ranges with the same identity", self)
        rng._parent = self
        self.structures.append(rng)

    def sequence(self, *args, **kw):
        seq = self._factory.sequence(*args, **kw)
        self.add_sequence(seq)
        return seq

    def range(self, *args, **kw):
        rng = self._factory.range(*args, **kw)
        self.add_range(rng)
        return rng


class Sequence(BaseMetadataObject):
    _type = "sc:Sequence"
    _uri_segment = "sequence/"
    _required = ["canvases"]
    _warn = ["@id"]
    _viewing_directions = VIEWINGDIRS
    _viewing_hints = MAN_VIEWINGHINTS
    _extra_properties = ["startCanvas"]

    canvases = []

    def __init__(self, *args, **kw):
        super(Sequence, self).__init__(*args, **kw)
        self.canvases = []

    def add_canvas(self, cvs, start=False):
        if cvs.id:
            for c in self.canvases:
                if c.id == cvs.id:
                    raise DataError("Cannot have two Canvases with the same identity", self)
        self.canvases.append(cvs)
        if start:
            self.set_start_canvas(cvs)

    def canvas(self, *args, **kw):
        cvs = self._factory.canvas(*args, **kw)
        self.add_canvas(cvs)
        return cvs

    def set_start_canvas(self, cvs):
        if type(cvs) in [unicode, str]:
            cvsid = cvs
        elif isinstance(cvs, Canvas):
            cvsid = cvs.id
        elif isinstance(cvs, OrderedDict):
            cvsid = cvs['@id']
        else:
            raise ValueError("Expected string, dict or Canvas, got %r" % cvs)

        okay = 0
        for c in self.canvases:
            if cvsid == c.id:
                okay = 1
                break
        if okay:
            self.startCanvas = cvsid
        else:
            raise RequirementError("Cannot set the startCanvas of a Sequence to a Canvas that is not in the Sequence")

### Canvas is a ContentResource as it can be segmented using oa:SpecificResource

class Canvas(ContentResource):
    _type = "sc:Canvas"
    _uri_segment = "canvas/"    
    _required = ["@id", "label", "height", "width"]
    _warn = ["images"]
    _viewing_hints = CVS_VIEWINGHINTS
    _extra_properties = ['height', 'width']
    _integer_properties = ['height', 'width']
    height = 0
    width = 0
    images = []
    otherContent = []

    def __init__(self, *args, **kw):
        super(Canvas, self).__init__(*args, **kw)
        self.images = []
        self.otherContent = []
        self.height = 0
        self.width = 0

    def set_hw(self, h,w):
        self.height = h
        self.width = w

    def add_image_annotation(self, imgid, iiif=True):
        self.maybe_warn("add_image_annotation is deprecated; use set_image_annotation() please")
        return self.set_image_annotation(imgid, iiif)

    def set_image_annotation(self, imgid, iiif=True):
        # Make simple image annotation
        anno = self.annotation()
        image = anno.image(ident=imgid, iiif=iiif)
        if iiif:
            image.set_hw_from_iiif()
        else:
            if imgid.startswith('http'):
                # take only last segment
                imgid = os.path.split(imgid)[1]
            self.set_hw_from_file(imgid)
        self.set_hw(image.height, image.width)
        return anno

    def add_annotation(self, imgAnno):
        self.images.append(imgAnno)
    def add_annotationList(self, annoList):
        self.otherContent.append(annoList)

    def annotation(self, *args, **kw):
        anno = self._factory.annotation(*args, **kw)
        anno.on = self.id
        self.add_annotation(anno)
        return anno

    def annotationList(self, *args, **kw):
        annol = self._factory.annotationList(*args, **kw)
        annol._canvas = self
        self.add_annotationList(annol)
        return annol

    def toJSON(self, top=False):
        # first verify that images are all for Image resources
        for anno in self.images:
            res = anno.resource
            # if res is neither an Image, nor part of an Image, nor a Choice of those then break
            if not (isinstance(res, Choice) or isinstance(res, Image) or (isinstance(res, SpecificResource) and isinstance(res.full, Image))):
                raise StructuralError("Annotations in Canvas['images'] must have Images for their resources, got: %r" % res, self)

        d = super(Canvas, self).toJSON(top)
        return d


class Annotation(BaseMetadataObject):
    _type = "oa:Annotation"
    _uri_segment = "annotation/"
    _required = ["motivation", "resource", "on"]
    _warn = ["@id"]
    _extra_properties = ['motivation', 'stylesheet']

    def __init__(self, *args, **kw):
        super(Annotation, self).__init__(*args, **kw)
        self.motivation = "sc:painting"
        self.on = ""
        self.resource = {}

    def image(self, ident="", label="", iiif=False):
        img = self._factory.image(ident, label, iiif)
        self.resource = img
        return img

    def text(self, text="", ident="", language="", format="text/plain"):
        txt = self._factory.text(text, ident, language, format)
        self.resource = txt
        return txt

    def audio(self, ident="", label=""):
        aud = self._factory.audio(ident, label)
        self.resource = aud
        return aud

    def choice(self, default, rest):
        chc = self._factory.choice(default, rest)
        self.resource = chc
        return chc

    def stylesheet(self, css, cls):
        # This has to go here, as need to modify both Annotation and Resource
        ss = OrderedDict([("@type", ["oa:CssStyle", "cnt:ContentAsText"]), 
            ("format", "text/css"), ("chars", css)])
        self.stylesheet = ss
        if not self.resource:
            raise ConfigurationError("Cannot set a stylesheet without first creating the body")
        if isinstance(self.resource, SpecificResource):
            self.resource.style = cls
        else:
            sr = SpecificResource(self._factory, self.resource)
            sr.style = cls
            self.resource = sr

class SpecificResource(BaseMetadataObject):
    _type = "oa:SpecificResource"
    _required = ['full']
    _warn = []
    _extra_properties = ['style', 'selector']
    style = ""
    selector = ""
    full = None

    def __init__(self, factory, full):
        self._factory = factory
        self.type = self.__class__._type
        self.full=full


class ExternalText(ContentResource):
    _type = "dctypes:Text"
    _required = []
    _factory = None
    _warn = ["format"]
    _uri_segment = "resources"
    _extra_properties = ['format', 'language']
    format = ""
    language = ""

    def __init__(self, factory, ident, language="", format=""):
        self._factory = factory
        self.format = format
        self.language = language
        self.type = self.__class__._type
        if ident.startswith('http'):
            self.id = ident
        else:
            self.id = self.id = factory.metadata_base + self.__class__._uri_segment + ident


class Text(ContentResource):
    _type = "cnt:ContentAsText"
    _required = ["chars"]
    _warn = ["format"]
    _extra_properties = ['format', 'chars', 'language']
    chars = ""
    format = ""
    language = ""

    def __init__(self, factory, text, language="", format="text/plain"):
        self._factory = factory
        self.type = self.__class__._type
        self.chars = text
        self.format = format
        if language:
            self.language = language

class Audio(ContentResource):
    _type = "dctypes:Sound"
    _required = ["@id"]
    _warn = ["format"]
    _uri_segment = "res"
    _extra_properties = ['format']

class Image(ContentResource):
    _type = "dctypes:Image"
    _required = ["@id"]
    _warn = ["format", "height", "width"]
    _extra_properties = ['format', 'height', 'width']
    _integer_properties = ['height', 'width']

    def __init__(self, factory, ident, label, iiif=False, region='full', size='full'):
        self._factory = factory
        self.type = self.__class__._type
        self.label = ""
        self.format = ""
        self.height = 0
        self.width = 0
        self._identifier = ""
        if label:
            self.set_label(label)

        if iiif:
            # add IIIF service -- iiif is version or bool
            # ident is identifier
            self.service = ImageService(factory, ident)

            if factory.default_image_api_version[0] == '1':
                self.id = factory.default_base_image_uri + '/' + ident + '/%s/%s/0/native.jpg' % (region, size)                
            else:
                self.id = factory.default_base_image_uri + '/' + ident + '/%s/%s/0/default.jpg' % (region, size)
            self._identifier = ident
            self.format = "image/jpeg"

        else:
            # Static image
            # ident is either full URL or filename
            if ident.startswith('http://') or ident.startswith('https://'):
                self.id = ident
            else:
                factory.assert_base_image_uri()
                self.id = factory.default_base_image_uri + ident

    def set_hw(self, h,w):
        self.height = h
        self.width = w

    def set_hw_from_iiif(self):
        if not self._identifier:
            raise ConfigurationError("Image is not configured with IIIF support")

        requrl = self._factory.default_base_image_uri + "/" + self._identifier + '/info.json';
        try:
            if self._factory.image_auth_token:
                req = urllib2.Request(requrl, headers={'Authorization': self._factory.image_auth_token})
            else:
                req = urllib2.Request(requrl)
            fh = urllib2.urlopen(req)
            data = fh.read()
            fh.close()
        except:
            raise ConfigurationError("Could not get IIIF Info from %s" % requrl)

        try:
            js = json.loads(data)
            self.height = int(js['height'])
            self.width = int(js['width'])
        except:
            print data
            raise ConfigurationError("Response from IIIF server did not have mandatory height/width")


    def set_hw_from_file(self, fn):

        # Try to do it automagically
        if not os.path.exists(fn):
            # Add base image dir
            fn2 = self._factory.default_base_image_dir + '/' + fn
            if not os.path.exists(fn2):
                raise ValueError("Could not find image file: %s" % fn)
            else:
                fn = fn2

        cmd = self._factory.whichid
        if cmd:
            # Try IM
            try:
                info = commands.getoutput(cmd + ' -ping -format "%h %w" ' + fn)
                (h, w) = info.split(" ")
                self.height = int(h)
                self.width = int(w)
                return
            except:
                pass

        if pil_image:
            # Try PIL
            try:
                img = pil_image.open(fn)
                (w,h) = img.size
                self.height = h
                self.width = w
                try:
                    img.close()
                except:
                    pass
                return
            except:
                pass

        raise ConfigurationError("No identify from ImageMagick and no PIL, you have to set manually")

class Choice(BaseMetadataObject):
    _type = "oa:Choice"
    _uri_segment = "annotation" # not really necessary
    _required = ["item"]
    _warn = ["default"]

    default = {}
    item = []

    def __init__(self, factory, default, rest):
        super(Choice, self).__init__(factory, indent="", label="", mdhash={})
        self.default = default
        if type(rest) != list:
            rest = [rest]
        self.item = rest


class AnnotationList(BaseMetadataObject):
    _type = "sc:AnnotationList"
    _uri_segment = "list/"    
    _required = ["@id"]
    _warn = []
    _canvas = None

    resources = []
    within = {}

    def __init__(self, *args, **kw):

        self.resources = []
        self.within = []
        self._canvas = None
        return super(AnnotationList, self).__init__(*args, **kw)

    def add_annotation(self, imgAnno):
        self.resources.append(imgAnno)

    def annotation(self, *args, **kw):
        anno = self._factory.annotation(*args, **kw)
        if self._canvas:
            anno.on = self._canvas.id
        self.add_annotation(anno)
        return anno

    def layer(self, *args, **kw):
        lyr = self._factory.layer(*args, **kw)
        self.within = lyr
        return lyr

class Range(BaseMetadataObject):
    _type = "sc:Range"
    _uri_segment = "range/"    
    _required = ["@id", "label"]
    _warn = ['canvases']
    _extra_properties = ['startCanvas']
    _viewing_hints = RNG_VIEWINGHINTS
    _viewing_directions = VIEWINGDIRS
    _parent = None

    startCanvas = ""
    canvases = []
    ranges = []

    def __init__(self, factory, ident="", label="", mdhash={}):
        super(Range, self).__init__(factory, ident, label, mdhash)
        self.canvases = []    
        self.ranges = []

    def __setattr__(self, which, value):
        if which == 'viewingHint': 
            if value == 'top':
                # unset canvases from _warn
                try:
                    self._warn.remove('canvases')
                except:
                    pass
            elif not 'canvases' in self._warn:
                self._warn.append('canvases')
        super(Range, self).__setattr__(which, value)

    def add_canvas(self, cvs, frag="", start=False):
        try:
            cvsid = cvs.id
        except:
            cvsid = cvs
            # Make sure we actually identify a canvas
            mf = self._parent
            okay = False
            testcvsid = cvsid
            hashidx = testcvsid.find('#')
            if hashidx > -1:
                testcvsid == testcvsid[:hashidx]
            for c in mf.sequences[0].canvases:
                if testcvsid == c.id:
                    okay = True
                    break
            if not okay:
                raise StructuralError("Can't add a canvas to a range that is not in the sequence: (%s)" % cvsid)

        if frag:
            cvsid += frag
        self.canvases.append(cvsid)
        if start:
            self.set_start_canvas(cvsid)

    def range(self, ident="", label="", mdhash={}):
        r = self._factory.range(ident, label, mdhash)
        self.add_range(r)
        return r

    def add_range(self, rng):
        self.ranges.append(rng.id)        

    def set_start_canvas(self, cvs):
        if type(cvs) in [unicode, str]:
            cvsid = cvs
        elif isinstance(cvs, Canvas):
            cvsid = cvs.id
        elif isinstance(cvs, OrderedDict):
            cvsid = cvs['@id']
        else:
            raise ValueError("Expected string, dict or Canvas, got %r" % cvs)

        if cvsid in self.canvases:
            self.startCanvas = cvsid
        else:
            raise RequirementError("Cannot set the startCanvas of a Range to a Canvas that is not in the Range")


class Layer(BaseMetadataObject):
    _type = "sc:Layer"        
    _uri_segment = "layer/"
    _required = ["@id", "label"]
    _warn = []


class Service(BaseMetadataObject):
    _type = ""
    _uri_segment = ""
    _required = ["@id"]
    _warn = ["@context", "profile"]
    _extra_properties = ['context', 'profile']
    context = ""


    def __init__(self, factory, ident, label="", context="", profile=""):
        if not ident.startswith('http'):
            raise RequirementError("Services must have an http[s] URI")
        BaseMetadataObject.__init__(self, factory, ident, label)
        self.context = context
        self.profile = profile

    def __setattr__(self, which, value):
        if which == "context":    
            object.__setattr__(self, which, value)            
        else:
            BaseMetadataObject.__setattr__(self, which, value)

class ImageService(Service):
    _type = ""
    _uri_segment = ""
    _required = ["@id", "@context"]
    _warn = ["profile"]
    context = ""    

    def __init__(self, factory, ident, label="", context="", profile=""):
        if not ident.startswith('http'):
            # prepend factory.base before passing up
            ident = factory.default_base_image_uri + '/' + ident    

        BaseMetadataObject.__init__(self, factory, ident, label)

        if not context:
            self.context = factory.default_image_api_context
        else:
            self.context = context
        if not profile and factory.default_image_api_level != -1:
            self.profile = factory.default_image_api_profile
        elif profile:
            self.profile = profile

# Need to set these at the end, after the classes have been defined
Collection._structure_properties = {'collections' : {'subclass': Collection, 'minimal': True, 'list': True}, 
                                    'manifests': {'subclass': Manifest, 'minimal': True, 'list': True}}
Manifest._structure_properties = {'sequences': {'subclass': Sequence, 'list':True}, 
                                  'structures': {'subclass': Range, 'list':True}}
Sequence._structure_properties = {'canvases': {'subclass':Canvas, 'list':True}}
Canvas._structure_properties = {'images': {'subclass': Annotation, 'list':True}, 
                                'otherContent':  {'subclass': AnnotationList, 'minimal':True, 'list':True}}
AnnotationList._structure_properties = {'resources': {'subclass': Annotation, 'list':True}}

Range._structure_properties = {'canvases': {'subclass':Canvas, 'list':True, 'minimal':True}, # Could be canvas.json#xywh= ...
                               'ranges': {'subclass': Range, 'list':True, 'minimal':True}}

# Don't type check these as they're Content subclasses 
Annotation._structure_properties = {'resource': {}, 'on':{'subclass': Canvas}}  
SpecificResource._structure_properties = {'full':{}}
Choice._structure_properties = {'default':{}, 'item':{}}

# Add Service object to all classes as structure
for c in [Collection, Manifest, Sequence, Canvas, Range, Layer, Image, AnnotationList, Annotation, Service]:
    c._structure_properties['service'] = {'subclass': Service}
    c._structure_properties['thumbnail'] = {'thumbnail': {'subclass':Image}}

if __name__ == "__main__":
    factory = ManifestFactory()    
    factory.set_base_metadata_uri("http://www.example.org/iiif/prezi/")
    factory.set_base_image_uri("http://www.example.org/iiif/image/")
    factory.set_iiif_image_info(version="2.0", lvl="2")

    mf = factory.manifest(label="Manifest")
    mf.viewingHint = "paged"

    seq = mf.sequence() 
    for x in range(1):
        cvs = seq.canvas(ident="c%s" % x, label="Canvas %s" % x)  
        cvs.set_hw(1000,1000)
        anno = cvs.annotation()  
        img = factory.image("f1r.c", iiif=True)
        img2 = factory.image("f1r", iiif=True)
        chc = anno.choice(img, [img2])

    print mf.toString(compact=False)