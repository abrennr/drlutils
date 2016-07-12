import sys
import os
import drlutils.date.utils
import drlutils.django.utils
import drlutils.mods.utils 
import drlutils.config
from lxml import etree
from copy import deepcopy
import re
import traceback


def filter_electronic_edition_cruft(mods):
    """
    Some of the MARC records we're using contain descriptions relating
    to the digitized / electronic / online edition of the item. There are
    statements that indicate we are an author, the digital colleciton is a 
    related series, etc.  These should all be removed so they don't cause
    confusion when displaying the MODS metadata online.
    """
    root = mods.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]

    # remove location element (contains url from MARC 856)
    etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}location')

    notes = mods.xpath('//mods:note', namespaces=drlutils.config.MODS_NS_MAP)    
    for note in notes:
        if note.get('type') == 'additional physical form' and 'Internet' in note.text:
            root.remove(note)
        elif note.get('type') == 'reproduction' and 'Digital Research Library' in note.text:
            root.remove(note)
        elif note.get('type') == 'system details' and 'World Wide Web' in note.text:
            root.remove(note)

    names = mods.xpath('//mods:name', namespaces=drlutils.config.MODS_NS_MAP)    
    for name in names:
        remove_me = False
        for e in name.iter():
            if e.text and 'Digital Research Library' in e.text:
                 remove_me = True
        if remove_me:
            root.remove(name)

    seriess = mods.xpath('//mods:relatedItem[@type="series"]', namespaces=drlutils.config.MODS_NS_MAP)
    for series in seriess: 
        remove_me = False
        for e in series.iter():
            if e.text and 'Historic Pittsburgh' in e.text:
                 remove_me = True
        if remove_me:
            root.remove(series)
       
    access_conditions = mods.xpath('//mods:accessCondition', namespaces=drlutils.config.MODS_NS_MAP)    
    for a_c in access_conditions:
        if a_c.text and 'Digital Research Library' in a_c.text:
            root.remove(a_c)

    return mods

def create(do_id):
    item = drlutils.django.utils.get_item(do_id)

    # get path for marc-xml file associated with this item
    marc_xml_file = drlutils.django.utils.get_marcxml_path(item) 
    assert os.path.exists(marc_xml_file)
    
    # parse marc-xml
    parser = etree.XMLParser(remove_blank_text=True)
    marc_xml = etree.parse(open(marc_xml_file, 'r'), parser)

    # parse stylesheet
    stylesheet = etree.parse(open(drlutils.config.MARC2MODS_XSL, 'r'))

    # apply stylesheet to transform marc-xml to mods
    transform = etree.XSLT(stylesheet)
    mods = transform(marc_xml)    

    # get rid of cataloging referring to electronic/digital/online edition
    mods = filter_electronic_edition_cruft(mods)            
    
    root = mods.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]

    # if this item record is serial, move the whole thing into a related item element
    # and then pull back selected parts to the top-level record
    #
    # NOTE: This needs to be done early, because for serials we often overwrite generic
    #       serial record data with more specific values for this particular item.
    issuances = mods.xpath('//mods:issuance', namespaces=drlutils.config.MODS_NS_MAP)    
    if issuances[0].text == 'continuing':
        # create a <relatedItem type="series"> element, copy other elements into it
        related_item = etree.Element(drlutils.config.MODS + 'relatedItem', type='series')
        # for all children of root, move them to the related item element
        # note: as elements are moved, they pop off the stack, so always move element index zero 
        for i in range(0,len(root)): 
            related_item.append(deepcopy(root[i]))
        # remove any existing relatedItems or notes that were from the serial record 
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}relatedItem')
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}note')
        root.append(related_item)
    else:
        pass

    # add identifier
    mods = drlutils.mods.utils.set_identifier(do_id, mods)

    # add copyright
    xsiSchemaLocation = root.get(drlutils.config.XSI + 'schemaLocation') + ' http://www.cdlib.org/inside/diglib/copyrightMD http://www.cdlib.org/groups/rmg/docs/copyrightMD.xsd'
    root.set(drlutils.config.XSI + 'schemaLocation', xsiSchemaLocation)
    accessCondition = etree.Element(drlutils.config.MODS + 'accessCondition')
    copyright = etree.Element(drlutils.config.COPYRIGHTMD + 'copyright', nsmap=drlutils.config.COPYRIGHTMD_NS_MAP)
    copyright.attrib['copyright.status'] = 'unknown'
    copyright.attrib['publication.status'] = 'unknown'

    if item.copyright_status:
        copyright.set('copyright.status', item.copyright_status)

    if item.publication_status:
        copyright.set('publication.status', item.publication_status) 

    if item.copyright_holder_name:
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

    # add depositor
    try:
        depositor = item.property_owner.depositor
        mods = drlutils.mods.utils.set_depositor(depositor, mods)
    except:
        print 'WARNING: Item %s - could not get depositor value' % (do_id,)

    
    # this override will be checked later when handling dates
    dateIssued_override = None
    try:
        # put enumeration into a titlePart element
        if item.enumeration:
            title_part = etree.Element(drlutils.config.MODS + 'partNumber')
            title_part.text = item.enumeration
            title_info = mods.xpath('/mods:mods/mods:titleInfo', namespaces=drlutils.config.MODS_NS_MAP)
            title_info[0].append(title_part)
        if item.date_issued:
            dateIssued_override = item.date_issued
        # TO DO: Check for patterns in enumeration string to create <part> elements
        # e.g. for volumes, issues, numbers, etc.
        if 'vol.' in item.enumeration:
            try:
                part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            except:
                part = etree.Element(drlutils.config.MODS + 'part')
                root.append(part)
            part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            detail = etree.Element(drlutils.config.MODS + 'detail', type="volume")
            number = etree.Element(drlutils.config.MODS + 'number')
            match = re.search('vol\. ([^,]+)', item.enumeration)
            number.text = match.group(1) 
            detail.append(number)
            caption = etree.Element(drlutils.config.MODS + 'caption')
            caption.text = 'vol.'
            detail.append(caption)
            part.append(detail)
        if 'no.' in item.enumeration:
            try:
                part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            except:
                part = etree.Element(drlutils.config.MODS + 'part')
                root.append(part)
            part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            detail = etree.Element(drlutils.config.MODS + 'detail', type="number")
            number = etree.Element(drlutils.config.MODS + 'number')
            match = re.search('no\. ([^,]+)', item.enumeration)
            number.text = match.group(1) 
            detail.append(number)
            caption = etree.Element(drlutils.config.MODS + 'caption')
            caption.text = 'no.'
            detail.append(caption)
            part.append(detail)
        if 'iss.' in item.enumeration:
            try:
                part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            except:
                part = etree.Element(drlutils.config.MODS + 'part')
                root.append(part)
            part = mods.xpath('/mods:mods/mods:part', namespaces=drlutils.config.MODS_NS_MAP)[0]
            detail = etree.Element(drlutils.config.MODS + 'detail', type="issue")
            number = etree.Element(drlutils.config.MODS + 'number')
            match = re.search('iss\. ([^,]+)', item.enumeration)
            number.text = match.group(1) 
            detail.append(number)
            caption = etree.Element(drlutils.config.MODS + 'caption')
            caption.text = 'iss.'
            detail.append(caption)
            part.append(detail)
    except Exception as e:
        print 'ERROR handling enumeration: %s' % (str(e),)            

    originInfo = mods.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]

    # handle date fields in originInfo
    #
    # A bit complex: For serials or monograph series, etc. we may have collected a
    # date that should override the date coming out of the bib record (which, for
    # serials, is often a range, often with an undertermined end point). 
    #
    # If the override date exists, use it to create a dateIssued, and remove all other
    # date elements in the originInfo.  The value (which should always be in the form
    # of YYYY) is also saved as the iso8601 value that will be used later to create
    # the display date and the sort date.
    #
    # If the override date does NOT exist, use the values pulled out of the marc 008
    # field, which are more controlled than what comes out of 260$c.  The 008 values
    # may be singular or a range, so create either a YYYY or YYYY/YYYY string for the 
    # iso8601 value.  As above, use this to create the dateIssued element, but in this
    # case also save whatever came from 260$c in a dateOther@type="260c" element before
    # proceeding.
    # 
    # Additionally, the marc 008 dates may have a qualifier (e.g. 'questionable') that
    # should be preserved, and used when generating the display date as well. 
    qualifier = None
    date_iso8601 = None 
    if dateIssued_override: 
        # remove any exisiting date elements
        etree.strip_elements(mods, drlutils.config.MODS + 'dateIssued')
        etree.strip_elements(mods, drlutils.config.MODS + 'dateCreated')
        # put year issued in dateIssued element
        date_issued = etree.Element('dateIssued', encoding="iso8601", keyDate="yes")
        date_issued.text = dateIssued_override 
        origin_info = mods.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)
        origin_info[0].append(date_issued)
        date_iso8601 = dateIssued_override 
    else:
        # get whatever the stylesheet grabbed from 008
        date_008s = mods.xpath('//mods:dateIssued[@encoding="marc"]', namespaces=drlutils.config.MODS_NS_MAP)
        # if there's nothing from 'dateIssued', check 'dateCreated', then 'copyrightDate'
        if len(date_008s) == 0:
            date_008s = mods.xpath('//mods:dateCreated[@encoding="marc"]', namespaces=drlutils.config.MODS_NS_MAP)
        if len(date_008s) == 0:
            date_008s = mods.xpath('//mods:copyrightDate[@encoding="marc"]', namespaces=drlutils.config.MODS_NS_MAP)
        if len(date_008s) > 1:
            # ignore date ranges that have unknown endpoints
            if 'u' in date_008s[1].text or '9999' in date_008s[1].text:
                date_iso8601 = date_008s[0].text
            else:
                date_iso8601 = '%s/%s' % (date_008s[0].text, date_008s[1].text)
            qualifier = date_008s[0].get('qualifier') or date_008s[1].get('qualifier')
        elif len(date_008s) == 1:
            date_iso8601 = date_008s[0].text
            qualifier = date_008s[0].get('qualifier')
        else:
            pass

        # remove encoding='marc' dates
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}dateIssued[@type="marc"]')
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}dateCreated[@type="marc"]')
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}copyrightDate[@type="marc"]')

        # if it exists, get the remaining dateIssued (presumably from 260$c) and change it to dateOther@type='260c'
        dateIssued_260c = mods.xpath('/mods:mods/mods:originInfo/mods:dateIssued', namespaces=drlutils.config.MODS_NS_MAP)
        if dateIssued_260c:
            date_260c = dateIssued_260c[0].text
            dateOther260c = etree.Element(drlutils.config.MODS + 'dateOther', type="260c")
            dateOther260c.text = date_260c
            originInfo.append(dateOther260c)
            # and, if the date from the 008 is None or isn't a normalzied date, try falling back to the 260c date
            if not date_iso8601 or not drlutils.date.utils.is_normalized_date(date_iso8601):
                date_iso8601 = date_260c

        # remove last pre-existing dateIssued
        etree.strip_elements(mods, '{http://www.loc.gov/mods/v3}dateIssued')

        # use the iso8601 value to populate dateIssued@encoding='iso8601' 
        originInfo = mods.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        dateIssued = etree.Element(drlutils.config.MODS + 'dateIssued', encoding="iso8601", keyDate="yes")
        dateIssued.text = date_iso8601 
        if qualifier:
            dateIssued.attrib['qualifier'] = qualifier
        originInfo.append(dateIssued)

    if not drlutils.date.utils.is_normalized_date(date_iso8601):
        print 'WARNING: Item %s has bad iso8601 date: %s' % (do_id, date_iso8601)

    # only generate these other dates if we have a value in date_iso8601
    if date_iso8601:
        # create the dateOther@type='display'
        dateOtherDisplay = etree.Element(drlutils.config.MODS + 'dateOther', type="display")
        if qualifier:
            questionable = True
        else:
            questionable = False
        dateOtherDisplay.text = drlutils.date.utils.get_display_date(date_iso8601, questionable) 
        originInfo.append(dateOtherDisplay)

        # create a dateOther@type='sort'
        dateOtherSort = etree.Element(drlutils.config.MODS + 'dateOther', type="sort")
        dateOtherSort.text = drlutils.date.utils.get_sort_date(date_iso8601) 
        originInfo.append(dateOtherSort)

    # set up repository path
    item = drlutils.django.utils.get_item(do_id) 
    repository_path = drlutils.django.utils.get_repository_path(item)

    # check if item already exists in repository
    if not os.path.exists(repository_path):
        return item.do_id + ' doesn\'t exist in repository - skipping'
    mods_file = item.do_id + '.mods.xml'
    mods_path = os.path.join(repository_path, mods_file)
    etree.ElementTree(mods.getroot()).write(mods_path, pretty_print=True)
    drlutils.django.utils.add_file_record(item, mods_path, 'TEXT_XML', 'MODS')
    return None

