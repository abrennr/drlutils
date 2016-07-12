from lxml import etree
import csv
import sys
import drlutils.django.utils
import drlutils.config


def modify_xml(do_id, dlxs_xml):
    item = drlutils.django.utils.get_item(do_id)
    spreadsheet = csv.DictReader(open(drlutils.config.PITTPRESS_CSV, 'r'))
    for row in spreadsheet:
        if row['BARCODE'] == do_id:
            if item.copyright_status != 'pd_expired':
            # modify digital edition availability
                dig_availablity = dlxs_xml.xpath('/DLPSTEXTCLASS/HEADER/FILEDESC/PUBLICATIONSTMT/AVAILABILITY/P')[0]
                dig_availablity.text = 'This is copyright-protected material.  All rights reserved by the University of Pittsburgh Press.  This material is provided for scholarly, educational, and research use. Any other use of this material, in whole or in part, including but not limited to any reproduction or  redistribution by any means, other than short quotations as permitted under the fair use doctrine, is strictly prohibited without the written permission of the publisher.'
                # modify source edition availability
                source_availability = etree.Element('AVAILABILITY')
                p = etree.Element('P')
                ref = etree.Element('REF', TYPE='url', TARGET=row['LINK'])
                ref.text = '[link]'
                source_pubstmt = dlxs_xml.xpath('/DLPSTEXTCLASS/HEADER/FILEDESC/SOURCEDESC/BIBLFULL/PUBLICATIONSTMT')[0]
                if 'permissionrequests.htm' in row['LINK']:
                    p.text = 'This book is out of print.  For information on requesting permission to reproduce material from this volume: ' 
                else:
                    p.text = 'For more information about this book, or to purchase a copy: '
                p.append(ref)
                source_availability.append(p)
                source_pubstmt.append(source_availability)

                # modify series statement?
                # add pittpress keywords
                keywords = etree.Element('KEYWORDS', SCHEME='local-pittpress')
                term = etree.Element('TERM')
                term.text = row['SUBJECT']
                keywords.append(term)
                textclass = dlxs_xml.xpath('/DLPSTEXTCLASS/HEADER/PROFILEDESC/TEXTCLASS')[0]
                textclass.append(keywords)
                return dlxs_xml
            else:
                pass
        print 'WARNING: No pittpress-specific record found for %s' % (do_id,)
        return dlxs_xml

