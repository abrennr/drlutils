from lxml import etree
import drlutils.config

def get_parsed_mods(mods_xml_file):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(open(mods_xml_file, 'r'), parser)

def set_root():
    root = etree.Element(drlutils.config.MODS + 'mods', nsmap=drlutils.config.MODS_NS_MAP)
    root.set(drlutils.config.XSI + 'schemaLocation', 'http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-4.xsd http://www.cdlib.org/inside/diglib/copyrightMD http://www.cdlib.org/groups/rmg/docs/copyrightMD.xsd')
    originInfo = etree.Element(drlutils.config.MODS + 'originInfo')
    root.append(originInfo)
    accessCondition = etree.Element(drlutils.config.MODS + 'accessCondition')
    copyright = etree.Element(drlutils.config.COPYRIGHTMD + 'copyright')
    copyright.attrib['copyright.status'] = 'unknown'
    copyright.attrib['publication.status'] = 'unknown'
    accessCondition.append(copyright)
    root.append(accessCondition)
    return root

def get_address(mods_xml):
    try:
        values = []
        for e in mods_xml.xpath('/mods:mods/mods:note[@type="address"]', namespaces=drlutils.config.MODS_NS_MAP):
            values.append(e.text)
        return ', '.join(value)
    except:
        return ''

def set_address(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        address = etree.Element(drlutils.config.MODS + 'note', type="address")
        address.text = value 
        root.append(address)
    return mods_xml

def set_contributor(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        name = etree.Element(drlutils.config.MODS + 'name')
        namePart = etree.Element(drlutils.config.MODS + 'namePart')
        namePart.text = value
        name.append(namePart)
        role = etree.Element(drlutils.config.MODS + 'role')
        roleTerm = etree.Element(drlutils.config.MODS + 'roleTerm', type="text")
        roleTerm.text = 'contributor'
        role.append(roleTerm)
        name.append(role)
        root.append(name)
    return mods_xml

def get_copyright_status(mods_xml):
    try:
        e = mods_xml.xpath('/mods:mods/mods:accessCondition/copyrightMD:copyright', namespaces=drlutils.config.MODS_NS_MAP)[0]
        return e.get('copyright.status')
    except:
        return ''

def set_copyright_status(value, mods_xml):
    copyright = mods_xml.xpath('/mods:mods/mods:accessCondition/copyrightMD:copyright', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    copyright.attrib['copyright.status'] = value
    return mods_xml

def set_creator(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        name = etree.Element(drlutils.config.MODS + 'name')
        namePart = etree.Element(drlutils.config.MODS + 'namePart')
        namePart.text = value
        name.append(namePart)
        role = etree.Element(drlutils.config.MODS + 'role')
        roleTerm = etree.Element(drlutils.config.MODS + 'roleTerm', type="text")
        roleTerm.text = 'creator'
        role.append(roleTerm)
        name.append(role)
        root.append(name)
    return mods_xml

def set_date(value, mods_xml):
    originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
    dateOther = etree.Element(drlutils.config.MODS + 'dateOther', type="display")
    dateOther.text = value 
    originInfo.append(dateOther)
    return mods_xml

def set_date_digitized(value, mods_xml):
    if value:
        originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        dateCaptured = etree.Element(drlutils.config.MODS + 'dateCaptured')
        dateOther.text = value 
        originInfo.append(dateCaptured)
    return mods_xml

def set_depositor(value, mods_xml):
    root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
    name = etree.Element(drlutils.config.MODS + 'name')
    namePart = etree.Element(drlutils.config.MODS + 'namePart')
    namePart.text = value
    name.append(namePart)
    role = etree.Element(drlutils.config.MODS + 'role')
    roleTerm = etree.Element(drlutils.config.MODS + 'roleTerm', type="text")
    roleTerm.text = 'depositor'
    role.append(roleTerm)
    name.append(role)
    root.append(name)
    return mods_xml

def set_description(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        description = etree.Element(drlutils.config.MODS + 'abstract')
        description.text = value 
        root.append(description)
    return mods_xml

def set_dimension(value, mods_xml):
    try:
        physicalDescription = mods_xml.xpath('/mods:mods/mods:physicalDescription[1]', namespaces=drlutils.config.MODS_NS_MAP)[0]
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        physicalDescription = etree.Element(drlutils.config.MODS + 'physicalDescription')
        root.append(physicalDescription)
    extent = etree.Element(drlutils.config.MODS + 'extent')
    extent.text = value 
    physicalDescription.append(extent)
    return mods_xml

def set_format(value, mods_xml):
    try:
        physicalDescription = mods_xml.xpath('/mods:mods/mods:physicalDescription[1]', namespaces=drlutils.config.MODS_NS_MAP)[0]
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        physicalDescription = etree.Element(drlutils.config.MODS + 'physicalDescription')
        root.append(physicalDescription)
    form = etree.Element(drlutils.config.MODS + 'form')
    form.text = value 
    physicalDescription.append(form)
    return mods_xml

def set_genre(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        genre = etree.Element(drlutils.config.MODS + 'genre')
        genre.text = value 
        root.append(genre)
    return mods_xml


def set_gift_of(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        gift_of = etree.Element(drlutils.config.MODS + 'note', type="donor")
        gift_of.text = value 
        root.append(gift_of)
    return mods_xml

def set_identifier(value, mods_xml):
    root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
    identifier = etree.Element(drlutils.config.MODS + 'identifier', type="pitt")
    identifier.text = value 
    root.append(identifier)
    return mods_xml


def set_pub_place(value, mods_xml):
    if value:
        originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        place = etree.Element(drlutils.config.MODS + 'place')
        placeTerm = etree.Element(drlutils.config.MODS + 'placeTerm', type="text")
        placeTerm.text = value
        place.append(placeTerm)
        originInfo.append(place)
    return mods_xml

def get_normalized_date(mods_xml):
    date = ''
    try:
        date = mods_xml.xpath('/mods:mods/mods:originInfo/mods:dateCreated[@keyDate="yes"]', namespaces=drlutils.config.MODS_NS_MAP)[0].text
    except:
        pass
    try:
        date = mods_xml.xpath('/mods:mods/mods:originInfo/mods:dateIssued[@keyDate="yes"]', namespaces=drlutils.config.MODS_NS_MAP)[0].text
    except:
        pass
    return date

def set_normalized_date(value, mods_xml):
    if value:
        originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        dateCreated = etree.Element(drlutils.config.MODS + 'dateCreated', encoding="iso8601", keyDate="yes")
        dateCreated.text = value
        originInfo.append(dateCreated)
    return mods_xml

def set_normalized_date_qualifier(value, mods_xml):
    # TODO handle if dateCreated doesn't already exist
    if value:
        normalized_date = mods_xml.xpath('/mods:mods/mods:originInfo/mods:dateCreated', namespaces=drlutils.config.MODS_NS_MAP)[0] 
        normalized_date.attrib['qualifier'] = 'approximate'
    return mods_xml

def get_publication_status(mods_xml):
    try:
        e = mods_xml.xpath('/mods:mods/mods:accessCondition/copyrightMD:copyright', namespaces=drlutils.config.MODS_NS_MAP)[0]
        return e.get('publication.status')
    except:
        return ''

def set_publication_status(value, mods_xml):
    if value:
        copyright = mods_xml.xpath('/mods:mods/mods:accessCondition/copyrightMD:copyright', namespaces=drlutils.config.MODS_NS_MAP)[0] 
        copyright.attrib['publication.status'] = value
    return mods_xml

def set_publisher(value, mods_xml):
    if value:
        originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        publisher = etree.Element(drlutils.config.MODS + 'publisher')
        publisher.text = value
        originInfo.append(publisher)
    return mods_xml

def set_rights_holder(value, mods_xml):
    if value:
        copyright = mods_xml.xpath('/mods:mods/mods:accessCondition/copyrightMD:copyright', namespaces=drlutils.config.MODS_NS_MAP)[0] 
        rh = etree.Element(drlutils.config.COPYRIGHTMD + 'rights.holder')
        name = etree.Element(drlutils.config.COPYRIGHTMD + 'name')
        name.text = value 
        rh.append(name)
        copyright.append(rh)
    return mods_xml

def set_scale(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        subject = etree.Element(drlutils.config.MODS + 'subject')
        cartographics = etree.Element(drlutils.config.MODS + 'cartographics')
        scale = etree.Element(drlutils.config.MODS + 'scale')
        scale.text = value
        cartographics.append(scale)
        subject.append(cartographics)
        root.append(subject)
    return mods_xml
    

def set_sort_date(value, mods_xml):
    if value:
        originInfo = mods_xml.xpath('/mods:mods/mods:originInfo', namespaces=drlutils.config.MODS_NS_MAP)[0]
        dateCreated = etree.Element(drlutils.config.MODS + 'dateOther', type="sort")
        dateCreated.text = value
        originInfo.append(dateCreated)
    return mods_xml

def set_source_citation(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    citation = etree.Element(drlutils.config.MODS + 'note', type="prefercite")
    citation.text = value
    relatedItem.append(citation)
    return mods_xml

def set_source_collection(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    titleInfo = etree.Element(drlutils.config.MODS + 'titleInfo')
    title = etree.Element(drlutils.config.MODS + 'title')
    title.text = value
    titleInfo.append(title)
    relatedItem.append(titleInfo)
    return mods_xml
    
def set_source_collection_date(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    originInfo = etree.Element(drlutils.config.MODS + 'originInfo')
    date = etree.Element(drlutils.config.MODS + 'dateCreated')
    date.text = value
    originInfo.append(date)
    relatedItem.append(originInfo)
    return mods_xml
    
def set_source_collection_id(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    identifier = etree.Element(drlutils.config.MODS + 'identifier')
    identifier.text = value
    relatedItem.append(identifier)
    return mods_xml
    
def set_source_container(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    container = etree.Element(drlutils.config.MODS + 'note', type="container")
    container.text = value
    relatedItem.append(container)
    return mods_xml
    
def set_source_ownership(value, mods_xml):
    try:
        relatedItem = mods_xml.xpath('/mods:mods/mods:relatedItem[@type="host"]', namespaces=drlutils.config.MODS_NS_MAP)[0] 
    except:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        relatedItem = etree.Element(drlutils.config.MODS + 'relatedItem', type="host", displayLabel="source")
        root.append(relatedItem)
    ownership = etree.Element(drlutils.config.MODS + 'note', type="ownership")
    ownership.text = value
    relatedItem.append(ownership)
    return mods_xml

def set_source_id(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        local_id = etree.Element(drlutils.config.MODS + 'identifier', type="source")
        local_id.text = value 
        root.append(local_id)
    return mods_xml

def set_subject(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        these_subjects = value.split(';')
        for s in these_subjects:
            subject = etree.Element(drlutils.config.MODS + 'subject')
            these_topics = s.split('--')
            for t in these_topics:
                topic = etree.Element(drlutils.config.MODS + 'topic')
                topic.text = t.strip()
                subject.append(topic)
            root.append(subject)
    return mods_xml

def set_subject_lcsh(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        these_subjects = value.split(';')
        for s in these_subjects:
            subject = etree.Element(drlutils.config.MODS + 'subject', authority="lcsh")
            these_topics = s.split('--')
            for t in these_topics:
                topic = etree.Element(drlutils.config.MODS + 'topic')
                topic.text = t.strip()
                subject.append(topic)
            root.append(subject)
    return mods_xml

def set_subject_local(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        these_subjects = value.split(';')
        for s in these_subjects:
            subject = etree.Element(drlutils.config.MODS + 'subject', authority="local")
            these_topics = s.split('--')
            for t in these_topics:
                topic = etree.Element(drlutils.config.MODS + 'topic')
                topic.text = t.strip()
                subject.append(topic)
            root.append(subject)
    return mods_xml

def set_subject_location(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        these_subjects = value.split(';')
        for s in these_subjects:
            subject = etree.Element(drlutils.config.MODS + 'subject', authority="lcsh")
            these_topics = s.split('--')
            for t in these_topics:
                topic = etree.Element(drlutils.config.MODS + 'geographic')
                topic.text = t.strip()
                subject.append(topic)
            root.append(subject)
    return mods_xml

def get_title(mods_xml):
    try:
        e = mods_xml.xpath('/mods:mods/mods:titleInfo/mods:title', namespaces=drlutils.config.MODS_NS_MAP)[0]
        return e.text
    except:
        return ''

def set_title(value, mods_xml):
    # note: this is simplistic, without many optional subelements
    root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
    titleInfo = etree.Element(drlutils.config.MODS + 'titleInfo')
    title = etree.Element(drlutils.config.MODS + 'title')
    title.text = value 
    titleInfo.append(title)
    root.append(titleInfo)
    return mods_xml

def set_type_of_resource(value, mods_xml):
    if value:
        root = mods_xml.xpath('/mods:mods', namespaces=drlutils.config.MODS_NS_MAP)[0]
        typeOfResource = etree.Element(drlutils.config.MODS + 'typeOfResource')
        typeOfResource.text = value 
        root.append(typeOfResource)
    return mods_xml

