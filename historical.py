import itertools
import re

def parse_date(column_name):
    match = re.match('(\d+)/(\d+) MATCH$', column_name)
    if match is None:
        return column_name
    month = match.group(1)
    day = match.group(2)
    if int(month) > 6:
        year = 2013
    else:
        year = 2012
    return int('%s%s%s' % (year, month, day))
    
def parse_mark(mark, student):
    if student.endswith(' ' + mark):
        student = student[:-len(mark)-1].strip()
        return (student, 'TRUE')
    elif student.startswith(mark + ' '):
        student = student[len(mark)+1:].strip()
        return (student, 'TRUE')
    return (student, '')

def parse_student(student):
    student = student.strip()
    (student, on_own) = parse_mark('OO', student)
    (student, avoid_tutor) = parse_mark('X', student)
    (student, good_match) = parse_mark(':-)', student)
    return (student, on_own, avoid_tutor, good_match)

def read_file(fn, session):
    output = []
    lines = [l.split(',') for l in open(fn).readlines()]
    header = [parse_date(c) for c in lines.pop(0)]
    for line in lines:
        tutor_first = None
        tutor_last  = None
        last_fld = None
        for (fld, val) in itertools.izip_longest(header, line):
            val = val.strip()
            if fld == 'TUTOR NAME':
                tutor_first = val
                (tutor_first, tutor_on_own) = parse_mark('OO', tutor_first)
            elif last_fld == 'TUTOR NAME':
                tutor_last = val
                (tutor_last, tutor_last_on_own) = parse_mark('OO', tutor_last)
                tutor_on_own = tutor_on_own or tutor_last_on_own
            elif type(fld) == int:
                if val == '':
                    continue
                date = fld
                avoid_student = ''
                if val.find('//') >= 0:
                    students = val.split('//')
                    avoid_student = 'TRUE'
                else:
                    students = val.split('/')
                for student in students:
                    (student, on_own, avoid_tutor, good_match) = parse_student(student)
                    # Sanity Check
                    if any([student.lower().find(mark.lower()) >= 0
                            for mark in ('OO', ' X ', ':-)', '*')]):
                        print ('Missed one? "%s" -- %s, %s %s %s %s' %
                               (student, val, session, tutor_first, tutor_last, date))
                    output.append([str(date), session, tutor_first,
                                   tutor_last, student,
                                   tutor_on_own, on_own,
                                   avoid_student,
                                   avoid_tutor,
                                   good_match])
            last_fld = fld
    return output

# In addition to the lines listed under "Missed one", there are also problems with
# lines like "Annabelle +"
# "Annabelle w/someone"
# and lines with no tutor
# and "see Natasha above"

output = [['Date',
           'Session',
           'Tutor First',
           'Tutor Last',
           'Student',
           'Tutor On Own',
           'On Own',
           'Avoid Student',
           'Avoid Tutor',
           'Good Match']]

output.extend(read_file('am_purple.csv', 'am_purple'))
output.extend(read_file('am_orange.csv', 'am_orange'))
output.extend(read_file('pm.csv', 'pm'))
for line in output:
    print ','.join(line)
