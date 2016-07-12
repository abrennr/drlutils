import os
import subprocess
import drlutils.django.utils 
import drlutils.config

def create_item_fits(item):
    masters = drlutils.django.utils.get_master_file_list(item)
    for file in masters:
        create(item, file)        


def create(item, file):
    repo_dir = drlutils.django.utils.get_repository_path(item)
    dest_filename = '%s.fits.xml' % (os.path.basename(file),) 
    dest_path = os.path.join(repo_dir, dest_filename)
    subprocess.call([drlutils.config.FITS_UTILITY, '-i', file, '-o', dest_path])
    drlutils.django.utils.add_file_record(item, dest_path, 'TEXT_XML', 'FITS')
