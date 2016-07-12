import sys
import os
import shutil
import subprocess
import zipfile
import drlutils.django.utils
import drlutils.image.utils
import drlutils.config

def create(do_id, c_id, zip=False):
    try:
    	item = drlutils.django.utils.get_item(do_id)
    	jpg_dest = os.path.join(drlutils.config.DLXS_IMAGE_PATH, c_id, 'jpg')
    	if item.type.name not in ['image', 'map']:
            jpg_dest = os.path.join(drlutils.config.DLXS_IMAGE_PATH, c_id, 'jpg', do_id)
    	if not os.path.exists(jpg_dest):
    		os.makedirs(jpg_dest)
    	#if item.type.name == 'map':
    	#	zip = True
    	if zip: 
    		zip_filename = item.do_id + '.zip'
    		zip_filepath = os.path.join(jpg_dest, zip_filename) 
    		zip = zipfile.ZipFile(zip_filepath, 'w')
    	files = drlutils.django.utils.get_master_file_list(item) 
    	for file in files:
    		shutil.copy(file, jpg_dest) 
    		jpg_source = os.path.join(jpg_dest, os.path.basename(file))	
    		jpg_file = drlutils.image.utils.encode_jpg(jpg_source) 
    		os.remove(jpg_source)
    		if not os.path.exists(jpg_file):
    			return item.do_id + ': ' + jpg_file + ' not created propery.'
    		if zip:
    			zip.write(jpg_file, os.path.basename(jpg_file))
    	if zip:
    		os.remove(jpg_file)
    		zip.close()
    except Exception as e:
    	return do_id + ' problem: ' + str(e)


if __name__ == '__main__':
    	create(sys.argv[1], sys.argv[2])

