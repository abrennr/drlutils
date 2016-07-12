import sys
import os
import csv
import codecs
import json
import urllib
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import workflow.core.models
import workflow.wflocal.models
import workflow.retrographer.models
import drlutils.django.utils 
import drlutils.date.utils 
import drlutils.text.utils
import drlutils.mods.utils
import drlutils.dublincore.mods2dc
import drlutils.config
from lxml import etree


def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield dict([(key.replace(' ', '_'), unicode(value, 'utf-8')) for key, value in row.iteritems()])

def getUnicodeDictReaderFieldnames(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    fixed_names = []
    for field in csv_reader.fieldnames:
        fixed_names.append(field.replace(' ', '_'))
    return fixed_names

def get_config_fields(c_id):
    url = 'http://%s/cgi-bin/drl/dlxs_img_config?c_id=%s&type=fields' % (drlutils.config.WEB_HOST, c_id,)
    u = urllib.urlopen(url)
    return json.load(u)

def get_config_maps():
    url = 'http://%s/django/workflow/metadata_maps?schema=MODS' % (drlutils.config.DJANGO_HOST,)
    u = urllib.urlopen(url)
    return json.load(u)

def map_field(fieldname, dataRow, id_fieldname, date_fieldname, date_qualifier_fieldname, source_fieldname, file_fieldname, field_overrides, logFile):

    if fieldname in field_overrides.keys():
        dataRow[fieldname] = field_overrides[fieldname]

    if fieldname == 'Display_Date':
        try:
            value = dataRow[fieldname] 
        except:
            if dataRow[date_qualifier_fieldname] == '':
                value = drlutils.date.utils.get_display_date(dataRow[date_fieldname]) 
            else:
                value = drlutils.date.utils.get_display_date(dataRow[date_fieldname], questionable=True) 
    elif fieldname == 'sort_date':
        if drlutils.date.utils.is_normalized_date(dataRow[date_fieldname]):
            value = drlutils.date.utils.get_sort_date(dataRow[date_fieldname])
        else:
            value = None
    elif (fieldname == 'Subject') and dataRow[fieldname] == '':
        value = 'cataloging in progress'
    elif fieldname == source_fieldname: 
        try:
            value = workflow.wflocal.models.Source_Collection.objects.get(source_id=dataRow[fieldname]).name
        except:
            value = dataRow[fieldname]
    elif fieldname == 'source_citation':
        try:
            value = workflow.wflocal.models.Source_Collection.objects.get(source_id=dataRow[source_fieldname]).full_citation
        except:
            value = dataRow[source_fieldname]
    elif fieldname == file_fieldname:
        pass
        try:
            value = workflow.core.models.Item_File.objects.get(item__do_id=dataRow[id_fieldname], use='MASTER').name
        except Exception as e:
            logFile.write('WARNING: ' + dataRow[id_fieldname].encode('utf-8') + ' failed image check: ' + str(e) + ' - skipping.\n')
            print 'WARNING: ' + dataRow[id_fieldname].encode('utf-8') + ' failed image check: ' + str(e) + ' - skipping.\n'
            value = dataRow[fieldname]
    elif fieldname == date_fieldname and not drlutils.date.utils.is_normalized_date(dataRow[fieldname]):
        logFile.write('WARNING: Incorrect normalized date for: ' + dataRow[id_fieldname].encode('utf-8') + ' date: ' + dataRow[fieldname].encode('utf-8') + '\n')
        print 'WARNING: Incorrect normalized date for: ' + dataRow[id_fieldname].encode('utf-8') + ' date: ' + dataRow[fieldname].encode('utf-8') 
        value = dataRow[fieldname]
    else:
        value = dataRow[fieldname]
    if not value:
        return ''
    else:
        filtered = drlutils.text.utils.filter_for_xml(drlutils.text.utils.filter_ms_characters(value))
        return filtered 

def main():
        
    try:
        sys.argv[1]
    except:
        print 'You must give a csv data file as an argument to this script'
        sys.exit()
    
    generated_fields = ['Digital_Collection', 'Collection_Id', 'Display_Date', 'source_citation', 'sort_date']
    field_overrides = {}
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            key, value = arg.split('=')
            field_overrides[key] = value
        for k in field_overrides.keys():
            generated_fields.append(k)
            
    collection_id = raw_input('Please enter the collection id to use for data field mapping: ')
    
    # open log file
    logFileName = '%s.mods_log.txt' % (collection_id,)
    logFile = codecs.open(logFileName, encoding='utf-8', mode='w')
    logFile.write('starting processing of %s using collection mappings for %s\n\n' % (sys.argv[1], collection_id))

    # each collection has config data stored in the database.
    # read config data, create lists to store config data 
    config_maps = get_config_maps()
    try:
        field_map = config_maps[collection_id]
    except:
        logFile.write('No config map found for collection %s.  This is required.\n' % (collection_id,))
        print 'No config map found for collection %s.  This is required.\n' % (collection_id,)
        sys.exit()
        
    # these fields require special validation or processing.  Because we don't know what
    # the field name used to represent these will be for any given collection, we use
    # the config mapping to capture the correct field name.
    id_fieldname, date_fieldname, date_qualifier_fieldname, source_fieldname, file_fieldname = ['', '', '', '', ''] 
    for field in field_map.keys():
        if 'identifier' in field_map[field]:
            id_fieldname = field
        elif 'normalized_date_qualifier' in field_map[field]:
            date_qualifier_fieldname = field
        elif 'normalized_date' in field_map[field]:
            date_fieldname = field
        elif 'source_collection' in field_map[field]:
            source_fieldname = field
        elif 'file_name' in field_map[field]:
            file_fieldname = field

    if not 'identifier' in field_map.values(): 
        logFile.write('No field found with DC.id in configuration data.  This is required.\n')
        print 'No field found with DC.id in configuration data.  This is required.'
        sys.exit()

    #if not 'file_name' in field_map.values(): 
    #    logFile.write('No field found with IC.fn in configuration data. This is required.\n')
    #    print 'No field found with IC.fn in configuration data. This is required.'
    #    sys.exit()

    # the image metadata is delivered as a csv file, which may contain
    # more fields than we need. 
    # read csv file into dictionary iterator, keyed by first row field names
    if collection_id in ['hpicasc', 'darlimg', 'darlbroadsides', 'corsini']:
        data_name_fields = ['Title', 'Collection', 'Identifier', \
            'File_Name', 'Batch', 'Normalized_Date', 'Image_Number', 'Location', 'Date', 'Address', \
            'Format', 'Rights', 'Creator', 'Date_Digitized', 'Digital_Notes', \
            'Notes', 'Image_Name', 'Ordering_Information', 'Date_Added', 'Date_Revised', 'Digital_Collection', \
            'Scanning_Status', 'Processing_Status', 'Completed_By', 'Digitized_Date', 'Description', 'Subject']
        myData = UnicodeDictReader(open(sys.argv[1]), fieldnames = data_name_fields) 
    else:
        myData = UnicodeDictReader(open(sys.argv[1]))
        data_name_fields = getUnicodeDictReaderFieldnames(open(sys.argv[1]))

    # check data fields to ensure all fields in config are present
    for field in field_map.keys():
        if field not in data_name_fields and field not in generated_fields:
            logFile.write('WARNING: ' + field + ' not found in data. skipping this field in output.\n')
            print 'WARNING: ' + field + ' not found in data. skipping this field in output.\n'

    # loop over each data row; write only those fields listed in config
    count = 0
    for dataRow in myData: 
        # only process rows that have a digital collection matching the one being processed
        if 'Digital_Collection' in data_name_fields:
            if not dataRow['Digital_Collection'] == collection_id:
                continue
        try:
            i = workflow.core.models.Item.objects.get(do_id=dataRow[id_fieldname])
        except Exception as e:
            logFile.write('WARNING: ' + dataRow[id_fieldname] + ' not found in workflow db - skipping this record' + str(e) + '\n')
            print 'WARNING: ' + dataRow[id_fieldname].encode('utf-8') + ' not found in workflow db - skipping this record' + str(e) + '\n'
            continue    
        count = count + 1

        print 'making mods for %s' % (i.do_id,)
        mods = drlutils.mods.utils.set_root()

        for field in field_map:
            if field in data_name_fields or field in generated_fields:
                # map and filter field value 
                value = map_field(field, dataRow, id_fieldname, date_fieldname, date_qualifier_fieldname, source_fieldname, file_fieldname, field_overrides, logFile)
                for mods_map_field in field_map[field].split(','):
                    function_name = 'set_%s' % (mods_map_field,)
                    function = getattr(drlutils.mods.utils, function_name)
                    mods = function(value, mods)    
        mods_file = dataRow[id_fieldname] + '.mods.xml'
        repo_path = drlutils.django.utils.get_repository_path(i)
        if not os.path.exists(repo_path):
            logFile.write('WARNING: ' + repo_path + ' not found. skipping creation of MODS for this item.\n')
            print 'WARNING: ' + repo_path + ' not found. skipping creation of MODS for this item.\n'
            continue
        mods_path = os.path.join(repo_path, mods_file)
        try:
            etree.ElementTree(mods).write(mods_path, pretty_print=True)
        except Exception as e:
            logFile.write('WARNING: Failed writing to %s: %s\n' % (mods_path, e))
            print 'Failed writing to %s: %s' % (mods_path, e)
        drlutils.django.utils.add_file_record(i, mods_path, 'TEXT_XML', 'MODS')
        dc_result = drlutils.dublincore.mods2dc.create(i.do_id)
        if dc_result:
            logFile.write('WARNING: Failed creating dublincore: %s\n' % (dc_result,))
            print 'Failed creating dublincore: %s' % (dc_result,)

if __name__ == '__main__':
    main()

