import sys
import os
import shutil
import subprocess
import drlutils.django.utils 
import drlutils.image.utils
import drlutils.config


def create(do_id):
    try:
        item = drlutils.django.utils.get_item(do_id)
        batch_name = drlutils.django.utils.get_batch_name(item) 
        # handle the csv part
        macrob_csv_dest = os.path.join(drlutils.config.MACROB_PATH, batch_name, 'csv')
        macrob_filename = item.do_id + '.macrob.txt'
        macrob_filepath = os.path.join(macrob_csv_dest, macrob_filename)
        if not os.path.exists(macrob_csv_dest):
            os.makedirs(macrob_csv_dest)
        outfile = open(macrob_filepath, 'w')
        outfile.write(drlutils.django.utils.get_macrob_csv(item.do_id))
        outfile.write('\n')
        # handle the thumbnail part
        macrob_thumb_dest = os.path.join(drlutils.config.MACROB_PATH, batch_name, 'thumb')
        if not os.path.exists(macrob_thumb_dest):
            os.makedirs(macrob_thumb_dest)
        thumb_repo_source = os.path.join(drlutils.django.utils.get_repository_path(item), item.thumb_filename)
        shutil.copy(thumb_repo_source, macrob_thumb_dest)
        thumb_encode_source = os.path.join(macrob_thumb_dest, item.thumb_filename)
        thumb_file = drlutils.image.utils.encode_jpg(thumb_encode_source, size='250', clobber=True)
        renamed_thumb = os.path.join(macrob_thumb_dest, (item.do_id + '.jpg'))
        os.remove(thumb_encode_source)
        os.rename(thumb_file, renamed_thumb) 

    except Exception as e:
        return do_id + ' problem: ' + str(e)
