import sys
import os
import drlutils.django.utils
import drlutils.config
from lxml import etree
from copy import deepcopy

def create_retrographer_point(do_id):
       
    # get the newest, in-use tag matching this object id
    retrographer_tag = drlutils.django.utils.get_retrographer_tag(do_id) 
    coordinates = '%s,%s' % (retrographer_tag.lat, retrographer_tag.long)

    # parse kml template 
    parser = etree.XMLParser(remove_blank_text=True)
    kml = etree.parse(open(drl.utils.KML_POINT_TEMPLATE_FILE, 'r'), parser)
    
    # set coordinate text
    c = kml.xpath('/kml:kml/kml:Placemark/kml:Point/kml:coordinates', namespaces=drlutils.config.KML_NS_MAP)[0]
    c.text = coordinates

    # set up repository path
    item = drlutils.django.utils.get_item(do_id) 
    repository_path = drl.django.utils.get_repository_path(item) 
    # check if item already exists in repository
    if not os.path.exists(repository_path):
        return item.do_id + ' doesn\'t exist in repository - skipping'
    kml_file = do_id + '.kml.xml'
    kml_path = os.path.join(repository_path, kml_file)
    etree.ElementTree(kml.getroot()).write(kml_path, pretty_print=True)
    drlutils.django.utils.add_file_record(item, kml_path, 'TEXT_XML', 'KML')
    return None

