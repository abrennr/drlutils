import sys
import os
import subprocess
import re
import shutil
import drlutils.django.utils 
import drlutils.image.utils 

def name_thumb_file_by_item(file_path, item, large=False):
    (f_path, f_name) = os.path.split(file_path)
    if large:
        f_name = '%s.thumb_large.png' % (item.do_id,)
    else:
        f_name = '%s.thumb.png' % (item.do_id,)
    new_file_path = os.path.join(f_path, f_name)
    shutil.move(file_path, new_file_path)
    return new_file_path
     

def create(do_id, size='250', clobber=False, type='summary', large=False, file_use='THUMB'):
    try:
        item = drlutils.django.utils.get_item(do_id)
        files = drlutils.django.utils.get_master_file_list(item) 
        if len(files) < 1:
            raise Exception('no master files found.')
        if type == 'summary':
            if item.thumb_filename:
                repo_path = drlutils.django.utils.get_repository_path(item)
                file = os.path.join(repo_path, item.thumb_filename) 
                files = [file]
            else:
                files = files[0:1]
                item.thumb_filename = os.path.basename(files[0])
                item.save()
        for file in files:
            if large:
                size = '500'
                encode_large(item, file, size, clobber)
            else:
                encode(item, file, size, clobber, file_use, type)
    except Exception as e:
        return '%s - problem: %s' % (do_id, e)

def encode(item, file, size, clobber=False, file_use='THUMB', type='summary'):
    thumb_file = drlutils.image.utils.encode_thumb(file, size=size, clobber=clobber) 
    if os.path.exists(thumb_file):
        if type == 'summary':
            t_path = name_thumb_file_by_item(thumb_file, item, large=False)
        else:
            t_path = thumb_file
        result = drlutils.django.utils.add_file_record(item, t_path, 'IMAGE_PNG', file_use)
        if result:    
            return '%s - error adding thumb file record to database: %s\n' % (item.do_id, result)
    else:
        return '%s -  %s not created properly.\n' % (item.do_id, thumb_file)

def encode_large(item, file, size='500', clobber=False):
    thumb_file = drlutils.image.utils.encode_thumb(file, size=size, clobber=False, desc='thumb_large', fixed_width=True) 
    if os.path.exists(thumb_file):
        t_path = name_thumb_file_by_item(thumb_file, item, large=True)
        result = drlutils.django.utils.add_file_record(item, t_path, 'IMAGE_PNG', 'THUMB_LARGE')
        if result:    
            return '%s - error adding thumb file record to database: %s\n' % (item.do_id, result)
    else:
        return '%s -  %s not created properly.\n' % (item.do_id, thumb_file)

if __name__ == '__main__':
    print create(sys.argv[1])
    
