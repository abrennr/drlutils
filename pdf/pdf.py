import sys
import subprocess
import os
import shutil
import glob
import zipfile
import traceback
import drlutils.image.utils
import drlutils.django.utils
import drlutils.text.utils
import drlutils.config
from reportlab.pdfgen import canvas


def encode_pdf(source_dir, annotation=None):
    if annotation:
        max_chars = 0
        for line in open(annotation, 'r').readlines():
            if len(line) > max_chars:
                max_chars = len(line)
    tifs = glob.glob(source_dir + '/*.tif')
    tifs.sort()
    pdf_file = source_dir + '/' + os.path.basename(source_dir) + '.pdf' 
    c = canvas.Canvas(pdf_file)
    for t in tifs:
        jpg = t + '.jpg'
        (w,h) = drlutils.image.utils.get_dimensions(t).split('x')
        if (int(w) > 2200):
            scale = '50%'
        else:
            scale = '100%'
        subprocess.check_call([drlutils.config.GM, 'convert', t, '-scale', scale, '-quality', '40', jpg])
        (x, y) = c.drawInlineImage(jpg, 0, 0)
        c.setPageSize([x, y])    
        if annotation:
            font_points = (x / max_chars) * 2.1
            padding = font_points * 4.6
            new_y = y + padding  
            c.setPageSize([x, new_y])    
            textobject = c.beginText()
            textobject.setFont("Helvetica", font_points)
            textobject.setTextOrigin(1.5*font_points, new_y-(1.5*font_points))
            line_count = 0
            for line in open(annotation, 'r').readlines():
                if line_count == 0:
                    textobject.setFont("Helvetica-Oblique", font_points)
                else:
                    textobject.setFont("Helvetica", font_points)
                line_count = line_count + 1
                textobject.textLine(line.strip())
            c.drawText(textobject)
        c.showPage()
        os.remove(jpg)
    c.save()
    return pdf_file

def optimize(source_file, dest_file):
    args = [drlutils.config.PDF_OPTIMIZER, source_file, dest_file]
    result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
    if result:
        return "Problem optimizing %s: %s" % (source_file, result)
    else:
        return

def create(do_id, c_id):
    try:
        item = drlutils.django.utils.get_item(do_id) 
        pdf_root = os.path.join(drlutils.config.DLXS_PDF_PATH, c_id)
        pdf_item = os.path.join(pdf_root, do_id)
        if os.path.exists(pdf_item):
            # print '%s has existing derivative directory -- replacing' % (item.do_id,)
            shutil.rmtree(pdf_item)
        os.makedirs(pdf_item)
        # copy files out of repository for processing 
        files = drlutils.django.utils.get_master_file_list(item) 
        if len(files) < 1:
            return '%s - problem - No master files found!?' % (do_id,)
        for file in files:
            shutil.copy(file, pdf_item)
        if c_id == 'ulsmanuscripts':
            pdf_file = handle_annotated_pdf(item, pdf_item)
        else:
            pdf_file = encode_pdf(pdf_item) 
            for tif in glob.glob(pdf_item + '/*.tif'):
                os.remove(tif)
        post_op_pdf = os.path.join(pdf_root, os.path.basename(pdf_file))
        result = optimize(pdf_file, post_op_pdf)
        if result:
            return result
        else:
            shutil.rmtree(pdf_item)
    except Exception as e:
        return do_id + ' - problem: ' + str(e) + traceback.print_exc()
        
def handle_annotated_pdf(item, pdf_item):
    item_annotxt = pdf_item + '/annotation.txt'
    mods_xml = drlutils.django.utils.get_mods_path(item) 
    subprocess.check_call([
        drlutils.config.JAVA, '-jar',
        drlutils.config.SAXON,
        '-s', mods_xml,
        '-o', item_annotxt,
        drlutils.config.MODS2PDFHEADER_XSL
    ]) 
    pdf_file = encode_pdf(pdf_item, item_annotxt) 
    for tif in glob.glob(pdf_item + '/*.tif'):
        os.remove(tif)
    os.remove(item_annotxt)
    return pdf_file

def extract_text(do_id):
    try:
        item = drlutils.django.utils.get_item(do_id) 
        pdf_file = drlutils.django.utils.get_pdf_path(item) 
        tmp_dir = os.path.join('/tmp', item.do_id)
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        text_file = os.path.join(tmp_dir, '%s.txt' % (do_id,))
        args = [drlutils.config.PDFTOTEXT, pdf_file, text_file]
        result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
        if result:
            return "Problem extracting text from %s: %s" % (source_file, result)
        try:
            drlutils.text.utils.split_textfile(text_file)
        except Exception as e:
            return "Problem splitting %s: %s" % (text_file, str(e))
        os.remove(text_file)
        repo_path = drlutils.django.utils.get_repository_path(item)
        zip_filename = item.do_id + '.ocr.zip'
        zip_filepath = os.path.join(repo_path, zip_filename)
        zip = zipfile.ZipFile(zip_filepath, 'w')
        for txt in glob.glob(tmp_dir + '/*.txt'):
            zip.write(txt, os.path.basename(txt))
        zip.close()
        drlutils.django.utils.add_file_record(item, zip_filepath, 'APPLICATION_ZIP', 'OCR_ZIP')
        shutil.rmtree(tmp_dir)
        return None
    except Exception as e:
        return item.do_id + ' - problem: ' + str(e) + traceback.print_exc() 

def extract_images(do_id, mode='rgb'):
    try:
        item = drlutils.django.utils.get_item(do_id) 
        existing_masters = drlutils.django.utils.get_master_file_list(item) 
        if len(existing_masters) > 0:
            return item.do_id + ' ' + str(len(existing_masters))  + ' master files already exist in repository'
        pdf_file = drlutils.django.utils.get_pdf_path(item) 
        tmp_dir = os.path.join('/tmp', item.do_id)
        if not os.path.exists(tmp_dir):
            os.mkdir(tmp_dir)
        tmp_pdf = os.path.join(tmp_dir, os.path.basename(pdf_file))
        shutil.copy(pdf_file, tmp_pdf)
        gs_output_arg = '-sOutputFile=%s/%%04d.tif' % (img_dir,)
        if mode == 'bitonal':
            gs_device = '-sDEVICE=tiffg4'
            gs_res = '-r600'
        else:
            gs_device = '-sDEVICE=tiff24nc'
            gs_res = '-r300'
        args = [drlutils.config.GHOSTSCRIPT, gs_device, gs_res, '-dNOPAUSE', '-dBATCH', gs_output_arg, tmp_pdf]
        result = subprocess.Popen(args, stderr=subprocess.PIPE).communicate()[1]
        if result:
            return "Problem extracting images from %s: %s" % (source_file, result)
        repository_path = drlutils.django.utils.get_repository_path(item)
        for tiff in glob.glob(tmp_dir + '/*.tif'):
            shutil.copy(tiff, repository_path)
            dest_file = os.path.join(repository_path, os.path.basename(tiff))
            drlutils.django.utils.add_file_record(item, dest_file, 'IMAGE_TIFF', 'MASTER')
        shutil.rmtree(tmp_dir)
        return None
    except Exception as e:
        return item.do_id + ' - problem: ' + str(e)

