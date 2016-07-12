import sys
import re
import datetime

MONTHS_DIGIT_KEYED = {'01':'January', '02':'February', '03':'March', '04':'April', '05':'May', '06':'June', '07':'July', '08':'August', '09':'September', '10':'October', '11':'November', '12':'December'}

MONTHS_NAME_KEYED = {'January':'01', 'February':'02', 'March':'03', 'April':'04', 'May':'05', 'June':'06', 'July':'07', 'August':'08', 'September':'09', 'October':'10', 'November':'11', 'December':'12', 'Winter':'12', 'Spring':'03', 'Summer':'06', 'Fall':'09'}

def get_today_normalized():
    return datetime.date.today().isoformat()

def get_now_normalized():
    return datetime.datetime.now().isoformat()

def get_display_month(m):
    try:
        return MONTHS_DIGIT_KEYED[m]    
    except:
        return ''
    
def get_normalized_month(m):
    try:
        return MONTHS_NAME_KEYED[m]    
    except:
        return ''
    

def is_normalized_date(d):
    try:
        if re.match('[0-2]\d\d\d$', d):
            return True
        elif re.match('[0-2]\d\d\d/[0-2]\d\d\d$', d):
            return True
        elif re.match('[0-2]\d\d\d-[0-1]\d$', d):
            [y, m] = d.split('-', 1)
            if int(m) in range(1,13):
                return True
            else:
                return False
        elif re.match('[0-2]\d\d\d-[0-1]\d/[0-2]\d\d\d-[0-1]\d$', d):
            [first, second] = d.split('/', 1)
            [y1, m1] = first.split('-', 1)
            [y2, m2] = second.split('-', 1)
            if int(m1) in range(1,13) and int(m2) in range(1,13):
                return True
            else:
                return False
        elif re.match('[0-2]\d\d\d-[0-1]\d-[0-3]\d$', d):
            [y, m, d] = d.split('-', 2)
            if int(m) in range(1,13) and int(d) in range(1,32):
                return True
            else:
                return False
        elif re.match('[0-2]\d\d\d-[0-1]\d-[0-3]\d/[0-2]\d\d\d-[0-1]\d-[0-3]\d$', d):
            [first, second] = d.split('/', 1)
            [y1, m1, d1] = first.split('-', 2)
            [y2, m2, d2] = second.split('-', 2)
            if int(m1) in range(1,13) and int(d1) in range(1,32) and int(m2) in range(1,13) and int(d2) in range(1,32):
                return True
            else:
                return False
        else:
            return False
    except:
        return False

def get_display_date(d, questionable=False):
    circa = 'ca. '
    # form of YYYY 
    if re.match('[0-2]\d\d\d$', d):
        date = d 
    # form of YYYY/YYYY 
    elif re.match('[0-2]\d\d\d/[0-2]\d\d\d$', d):
        questionable = True
        [first, second] = d.split('/', 1)
        if first[0:3] == second[0:3] and first.endswith('0') and second.endswith('9'):
            date =  str(first) + 's'
        else:
            date =  str(first) + '-' + str(second)
    # form of YYYY-MM
    elif re.match('[0-2]\d\d\d-[0-1]\d$', d):
        [y, m] = d.split('-', 1)
        month = get_display_month(m)    
        date =  month + ', ' + y 
    # form of YYYY-MM/YYYY-MM
    elif re.match('[0-2]\d\d\d-[0-1]\d/[0-2]\d\d\d-[0-1]\d$', d):
        questionable = True
        [first, second] = d.split('/', 1)
        [y1, m1] = first.split('-', 1)
        [y2, m2] = second.split('-', 1)
        month1 = get_display_month(m1)    
        month2 = get_display_month(m2)    
        if y1 == y2:
            date = month1 + '-' + month2 + ', ' + str(y1)
        else:
            date = month1 + ', ' + str(y1) + '-' + month2 + ', ' + str(y2)
    # form of YYYY-MM-DD
    elif re.match('[0-2]\d\d\d-[0-1]\d-[0-3]\d$', d):
        [y, m, d] = d.split('-', 2)
        day = str(int(d))
        month = get_display_month(m)    
        date = month + ' ' + day + ', ' + y
    # form of YYYY-MM-DD/YYYY-MM-DD
    elif re.match('[0-2]\d\d\d-[0-1]\d-[0-3]\d/[0-2]\d\d\d-[0-1]\d-[0-3]\d$', d):
        questionable = True
        [first, second] = d.split('/', 1)
        [y1, m1, d1] = first.split('-', 2)
        day1 = str(int(d1))
        month1 = get_display_month(m1)    
        [y2, m2, d2] = second.split('-', 2)
        day2 = str(int(d2))
        month2 = get_display_month(m2)    
        if y1 == y2:
            if m1 == m2:
                date = month1 + ' ' + day1 + '-' + day2 + ', ' + y1
            else:
                date = month1 + ' ' + day1 + '-' + month2 + ' ' + day2 + ', ' + y1
        else:
            date = month1 + ' ' + day1 + ', ' + y1 + '-' + month2 + ' ' + day2 + ', ' + y2
    else:
        date = d
    if questionable:
        return '%s%s' % (circa, date)
    else:
        return date

def get_normalized_date(d):
    try:
        d = d.strip()
        d = re.sub('\[', '', d)
        d = re.sub('\]', '', d)
        d = re.sub('^circa\s?', '', d)
        d = re.sub('^ca\.\s?', '', d)
        d = re.sub('^c\.\s?', '', d)
        d = re.sub('(\d\d?)th', '\g<1>', d)
        d = re.sub('(\d\d?)nd', '\g<1>', d)
        d = re.sub('(\d\d?)rd', '\g<1>', d)
        d = re.sub('(\d\d?)st', '\g<1>', d)
        # form of "YYYY"
        if re.match('^\d\d\d\d$', d):
            return d
        # form of "YYYY-YYYY"
        elif re.match('^\d\d\d\d-\d\d\d\d', d):
            d = re.sub('-', '/', d)
            return d
        # form of "Month, YYYY"
        m = re.match('(?P<month>\w+),?\s?(?P<year>\d\d\d\d)$', d)
        if m:
            return '%s-%s' % (m.group('year'), MONTHS_NAME_KEYED[m.group('month')])
        # form of "Month-Month, YYYY"
        m = re.match('(?P<month1>\w+)-(?P<month2>\w+),?\s?(?P<year>\d\d\d\d)$', d)
        if m:
            return '%s-%s/%s-%s' % (m.group('year'), MONTHS_NAME_KEYED[m.group('month1')], m.group('year'), MONTHS_NAME_KEYED[m.group('month2')])
        # form of "Month [day], YYYY"
        m = re.match('(?P<month>\w+) (?P<day>\d\d?),?\s?(?P<year>\d\d\d\d)$', d)
        if m:
            day = zeropad(m.group('day'), places=2)
            return '%s-%s-%s' % (m.group('year'), MONTHS_NAME_KEYED[m.group('month')], day)
            return d
        # form of "Month [day]-[day], YYYY"
        m = re.match('(?P<month>\w+) (?P<day1>\d\d?)-(?P<day2>\d\d?),?\s?(?P<year>\d\d\d\d)$', d)
        if m:
            day1 = zeropad(m.group('day1'), places=2)
            day2 = zeropad(m.group('day2'), places=2)
            return '%s-%s-%s/%s-%s-%s' % (m.group('year'), MONTHS_NAME_KEYED[m.group('month')], day1, m.group('year'), MONTHS_NAME_KEYED[m.group('month')], day2)
        # form of "Month [day], YYYY-Month [day], YYYY"
        m = re.match('(?P<month1>\w+) (?P<day1>\d\d?),?\s?(?P<year1>\d\d\d\d)\s?-\s?(?P<month2>\w+) (?P<day2>\d\d?),?\s?(?P<year2>\d\d\d\d)$', d)
        if m:
            day1 = zeropad(m.group('day1'), places=2)
            day2 = zeropad(m.group('day2'), places=2)
            return '%s-%s-%s/%s-%s-%s' % (m.group('year1'), MONTHS_NAME_KEYED[m.group('month1')], day1, m.group('year2'), MONTHS_NAME_KEYED[m.group('month2')], day2)
        return d
    except:
        return d

def get_sort_date(d):
    try:
        # if date is a range, use only the first value to create sort date
        if '/' in d: 
            [first, second] = d.split('/', 1)
            d = first 

        # form of YYYY 
        if re.match('[0-2]\d\d\d$', d):
            year = int(d)
            month = 1
            day = 1
            return datetime.datetime(year, month, day).isoformat()
        # form of YYYY-MM
        elif re.match('[0-2]\d\d\d-[0-1]\d$', d):
            [year, month] = d.split('-', 1)
            day = 1
            return datetime.datetime(int(year), int(month), day).isoformat()
        # form of YYYY-MM-DD
        elif re.match('[0-2]\d\d\d-[0-1]\d-[0-3]\d$', d):
            [year, month, day] = d.split('-', 2)
            return datetime.datetime(int(year), int(month), int(day)).isoformat()
        else:
            return None
    except:
        return None
 
