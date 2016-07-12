import sys
import os
from lxml import etree
import drlutils.text.utils
import drlutils.config

def get_parsed_mets(mets_path):
    return etree.parse(open(mets_path, 'r'))

def get_page_label_dict(mets):
    """ Parse the METS structMap to get proper page label """
    labels = {}
    for file in mets.iter(drlutils.config.METS + 'file'):
        file_id = file.get('ID')
        file_name = file[0].get(drlutils.config.XLINK + 'href')
        xpath_string = '//mets:div[@TYPE="page"]/mets:fptr[@FILEID="%s"]' % (file_id,)
        fptr = mets.xpath(xpath_string, namespaces=drlutils.config.METS_NS_MAP)[0]
        label = fptr.getparent().get('LABEL')
        labels[file_name] = label
    return labels

def clean_page_labels(dict):
    """ Make page labels more display-friendly """
    cleaned_dict = {}
    for file in dict.keys():
        label = dict[file]
        if not label:
            label == 'unum'
        if label == 'unum':
            seq = str(int(os.path.splitext(file)[0]))
            cleaned_dict[file] = '[unnumbered page (%s)]' % (seq,)
        elif label.startswith('r0'):
            digit = int(label[1:4])
            roman = drlutils.text.utils.get_roman_numeral(digit)
            cleaned_dict[file] = 'Page %s' % (roman,)
        else:
            try:
                i = int(label)
                cleaned_dict[file] = 'Page %s' % (i,)
            except:
                cleaned_dict[file] = '[page %s]' % (label,)
    return cleaned_dict
