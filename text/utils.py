import re

ROMAN_NUMERALS = ['0', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx', 'xxi', 'xxii', 'xxiii', 'xxiv', 'xxv', 'xxvi', 'xxvii', 'xxviii', 'xxix', 'xxx', 'xxxi', 'xxxii', 'xxxiii', 'xxxiv', 'xxxv', 'xxxvi', 'xxxvii', 'xxxviii', 'xxxix', 'xl', 'xli', 'xlii', 'xliii', 'xliv', 'xlv', 'xlvi', 'xlvii', 'xlviii', 'xlix', 'l']

cp1252 = {
    # from http://www.microsoft.com/typography/unicode/1252.htm
    u"\x80": u"\u20AC", # EURO SIGN
    u"\x82": u"\u201A", # SINGLE LOW-9 QUOTATION MARK
    u"\x83": u"\u0192", # LATIN SMALL LETTER F WITH HOOK
    u"\x84": u"\u201E", # DOUBLE LOW-9 QUOTATION MARK
    u"\x85": u"\u2026", # HORIZONTAL ELLIPSIS
    u"\x86": u"\u2020", # DAGGER
    u"\x87": u"\u2021", # DOUBLE DAGGER
    u"\x88": u"\u02C6", # MODIFIER LETTER CIRCUMFLEX ACCENT
    u"\x89": u"\u2030", # PER MILLE SIGN
    u"\x8A": u"\u0160", # LATIN CAPITAL LETTER S WITH CARON
    u"\x8B": u"\u2039", # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    u"\x8C": u"\u0152", # LATIN CAPITAL LIGATURE OE
    u"\x8E": u"\u017D", # LATIN CAPITAL LETTER Z WITH CARON
    u"\x91": u"\u2018", # LEFT SINGLE QUOTATION MARK
    u"\x92": u"\u2019", # RIGHT SINGLE QUOTATION MARK
    u"\x93": u"\u201C", # LEFT DOUBLE QUOTATION MARK
    u"\x94": u"\u201D", # RIGHT DOUBLE QUOTATION MARK
    u"\x95": u"\u2022", # BULLET
    u"\x96": u"\u2013", # EN DASH
    u"\x97": u"\u2014", # EM DASH
    u"\x98": u"\u02DC", # SMALL TILDE
    u"\x99": u"\u2122", # TRADE MARK SIGN
    u"\x9A": u"\u0161", # LATIN SMALL LETTER S WITH CARON
    u"\x9B": u"\u203A", # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    u"\x9C": u"\u0153", # LATIN SMALL LIGATURE OE
    u"\x9E": u"\u017E", # LATIN SMALL LETTER Z WITH CARON
    u"\x9F": u"\u0178", # LATIN CAPITAL LETTER Y WITH DIAERESIS
}

def filter_ms_characters(t):
    # originally from http://effbot.org/zone/unicode-gremlins.htm
    # map cp1252 gremlins to real unicode characters
    if isinstance(t, type("")):
        # make sure we have a unicode string
        t = unicode(t, "iso-8859-1")
    if re.search(u"[\x80-\x9f]", t):
        def fixup(m):
            s = m.group(0)
            return cp1252.get(s, s)
        if isinstance(t, type("")):
            # make sure we have a unicode string
            t = unicode(t, "iso-8859-1")
        t = re.sub(u"[\x80-\x9f]", fixup, t)
    return t


def filter_to_ascii(t):
    printable = frozenset('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r')
    return filter(printable.__contains__, t)

def filter_whitespace(t):
    filter_dict = {
        '\n' : ' ',
        '\t' : ' ',
        '\r' : ' ',
    }
    regex = re.compile("(%s)" % "|".join(map(re.escape, filter_dict.keys())))
    return regex.sub(lambda mo: filter_dict[mo.string[mo.start():mo.end()]], t)


def filter_for_xml(t):
    filter_dict = {
        '&' : '&amp;',
        '>' : '&gt;',
        '<' : '&lt;',
    }
    regex = re.compile("(%s)" % "|".join(map(re.escape, filter_dict.keys())))
    return regex.sub(lambda mo: filter_dict[mo.string[mo.start():mo.end()]], t)


def identifier_is_valid(id):
    if re.search('[^a-zA-Z0-9\-_.]', id): 
        return False 
    else:
        return True 

def get_roman_numeral(i):
    try:
        return ROMAN_NUMERALS[i]
    except:
        return i

def shorten_string(title, length=50):
    if len(title) > length:
        return title[0:length] + '[...]'
    else:
        return title

def get_humanized_bytes(bytes):
    if not bytes:
        return '0'
    elif bytes < 1048576:
        return str(bytes/1024) + ' KB'
    elif bytes < 1073741824:
        return str(bytes/1048576) + ' MB'
    else:
        return str(bytes/1073741824) + ' GB'

def zeropad(i, places=4):
    s = str(i)
    while len(s) < places:
        s = '0%s' % (s,)
    return s


def split_textfile(file, split_char=''):
    (sourcedir, filename) = os.path.split(file)
    sourcefile = open(file)
    pages = sourcefile.read().split(split_char)
    # last 'page' is non-existant, because split on final page break char
    # remove it.
    pages.pop()
    for (page_no, page_text) in enumerate(pages, start=1):
        filename = '%s.txt' % (zeropad(page_no),)
        filepath = os.path.join(sourcedir, filename)
        split_file = open(filepath, 'w')
        split_file.write(page_text)
        split_file.close()


def quote_field(s):
    return '"%s"' % (s,)


def tab2csv(file_obj):
    csv = []
    for line in file_obj: 
        line = line.strip() 
        line = re.sub('"', '""', line)
        fields = line.split('\t')
        quoted_fields = map(quote_field, fields)
        csv_line = ','.join(quoted_fields)
        csv.append(csv_line)
    return '\n'.join(csv)

        
def indent_markup(text):
    """ NOTE: This is not working properly -- needs work """
    inputLines = text.split('\n')
    output = []
 
    level = 0
 
    for line in inputLines:
        line = line.strip()
        split_lines = line.split('<')
        for s_line in split_lines:
            s_line = '<' + s_line
            output.append(('    ' * level) + s_line)
            if s_line.startswith('</'):
                level -= level
            else:
                level += level
    return '\n'.join(output)
 
