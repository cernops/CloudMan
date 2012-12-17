from piston.emitters import Emitter, XMLEmitter
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class MyXMLEmitter(Emitter):
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                self._to_xml(xml, item)
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                if isinstance(value, dict):
                    attr = getDictAttribute(value)
                    xml.startElement(key, attr)
                    self._to_xml(xml, value)
                    xml.endElement(key)
                elif isinstance(value, (list, tuple)):
                    xml.startElement(key, {})
                    for item in value:
                        self._to_xml(xml, item)
                    xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))


    '''def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                self._to_xml(xml, item)
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))            
'''
    def render(self, request):
        stream = StringIO.StringIO()
        xml = SimplerXMLGenerator(stream, "utf-8")
        xml.startDocument()
        self._to_xml(xml, self.construct())
        xml.endDocument()
        return stream.getvalue()


def getDictAttribute(myDict):
    attr ={}
    try:
        if isinstance(myDict, dict):
            for key, value in myDict.iteritems():
                if isinstance(value, (list,tuple,dict)):
                    pass
                else:
                    attr[key] = value
    except Exception:
        pass
    return attr 

