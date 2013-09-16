"""
Functions to deal with historical data in Top Honors pairing

Run doctests with:
  python -m doctest historical.py
or
  python -m doctest -v historical.py

Terminology:

A Pair is a (date, tutor, student) tuple, which represents a tutor
matched to a single student for a single week.  If, one week, a tutor
is matched with 3 students, that is stored as three separate Pairs.

A Pairing is a set of Pairs that matches all the students to tutors
for a particular week.  The goal of the Pairing Algorithm is to find
the best Pairing for a week, given the Pairings for all previous weeks.

HistoricalData is the set of all past Pairings.  

"""
# -------------------------------------------------------

from __future__ import absolute_import, division, with_statement

import collections
import optparse
import itertools
import re

# -------------------------------------------------------

def main():
    hist = HistoricalData.read_all_data()
    #print hist.to_csv()

    date = 20130413
    session = 'am_purple'

    actual = hist.get_pairing(date, session)
    #print actual
    past_data = hist.get_data_before(date, session)
    print score(actual, past_data)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--date',
                      type=int,
                      default=20130403)
    parser.add_option('--session',
                      default='am_purple')
    args = parser.parse()
    return args

# -------------------------------------------------------

class Pair(object):
    HEADER = ('Date',
              'Session',
              'Tutor First',
              'Tutor Last',
              'Student',
              'Tutor On Own',
              'On Own',
              'Avoid Student',
              'Avoid Tutor',
              'Good Match')

    def __init__(self,
                 date, session,
                 tutor_first, tutor_last,
                 student,
                 tutor_on_own, on_own, avoid_student, avoid_tutor, good_match):
        self.date          = date
        self.session       = session
        self.tutor_first   = tutor_first
        self.tutor_last    = tutor_last
        self.student       = student
        self.tutor_on_own  = tutor_on_own
        self.on_own        = on_own
        self.avoid_student = avoid_student
        self.avoid_tutor   = avoid_tutor
        self.good_match    = good_match

    @classmethod
    def csv_header(cls):
        return ','.join(cls.HEADER)

    @classmethod
    def csv_bool(cls, val):
        return 'TRUE' if val else ''

    def to_csv(self):
        return ','.join(str(s) for s in (self.date,
                                         self.session,
                                         self.tutor_first,
                                         self.tutor_last,
                                         self.csv_bool(self.tutor_on_own),
                                         self.csv_bool(self.on_own),
                                         self.csv_bool(self.avoid_student),
                                         self.csv_bool(self.avoid_tutor),
                                         self.csv_bool(self.good_match)))

    @property
    def tutor(self):
        return '{0} {1}'.format(self.tutor_first, self.tutor_last)

class HistoricalData(object):
    def __init__(self, data=None):
        self.data = [] if data is None else data
        self._data_by_tutor = None

    def to_csv(self):
        return '\n'.join([Pair.csv_header()] +
                         [pair.to_csv()
                          for pair in self.data])

    @classmethod
    def parse_date(cls, column_name):
        """
        >>> HistoricalData.parse_date('05/04 MATCH')
        20130504
        >>> HistoricalData.parse_date('12/15 MATCH')
        20121215
        >>> HistoricalData.parse_date('TUTOR NAME')
        'TUTOR NAME'
        """
        match = re.match('(\d+)/(\d+) MATCH$', column_name)
        if match is None:
            return column_name
        month = int(match.group(1))
        day = int(match.group(2))
        if int(month) < 6:
            year = 2013
        else:
            year = 2012
        return int('{0:04d}{1:02d}{2:02d}'.format(year, month, day))
    
    @classmethod
    def parse_mark(cls, mark, student):
        """
        >>> HistoricalData.parse_mark('OO', 'Nachy OO')
        ('Nachy', True)
        >>> HistoricalData.parse_mark(':-)', 'Tyrique  :-)')
        ('Tyrique', True)
        >>> HistoricalData.parse_mark('X', 'X William P.')
        ('William P.', True)
        >>> HistoricalData.parse_mark('X', 'Alex')
        ('Alex', False)
        >>> HistoricalData.parse_mark('OO', "D'Shun")
        ("D'Shun", False)
        """
        if student.endswith(' ' + mark):
            student = student[:-len(mark)-1].strip()
            return (student, True)
        elif student.startswith(mark + ' '):
            student = student[len(mark)+1:].strip()
            return (student, True)
        return (student, False)

    @classmethod
    def parse_student(cls, student):
        """
        >>> HistoricalData.parse_student('X William P.')
        ('William P.', False, True, False)
        >>> HistoricalData.parse_student('Tyrique  :-)  ')
        ('Tyrique', False, False, True)
        """
        student = student.strip()
        (student, on_own) = cls.parse_mark('OO', student)
        (student, avoid_tutor) = cls.parse_mark('X', student)
        (student, good_match) = cls.parse_mark(':-)', student)
        return (student, on_own, avoid_tutor, good_match)

    @classmethod
    def parse_students(cls, students):
        """
        >>> HistoricalData.parse_students('Maelease / Alyssa')
        (['Maelease ', ' Alyssa'], False)
        >>> HistoricalData.parse_students('Carmen / Mika-Elle')
        (['Carmen ', ' Mika-Elle'], False)
        >>> HistoricalData.parse_students('Michael G.  /  Carmen / Derk')
        (['Michael G.  ', '  Carmen ', ' Derk'], False)
        >>> HistoricalData.parse_students('Chloe // Amanda')
        (['Chloe ', ' Amanda'], True)
        """
        if students.find('//') >= 0:
            students = students.split('//')
            avoid_student = True
        else:
            students = students.split('/')
            avoid_student = False
        return (students, avoid_student)

    def read_file(self, fn, session):
        # In addition to the lines listed under "Missed one", there
        # are also problems with lines like:
        #   "Annabelle +"
        #   "Annabelle w/someone"
        #   lines with no tutor
        #   "see Natasha above"
        self._data_by_tutor = None
        lines = [l.split(',') for l in open(fn).readlines()]
        header = [self.parse_date(c) for c in lines.pop(0)]
        for line in lines:
            tutor_first = None
            tutor_last  = None
            last_fld = None
            for (fld, val) in itertools.izip_longest(header, line):
                val = val.strip()
                if fld == 'TUTOR NAME':
                    tutor_first = val
                    (tutor_first, tutor_on_own) = self.parse_mark(
                        'OO', tutor_first)
                elif last_fld == 'TUTOR NAME':
                    tutor_last = val
                    (tutor_last, tutor_last_on_own) = self.parse_mark(
                        'OO', tutor_last)
                    tutor_on_own = tutor_on_own or tutor_last_on_own
                elif type(fld) == int:
                    if val == '':
                        continue
                    date = fld
                    (students, avoid_student) = self.parse_students(val)
                    for student in students:
                        (student, on_own, avoid_tutor,
                         good_match) = self.parse_student(student)
                        # Sanity Check
                        if any([student.lower().find(mark.lower()) >= 0
                                for mark in ('OO', ' X ', ':-)', '*')]):
                            print 'Missed one? "{0}" -- {1}, {2} {3} {4} {5}'.format(
                                student, val, session, tutor_first,
                                tutor_last, date)
                        self.data.append(Pair(date, session, tutor_first,
                                              tutor_last, student,
                                              tutor_on_own, on_own,
                                              avoid_student,
                                              avoid_tutor,
                                              good_match))
                last_fld = fld

    @classmethod
    def read_all_data(cls):
        obj = cls()
        obj.read_file('am_purple.csv', 'am_purple')
        obj.read_file('am_orange.csv', 'am_orange')
        obj.read_file('pm.csv', 'pm')
        return obj

    @property
    def data_by_tutor(self):
        if self._data_by_tutor is None:
            self._data_by_tutor = collections.defaultdict(list)
            for pair in self.data:
                self._data_by_tutor[(pair.date, pair.tutor)].append(pair)
        return self._data_by_tutor

    def get_pairing(self, date, session):
        return [(d.tutor, d.student)
                for d in self.data
                if d.date == date and d.session == session]

    def get_data_before(self, date, session):
        return HistoricalData([d for d in self.data
                               if d.date < date and d.session == session])

    def get_matches(self,
                    tutor=None,
                    student=None,
                    date=None,
                    session=None):
        return [d for d in self.data
                if ((date is None or date == d.date)
                    and (session is None or session == d.session)
                    and (tutor   is None or tutor == d.tutor)
                    and (student is None or student == d.student))]

    def get_student_pairings(self, student1, student2):
        return [students
                for students in self.data_by_tutor.itervalues()
                if (len(students) > 1
                    and any([s.student == student1 for s in students])
                    and any([s.student == student2 for s in students]))]

# --------------------------------------------------------------------

def score(pairing,
          hist,
          award_past_work=1,
          award_good_match=5,
          penalty_avoid_tutor=20,
          penalty_multiple_students=1,
          penalty_avoid_student=20,
          penalty_tutor_on_own=10,
          penalty_student_on_own=10):
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
    by_tutor = collections.defaultdict(list)
    score = 0
    for (tutor, student) in pairing:
        by_tutor[tutor].append(student)
        prev = hist.get_matches(tutor=tutor, student=student)
        score += len(prev) * award_past_work
        if any([p.avoid_tutor for p in prev]):
            score -= penalty_avoid_tutor
        if any([p.good_match for p in prev]):
            score += award_good_match
    for tutor in by_tutor:
        n_students = len(by_tutor[tutor])
        if n_students < 2:
            continue
        score -= (n_students - 1) * penalty_multiple_students
        if any([p.tutor_on_own for p in hist.get_matches(tutor=tutor)]):
            score -= penalty_tutor_on_own
        if any([p.on_own for p in hist.get_matches(student=student)]):
            score -= penalty_student_on_own
        for ii in xrange(n_students):
            for jj in xrange(ii+1, n_students):
                for pairs in hist.get_student_pairings(by_tutor[tutor][ii],
                                                       by_tutor[tutor][jj]):
                    if any([p.avoid_student for p in pairs]):
                        score -= penalty_avoid_student
                        break
    return score

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

