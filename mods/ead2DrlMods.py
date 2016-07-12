import sys
import os
import subprocess
import drlutils.date.utils
import drlutils.config
import drlutils.django.utils
from lxml import etree
from copy import deepcopy
import re


def enhance_mods(mods, do_id, report):
    """
    Add some specific extra data to the MODS that is generated from the stylesheet.
    This stuff either requires database lookup or some other programmatic logic not suited for XSLT.
    @param mods = the parsed mods document.  Returned again after modification.
    @param do_id = the digital object identifier
    """
    root = mods.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]

    # add copyright
    xsiSchemaLocation = root.get(drlutils.config.XSI + 'schemaLocation') + ' http://www.cdlib.org/inside/diglib/copyrightMD http://www.cdlib.org/groups/rmg/docs/copyrightMD.xsd'
    root.set(drlutils.config.XSI + 'schemaLocation', xsiSchemaLocation)
    accessCondition = etree.Element(drlutils.config.MODS + 'accessCondition')
    copyright = etree.Element(drlutils.config.COPYRIGHTMD + 'copyright', nsmap=drlutils.config.COPYRIGHTMD_NS_MAP)
    copyright.attrib['copyright.status'] = 'unknown'
    copyright.attrib['publication.status'] = 'unknown'
    item = drlutils.django.utils.get_item(do_id)
    if item and item.copyright_status:
            copyright.set('copyright.status', item.copyright_status)

    if item and item.publication_status:
        copyright.set('publication.status', item.publication_status) 

    if item and item.copyright_holder_name:
        rights_holder = etree.Element(drlutils.config.COPYRIGHTMD + 'rights.holder')
        rh_name = etree.Element(drlutils.config.COPYRIGHTMD + 'name')
        rh_name.text = item.copyright_holder_name
        rights_holder.append(rh_name)
        copyright.append(rights_holder)
        if item.permission_notes:
            note = etree.Element(drlutils.config.COPYRIGHTMD + 'note')
            note.text = item.permission_notes
            rights_holder.append(note)

    accessCondition.append(copyright)
    root.append(accessCondition)


    # convert date fields in originInfo

    # first, get the only date we have: whatever is in dateOther@type="display"
    date_display = mods.xpath('//mods:dateOther[@type="display"]', namespaces=drlutils.config.MODS_NS_MAP)[0].text
    if date_display:
        # any of these characters in the date string signal the date is questionable
        if re.search('[\[\]\?]', date_display):
            questionable = True
        else:
            questionable = False
        # attempt to parse a normalized date from display date
        date_iso8601 = drlutils.date.utils.get_normalized_date(date_display)
        if not drlutils.date.utils.is_normalized_date(date_iso8601):
            report = report +  u'WARNING: Item %s has bad iso8601 date: %s\n' % (do_id, date_iso8601)
        else:
            # (only do this stuff if we have a valid normalized date to work with...
            # use the iso8601 value to populate dateIssued@encoding='iso8601' 
            originInfo = mods.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
            dateCreated = etree.Element(drlutils.config.MODS + 'dateCreated', encoding="iso8601", keyDate="yes")
            dateCreated.text = date_iso8601 
            if questionable:
                dateCreated.attrib['qualifier'] = 'questionable'
            originInfo.append(dateCreated)

            # create a dateOther@type='sort'
            dateOtherSort = etree.Element(drlutils.config.MODS + 'dateOther', type="sort")
            dateOtherSort.text = drlutils.date.utils.get_sort_date(date_iso8601) 
            originInfo.append(dateOtherSort)

    return (mods, report)

def create_mods_from_ead(ead_xml_file):

    report = u'working with %s\n' % (ead_xml_file,)

    # parse ead-xml
    parser = etree.XMLParser(remove_blank_text=True)
    ead_xml = etree.parse(open(ead_xml_file, 'r'), parser)

    # get all DAOs out of ead to re-open mods for modification 
    dao_elements = ead_xml.xpath('//ead:dao', namespaces=drlutils.config.EAD_NS_MAP)
    dao_ids = []
    has_dupes = False
    for dao in dao_elements:
        dao_id = dao.get(drlutils.config.XLINK + 'href')
        if dao_id in dao_ids:
            report = report + u'ERROR: %s is a duplicate ID\n' % (dao_id,)
            has_dupes = True
        dao_ids.append(dao_id)

    if has_dupes:
        report = report + u'Exiting due to duplicate DAO ids in EAD'
        return report
    else:
        report = report + u'found %s dao objects to process...\n' % (len(dao_ids),)


    # save current working dir, switch to MODS output dir
    cwd = os.getcwd()
    os.chdir(drlutils.config.MODS_PATH)

    # apply stylesheet to transform ead-xml to mods
    # note: using xsltproc here to support xslt
    ead_xml_file_path = os.path.join(cwd, os.path.basename(ead_xml_file))
    try:
        subprocess.check_call([drlutils.config.JAVA, '-jar', drlutils.config.SAXON, '-s', ead_xml_file_path, drlutils.config.EAD2MODS_XSL]) 
    except Exception as e:
        report = report +  u'ERROR: in intital EAD -> MODS XSLT: %s\n' % (str(e),)
        return report

    # switch back to previous current working dir
    os.chdir(cwd)

    # open each mods and alter
    for do_id in dao_ids:
        mods_xml = '%s/%s.mods.xml' % (drlutils.config.MODS_PATH, do_id,)
        if not os.path.exists(mods_xml):
            report = report +  u'ERROR: MODS file not found at %s\n' % (mods_xml)
            continue

        mods = etree.parse(open(mods_xml, 'r'), parser)
        (mods, report) = enhance_mods(mods, do_id, report)
            
        # done, write back the MODS xml
        etree.ElementTree(mods.getroot()).write(mods_xml, pretty_print=True)
            
    return report
