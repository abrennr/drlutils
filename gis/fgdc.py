import sys
import os
import drlutils.django.utils
from lxml import etree
from copy import deepcopy
import drlutils.config

def set_text_at_xpath(tree, xpath, text):
    x = tree.xpath(xpath)[0]
    x.text = text
    return tree

def create(do_id):
       
    geo_clip = drlutils.django.utils.get_map_sheet(do_id)

    # parse fgdc template 

    parser = etree.XMLParser(remove_blank_text=True)
    fgdc = etree.parse(open(drlutils.config.FGDC_TEMPLATE_FILE, 'r'), parser)
    
    # FGDC 1. Identification Information
    # Citation - GEOREFERENCED MAP SHEET IMAGE
    
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/pubdate[1]', geo_clip.date.isoformat())
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/title[1]', geo_clip.title)
    
    # Larger Work Citation - PAPER MAP SHEET
    
    text = geo_clip.map_sheet.volume.creator or geo_clip.map_sheet.creator
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/origin[1]', text)

    text = geo_clip.map_sheet.volume.date.isoformat() or geo_clip.map_sheet.pub_date.isoformat()
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubdate[1]', text)
    
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/title[1]', geo_clip.map_sheet.title)

    text = geo_clip.map_sheet.volume.pub_place or geo_clip.map_sheet.pub_place
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubinfo[1]/pubplace[1]', text)

    text = geo_clip.map_sheet.volume.publisher or geo_clip.map_sheet.publisher
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubinfo[1]/publish[1]', text)

    # Larger Work Citation - VOLUME (IF PRESENT)

    if (geo_clip.map_sheet.volume):
        fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/origin[1]', geo_clip.map_sheet.volume.creator)
        fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubdate[1]', geo_clip.map_sheet.volume.date.isoformat())
        fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/title[1]', geo_clip.map_sheet.volume.title)
        fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubinfo[1]/pubplace[1]', geo_clip.map_sheet.volume.pub_place)
        fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/citation[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/lworkcit[1]/citeinfo[1]/pubinfo[1]/publish[1]', geo_clip.map_sheet.volume.publisher)

    # FGDC 1.2 Description 

    text = geo_clip.map_sheet.collection.description or geo_clip.map_sheet.description
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/descript[1]/abstract[1]', text)

    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/descript[1]/purpose[1]', geo_clip.map_sheet.collection.map_purpose)

    text = geo_clip.map_sheet.volume.content_date or geo_clip.map_sheet.content_date
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/timeperd[1]/timeinfo[1]/sngdate[1]/caldate[1]', text)

    text = geo_clip.map_sheet.volume.content_current_ref or geo_clip.map_sheet.content_current_ref
    fgdc = set_text_at_xpath(fgdc, '/metadata/idinfo[1]/timeperd[1]/current[1]', text)

    # 1.6 Keywords
    # 1.6.1.2 Theme Keyword

    theme = fgdc.xpath('/metadata/idinfo[1]/keywords[1]/theme[1]')[0]    
    themekey = fgdc.xpath('/metadata/idinfo[1]/keywords[1]/theme[1]/themekey[1]')[0]    
    k = geo_clip.map_sheet.theme_keywords or geo_clip.map_sheet.collection.theme_keywords
    keywords = k.split(',')
    if len(keywords) > 0:
        theme.remove(themekey)
    for keyword in keywords:
        themekey = etree.Element('themekey')
        themekey.text = keyword.strip()
        theme.append(themekey)
    
    # 1.6.2.2 Place Keyword

    place = fgdc.xpath('/metadata/idinfo[1]/keywords[1]/place[1]')[0]    
    placekey = fgdc.xpath('/metadata/idinfo[1]/keywords[1]/place[1]/placekey[1]')[0]    
    place_fields = [geo_clip.map_sheet.place_keywords, geo_clip.map_sheet.municipality, geo_clip.map_sheet.streets, geo_clip.map_sheet.other_features, geo_clip.map_sheet.ward_name]
    for p in place_fields:
        if not p:
            place_fields.remove(p)
    placewordsstring = ','.join(place_fields)
    placewords = placewordsstring.split(',')
    if len(placewords) > 0:
        place.remove(placekey)
    for placeword in placewords:
        placekey = etree.Element('placekey')
        placekey.text = placeword.strip()
        place.append(placekey)

    # 2.5 Lineage
    # 2.5.1 Source Information -- PAPER MAP SHEET
    
    text = geo_clip.map_sheet.creator or geo_clip.map_sheet.volume.creator
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccite[1]/citeinfo[1]/origin[1]', text)

    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccite[1]/citeinfo[1]/pubdate[1]', geo_clip.map_sheet.date.isoformat())
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccite[1]/citeinfo[1]/title[1]', geo_clip.map_sheet.title)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccite[1]/citeinfo[1]/pubinfo[1]/pubplace[1]', geo_clip.map_sheet.pub_place)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccite[1]/citeinfo[1]/pubinfo[1]/publish[1]', geo_clip.map_sheet.publisher)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srcscale[1]', str(geo_clip.map_sheet.scale_den))
    
    text = geo_clip.map_sheet.content_date or geo_clip.map_sheet.volume.content_date
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srctime[1]/timeinfo[1]/sngdate[1]/caldate[1]', text)
    
    text = geo_clip.map_sheet.content_current_ref or geo_clip.map_sheet.volume.content_current_ref
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srctime[1]/srccurr[1]', text)
    
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[1]/srccitea[1]', geo_clip.map_sheet.title)

    # 2.5.1 Source Information -- DIGITAL MAP SHEET IMAGE

    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[2]/srccite[1]/citeinfo[1]/title[1]', geo_clip.map_sheet.filename)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[2]/srcscale[1]', str(geo_clip.map_sheet.scale_den))
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[2]/srccitea[1]', geo_clip.map_sheet.filename)

    # 2.5.1 Source Information -- REFERENCING LAYER DATASET

    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/origin[1]', geo_clip.reference_layer.creator)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/pubdate[1]', geo_clip.reference_layer.pub_date)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/title[1]', geo_clip.reference_layer.title)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/geoform[1]', geo_clip.reference_layer.data_present)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/pubinfo[1]/pubplace[1]', geo_clip.reference_layer.pub_place)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccite[1]/citeinfo[1]/pubinfo[1]/publish[1]', geo_clip.reference_layer.publisher)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srcscale[1]', str(geo_clip.reference_layer.scale_den))
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/typesrc[1]', geo_clip.reference_layer.source_media)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srctime[1]/timeinfo[1]/sngdate[1]/caldate[1]', geo_clip.reference_layer.content_date)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srctime[1]/srccurr[1]', geo_clip.reference_layer.content_current_ref)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/srcinfo[3]/srccitea[1]', geo_clip.reference_layer.citabbrev)
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/procstep[1]/srcused[1]', '%s %s' % (geo_clip.reference_layer.citabbrev, geo_clip.map_sheet.filename))
    fgdc = set_text_at_xpath(fgdc, '/metadata/dataqual[1]/lineage[1]/procstep[1]/procdate[1]', geo_clip.date.isoformat())
    
    # 7. Metadata Reference Information

    fgdc = set_text_at_xpath(fgdc, '/metadata/metainfo[1]/metd[1]', geo_clip.date.isoformat())

    # set up repository path
    repository_path = '/usr/local/dlxs/prep/t/test/fgdc'
    # check if item already exists in repository
    #if not os.path.exists(repository_path):
    #    return item.do_id + ' doesn\'t exist in repository - skipping'
    fgdc_file = do_id + '.fgdc.xml'
    fgdc_path = os.path.join(repository_path, fgdc_file)
    etree.ElementTree(fgdc.getroot()).write(fgdc_path, pretty_print=True)
    #drlutils.django.utils.add_file_record(item, fgdc_path, 'TEXT_XML', 'FGDC-XML')
    return None

