import sys
import os
import shutil
import datetime
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import drlutils.django.utils
import drlutils.repository.item
import drlutils.preservation.fits
import drlutils.image.thumbnail
import drlutils.image.jp2
import drlutils.config


def validate_directory_files(dir, type):
    errors = []
    all_files = os.listdir(dir)
    if len(all_files) == 0:
        return 'no files in directory'
    for file in all_files:
        if not file.endswith(('.tif', '.jpg', '.pdf', '.png', '.mods.xml', '.mets.xml', '.ocr.zip', '.marcxml.xml', '.body.xml', '.dc.xml')):
            errors.append('invalid file found : "' + file + '"')
    if len(errors) > 0:
        return '\n'.join(errors)
    else:
        return None

def handle_image_type_files(item):
    batch = workflow.core.models.Batch.objects.filter(batch_item__item=item).latest('date')
    delivery_batch =  os.path.join(drlutils.config.DELIVERY_PATH, batch.name)
    if not os.path.exists(delivery_batch):
        return item.do_id +' missing batch directory in delivery.  Expecting: ' + delivery_batch
    # lowercase image filenames if needed
    for f in os.listdir(delivery_batch):
        if f.islower() or f.isdigit():
            pass
        else:
            lower = f.lower()
            shutil.move(os.path.join(delivery_batch, f), os.path.join(delivery_batch, lower))
    delivery_item = os.path.join(drlutils.config.DELIVERY_PATH, item.do_id) 
    if os.path.exists(delivery_item):
        if os.listdir(delivery_item):
            return item.do_id +' non-empty item directory found. Don\'t want to clobber ' + delivery_item
        else:
            os.rmdir(delivery_item)
    os.mkdir(delivery_item)
    delivery_files = []    
    target_files = []    
    item_file_set = workflow.core.models.Item_File.objects.filter(item=item, use='MASTER')
    if len(item_file_set) == 0:
        return item.do_id + ' - image item type, but no files associated!?'
    # get expected paths for all assocaited files, check for existence
    for i_f in item_file_set:
        delivery_file = os.path.join(drlutils.config.DELIVERY_PATH, batch.name, i_f.name)
        if not os.path.exists(delivery_file):
            return item.do_id +' missing file(s) in delivery.  Expecting: ' + delivery_file
        else:
            delivery_files.append(delivery_file)
        file_ext = os.path.splitext(i_f.name)[1]
        if not file_ext:
            continue
        target_name = i_f.name.replace(file_ext, '_target' + file_ext)
        target_file = os.path.join(drlutils.config.DELIVERY_PATH, batch.name, target_name)
        if os.path.exists(target_file):
            target_files.append(target_file)
    for f in delivery_files:
        shutil.move(f, delivery_item)
    for t in target_files:
        shutil.move(t, '%s/target.tif' % (delivery_item,))
    return

def ingest(do_id):
    try:
        item = workflow.core.models.Item.objects.get(do_id=do_id)
    except Exception as e:
        return 'problem ingesting ' + do_id + ': ' + str(e)

    # image-like items are delivered in a batch directory.
    # handle them here to be in a directory named by id
    if item.type.name in ['image', 'map']:
        image_errors = handle_image_type_files(item)        
        if image_errors:
            return item.do_id + ' - ' + image_errors + ' - skipping'

    delivery_item = os.path.join(drlutils.config.DELIVERY_PATH, item.do_id)

    # check that item exists
    if not os.path.exists(delivery_item):
        return item.do_id +' not found in delivery at ' + delivery_item 

    # make sure directory contains only what we want
    file_errors = validate_directory_files(delivery_item, item.type.name)
    if file_errors:
        return item.do_id + ' - ' + file_errors
    
    # set up repository directory and initialize with appropriate files
    repository_path = drlutils.django.utils.get_repository_path(item) 
    if not os.path.exists(repository_path):
        result = drlutils.repository.item.initialize(item.do_id)
        if result:
            return item.do_id + ' - repository setup error - ' + result

    # check if master images already exist in repository
    try:
        existing_masters = workflow.core.models.Item_File.objects.filter(item=item, use='MASTER', path__isnull=False)
        if len(existing_masters) > 0:
            return item.do_id + ' ' + str(len(existing_masters))  + ' master files already exist in repository'
    except:
        pass

    # copy files from delivery to repository
    try:
        all_files = os.listdir(delivery_item)
        for file in all_files:
            source_file = os.path.join(delivery_item, file)
            shutil.copy(source_file, repository_path)
            dest_file = os.path.join(repository_path, file)
            if os.path.basename(file) == 'target.tif':
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_TIFF', 'TARGET')
            elif file.endswith('.tif'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_TIFF', 'MASTER')
            elif file.endswith('thumb_large.jpg'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_JPEG', 'THUMB_LARGE')
            elif file.endswith('thumb_large.png'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_PNG', 'THUMB_LARGE')
            elif file.endswith('thumb.jpg'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_JPEG', 'THUMB')
            elif file.endswith('thumb.png'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_PNG', 'THUMB')
            # if we've gotten past the thumb jpegs at this point, assume a jpg is a master
            elif file.endswith('.jpg'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_JPEG', 'MASTER')
            elif file.endswith('.marcxml.xml'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'TEXT_XML', 'MARCXML')
            elif file.endswith('.mods.xml'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'TEXT_XML', 'MODS')
            elif file.endswith('.mets.xml'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'TEXT_XML', 'METS')
            elif file.endswith('.fits.xml'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'TEXT_XML', 'FITS')
            elif file.endswith('.dc.xml'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'TEXT_XML', 'DC')
            elif file.endswith('.pdf'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'APPLICATION_PDF', 'PDF')
            elif file.endswith('.ocr.zip'):
                result = drlutils.django.utils.add_file_record(item, dest_file, 'APPLICATION_ZIP', 'OCR_ZIP')
            if result:
                return item.do_id + ' - error adding files: ' + result
    except Exception as e:
        return item.do_id + ' - error copying to files: ' + str(e)
    

    # create fits records for master images
    try:
        drlutils.preservation.fits.create_item_fits(item)
    except Exception as e:
        return item.do_id + ' - error creating Fits: ' + str(e)
        
    # create jp2 derivatives for master images
    try:
        error = drlutils.image.jp2.add_to_repo(item.do_id)
        if error:
            return item.do_id + ' - error creating jp2 derivatives: ' + error
    except Exception as e:
        return item.do_id + ' - error creating jp2 derivatives: ' + str(e)

    # attempt to create a thumbnail
    try:
        drlutils.image.thumbnail.create(item.do_id)
        drlutils.image.thumbnail.create(item.do_id, large=True)
    except Exception as e:
        return item.do_id + ' - error creating thumbnails: ' + str(e)
        
    # upon successful copy, delete files from delivery 
    try:
        shutil.rmtree(delivery_item)
    except Exception as e:
        return item.do_id + ' - error removing files from delivery: ' + str(e)
    return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('when running as a script, you must provide a digital object id as an argument')
    do_id = sys.argv[1]
    item = drlutils.django.utils.get_item(do_id) 
    user = drlutils.django.utils.get_user('gort')
    action = drlutils.django.utils.get_action('ingest')
    result = ingest(item.do_id)    
    if result:
        print result
    else:
        drlutils.django.utils.update_item_status(item, action, user, 'True')
