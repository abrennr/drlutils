import sys
import os
import subprocess
import re
import shutil
import drlutils.django.utils 
import drlutils.image.utils 


def create(do_id, size='500', clobber=False, type='all', file_use='PAGE_THUMB'):
    try:
        item = drlutils.django.utils.get_item(do_id)
        files = drlutils.django.utils.get_master_file_list(item) 
        if len(files) < 1:
            raise Exception('no master files found.')
        for file in files:
            encode(item, file, size, clobber, file_use)
    except Exception as e:
        return '%s - problem: %s' % (do_id, e)

def encode(item, file, size, clobber=False, type='all'):
    thumb_file = drlutils.image.utils.encode_thumb_jpg(file, size=size, clobber=clobber) 
    if os.path.exists(thumb_file):
        t_path = thumb_file
        result = drlutils.django.utils.add_file_record(item, t_path, 'IMAGE_JPEG', file_use)
        if result:    
            return '%s - error adding thumb file record to database: %s\n' % (item.do_id, result)
    else:
        return '%s -  %s not created properly.\n' % (item.do_id, thumb_file)

if __name__ == '__main__':
    print create(sys.argv[1])
    
