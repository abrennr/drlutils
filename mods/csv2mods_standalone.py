import sys
import os
import csv
import codecs
os.environ["DJANGO_SETTINGS_MODULE"] = 'workflow.settings'
import drlutils.config
import drlutils.date.utils 
import drlutils.text.utils
import drlutils.mods.utils
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

def map_field(fieldname, dataRow, logFile):

    if fieldname == 'date':
        if dataRow['normalized_date_qualifier'] == '':
            value = drlutils.date.utils.get_display_date(dataRow['normalized_date']) 
        else:
            value = drlutils.date.utils.get_display_date(dataRow['normalized_date'], questionable=True) 
    elif fieldname == 'sort_date':
        if drlutils.date.utils.is_normalized_date(dataRow['normalized_date']):
            value = drlutils.date.utils.get_sort_date(dataRow['normalized_date'])
        else:
            value = None
    elif fieldname == 'normalized_date' and not drlutils.date.utils.is_normalized_date(dataRow['normalized_date']):
        logFile.write('WARNING: Incorrect normalized date for: ' + dataRow['identifier'].encode('utf-8') + ' date: ' + dataRow['normalized_date'].encode('utf-8') + '\n')
        print 'WARNING: Incorrect normalized date for: ' + dataRow['identifier'].encode('utf-8') + ' date: ' + dataRow['normalized_date'].encode('utf-8') 
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
    
    # open log file
    logFileName = '%s.mods_log.txt' % (sys.argv[1],)
    logFile = codecs.open(logFileName, encoding='utf-8', mode='w')
    logFile.write('starting processing of %s\n\n' % (sys.argv[1],))

    modsFileDirName = '%s-%s-mods' % (sys.argv[1], drlutils.date.utils.get_today_normalized())
    if not os.path.exists(modsFileDirName):
        os.mkdir(modsFileDirName)

    # the image metadata is delivered as a csv file, which may contain
    # more fields than we need. 
    # read csv file into dictionary iterator, keyed by first row field names
    myData = UnicodeDictReader(open(sys.argv[1]))
    data_name_fields = getUnicodeDictReaderFieldnames(open(sys.argv[1]))

    # make sure we at least have an indentifier field
    if not 'identifier' in data_name_fields: 
        logFile.write('No identifier field found in data file.  This is required.\n')
        print 'No identifier field found in data file.  This is required.'
        sys.exit()

    # 'date' and 'sort_date' can be generated here and may not be
    # in source data file.  If not, add them to the list of field names
    if 'normalized_date' in data_name_fields and not 'date' in data_name_fields:
        data_name_fields.append('date')

    if 'normalized_date' and not 'sort_date' in data_name_fields:
        data_name_fields.append('sort_date')

    # check data fields against expected mods field names. 
    # if unknown fields are found, warn and ask for confirmation before
    # continuing 
    for field in data_name_fields:
        if field not in drlutils.config.MODS_FIELD_NAMES: 
            logFile.write('WARNING: ' + field + ' not recognized. Skipping this field in output.\n')
            print 'WARNING: ' + field + ' not recognized. Skipping this field in output.\n'

    keep_going = raw_input('Continue processing? ENTER to continue, CTRL-C to exit\n')

    # loop over each data row; write only those fields recognized as MODS 
    count = 0
    for dataRow in myData: 
        count = count + 1

        if not dataRow['identifier']:
            logFile.write('WARNING: no identifier found in record %s - skipping.\n' % (count,))
            print 'WARNING: no identifier found in record %s - skipping.' % (count,)
            continue
        print 'making mods for %s' % (dataRow['identifier'],)
        mods_xml = drlutils.mods.utils.set_root()
        for field in data_name_fields:
            if field in drlutils.config.MODS_FIELD_NAMES: 
                # map and filter field value 
                value = map_field(field, dataRow, logFile)
                if not value:
                    continue
                function_name = 'set_%s' % (field,)
                function = getattr(drlutils.mods.utils, function_name)
                mods_xml = function(value, mods_xml)    
        mods_file = dataRow['identifier'] + '.mods.xml'
        mods_path = os.path.join(modsFileDirName, mods_file)
        try:
            etree.ElementTree(mods_xml).write(mods_path, pretty_print=True)
        except Exception as e:
            logFile.write('WARNING: Failed writing to %s: %s\n' % (mods_path, e))
            print 'Failed writing to %s: %s' % (mods_path, e)

if __name__ == '__main__':
    main()

