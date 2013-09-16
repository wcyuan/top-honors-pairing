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
import itertools
import logging
import optparse
import re

# -------------------------------------------------------

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

def main():
    opts = getopts()
    hist = HistoricalData.read_all_data()
    logging.debug(hist.to_csv())
    logging.getLogger().setLevel(logging.DEBUG)
    print score_historical(hist, opts.date, opts.session)
    logging.getLogger().setLevel(logging.WARN)
    actual = hist.get_pairing(opts.date, opts.session)

    best = good_historical_score(hist, opts.date, opts.session)
    logging.getLogger().setLevel(logging.DEBUG)
    print score(best, hist.get_data_before(opts.date, opts.session))
    print best

    diff_pairings(actual, best)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--date',
                      type=int,
                      default=20130413)
    parser.add_option('--session',
                      default='am_purple')
    parser.add_option('--verbose',
                      action='store_true',
                      help='set log level to DEBUG')
    parser.add_option('--log_level',
                      help='set the log level')
    (opts, args) = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.log_level is not None:
        level = getattr(logging, opts.log_level.upper())
        logging.getLogger().setLevel(level)
        logging.info("Setting log level to %s", level)
        
    return opts

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

    @property
    def all_students(self):
        return sorted(set([d.student for d in self.data]))

    @property
    def all_tutors(self):
        return sorted(set([d.tutor for d in self.data]))

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
        points_past_work = len(prev) * award_past_work
        score += points_past_work
        if points_past_work > 0:
            logging.debug("Score %s: Increasing score by %s because %s and %s "
                          "have worked together %s other times",
                          score, points_past_work, tutor, student, len(prev))
        if any([p.avoid_tutor for p in prev]):
            logging.debug("Score %s: Decreasing score by %s because %s should "
                          "avoid tutor %s",
                          score, penalty_avoid_tutor, student, tutor)
            score -= penalty_avoid_tutor
        if any([p.good_match for p in prev]):
            logging.debug("Score %s: Increasing score by %s because %s is a "
                          "good fit with tutor %s",
                          score, award_good_match, student, tutor)
            score += award_good_match
    for tutor in by_tutor:
        n_students = len(by_tutor[tutor])
        if n_students < 2:
            continue
        points_multiple_students = (n_students - 1)**2 * penalty_multiple_students
        score -= points_multiple_students
        logging.debug("Score %s: Decreasing score by %s because %s is working "
                      "with %s students: %s",
                      score, points_multiple_students, tutor, n_students,
                      by_tutor[tutor])
        if any([p.tutor_on_own for p in hist.get_matches(tutor=tutor)]):
            logging.debug("Score %s: Decreasing score by %s because tutor %s "
                          "should work alone",
                          score, penalty_tutor_on_own, tutor)
            score -= penalty_tutor_on_own
        if any([p.on_own for p in hist.get_matches(student=student)]):
            logging.debug("Score %s: Decreasing score by %s because student %s "
                          "should work alone",
                          score, penalty_student_on_own, student)
            score -= penalty_student_on_own
        for ii in xrange(n_students):
            for jj in xrange(ii+1, n_students):
                for pairs in hist.get_student_pairings(by_tutor[tutor][ii],
                                                       by_tutor[tutor][jj]):
                    if any([p.avoid_student for p in pairs]):
                        logging.debug("Score %s: Decreasing score by %s "
                                      "because student %s "
                                      "should not work with student %s",
                                      score, penalty_avoid_student,
                                      by_tutor[tutor][ii], by_tutor[tutor][jj])
                        score -= penalty_avoid_student
                        break
    return score

def score_historical(hist, date, session):
    actual = hist.get_pairing(date, session)
    past_data = hist.get_data_before(date, session)
    return score(actual, past_data)

def good_pairing(hist, students, tutors):
    """
    Start with an empty pairing.
    Sort the students by their attendance record.
    For each student:
      Calculate the score from adding (tutor, student) to the pairing
      for each tutor.  Take the tutor that results in the highest score.

    This is not guaranteed to result in the best pairing, but it will
    usually result in a pretty good one.

    No attempt was made to make this efficient.
    """
    by_attendance = sorted(students,
                           key = lambda s: len(hist.get_matches(student=s)))
    pairing = []
    for student in by_attendance:
        best_score = None
        best_pair = None
        for tutor in tutors:
            this_score = score(pairing + [(tutor, student)], hist)
            if best_score is None or this_score > best_score:
                best_score = this_score
                best_pair = (tutor, student)
        pairing.append(best_pair)
    return pairing

def good_historical_score(hist, date, session):
    actual = hist.get_pairing(date, session)
    students = set([p[1] for p in actual])
    tutors = set([p[0] for p in actual if p[0].strip() != ''])
    past_data = hist.get_data_before(date, session)
    return good_pairing(past_data, students, tutors)

def diff_pairings(pairing1, pairing2):
    by_student1 = dict((s, t) for (t, s) in pairing1)
    by_student2 = dict((s, t) for (t, s) in pairing2)
    for student in by_student1:
        if student not in by_student2:
            print "-{0}".format(student)
        elif by_student1[student] != by_student2[student]:
            print "{0}: {1} -> {2}".format(student, by_student1[student],
                                           by_student2[student])
    for student in by_student2:
        if student not in by_student1:
            print "+{0}".format(student)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

