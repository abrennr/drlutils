import sys
import os
import shutil
import subprocess
import drlutils.django.utils
import drlutils.config

def create(do_id, c_id):
	try:
		item = drlutils.django.utils.get_item(do_id) 
		zoomify_root = os.path.join(drlutils.config.DLXS_IMAGE_PATH, c_id, 'zoomify')
		jp2_root = os.path.join(drlutils.config.DLXS_IMAGE_PATH, c_id, 'jp2')
		for path in [jp2_root, zoomify_root]:
			if not os.path.exists(path):
				os.makedirs(path)
		files = drlutils.django.utils.get_master_file_list(item) 
		for file in files:
			shutil.copy(file, zoomify_root) 
			zoomify_source = os.path.join(zoomify_root, os.path.basename(file))	
			zoomify_final = os.path.join(zoomify_root, do_id)	
			zoomify_result = subprocess.Popen([drlutils.config.ZOOMIFY_ENCODER, zoomify_source], stdout=subprocess.PIPE).communicate()[0].strip()
			os.remove(zoomify_source)
			if not os.path.exists(zoomify_result):
				return do_id + ' - ' + zoomify_result + ' not created properly.\n'
			jp2_filename = os.path.basename(file).replace('.tif', '.jp2')
			jp2_filepath = os.path.join(jp2_root, jp2_filename)
			shutil.copy(drlutils.config.DUMMY_JP2, jp2_filepath)
	except Exception as e:
		return do_id + ' - problem: ' + str(e)

