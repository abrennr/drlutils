import sys
import os
import shutil
import datetime
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import workflow.wflocal.models
import drlutils.django.utils
import drlutils.text.utils
import drlutils.config
from lxml import etree
import zipfile
import re
import string
import traceback


def handle_collection_extras(do_id, coll_id, dlxs_xml):
    """This is where any collection-specific XML processing can be handled.  Just to keep things contained, place the import statements within this function"""
    if coll_id == 'pittpress':
    	import drlutils.dlxs.textclass_xml_pittpress
    	return drlutils.dlxs.textclass_xml_pittpress.modify_xml(do_id, dlxs_xml)
    else:
    	return dlxs_xml

def has_ocr(do_id):
    try:
        workflow.core.models.Item_Actions_Status.objects.get(item__do_id=do_id, action__name='ocr')
        return True
    except:
        return False

def filter_ocr(page_text):
    #page_text = drlutils.text.utils.filter_to_ascii(page_text)
    page_text = drlutils.text.utils.filter_whitespace(page_text)
    page_text = drlutils.text.utils.filter_ms_characters(page_text)
    return drlutils.text.utils.filter_for_xml(page_text)

def get_availability_statement(item):
    status = item.copyright_status
    if not status:
    	print 'WARNING: no copyright info found for ' + item.do_id
    if (status == 'pd_expired'):
    	return ' '.join(open(drlutils.config.PD_EXPIRED_TXT, 'r').readlines()).strip()
    elif status == 'copyrighted':
    	owner = item.copyright_holder_name
    	if owner:
    		preface = 'Copyright, ' + owner + '. All rights reserved. '
    	else:
    		preface = 'This is copyright-protected material. All rights reserved. '
    	boilerplate = ' '.join(open(drlutils.config.COPYRIGHT_TXT, 'r').readlines()).strip()
    	return preface + boilerplate
    else:
    	return 'These pages may be freely searched and displayed. Permission must be received for subsequent distribution in print or electronically.'


def build(do_id, c_id):
    """Create a DLXS-appropriate xml file for the item by using data from the assoicated mods, mets, and ocr files.  After a collection-generic XML is created, it's passed to the handle_collection_extras method for any additional collection-specific transformation.  Finally, the XML is written to a directory for that collection."""
    item = drlutils.django.utils.get_item(do_id) 
    mods_file = drlutils.django.utils.get_mods_path(item) 
    if not mods_file:
    	return do_id + ' - no mods file found'
    mets_file = drlutils.django.utils.get_mets_path(item) 
    if not mets_file:
    	return do_id + ' - no mets file found'
    try:
    	# mods is transformed into the header
    	mods = etree.parse(open(mods_file, 'r'))
    	mods_stylesheet = etree.parse(open(drlutils.config.MODS2DLXS_XSL, 'r'))
    	transform_mods = etree.XSLT(mods_stylesheet)
    	dlxs = transform_mods(mods)	
    	# mets is transformed into the body 
    	mets = etree.parse(open(mets_file, 'r'))
    	mets_stylesheet = etree.parse(open(drlutils.config.METS2DLXS_XSL, 'r'))
    	transform_mets = etree.XSLT(mets_stylesheet)
    	body = transform_mets(mets)	
    	# the body is appended to the header
    	dlxs.getroot().append(body.getroot())
        if has_ocr(do_id):
            try:
                ocr_file = drlutils.django.utils.get_ocr_zip_path(item) 
            except:
                return do_id + ' - no ocr file found'
            # the ocr is unzipped and added to the pages
            ocr_zip = zipfile.ZipFile(ocr_file, 'r')
            for ocr in ocr_zip.namelist():
                oimage = re.sub('.txt', '.tif', os.path.basename(ocr))
                xpath_for_p_element = '//P[@REF=\'' + oimage + '\']'    
                page_content = " ".join(ocr_zip.open(ocr).readlines())
                filtered_text = ' '
                if page_content:
                    filtered_text = filter_ocr(page_content) or ' ' 
                try:
                    p = dlxs.xpath(xpath_for_p_element)[0]
                    p.text = filtered_text
                except Exception as e:
                    print 'OCR exception: %s - %s - %s' % (str(e), do_id, xpath_for_p_element)
    	# remove the REF attribute of the P elements, which was our hook for the OCR
    	for p_tag in dlxs.xpath('//P'):
    		etree.strip_attributes(p_tag, 'REF')
    	# add digital object identifier
    	#idno = dlxs.xpath('//IDNO[@TYPE=\'uls-drl\']')[0]
    	idno = dlxs.xpath('//IDNO')[0]
    	idno.text = item.do_id
    	# add digital publication date
    	date = dlxs.xpath('/DLPSTEXTCLASS/HEADER/FILEDESC/PUBLICATIONSTMT/DATE')[0]
    	try:
    		pub = item.online_pub_date.year
    		date.text = str(pub)
    	except:
    		new_pub_date = str(datetime.date.today().year)
    		date.text = new_pub_date 
    	# add availability statement
    	availability = dlxs.xpath('/DLPSTEXTCLASS/HEADER/FILEDESC/PUBLICATIONSTMT/AVAILABILITY/P')[0]
    	availability.text = get_availability_statement(item)
    	# add extent (number) of digital files
    	pages = dlxs.xpath('//PB')
    	page_count = str(len(pages))
    	extent = dlxs.xpath('/DLPSTEXTCLASS/HEADER/FILEDESC/EXTENT')[0]
    	extent.text = page_count + ' digitized page images'
    	title_main = dlxs.xpath('//TITLE[@TYPE=\'245\']')[0]
    	div1_head = dlxs.xpath('//DIV1/HEAD')[0]
    	div1_head.text = title_main.text
    	# add tei encoding level
    	divs = dlxs.xpath('//DIV2')
    	if len(divs) > 1:
    		level = 2
    	else:
    		level = 1 
    	encodingdecl = dlxs.xpath('//EDITORIALDECL')[0]
    	encodingdecl.set("N", str(level))
    	# handle collection-specific extra processing
    	dlxs = handle_collection_extras(item.do_id, c_id, dlxs)
    	outdir = os.path.join(drlutils.config.DLXS_XML_PATH, c_id)
    	if not os.path.exists(outdir):
    		os.makedirs(outdir)
    	outfile = item.do_id + '.xml'
    	outpath = os.path.join(outdir, outfile)
    	etree.ElementTree(dlxs.getroot()).write(outpath, pretty_print=True)
    	return None
    except Exception as e:
    	return 'problem with %s: %s, %s' % (do_id, str(e), traceback.print_tb(sys.exc_info()[2]))

if __name__ == '__main__':
        try:
    		do_id = sys.argv[1]
    		c_id = sys.argv[2]
        except:
    		sys.exit('when running as a script, you must provide a digital object id and a collection id as arguments')
        item = drlutils.django.utils.get_item(do_id)
        user = drlutils.django.utils.get_user('gort')
        #action = drlutils.django.utils.get_action('make DLXS xml')
        result = build(item.do_id, c_id)
        if result:
    		print result
        else:
    		pass
    		#drlutils.django.utils.update_item_status(item, action, user, 'True')

