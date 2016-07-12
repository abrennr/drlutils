import sys
import os
import drlutils.django.utils
import drlutils.config
from lxml import etree

def transform(mods_sourcefile, dc_outfile):
    # parse mods-xml
    parser = etree.XMLParser(remove_blank_text=True)
    mods_xml = etree.parse(open(mods_sourcefile, 'r'), parser)

    # parse stylesheet
    stylesheet = etree.parse(open(drlutils.config.MODS2DC_XSL, 'r'))

    # apply stylesheet to transform MODS to Dublin Core 
    transform = etree.XSLT(stylesheet)
    dublincore = transform(mods_xml)    

    etree.ElementTree(dublincore.getroot()).write(dc_outfile, pretty_print=True)

def create(do_id):
    try:
        item = drlutils.django.utils.get_item(do_id) 

        # get path for mods-xml file associated with this item
        mods_sourcefile = drlutils.django.utils.get_mods_path(item) 
        if not mods_sourcefile and os.path.exists(mods_sourcefile):
            return item.do_id + ' - MODS XML doesn\'t exist in repository - skipping'
        
        # set up repository path
        repository_path = drlutils.django.utils.get_repository_path(item)
        dc_filename = item.do_id + '.dc.xml'
        dc_outfile = os.path.join(repository_path, dc_filename)
        transform(mods_sourcefile, dc_outfile)

        drlutils.django.utils.add_file_record(item, dc_outfile, 'TEXT_XML', 'DC')
        return None
    except Exception as e:
        return str(e)

