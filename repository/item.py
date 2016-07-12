import sys
import os
import shutil
import drlutils.django.utils 
import drlutils.repository.utils 
import drlutils.mods.marc2DrlMods
import drlutils.dublincore.mods2dc
import drlutils.config


def initialize(do_id):
    try:
        item = drlutils.django.utils.get_item(do_id) 
        repository_path = drlutils.django.utils.get_repository_path(item)
        if not os.path.exists(repository_path):
            os.makedirs(repository_path)
        msg = ingest_object_metadata(item)
        if msg:
            raise Exception(msg)
    except Exception as e:
        return do_id + ' - problem - ' + str(e)

def ingest_object_metadata(item):
    if item.type.name in  ['text - cataloged', 'newspaper - cataloged']:
        ingest_marcxml(item)
        msg = drlutils.mods.marc2DrlMods.create(item.do_id)
        if msg:
            return msg
        msg = drlutils.dublincore.mods2dc.create(item.do_id)
        if msg:
            return msg
    elif item.type.name in ['text - uncataloged', 'newspaper - uncataloged']:
        pass
    elif item.type.name == 'manuscript':
        ingest_manuscript_mods(item)
        msg = drlutils.dublincore.mods2dc.create(item.do_id)
        if msg:
            return msg
    elif item.type.name == 'georeferenced map':
        # can make FGDC, MODS, DC here
        pass
    elif item.type.name == 'image':
        # don't ususally have meaningful metadata at ingest 
        pass

def ingest_marcxml(item):
    repository_path = drlutils.django.utils.get_repository_path(item)
    marcxml_file = item.voyager_id + '.marcxml.xml'
    marcxml_source = os.path.join(drlutils.config.MARCXML_PATH, marcxml_file) 
    assert os.path.exists(marcxml_source)
    marcxml_dest_path = os.path.join(repository_path, marcxml_file)
    if os.path.exists(marcxml_dest_path):
        os.remove(marcxml_dest_path) 
    shutil.copy(marcxml_source, marcxml_dest_path)
    drlutils.django.utils.add_file_record(item, marcxml_dest_path, 'TEXT_XML', 'MARCXML')

def ingest_manuscript_mods(item):
    repository_path = drlutils.django.utils.get_repository_path(item)
    mods_filename = item.do_id + '.mods.xml'
    mods_source_path = os.path.join(drlutils.config.MODS_PATH, mods_filename)
    mods_dest_path = os.path.join(repository_path, mods_filename)
    if os.path.exists(mods_dest_path):
        os.remove(mods_dest_path) 
    shutil.copy(mods_source_path, mods_dest_path)
    drlutils.django.utils.add_file_record(item, mods_dest_path, 'TEXT_XML', 'MODS')

