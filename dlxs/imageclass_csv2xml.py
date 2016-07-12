#!/usr/local/bin/python
import sys
import os
import csv
import codecs
import json
import urllib
import drlutils.date.utils 
import drlutils.text.utils
import drlutils.django.utils
import drlutils.config

generated_fields = ['Digital_Collection', 'Collection_Id', 'Display_Date', 'Longitude', 'Latitude', 'Heading', 'Pitch', 'Zoom']

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

def get_config_maps(c_id):
	url = 'http://%s/cgi-bin/drl/dlxs_img_config?c_id=%s&type=maps' % (drlutils.config.WEB_HOST, c_id,)
	u = urllib.urlopen(url)
	return json.load(u)

def main(csv_file):
		
	if not csv_file and os.path.exists(csv_file):
		print 'You must give a csv data file as an argument to this script'
		sys.exit()

	collection_id = raw_input('Please enter the collection id to be processed: ')
	c = drlutils.django.utils.get_collection(collection_id) 
	drl_c = drlutils.django.utils.get_DRL_collection(c)

	# each collection has config data stored in the database.
	# read config data, create lists to store config data 
	config_name_fields = get_config_fields(collection_id)
	config_maps = get_config_maps(collection_id)

	# open log file
	logFileName = c.c_id + '.log.txt'
	logFile = codecs.open(logFileName, encoding='utf-8', mode='w')
	logFile.write('starting processing of ' + c.c_id + '\n\n')

	# these fields require special validation or processing.  Because we don't know what
	# the field name used to represent these will be for any given collection, we use
	# the Dublin Core mapping in the config file to capture the field name.
	id_fieldname = config_maps['dc_id'] 
	date_fieldname = config_maps['dc_da'] 
	dc_source_fieldname = config_maps['dc_so'] 
	file_fieldname = config_maps['ic_fn'] 

	if not id_fieldname:
		logFile.write('No field found with DC.id in configuration data.  This is required.\n')
		print 'No field found with DC.id in configuration data.  This is required.'
		sys.exit()

	if not file_fieldname:
		logFile.write('No field found with IC.fn in configuration data. This is required.\n')
		print 'No field found with IC.fn in configuration data. This is required.'
		sys.exit()

	# the image metadata is delivered as a csv file, which may contain
	# more fields than we need. 
	# read csv file into dictionary iterator, keyed by first row field names
	if c.c_id in ['hpicasc', 'darlimg', 'darlbroadsides', 'corsini']:
		data_name_fields = ['Title', 'Collection', 'Identifier', \
			'File_Name', 'Batch', 'Normalized_Date', 'Image_Number', 'Location', 'Date', 'Address', \
			'Format', 'Rights', 'Creator', 'Date_Digitized', 'Digital_Notes', \
			'Notes', 'Image_Name', 'Ordering_Information', 'Date_Added', 'Date_Revised', 'Digital_Collection', \
			'Scanning_Status', 'Processing_Status', 'Completed_By', 'Digitized_Date', 'Description', 'Subject']
		myData = UnicodeDictReader(open(csv_file), fieldnames = data_name_fields) 
	else:
		myData = UnicodeDictReader(open(csv_file))
		data_name_fields = getUnicodeDictReaderFieldnames(open(csv_file))

	# check data fields to ensure all fields in config are present
	for config_field in config_name_fields:
		if config_field not in data_name_fields and config_field not in generated_fields:
			print 'WARNING: ' + config_field + ' not found in data. skipping this field in output.\n'
			logFile.write('WARNING: ' + config_field + ' not found in data. skipping this field in output.\n')

	# to enable sorting of data records, create a dictionary with the value of the designated sort field
	# as the key and the whole data row as the value 
	sort_dict = {}
	print 'getting sort values out of data...'
	for row in myData:
		sort_val = str(row[drl_c.sort_field])
		if sort_val == None:
			sort_val == '0'
		# because a dict can't have duplicate keys, if we have duplicate
		# values in the sort field, we have to make them artificially
		# unique, albeit in a way that won't disrupt the sorting:
		try:
			while sort_dict[sort_val]:
				sort_val = sort_val + '_'
		except:
			sort_dict[sort_val] = row
	print 'done getting sort values.'


	# open XML file for writing data
	dataFile = c.c_id + '-data.xml'
	dataXml = codecs.open(dataFile, encoding='utf-8', mode='w')
	dataXml.write('<?xml version="1.0" encoding="UTF-8" ?><!-- This grammar has been deprecated - use FMPXMLRESULT instead --><FMPDSORESULT xmlns="http://www.filemaker.com/fmpdsoresult"><ERRORCODE>0</ERRORCODE><DATABASE>hpicchatham-data Converted.fp7</DATABASE><LAYOUT></LAYOUT>')

	# open txt file for writing asc database macro d data
	macroDFile = c.c_id + '-macrod.txt'
	macroDtxt = open(macroDFile, 'w')

	# loop over each data row; write only those fields listed in config
	count = 0
	for k in sorted(sort_dict.keys()): 
		dataRow = sort_dict[k]
		# only process rows that have a digital collection matching the one being processed
		if 'Digital_Collection' in data_name_fields:
			if not dataRow['Digital_Collection'] == c.c_id:
				continue
		try:
			i = drlutils.django.utils.get_item(dataRow[id_fieldname])
		except Exception as e:
			print 'WARNING: ' + dataRow[id_fieldname].encode('utf-8') + ' not found in workflow db - skipping this record' + str(e) + '\n'
			logFile.write('WARNING: ' + dataRow[id_fieldname] + ' not found in workflow db - skipping this record' + str(e) + '\n')
			continue	
		macroDtxt.write('"' + dataRow[id_fieldname] + '"\n')
		count = count + 1
		rowTag = '<ROW MODID="0" RECORDID="' + str(count) + '">'
		dataXml.write(rowTag)
		for fieldname in config_name_fields:
			line = ''
			field = fieldname.replace(' ', '_')
			fieldOpen = '<' + field + '>'
			fieldClose = '</' + field + '>'
			# map Digital Collection fieldname to collection URL 
			if fieldname == 'Digital_Collection':
				try:
					line = drlutils.django.utils.get_source_collection(dataRow[dc_source_fieldname]).url
				except:
					if drl_c.url:
						line = drl_c.url
			elif fieldname == 'Display_Date':
				try:
					line = dataRow[fieldname] 
				except:
					line = drlutils.date.utils.get_display_date(dataRow[date_fieldname]) 
			elif (fieldname == 'Subject') and dataRow[fieldname] == '':
				line = 'cataloging in progress'
			elif fieldname == dc_source_fieldname: 
				try:
					line = drlutils.django.utils.get_source_collection(dataRow[fieldname]).name
				except:
					line = dataRow[fieldname]
			elif fieldname == 'Collection_Id': 
				try:
					line = drlutils.django.utils.get_source_collection(dataRow[dc_source_fieldname]).digital_collection_id
				except:
					line =  dataRow[dc_source_fieldname]
			elif fieldname == 'Longitude': 
				#try:
			#		line = drlutils.django.utils.get_retrographer_tag(dataRow[id_fieldname]).long
			#		line = str(line)
			#	except:
					line = ""
			elif fieldname == 'Latitude':
			#	try:
			#		line = drlutils.django.utils.get_retrographer_tag(dataRow[id_fieldname]).lat
			#		line = str(line)
			#	except:
					line = ""
			elif fieldname == 'Heading':
			#	try:
			#		line = drlutils.django.utils.get_retrographer_tag(dataRow[id_fieldname]).heading
			#		line = str(line)
			#	except:
					line = ""
			elif fieldname == 'Zoom':
			#	try:
			#		line = drlutils.django.utils.get_retrographer_tag(dataRow[id_fieldname]).zoom
			#		line = str(line)
			#	except:
					line = ""
			elif fieldname == 'Pitch':
			#	try:
			#		line = drlutils.django.utils.get_retrographer_tag(dataRow[id_fieldname]).pitch
			#		line = str(line)
			#	except:
					line = ""
			elif fieldname in data_name_fields:
				if fieldname == file_fieldname:
					try:
						line = os.path.basename(drlutils.django.utils.get_master_file_list(i)[0])
					except Exception as e:
						print 'WARNING: ' + dataRow[id_fieldname].encode('utf-8') + ' failed image check: ' + str(e) + ' - skipping.\n'
						logFile.write('WARNING: ' + dataRow[id_fieldname] + ' failed image check: ' + str(e) + ' - skipping\n')
						line = dataRow[fieldname]
				else:
					line = dataRow[fieldname]
				if fieldname == date_fieldname and not drlutils.date.utils.is_normalized_date(dataRow[fieldname]):
					logFile.write('WARNING: Incorrect normalized date for: ' + dataRow[id_fieldname] + ' date: ' + dataRow[fieldname] + '\n') 
					print 'WARNING: Incorrect normalized date for: ' + dataRow[id_fieldname].encode('utf-8') + ' date: ' + dataRow[fieldname].encode('utf-8') 
			# filter data to de-microsoft characters
			filtered = drlutils.text.utils.filter_for_xml(drlutils.text.utils.filter_ms_characters(line))
			if filtered:
				dataXml.write(fieldOpen + filtered + fieldClose)
			else:
				dataXml.write(fieldOpen + fieldClose)
		dataXml.write('</ROW>')
	dataXml.write('</FMPDSORESULT>')

