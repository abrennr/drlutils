import sys
import os
import shutil
import time
import re
import zipfile
import glob
import subprocess
import drlutils.django.utils
import drlutils.config


def ocr_complete(dir, last_file=None, minutes=0):
	time.sleep(60)
	tifs = glob.glob(dir + '/*.tif')
	tifs.sort()
	for file in tifs: 
		ocr_file = re.sub('.tif$', '.txt', file)
		if not os.path.exists(ocr_file):
			# if we're still waiting for the same file, increment time counter
			if (last_file and last_file == file):
				# if we cross the five minute threshold, exit with a false return
				if minutes > 15:
					raise Exception(file)	
				minutes = minutes + 1 
			else:
				minutes = 0
			# recurse here.  If the recursion returns false (which would be because
			# of timing out, pass the false return back up the call chain
			if not (ocr_complete(dir, file, minutes)):
				return False	
	# when we've found all ocr files and not timed out...
	return True 

def ocr(do_id):
	try:
		item = drlutils.django.utils.get_item(do_id) 
	except Exception as e:
		return 'problem with ocr: ' + do_id + ': '  + str(e)
	ocr_predest = os.path.join(drlutils.config.OCR_PREPROCESS_PATH, item.do_id)
	ocr_dest = os.path.join(drlutils.config.OCR_PATH, item.do_id)
	if os.path.exists(ocr_predest):
		shutil.rmtree(ocr_predest)
	if os.path.exists(ocr_dest):
		shutil.rmtree(ocr_dest)
	try:
		os.mkdir(ocr_predest)
		files = drlutils.django.utils.get_master_file_list(item) 
		for file in files:
			shutil.copy(file, ocr_predest) 
		for image in glob.glob(os.path.join(ocr_predest, '*')):
			subprocess.call([drlutils.config.GM, 'mogrify', '-threshold', '55%', '-compress', 'Group4', image])
		shutil.move(ocr_predest, drlutils.config.OCR_PATH)
		try:
			ocr_complete(ocr_dest, files)
		except Exception as e:
			shutil.rmtree(ocr_dest)
			raise Exception('OCR aborted: wait time exceeded 15 minutes for a single page: ' + str(e))
		# zip the files and move them to the item's repository directory
		repo_path = drlutils.django.utils.get_repository_path(item)
		zip_filename = item.do_id + '.ocr.zip'
		zip_filepath = os.path.join(repo_path, zip_filename)
		zip = zipfile.ZipFile(zip_filepath, 'w')
		for file in files:
			ocr_filename = re.sub('.tif', '.txt', os.path.basename(file))
			ocr_filepath = os.path.join(ocr_dest, ocr_filename)
			zip.write(ocr_filepath, os.path.basename(ocr_filepath))
		zip.close()
		drlutils.django.utils.add_file_record(item, zip_filepath, 'APPLICATION_ZIP', 'OCR_ZIP')
		shutil.rmtree(ocr_dest)
		return None
	except Exception as e:
		return item.do_id + ' problem: ' + str(e)

if __name__ == '__main__':
        try:
                do_id = sys.argv[1]
        except:
                sys.exit('when running as a script, you must provide a digital object id as an argument')
        item = drlutils.django.utils.get_item(do_id) 
        user = drlutils.django.utils.get_user('gort')
        action = drlutils.django.utils.get_action('ocr')
        result = ocr(item.do_id)
        if result:
                print result
        else:
                drlutils.django.utils.update_item_status(item, action, user, 'True')

