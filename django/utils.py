import sys
import re
import os
import ntpath 
import httplib
import json
import datetime
import shutil
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import workflow.core.status
import workflow.wflocal.models
import workflow.retrographer.models
import workflow.maps.models
import drlutils.messaging.utils
import drlutils.text.utils
import drlutils.config


def get_dlxs_image_config(c_id):
    rows = workflow.wflocal.models.Dlxs_Image_Config.objects.filter(collection__name=c_id)
    data = []
    for row in rows:
        data.append([row.name, row.abbreviation, row.metaname, row.admin_mapping])
    return data

def get_item(do_id):
    try:
        return workflow.wflocal.models.Local_Item.objects.get(do_id=do_id)
    except:
        return None

def get_item_actions(item):
    try:
        return workflow.core.models.Item_Actions_Status.objects.filter(item=item)
    except:
        return None

def get_action(name):
    try:
        return workflow.core.models.Action.objects.get(name=name)
    except:
        return None

def get_user(name):
    try:
        return workflow.core.models.User.objects.get(first_name=name)
    except:
        return None

def get_batch_name(item):
    return workflow.core.models.Batch.objects.get(batch_item__item=item).name

def get_batch_items(batch_name):
    batch = workflow.core.models.Batch.objects.get(name=batch_name)
    return workflow.core.models.Item.objects.filter(batch_item__batch=batch)

def get_collection(c_id):
    try:
        return workflow.core.models.Collection.objects.get(c_id=c_id)
    except:
        return None

def get_collection_items(c_id, primary=True):
    try:
        c = workflow.core.models.Collection.objects.get(c_id=c_id)
    except Exception as e:
        return 'problem getting collection: %s' % (e,)
    if primary:
        return workflow.wflocal.models.Local_Item.objects.filter(primary_collection=c)
    else:
        return workflow.wflocal.models.Local_Item.objects.filter(collection_item__collection=c)

def get_DRL_collection(c):
    try:
        return workflow.wflocal.models.DRL_Collection.objects.get(collection=c)
    except:
        return None

def get_source_collection(id):
    try:
        return workflow.wflocal.models.Source_Collection.objects.get(source_id=id)
    except:
        return None

def get_thumb_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use="THUMB").path
    except:
        return None

def get_retrographer_tag(photo_id):
    try:
        return workflow.retrographer.models.Tag.objects.filter(photo_id=photo_id, is_used=True).order_by('-timestamp')[0]
    except:
        return None

def get_map_sheet(do_id):
    try:
        return workflow.maps.models.Georeferenced_Map_Sheet.objects.get(do_id=do_id)
    except:
        return None

def delete_django_item(item_id):
    """Removes item from batch, collection_items table, and transactions.  Deletes repository and bodybuilder directories. """
    item = workflow.core.models.Item.objects.get(do_id=item_id)
    b_items = workflow.core.models.Batch_Item.objects.filter(item=item)
    for b_item in b_items:
        batch = b_item.batch
        batch.item_count = batch.item_count - 1
        batch.save()
    coll_items = workflow.core.models.Collection_Item.objects.filter(item=item)
    for coll_item in coll_items:
        try:
            cbis = workflow.wflocal.models.Collection_Building_Item_Status.objects.get(item=coll_item)
            cbis.delete()
        except:
            pass
        coll_item.delete()
    repo_path = get_repository_path(item)    
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)    
    metadata_path = os.path.join(drlutils.config.BODYBUILDER_PATH, item.do_id,)
    if os.path.exists(metadata_path):
        shutil.rmtree(metadata_path)    
    transactions = workflow.core.models.Transaction.objects.filter(item=item)
    for transaction in transactions:
        transaction.delete()
    item.delete()
    

def delete_django_batch_and_items(batch_name):
    batch = workflow.core.models.Batch.objects.get(name=batch_name)
    batch_items = workflow.core.models.Batch_Item.objects.filter(batch=batch)
    for batch_item in batch_items:
        item = batch_item.item 
        parent_batches = workflow.core.models.Batch_Item.objects.filter(item=item)
        for parent_batch in parent_batches:
            b = parent_batch.batch
            b.item_count = batch.item_count - 1
            b.save()
        delete_django_item(item.do_id)
    batch.delete()
    

def get_macrob_csv(item_id):
    item = workflow.core.models.Item.objects.get(do_id=item_id)
    thumb = workflow.core.models.Item_File.objects.get(item=item, use='THUMB')
    thumb.name = thumb.name.replace('.thumb.png', '.jpg') 
    master = workflow.core.models.Item_File.objects.get(item=item, use='MASTER')
    master_path = re.sub('\\\\usr\\\\local\\\\dlxs\\\\repository', '\\\\\\\\' + drlutils.config.HOSTNAME + '\\\\repository$', ntpath.normpath(master.path))
    quoted = []
    for i in [item.do_id, thumb.name, master.name, master_path]:
        quoted.append('"' + i + '"')
    return ",".join(quoted)            

def get_items_ready_for(action):
    actions = {'ingest': '3', 'prep_for_bodybuilder': '4', 'make_pdf': '6'}
    a = actions[action]
    conn = httplib.HTTPConnection(drlutils.config.DJANGO_HOST)
    conn.request("GET", "/django/workflow/status/ready/" + a + "/")
    r = conn.getresponse()
    my_json = json.load(r)    
    items = []
    for i in my_json:
        items.append(i['pk'])
    return items    

def record_completed_task(item, action, user): 
    try:
        item.set_action_complete(action)
        item.set_next_action_ready(action)
        workflow.core.transaction.record_transaction(action, item, user, 'True')
        return None
    except Exception as e:
        return item.do_id + ' - error updating database status: ' + str(e) + '\n'

def add_file_record(item, path, mime_type, use_type):
    try:
        f_name = os.path.basename(path)
        f_path = path
        f_size = os.path.getsize(f_path)
        f_host = drlutils.config.HOSTNAME 
        f_mime_type = mime_type
        f_use = use_type
        # see if we already have an entry for this file to update,
        # else create a new one
        try:
            i_f = workflow.core.models.Item_File.objects.get(item=item, name=f_name)
            i_f.path = f_path
            i_f.size_bytes = f_size
            i_f.host = f_host
            i_f.mime_type = f_mime_type
            i_f.use = f_use
            i_f.timestamp = datetime.datetime.now()
        except:
            i_f = workflow.core.models.Item_File(item=item, name=f_name, path=f_path, size_bytes=f_size, host=f_host, mime_type=f_mime_type, use=f_use)
        i_f.save()
    except Exception as e:
        return 'problem adding file for ' + item.do_id + ': ' + str(e)


def update_item_status(item, action, user, status):
    try:
        workflow.core.status.set_status(item, action, user, status)
        return None
    except Exception as e:
        return item.do_id + ' - error updating database status: ' + str(e)

def process_items_ready_for(action_name, process):
    """
    Get all items having the current ready action matching that of the passed parameter.
    For each item, call the passed 'process' function with the item's identifier.
    If the item is successfully processed, update the item status to indicate the
    action was successfully completed.  Send email notification of results.
    This design assumes the function called accepts the item's identifier as the only
    argument, and returns None on successful completion.  If the process fails, an
    error message may be returned and will be passed into the results report.
    """
    has_error = False 
    msg = 'Started at '  + datetime.datetime.today().isoformat() + '\n\n'
    action = get_action(action_name)
    user = get_user('gort')
    items = workflow.core.models.Item.objects.filter(item_current_status__ready_action=action)
    if len(items) == 0:
        return 'no items to process'
    for item in items:
        result = process(item.do_id)        
        if result:
            msg = msg + result + ' - skipping\n'
            has_error = True
            continue
        result = update_item_status(item, action, user, 'True')
        if result:
            msg = msg + result + ' - skipping\n'
            has_error = True
            continue
        msg = msg + item.do_id + ' - ' + drlutils.text.utils.shorten_string(item.name) + ' - OK\n'
    recipients = drlutils.messaging.utils.get_recipients(action, has_error)
    if not recipients:
        return
    dt = datetime.datetime.today()
    time_string = dt.strftime("%I:%M%p - %A %B %d, %Y")
    subject = action.name + ' report - ' +  time_string
    if has_error:
        subject = 'ATTN: Error in ' + subject
    drlutils.messaging.utils.send_email(recipients, subject, msg)

def get_repository_path(item):
    coll_id = item.primary_collection.c_id
    coll_path = coll_id[0] + '/' + coll_id
    return os.path.join(drlutils.config.REPOSITORY_ROOT, coll_id[0], coll_id, item.do_id)

def get_jp2_file_list(item):
    files = workflow.core.models.Item_File.objects.filter(item=item, use='JP2').order_by('name')
    paths = []
    for f in files:
        paths.append(f.path)
    return paths

def get_master_file_list(item):
    files = workflow.core.models.Item_File.objects.filter(item=item, use='MASTER').order_by('name')
    paths = []
    for f in files:
        paths.append(f.path)
    return paths

def get_dc_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='DC').path
    except:
        return ''

def get_mods_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='MODS').path
    except:
        return ''

def get_marcxml_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='MARCXML').path
    except:
        return ''

def get_mets_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='METS').path
    except:
        return ''

def get_pdf_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='PDF').path
    except:
        return ''

def get_ocr_zip_path(item):
    try:
        return workflow.core.models.Item_File.objects.get(item=item, use='OCR_ZIP').path
    except:
        return ''

def get_url_for_item(do_id):
    item = workflow.core.models.Item.objects.get(do_id=do_id)
    c_id = item.primary_collection.c_id
    if item.type.name.startswith('text'):
        return 'http://%s/cgi-bin/t/text/text-idx?idno=%s;view=toc;c=%s' % (drlutils.config.WEB_HOST, do_id, c_id)
    elif item.type.name.startswith('image') or item.type.name.startswith('map'):
        return 'http://%s/cgi-bin/i/image/image-idx?view=entry;cc=%s;entryid=x-%s' % (drlutils.config.WEB_HOST, c_id, do_id)
    elif item.type.name.startswith('manuscript'):
        return 'http://%s/u/ulsmanuscripts/pdf/%s.pdf' % (drlutils.config.WEB_HOST, do_id,)


