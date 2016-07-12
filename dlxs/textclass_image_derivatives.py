import sys
import os
import shutil
import subprocess
import re
import drlutils.dlxs.textclass_xml
import drlutils.django.utils
import drlutils.collection_building.utils
import drlutils.config


def build(collection_item):
    try:
        item = collection_item.item 
        collection = collection_item.collection
        item_dest = os.path.join(drlutils.config.DLXS_OBJ_PATH, collection.c_id, item.do_id)
        if os.path.exists(item_dest):
            shutil.rmtree(item_dest)
        os.makedirs(item_dest)
        # copy jp2s out of repository
        jp2_result = drlutils.collection_building.utils.get_jp2_for_dlxs(collection_item)
        if jp2_result:
            raise Exception(jp2_result)
        pageview_dict_file = item.do_id + '.pageview_dict.txt'
        pageview_path = os.path.join(item_dest, pageview_dict_file)
        pageview = open(pageview_path, 'w')
        files = drlutils.django.utils.get_master_file_list(item) 
        for file in files:
            file_name = os.path.basename(file)
            jp2_filename = file_name.replace('.tif', '.jp2') 
            pageview.write('\t'.join([file_name, jp2_filename]) + '\n')
        pageview.close()
        return None
    except Exception as e:
        return collection_item.item.do_id + ' problem: ' + str(e)

