import sys
import os
import shutil
import drlutils.django.utils
import drlutils.config


def remove_item_file(i_f):
    try:
        os.remove(i_f.path)
        i_f.delete()
        return 
    except Exception as e:
        return 'file %s - problem %s' % (i_f.path, str(e))

def add_marcxml_file(do_id):
    item = drlutils.django.utils.get_item(do_id) 
    # item must be the right type
    if item.type.name not in ['text - cataloged', 'newspaper - cataloged']:
        return '%s not cataloged text' % (do_id,)
    repository_path = drlutils.django.utils.get_repository_path(item)
    # item's repository path must exist
    if not os.path.exists(repository_path):
        return '%s not found' % (repository_path,)
    try:
        marcxml_file = item.voyager_id + '.marcxml.xml'
        marcxml_source = os.path.join(drlutils.config.MARCXML_PATH, marcxml_file)
        marcxml_dest_path = os.path.join(repository_path, marcxml_file)
        # don't clobber existing file
        if os.path.exists(marcxml_dest_path):
            return
        shutil.copy(marcxml_source, marcxml_dest_path)
        drlutils.django.utils.add_file_record(item, marcxml_dest_path, 'TEXT_XML', 'MARCXML')
    except Exception as e:
        return 'Exeception caught: %s' % (str(e),)

def check_for_master_images(item):
    actions = drlutils.django.utils.get_item_actions(item) 
    this_actions = {} 
    for a in actions:
        this_actions[a.action.name] = a.complete
    if 'scan' in this_actions.keys():
        if not this_actions['scan']:
            return True
    elif 'release online ' in this_actions.keys():
        if not this_actions['release_online']:
            return True
    masters = drlutils.django.utils.get_master_file_list(item) 
    if len(masters) < 1:
        return False
    else:
        return True

def check_for_mets(item):
    mets = drlutils.django.utils.get_mets_path(item) 
    if mets:
        return True
    else:
        return False

def check_for_dc(item):
    dc = drlutils.django.utils.get_dc_path(item) 
    if dc:
        return True
    else:
        return False

def check_for_marcxml(item):
    marcxml = drlutils.django.utils.get_marcxml_path(item) 
    if marcxml:
        return True
    else:
        return False

def check_for_mods(item):
    mods = drlutils.django.utils.get_mods_path(item) 
    if mods:
        return True
    else:
        return False

def check_for_ocr(item):
    ocr_zip = drlutils.django.utils.get_ocr_zip_path(item) 
    if ocr_zip:
        return True
    else:
        return False

def check_for_thumb(item):
    thumb = drlutils.django.utils.get_thumb_path(item) 
    if thumb:
        return True
    else:
        return False

def check_for_voyager_id(item):
    if item.local_item.voyager_id: 
        return True
    else:
        return False

def check_for_copyright(item):
    if item.local_item.copyright_status: 
        return True
    else:
        return False

def check_for_ead_id(item):
    if item.local_item.ead_id: 
        return True
    else:
        return False

def validate_baseline_item(item):
    errors = []
    if not check_for_mods(item):
        errors.append('Missing MODS')
    if not check_for_dc(item):
        errors.append('Missing DC')
    if not check_for_thumb(item):
        errors.append('Missing thumbnail')
    if len(errors) > 0:
        return " / ".join(errors) 


def validate_cataloged_text(item):
    errors = []
    if not check_for_marcxml(item):
        errors.append('Missing MARCXML')
    if not check_for_mods(item):
        errors.append('Missing MODS')
    if not check_for_mets(item):
        errors.append('Missing METS')
    if not check_for_ocr(item):
        errors.append('Missing OCR')
    if not check_for_master_images(item):
        errors.append('Missing master images')
    if not check_for_voyager_id(item):
        errors.append('Missing voyager id')
    if not check_for_copyright(item):
        errors.append('Missing copyright')
    if len(errors) > 0:
        return " / ".join(errors) 

def validate_uncataloged_text(item):
    errors = []
    if not check_for_mods(item):
        errors.append('Missing MODS')
    if not check_for_mets(item):
        errors.append('Missing METS')
    if not check_for_ocr(item):
        errors.append('Missing OCR')
    if not check_for_master_images(item):
        errors.append('Missing master images')
    if len(errors) > 0:
        return " / ".join(errors) 

def validate_image(item):
    errors = []
    baseline = validate_baseline_item(item)
    if baseline:
        errors.append(baseline)
    if not check_for_thumb(item):
        errors.append('Missing thumbnail')
    if not check_for_master_images(item):
        errors.append('Missing master images')
    if len(errors) > 0:
        return " / ".join(errors) 


def validate_manuscript(item):
    errors = []
    if not check_for_mods(item):
        errors.append('Missing MODS')
    if not check_for_mets(item):
        errors.append('Missing METS')
    if not check_for_master_images(item):
        errors.append('Missing master images')
    if not check_for_ead_id(item):
        errors.append('Missing ead id')
    if len(errors) > 0:
        return " / ".join(errors) 

def validate_map(item):
    errors = []
    if not check_for_thumb(item):
        errors.append('Missing thumbnail')
    if not check_for_master_images(item):
        errors.append('Missing master images')
    if len(errors) > 0:
        return " / ".join(errors) 

