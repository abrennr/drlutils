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
	except Exception as e:
		return 'problem with bodybuilder prep: ' + do_id + ': '  + str(e)
	bodybuilder_dest = os.path.join(drlutils.config.BODYBUILDER_PATH, item.do_id)
	if os.path.exists(bodybuilder_dest):
		shutil.rmtree(bodybuilder_dest)
	try:
		os.mkdir(bodybuilder_dest)
		files = drlutils.django.utils.get_master_file_list(item) 
		for file in files:
			shutil.copy(file, bodybuilder_dest) 
			jpg_source = os.path.join(bodybuilder_dest, os.path.basename(file))	
			jpg_file = drlutils.image.utils.encode_jpg(jpg_source, size='850')
			if not os.path.exists(jpg_file):
				return '%s - %s - not created properly -- check the master file %s for corruption' % (item.do_id, jpg_file, file.name)
			os.remove(jpg_source)
			if 'thumb' in jpg_file:
 				fix_name = jpg_file.replace('thumb.', '')
				shutil.move(jpg_file, fix_name)	
				jpg_file = fix_name
	except Exception as e:
		return item.do_id + ' problem: ' + str(e)

if __name__ == '__main__':
        try:
                do_id = sys.argv[1]
        except:
                sys.exit('when running as a script, you must provide a digital object id as an argument')
        item = drlutils.django.utils.get_item(do_id)
        user = drlutils.django.utils.get_user('gort')
        action = drlutils.django.utils.get_action('prep for bodybuilder')
        result = bodybuilder_prep(item.do_id)
        if result:
                print result
        else:
                drlutils.django.utils.update_item_status(item, action, user, 'True')

