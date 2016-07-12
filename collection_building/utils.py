import sys
import os
import os.path
import datetime
import shutil
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import workflow.wflocal.models
import drlutils.django.utils
import drlutils.image.utils as drlimgutils
import drlutils.config

def create_collection_building_item_status(do_id, c_id):
    collection_building_actions = workflow.wflocal.models.Collection_Building_Actions.objects.filter(collection__c_id=c_id).order_by('order')
    if len(collection_building_actions) == 0:
        return
    collection_item = workflow.core.models.Collection_Item.objects.get(collection__c_id=c_id, item__do_id=do_id)
    for collection_action in collection_building_actions:
        # only create if one doesn't already exist; we don't want duplicates 
        try:
            status = workflow.wflocal.models.Collection_Building_Item_Status.objects.get(item=collection_item, action=collection_action.action)
        except:
            status = workflow.wflocal.models.Collection_Building_Item_Status()
            status.item=collection_item
            status.action = collection_action.action
            status.order = collection_action.order
            status.timestamp = None 
            status.save()


def get_thumbnail_for_dlxs(collection_item):
    try:
        item = drlutils.django.utils.get_item(collection_item.item.do_id) 
        thumb_dest = os.path.join(drlutils.config.DLXS_IMAGE_PATH, collection_item.collection.c_id, 'thumbjp2')
        if not os.path.exists(thumb_dest):
            os.makedirs(thumb_dest)
        thumb_repo_source = os.path.join(drlutils.django.utils.get_repository_path(item), item.thumb_filename) 
        shutil.copy(thumb_repo_source, thumb_dest) 
        thumb_encode_source = os.path.join(thumb_dest, item.thumb_filename)
        thumb_file = drlimgutils.encode_jpg(thumb_encode_source, size='150', clobber=True) 
        # have to remove source first, in case it is a jpg master, to avoid name conflict later
        os.remove(thumb_encode_source)
        # now it's ok to change thumbnail extension
        dlxs_thumb_name = thumb_file.replace('.thumb.jpg', '.jpg')
        shutil.move(thumb_file, dlxs_thumb_name)
        if not os.path.exists(dlxs_thumb_name):
            return item.do_id + ': ' + dlxs_thumb_name + ' not created propery.'
    except Exception as e:
        return 'problem creating thumbnail for %s - %s: %s' % (collection_item.collection.c_id, collection_item.item.do_id, str(e))
        

def get_jp2_for_dlxs(collection_item):
    """
    retrieves jpeg2000 derivatives for staging into DLXS 
    """
    try:
        item = collection_item.item 
        collection = collection_item.collection
        if 'text' in item.type.name:
            jp2_dest = os.path.join(drlutils.config.DLXS_OBJ_PATH, collection.c_id, item.do_id)
        else:
            jp2_dest = os.path.join(drlutils.config.DLXS_IMAGE_PATH, collection.c_id, 'jp2')
        if not os.path.exists(jp2_dest):
            os.makedirs(jp2_dest)
        files = drlutils.django.utils.get_jp2_file_list(item) 
        for file in files:
            shutil.copy(file, jp2_dest) 
    except Exception as e:
        return 'problem copying jp2s for %s - %s: %s' % (collection_item.collection.c_id, collection_item.item.do_id, str(e))

def create_collection_building_actions(c_id, type):
    textclass_actions = ['dlxs textclass image derivatives', 'dlxs textclass xml', 'deliver dlxs textclass to webserver', 'release online']
    imageclass_jp2_actions = ['make jpg2000', 'deliver imageclass jp2 to webserver', 'release online']
    imageclass_zoomify_actions = ['make zoomify', 'deliver imageclass zoomify to webserver', 'release online']
    imageclass_zoomify_jpg_actions = ['make zoomify', 'make jpg', 'deliver to webserver', 'release online']
    if type == 'textclass':
        actions = textclass_actions
    elif type == 'imageclass_jp2':
        actions = imageclass_jp2_actions
    elif type == 'imageclass_zoomify':
        actions = imageclass_zoomify_actions
    elif type == 'imageclass_zoomify_jpg':
        actions = imageclass_zoomify_jpg_actions
    else:    
        return 'can\'t create collection building actions for unknown type: %s' % (type,)
    c = workflow.core.models.Collection.objects.get(c_id=c_id)
    i = 0
    for action in actions:
        i = i + 1
        a = workflow.wflocal.models.Building_Action.objects.get(name=action)
        cba = workflow.wflocal.models.Collection_Building_Actions(collection=c, action=a, order=i)
        cba.save()


def update_timestamp(do_id, action_name='all', clear=False):
    collection_items = workflow.core.models.Collection_Item.objects.filter(item__do_id=do_id)
    for c_i in collection_items:
        actions = get_collection_building_actions(c_i)
        for action in actions:
            if (action_name == 'all') or (action_name == action.action.name):
                if clear:
                    # this will set timestamp to no value
                    action.set_timestamp(None)
                else:
                    # this will set timestamp to current time
                    action.set_timestamp()
    return


def handle_release_online(collection_item):
    status = workflow.wflocal.models.Collection_Building_Item_Status.objects.get(item=collection_item, action__name='release online')
    try:
        local_item = workflow.wflocal.models.Local_Item.objects.get(do_id=collection_item.item.do_id)
        if not local_item.online_pub_date or local_item.online_pub_date == '':
            local_item.online_pub_date = datetime.date.today()
            local_item.save()
    except:
        local_item = workflow.wflocal.models.Local_Item(item=collection_item.item, online_pub_date=datetime.date.today())
        local_item.save()
    status.set_timestamp()
    return

def get_ready_collection_items(c_id, type='collection'):
    ready_items = []
    if type == 'primary':
        for item in workflow.core.models.Item.objects.filter(primary_collection__c_id=c_id):
            ics = workflow.core.models.Item_Current_Status.objects.get(item=item)
            if ics.ready_action == None or ics.ready_action.name == 'check-out':
                ready_items.append(item)
    else:
        for collection_item in workflow.core.models.Collection_Item.objects.filter(collection__c_id=c_id):
            ics = workflow.core.models.Item_Current_Status.objects.get(item=collection_item.item)
            if ics.ready_action == None or ics.ready_action.name == 'check-out':
                ready_items.append(collection_item)
    return ready_items
    

def update_collection_item_counts(scope='all'):
    if scope == 'all':
        collections = workflow.core.models.Collection.objects.all()
    else:
        collections = workflow.core.models.Collection.objects.filter(c_id=scope)
    errors = []
    for c in collections:
        try:
            drl_c = workflow.wflocal.models.DRL_Collection.objects.get(collection=c)
            drl_c.item_count = workflow.core.models.Collection_Item.objects.filter(collection=c).count()
            drl_c.completed_item_count = len(get_ready_collection_items(c.c_id))
            drl_c.save()
        except Exception as e:
            errors.append('%s - %s' % (c.c_id, e))
    if len(errors) > 0:
        raise Exception('\n'.join(errors)) 

def update_collection_building_counts(scope='all'):
    """
    Loops over collections. 
    
    - For each collection:

        - Get the collection-building actions and
          create a dictionary of them, to hold the
          number of items ready for each.

        - Get all of the "ready items" for the collection.

        - For each ready item

            - For each collection-building action:

                - If the action is outdated for that item,
                  add it to the dictionary

        - After the ready items have been checked, use the 
          dictionary to set the value in the collection-
          building action object 
 
    """
    if scope == 'all':
        collections = workflow.core.models.Collection.objects.all()
    else:
        collections = workflow.core.models.Collection.objects.filter(c_id=scope)
    errors = []
    for c in collections:
        try:
            cbas = workflow.wflocal.models.Collection_Building_Actions.objects.filter(collection=c).order_by('order')
            cba_count_dict = {}
            for cba in cbas:
                cba_count_dict[cba.id] = 0
            ready_items = get_ready_collection_items(c.c_id)
            for ready_item in ready_items:
                for cba in cbas:
                    if workflow.wflocal.models.Collection_Building_Item_Status.objects.get(item=ready_item, action=cba.action).is_outdated():
                        cba_count_dict[cba.id] = cba_count_dict[cba.id] + 1
            for cba_id in cba_count_dict.keys():
                cba = workflow.wflocal.models.Collection_Building_Actions.objects.get(id=cba_id)
                cba.item_ready_count = cba_count_dict[cba_id]
                cba.save()
        except Exception as e:
            errors.append('%s - %s' % (c.c_id, e))
    if len(errors) > 0:
        raise Exception('\n'.join(errors)) 

        
def get_collection_building_actions(collection_item):
    statuses = workflow.wflocal.models.Collection_Building_Item_Status.objects.filter(item=collection_item).order_by('order')
    return statuses

def clean_collection_building_actions(batch_id):
    batch_items = workflow.core.models.Batch_Item.objects.filter(batch__name=batch_id)
    remove_actions = [7, 8, 9, 11, 15]
    for b_i in batch_items:
        for a in remove_actions:
            action = workflow.core.models.Action.objects.get(id=a)
            b_i.item.remove_action(action)
            print ' - '.join([b_i.item.do_id, 'OK'])

def get_ready_items(action_name, prerequisite_action_names):
    """Return collection_item objects that are ready for action AND have all prerequisite actions completed.  To save time, iterate over collections and skip any collections that have no items ready specified actions."""
    ready_items = []
    ready_count = 0
    collections = workflow.core.models.Collection.objects.all()
    for c in collections:
        try:
            ready_count = workflow.wflocal.models.Collection_Building_Actions.objects.get(collection=c, action__name=action_name).item_ready_count
        except:
            continue
        if ready_count > 0:
            this_action = workflow.wflocal.models.Building_Action.objects.get(name=action_name)
            possible_items = workflow.wflocal.models.Collection_Building_Item_Status.objects.filter(action=this_action, item__collection=c)
            for item in possible_items:
                if not item.is_outdated():
                    pass
                elif not item.prerequisites_complete(prerequisite_action_names):
                    pass
                else:
                    ready_items.append(item.item)
    return ready_items

def coll_has_any_ready_items(c, action_name, prerequisite_action_names):
    ready_count = 0
    try:
        ready_count = workflow.wflocal.models.Collection_Building_Actions.objects.get(collection=c, action__name=action_name).item_ready_count
        for p in prerequisite_action_names:
            i = workflow.wflocal.models.Collection_Building_Actions.objects.get(collection=c, action__name=p)
    except:
        return False
    if ready_count > 0:
        this_action = workflow.wflocal.models.Building_Action.objects.get(name=action_name)
        possible_items = workflow.wflocal.models.Collection_Building_Item_Status.objects.filter(action=this_action, item__collection=c)
        for item in possible_items:
            if not item.is_outdated():
                pass
            elif not item.prerequisites_complete(prerequisite_action_names):
                pass
            else:
                return True 
    return False

def get_textclass_colls_to_rebuild():
    ready_colls = []
    collections = workflow.core.models.Collection.objects.all()
    for c in collections:
        if coll_has_any_ready_items(c, 'release online', ['dlxs textclass image derivatives', 'dlxs textclass xml', 'deliver dlxs textclass to webserver']):
            ready_colls.append(c)
    return ready_colls
