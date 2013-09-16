"""
Functions to deal with historical data in Top Honors pairing
"""
# -------------------------------------------------------

from __future__ import absolute_import, division, with_statement
import itertools
import re

# -------------------------------------------------------

HEADER = ['Date',
          'Session',
          'Tutor First',
          'Tutor Last',
          'Student',
          'Tutor On Own',
          'On Own',
          'Avoid Student',
          'Avoid Tutor',
          'Good Match']

# -------------------------------------------------------

def main():
    output = read_all_data()
    #for line in output:
    #    print ','.join(str(s) for s in line)
    date = 20130403
    session = 'am_purple'

    actual = get_pairing(output, date, session)
    past_data = get_data_before(output, date, session)
    print score(actual, past_data)

# -------------------------------------------------------

def parse_date(column_name):
    match = re.match('(\d+)/(\d+) MATCH$', column_name)
    if match is None:
        return column_name
    month = match.group(1)
    day = match.group(2)
    if int(month) < 6:
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
                    output.append([date, session, tutor_first,
                                   tutor_last, student,
                                   tutor_on_own, on_own,
                                   avoid_student,
                                   avoid_tutor,
                                   good_match])
            last_fld = fld
    return output

def read_all_data():
    return (read_file('am_purple.csv', 'am_purple')
            + read_file('am_orange.csv', 'am_orange')
            + read_file('pm.csv', 'pm'))

# In addition to the lines listed under "Missed one", there are also problems with
# lines like "Annabelle +"
# "Annabelle w/someone"
# and lines with no tutor
# and "see Natasha above"

# --------------------------------------------------------------------

def get_pairing(historical_data, date, session):
    return [(' '.join((d[2], d[3])), d[4])
            for d in historical_data
            if d[0] == date and d[1] == session]

def get_data_before(historical_data, date, session):
    return [d for d in historical_data
            if d[0] < date and d[1] == session]

def get_matches(historical_data,
                tutor_name=None,
                student=None,
                date=None,
                session=None):
    return [d for d in historical_data
            if (date is None or date == d[0]
                and session is None or session == d[1]
                and (tutor_name is None or tutor_name == ' '.join((d[2], d[3])))
                and student is None or student == d[4])]

def score(pairing, historical_data):
    """
    For each student-tutor pair:

    - If the student and tutor have ever been marked as incompatible,
      subtract 20.  Otherwise, add 1 for each time the student and tutor
      have been paired together in the past.

    - For each time in the past when the student and tutor have ever
      been marked as a particularly good match, add another 5.

    For each tutor that is paired with more than one student: Let's
    say there are S students in the group.
    
    - Subtract S-1 from the score (if we have enough tutors, we want to
      encourage one-on-one tutoring).

    - If the students have ever been marked incompatible with each
      other, subtract 20.
    
    - If any student or the tutor have been marked as 'on own',
      subtract 10.
    
    - If any of the students are scheduled to be working on different
      subjects, subtract 5.

    - If any of the students are not the same grade, subtract 2.
    """
    pass

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

