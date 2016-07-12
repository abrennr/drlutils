from lxml import etree
import drlutils.config

def get_parsed_dc(dc_xml_file):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(open(dc_xml_file, 'r'), parser)

def get_dc_root(dc_xml_file):
    dc = get_parsed_dc(dc_xml_file)
    return dc.xpath('/dc:elementContainer', namespaces=drlutils.config.DC_NS_MAP)[0]
