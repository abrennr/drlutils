import sys
import os
from lxml import etree
import re
import drlutils.config


def build(dlxs_xml_file):
	try:
		# pageview filename data is read from derivative image directory
		do_id = re.sub('.xml', '', os.path.basename(dlxs_xml_file))
		pageview_dict = {}
		pageview_dict_source = os.path.join(drlutils.config.DLXS_OBJ_PATH, do_id, do_id) + '.pageview_dict.txt'
		for line in open(pageview_dict_source, 'r').readlines():
			[key, value] = line.strip().split('\t')
			pageview_dict[key] = value
		# dlxs xml is transformed into pageview data 
		dlxs = etree.parse(open(dlxs_xml_file, 'r'))
		pageview_stylesheet = etree.parse(open(drlutils.config.XML2PAGEVIEW_XSL, 'r'))
		transform_dlxs = etree.XSLT(pageview_stylesheet)
		pageview = transform_dlxs(dlxs)	
		# the output from the tranformation is read into a string and
		# further processed to substitute in the correct filename
		p = pageview.__str__()
		lines = p.split('\n')			
		pageview_file = do_id + '.pageview.txt'
		pageview_path = os.path.join(drlutils.config.DLXS_PAGEVIEW_PATH, pageview_file)
		pageview = open(pageview_path, 'w')
		for line in lines:
			if len(line) > 1:
				[idno, image, seq, n, cnf, ftr] = line.split('\t')
				image = pageview_dict[image]
				pageview.write('\t'.join([idno, image, seq, n, cnf, ftr]) + '\n')	
		pageview.close()
		return None
	except Exception as e:
		return 'problem with pageview: ' + do_id + ' - ' + str(e)

if __name__ == '__main__':
        try:
                dlxs_xml_file = sys.argv[1]
        except:
                sys.exit('when running as a script, you must provide a path to a dlxs textclass xml file a an argument')
        result = build(dlxs_xml_file)
        if result:
                print result
        else:
				pass

