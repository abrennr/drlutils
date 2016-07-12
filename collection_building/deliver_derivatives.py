import sys
import os
import subprocess
import shutil
import drlutils.collection_building.utils
import drlutils.django.utils
import drlutils.config


def handle_jp2_items():
    msg = [] 
    jp2_delivery_items = drlutils.collection_building.utils.get_ready_items('deliver imageclass jp2 to webserver', ['make jpg2000'])
    for jp2_item in jp2_delivery_items:
        result = deliver_jp2_item(jp2_item)
        if result:
            raise Exception('problem delivering jp2 item %s - %s' % (jp2_item.item.do_id, result)) 
        else:
            msg.append('%s - delivered jp2 derivatives OK' % (jp2_item.item.do_id,))
    if len(msg) > 0:
        return '\n'.join(msg)

def handle_zoomify_items():
    msg = [] 
    zoomify_delivery_items = drlutils.collection_building.utils.get_ready_items('deliver imageclass zoomify to webserver', ['make zoomify'])
    for zoomify_item in zoomify_delivery_items:
        result = deliver_zoomify_item(zoomify_item)
        if result:
            raise Exception('problem delivering zoomify item %s - %s' % (zoomify_item.item.do_id, result)) 
        else:
            msg.append('%s - delivered zoomify derivatives OK' % (zoomify_item.item.do_id,))
    if len(msg) > 0:
        return '\n'.join(msg)


def handle_pdf_items():
    msg = [] 
    pdf_delivery_items = drlutils.collection_building.utils.get_ready_items('deliver manuscript pdf to webserver', ['make pdf'])
    for pdf_item in pdf_delivery_items:
        result = deliver_pdf_item(pdf_item)
        if result:
            raise Exception('problem delivering pdf item %s - %s' % (pdf_item.item.do_id, result)) 
        else:
            msg.append('%s - delivered pdf OK' % (pdf_item.item.do_id,))
    if len(msg) > 0:
        return '\n'.join(msg)

def handle_textclass_items():
    msg = [] 
    textclass_delivery_items = drlutils.collection_building.utils.get_ready_items('deliver dlxs textclass to webserver', ['dlxs textclass image derivatives', 'dlxs textclass xml'])
    for textclass_item in textclass_delivery_items:
        result = deliver_textclass_item(textclass_item)
        if result:
            raise Exception('problem delivering text item %s - %s' % (textclass_item.item.do_id, result)) 
        else:
            msg.append('%s - delivered textclass derivatives OK' % (textclass_item.item.do_id,))
    if len(msg) > 0:
        return '\n'.join(msg)


def deliver_jp2_item(jp2_item):
    coll_id = jp2_item.collection.c_id
    source_root = os.path.join(drlutils.config.DLXS_IMAGE_PATH, coll_id)
    dest_root = os.path.join(drlutils.config.REMOTE_IMG_PATH, coll_id[0], coll_id)
    master_file = drlutils.django.utils.get_master_file_list(jp2_item.item)[0]
    file_root = os.path.splitext(os.path.basename(master_file))[0]
    # copy jp2
    jp2_file_name = file_root + '.jp2'
    jp2_source = os.path.join(source_root, 'jp2', jp2_file_name)
    jp2_dest = os.path.join(dest_root, 'jp2')
    args = ['scp', '-r', jp2_source, jp2_dest]
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        raise Exception("problem delivering jp2: %s" % (result,))
    # copy thumbnail
    thumbnail_file_name = file_root + '.jpg'
    thumb_source = os.path.join(source_root, 'thumbjp2', thumbnail_file_name)
    thumb_dest = os.path.join(dest_root, 'thumbjp2')
    args = ['scp', '-r', thumb_source, thumb_dest]
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        raise Exception("problem delivering jpg: %s" % (result,))
    else:
        os.unlink(jp2_source)
        os.unlink(thumb_source)
    drlutils.collection_building.utils.update_timestamp(jp2_item.item.do_id, 'deliver imageclass jp2 to webserver')
    return

def deliver_zoomify_item(zoomify_item):
    return

def deliver_pdf_item(pdf_item):
    coll_id = pdf_item.collection.c_id
    item_id = pdf_item.item.do_id
    pdf_filename = '%s.pdf' % (item_id,)
    pdf_source = os.path.join(drlutils.config.DLXS_PDF_PATH, coll_id, pdf_filename)
    pdf_dest = os.path.join(drlutils.config.REMOTE_PDF_PATH, coll_id[0], coll_id, 'pdf')
    args = ['scp', '-r', pdf_source, pdf_dest]
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        raise Exception("problem delivering obj: %s" % (result,))
    else:
        os.unlink(pdf_source)
    drlutils.collection_building.utils.update_timestamp(pdf_item.item.do_id, 'deliver manuscript pdf to webserver')
    return
    

def deliver_textclass_item(textclass_item):
    coll_id = textclass_item.collection.c_id
    item_id = textclass_item.item.do_id
    obj_source = os.path.join(drlutils.config.DLXS_OBJ_PATH, coll_id, item_id)
    args = ['scp', '-r', obj_source, drlutils.config.REMOTE_OBJ_PATH] 
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        raise Exception("problem delivering obj: %s" % (result,))
    xml_filename = item_id + '.xml'
    xml_source = os.path.join(drlutils.config.DLXS_XML_PATH,  coll_id, xml_filename)
    xml_dest = os.path.join(drlutils.config.REMOTE_XML_PATH, coll_id[0], coll_id, 'xml')
    args = ['scp', xml_source, xml_dest]
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        raise Exception("problem delivering xml: %s" % (result,))
    else:
        shutil.rmtree(obj_source)
        os.unlink(xml_source)
    drlutils.collection_building.utils.update_timestamp(textclass_item.item.do_id, 'deliver dlxs textclass to webserver')
    return
     

