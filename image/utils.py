import subprocess
import os
import shutil
import drlutils.config


def get_bit_depth_old(file):
    args = ['identify', '-format', '%z', file]
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].strip()

def get_bit_depth(file):
    args = [drlutils.config.GETBITDEPTH, file]
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].strip()

def get_dimensions(file):
    args = [drlutils.config.GETDIMENSIONS, file]
    return subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0].strip()

def bitonalize(file):
    (dir, filename) = os.path.split(file)
    temp_filename = filename + '.tmp'
    temp_file = os.path.join(dir, temp_filename)	
    subprocess.call([drlutils.config.TIFF2BW, '-c', 'g4', file, temp_file])
    shutil.move(temp_file, file)
    return None
    
def encode_jpg(source, size='original', clobber=False, quality='40'):
    try:
        (s_dir, s_filename) = os.path.split(source)
        (s_filestem, s_ext) = os.path.splitext(s_filename)
        jpg_filename = '%s.jpg' % (s_filestem,) 
        jpg_dest = os.path.join(s_dir, jpg_filename)
        if not clobber: 
            if os.path.exists(jpg_dest):    
                return '%s exists - skipping' % (jpg_dest,)
        if size == 'original':
            subprocess.call([
                drlutils.config.GM, 'convert',
                '-quality', quality,
                source, jpg_dest
            ])
        else:
            resample = '%sx%s>' % (size, size)
            subprocess.call([
                drlutils.config.GM, 'convert',
                '-thumbnail', resample,
                '-quality', quality,
                source, jpg_dest]
            )
        return jpg_dest
    except Exception as e:
    	return source + ' problem: ' + str(e)

def encode_thumb(source, clobber=False, size='250', quality='80', desc='thumb', fixed_width=False):
    try:
        (s_dir, s_filename) = os.path.split(source)
        (s_filestem, s_ext) = os.path.splitext(s_filename)
        thumb_filename = '%s.%s.png' % (s_filestem, desc) 
        thumb_dest = os.path.join(s_dir, thumb_filename)
        if not clobber: 
            if os.path.exists(thumb_dest):    
                return '%s exists - skipping' % (thumb_dest,)
        if fixed_width:
            size_param = '%s' % (size)
        else:
            size_param = '%sx%s>' % (size, size)
        crop = '%sx%s+0+0' % (size, size)
        subprocess.call([
            drlutils.config.IMAGEMAGICK_CONVERT,
            source,
            '+profile', '"*"',
            '-thumbnail', size_param,
            '-bordercolor', 'transparent',
            '-border', '50',
            '-gravity', 'center',
            '-crop', crop,
            '+repage',
            '-unsharp', '0x1',
            thumb_dest
        ])
        if not os.path.exists(thumb_dest):
            raise Exception('thumb not made at %s' % (thumb_dest,))
        return thumb_dest
    except Exception as e:
    	return source + ' problem: ' + str(e)

def encode_thumb_jpg(source, clobber=False, size='250', quality='80', desc='thumb', fixed_width=False):
    try:
        (s_dir, s_filename) = os.path.split(source)
        (s_filestem, s_ext) = os.path.splitext(s_filename)
        thumb_filename = '%s.%s.jpg' % (s_filestem, desc) 
        thumb_dest = os.path.join(s_dir, thumb_filename)
        if not clobber: 
            if os.path.exists(thumb_dest):    
                return '%s exists - skipping' % (thumb_dest,)
        if fixed_width:
            size_param = '%s' % (size)
        else:
            size_param = '%sx%s>' % (size, size)
        subprocess.call([
            drlutils.config.GM, 'convert',
            '-thumbnail', size_param,
            '-quality', quality,
            '-unsharp', '0x1',
            source, jpg_dest
        ])
        if not os.path.exists(thumb_dest):
            raise Exception('thumb not made at %s' % (thumb_dest,))
        return thumb_dest
    except Exception as e:
    	return source + ' problem: ' + str(e)

def encode_jp2(source, clobber=False, type='image'):
    try:
        (s_dir, s_filename) = os.path.split(source)
        (s_filestem, s_ext) = os.path.splitext(s_filename)
        # make a temp TIFF no matter what source image is:
        temp_filename = '%s.temp.tif' % (s_filestem,) 
        temp_dest = os.path.join(s_dir, temp_filename)
        jp2_filename = '%s.jp2' % (s_filestem,) 
        jp2_dest = os.path.join(s_dir, jp2_filename)
        if not clobber: 
            if os.path.exists(jp2_dest):    
                return '%s exists - skipping' % (jp2_dest,)
        if type == 'text':
            subprocess.call([
                'gm', 'convert',
                '-compress', 'None',
                '-resample', '300x300',
                '-depth', '8',
                source, temp_dest
            ])
        else:
            subprocess.call([
                'gm', 'convert',
                '-compress', 'None',
                '-depth', '8',
                source, temp_dest
            ])
        subprocess.call([
            drlutils.config.KDU_COMPRESS,
            '-i', temp_dest,
            '-o', jp2_dest,
            '-rate', '0.5',
            'Clayers=1', 'Clevels=7', '-quiet'
        ])
        os.remove(temp_dest)
        return jp2_dest
    except Exception as e:
    	return source + ' problem: ' + str(e)

