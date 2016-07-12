import sys
import os
import drlutils.collection_building.utils
import drlutils.dlxs.textclass_xml
import drlutils.dlxs.textclass_image_derivatives
import drlutils.image.jpg as drljpg
import drlutils.image.jp2 as drljp2
import drlutils.image.zoomify as drlzoomify
import drlutils.pdf.pdf as drlpdf

def process_action(collection_item, action_status):
    if action_status.action.name == 'dlxs textclass image derivatives':
        image_result = drlutils.dlxs.textclass_image_derivatives.build(collection_item)
        if image_result: 
            return ' - problem with image derivatives: ' + image_result
        else:
            action_status.set_timestamp()
            return ' - image derivatives - OK'
    elif action_status.action.name == 'dlxs textclass xml':
        xml_result = drlutils.dlxs.textclass_xml.build(collection_item.item.do_id, collection_item.collection.c_id)
        if xml_result: 
            return  ' - problem with xml build: ' + xml_result
        else:
            action_status.set_timestamp()
            return ' - xml build - OK'
    elif action_status.action.name == 'deliver to webserver':
        pass
    elif action_status.action.name == 'release online':
        pass
    elif action_status.action.name == 'make jpg2000':
        thumb_result = drlutils.collection_building.utils.get_thumbnail_for_dlxs(collection_item)
        if thumb_result: 
            return  ' - problem with copying thumbnail: ' + thumb_result
        jp2_result = drljp2.create(collection_item.item.do_id, collection_item.collection.c_id)
        if jp2_result: 
            return  ' - problem with make jpg2000: ' + jp2_result
        else:
            action_status.set_timestamp()
            return ' - make jpg2000 - OK'
    elif action_status.action.name == 'make zoomify':
        thumb_result = drlutils.collection_building.utils.get_thumbnail_for_dlxs(collection_item)
        if thumb_result: 
            return  ' - problem with copying thumbnail: ' + thumb_result
        zoomify_result = drlzoomify.create(collection_item.item.do_id, collection_item.collection.c_id)
        if zoomify_result: 
            return  ' - problem with make zoomify: ' + zoomify_result
        else:
            action_status.set_timestamp()
            return '  - make zoomify - OK'
    elif action_status.action.name == 'make jpg':
        jpg_result = drljpg.create(collection_item.item.do_id, collection_item.collection.c_id)
        if jpg_result: 
            return  ' - problem with make jpg: ' + jpg_result
        else:
            action_status.set_timestamp()
            return ' - make jpg - OK'
    elif action_status.action.name == 'make pdf':
        item = str(collection_item.item.do_id)
        coll = str(collection_item.collection.c_id)
        drlpdf.create(item, coll)
        action_status.set_timestamp()


def handle_item(collection_item, action='all', criteria='ready'):
    """actions can be 'all' or a specific action name; criteria can be 'all', 'ready', or 'new'"""
    msgs = []
    action_statuses = drlutils.collection_building.utils.get_collection_building_actions(collection_item)
    if len(action_statuses) == 0:
        pass
        # msg = "Warning: no action statuses for %s in %s" % (collection_item.item.do_id, c_id) 
    for action_status in action_statuses:
        # if a particular action is specified and this is not it, skip
        if action != 'all' and action != action_status.action.name:
            continue
        # if criteria is 'all', go ahead and do it
        elif criteria == 'all':
            result =  process_action(collection_item, action_status)
            if result:
                msgs.append(collection_item.item.do_id + result)
        # if the criteria is 'new' and this action hasn't been done (i.e. no timestamp), process it
        elif criteria == 'new' and not action_status.timestamp:
            result =  process_action(collection_item, action_status)
            if result:
                msgs.append(collection_item.item.do_id + result)
        # if 
        elif criteria == 'ready' and action_status.is_outdated():
            result =  process_action(collection_item, action_status)
            if result:
                msgs.append(collection_item.item.do_id + result)
        else:
            pass
    if len(msgs) > 0:
        return '\n'.join(msgs)

def handle_collection(c_id, action='all', criteria='ready'):
    results = []
    for collection_item in drlutils.collection_building.utils.get_ready_collection_items(c_id):
        try:
            result = handle_item(collection_item, action, criteria)
            if result:
                results.append(result)
        except Exception as e:
            raise Exception('%s - %s - %s' % (c_id, collection_item.item.do_id, str(e)))
    return '\n'.join(map(str, results))
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'usage: build_collection_derivatives collection_id [action:all, or action name] [criteria:ready, or all,new]'
        sys.exit()
    c_id = sys.argv[1]
    if len(sys.argv) > 3:     
        handle_collection(c_id, sys.argv[2], sys.argv[3])
    elif len(sys.argv) > 2:     
        handle_collection(c_id, sys.argv[2])
    else:
        handle_collection(c_id)

