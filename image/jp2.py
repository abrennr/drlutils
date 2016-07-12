import sys
import os
import shutil
import subprocess
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import drlutils.django.utils 
import drlutils.image.utils 
import drlutils.config


def create(do_id, c_id, clobber=True):
    """
    Creates jpeg2000 derivatives for staging into DLXS 
    """
    try:
        item = drlutils.django.utils.get_item(do_id) 
        jp2_dest = os.path.join(drlutils.config.DLXS_IMAGE_PATH, c_id, 'jp2')
        if not os.path.exists(jp2_dest):
            os.makedirs(jp2_dest)
        files = drlutils.django.utils.get_master_file_list(item) 
        for file in files:
            shutil.copy(file, jp2_dest) 
            jp2_source = os.path.join(jp2_dest, os.path.basename(file))    
            jp2_file = drlutils.image.utils.encode_jp2(jp2_source, clobber) 
            os.remove(jp2_source)
            if not os.path.exists(jp2_file):
                return item.do_id + ': ' + jp2_file + ' not created propery.'
    except Exception as e:
        return do_id + ' problem: ' + str(e)

def add_to_repo(do_id, clobber=False):
    """
    Create JP2s from master tiff files for an item, add to repository.
     
    Use different JP2 encoder script based on item type. 
    Check first to see if JP2 exists before creating.
    """
    try:
        item = drlutils.django.utils.get_item(do_id) 
        type = 'image'
        if item.type.name in ['text - cataloged', 'text - uncataloged', 'manuscript', 'newspaper - cataloged']:
            type = 'text' 
        jp2_dest = drlutils.django.utils.get_repository_path(item) 
        if not os.path.exists(jp2_dest):
            return '%s - repository directory not found at %s - skipping' % (do_id, jp2_dest)
        files = drlutils.django.utils.get_master_file_list(item) 
        for file in files:
            jp2_file = drlutils.image.utils.encode_jp2(file, clobber=clobber, type=type) 
            if not os.path.exists(jp2_file):
                return item.do_id + ': ' + jp2_file + ' not created propery.'
            drlutils.django.utils.add_file_record(item, jp2_file, 'IMAGE_JP2', 'JP2')
    except Exception as e:
        return '%s problem: %s' % (do_id, str(e))

if __name__ == '__main__':
        try:
                do_id = sys.argv[1]
        except:
                sys.exit('when running as a script, you must provide a digital object id as an argument')
        item = drlutils.django.utils.get_item(do_id) 
        user = drlutils.django.utils.get_user('gort')
        action = drlutils.django.utils.get_action('make jpg2000')
        result = create(item.do_id)
        if result:
                print result
        else:
                drlutils.django.utils.update_item_status(item, action, user, 'True')

