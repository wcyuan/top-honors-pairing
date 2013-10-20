#!/usr/bin/env python
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

 - API
 set current attendance for tutors and students
 run pairing for this week (overwriting anything that's there)
 modify the pairing
 score the given pairing
 set compatibility information
 validate (make sure no names are misspelled, that the format is ok, etc)

 - data layout: many separate files
   - input attendance
   - historical data
   - score parameters
   - a run log
   - a bitbucket git repo inside of a dropbox shared folder (?)
     - stores everything (including data)?  or just the code?
       or just the code and the historical data?
       is the data sensitive?  Just use github?

 - plan:
 figure out the new format -- how to represent compatibility info?
 create a class for reading/writing a new format
 reformat the historical data into sample data
 create Windows shortcuts to run on the sample data (each value in the API)
 put things on dropbox/git

 - maybe/somday?
 python gui?
 http://farhadi.ir/projects/html5sortable/

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
    hist = get_2012_data()
    given_params = dict((k, getattr(opts, k))
                        for k in ScoreParams.PARAMS
                        if hasattr(opts, k))
    params = ScoreParams(**given_params)
    run_pairing_code(opts.date,
                     opts.session,
                     hist=hist,
                     params=params,
                     show_details=opts.verbose)

def run_pairing_code(date, session,
                     hist=None,
                     params=None,
                     show_details=False):
    if hist is None:
        hist = get_2012_data()
    if params is None:
        params = ScoreParams()

    print "Calculating ... "
    print

    actual = hist.get_pairing(date, session)
    (actual_score, actual_ann) = score_historical(hist, date, session, params)

    best = good_historical_score(hist, date, session, params)
    (best_score, best_ann) = get_score(
        best, hist.get_data_before(date, session))

    print " ... Done"
    print

    if not show_details:
        actual_ann = None
        best_ann = None

    print "Score for the actual pairing used: ", actual_score
    print "Score for the suggested pairing: ", best_score
    print
    print "Here is the actual pairing used on ", date, session
    print
    print_pairing(actual, actual_ann)
    print
    print "Here is the suggested pairing:"
    print
    print_pairing(best, best_ann)
    print
    print "Here are the differences:"
    print
    diff_pairings(actual, best, actual_ann, best_ann)

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--date',
                      type=int,
                      default=20130413)
    parser.add_option('--session',
                      default='am_purple')
    parser.add_option('--verbose',
                      action='store_true',
                      help='show score annotations')
    parser.add_option('--log_level',
                      help='set the log level')
    for param in ScoreParams.PARAMS:
        parser.add_option('--' + param,
                          default=ScoreParams.PARAMS[param])

    (opts, args) = parser.parse_args()

    if len(args) > 0:
        raise ValueError("Did not expect to get any arguments: {0}".
                         format(args))

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
        # Instead of avoid_student being a boolean, should it be a
        # list of the names students to avoid?
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
                                         self.student,
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
    def pairing_by_tutor(cls, pairing):
        """
        Given a pairing (a list of (tutor, student)), return a dictionary
        from tutor to a list of students.
        """
        by_tutor = collections.defaultdict(list)
        for (tutor, student) in pairing:
            by_tutor[tutor].append(student)
        return by_tutor

    def add_pairings(self, pairings):
        self._data_by_tutor = None
        self.data.extend(pairings)

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

class ParseManualFile(object):
    @classmethod
    def parse_date(cls, column_name, start_year=2012):
        """
        >>> ParseManualFile.parse_date('05/04 MATCH', 2012)
        20130504
        >>> ParseManualFile.parse_date('12/15 MATCH', 2012)
        20121215
        >>> ParseManualFile.parse_date('TUTOR NAME', 2012)
        'TUTOR NAME'
        """
        match = re.match('(\d+)/(\d+) MATCH$', column_name)
        if match is None:
            return column_name
        month = int(match.group(1))
        day = int(match.group(2))
        if int(month) < 6:
            year = start_year + 1
        else:
            year = start_year
        return int('{0:04d}{1:02d}{2:02d}'.format(year, month, day))

    @classmethod
    def parse_mark(cls, mark, student):
        """
        >>> ParseManualFile.parse_mark('OO', 'Nachy OO')
        ('Nachy', True)
        >>> ParseManualFile.parse_mark(':-)', 'Tyrique  :-)')
        ('Tyrique', True)
        >>> ParseManualFile.parse_mark('X', 'X William P.')
        ('William P.', True)
        >>> ParseManualFile.parse_mark('X', 'Alex')
        ('Alex', False)
        >>> ParseManualFile.parse_mark('OO', "D'Shun")
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
        >>> ParseManualFile.parse_student('X William P.')
        ('William P.', False, True, False)
        >>> ParseManualFile.parse_student('Tyrique  :-)  ')
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
        >>> ParseManualFile.parse_students('Maelease / Alyssa')
        (['Maelease ', ' Alyssa'], False)
        >>> ParseManualFile.parse_students('Carmen / Mika-Elle')
        (['Carmen ', ' Mika-Elle'], False)
        >>> ParseManualFile.parse_students('Michael G.  /  Carmen / Derk')
        (['Michael G.  ', '  Carmen ', ' Derk'], False)
        >>> ParseManualFile.parse_students('Chloe // Amanda')
        (['Chloe ', ' Amanda'], True)
        """
        if students.find('//') >= 0:
            students = students.split('//')
            avoid_student = True
        else:
            students = students.split('/')
            avoid_student = False
        return (students, avoid_student)

    @classmethod
    def read_file(cls, fn, session, start_year=2012):
        data = []
        # In addition to the lines listed under "Missed one", there
        # are also problems with lines like:
        #   "Annabelle +"
        #   "Annabelle w/someone"
        #   lines with no tutor
        #   "see Natasha above"
        lines = [l.split(',') for l in open(fn).readlines()]
        header = [cls.parse_date(c, start_year=start_year)
                  for c in lines.pop(0)]
        for line in lines:
            tutor_first = None
            tutor_last  = None
            last_fld = None
            for (fld, val) in itertools.izip_longest(header, line):
                val = val.strip()
                if fld == 'TUTOR NAME':
                    tutor_first = val
                    (tutor_first, tutor_on_own) = cls.parse_mark(
                        'OO', tutor_first)
                elif last_fld == 'TUTOR NAME':
                    tutor_last = val
                    (tutor_last, tutor_last_on_own) = cls.parse_mark(
                        'OO', tutor_last)
                    tutor_on_own = tutor_on_own or tutor_last_on_own
                elif type(fld) == int:
                    if val == '':
                        continue
                    date = fld
                    (students, avoid_student) = cls.parse_students(val)
                    for student in students:
                        (student, on_own, avoid_tutor,
                         good_match) = cls.parse_student(student)
                        # Sanity Check
                        if any([student.lower().find(mark.lower()) >= 0
                                for mark in ('OO', ' X ', ':-)', '*')]):
                            logging.info('Missed one? "{0}" -- {1}, {2} {3} {4} {5}'.
                                         format(student, val, session,
                                                tutor_first, tutor_last, date))
                        data.append(Pair(date, session, tutor_first,
                                         tutor_last, student,
                                         tutor_on_own, on_own,
                                         avoid_student,
                                         avoid_tutor,
                                         good_match))
                last_fld = fld
        return data

def get_2012_data():
    data = []
    data.extend(ParseManualFile.read_file('am_purple.csv', 'am_purple', 2012))
    data.extend(ParseManualFile.read_file('am_orange.csv', 'am_orange', 2012))
    data.extend(ParseManualFile.read_file('pm.csv', 'pm', 2012))
    return HistoricalData(data)

# --------------------------------------------------------------------

class ScoreParams(object):
    PARAMS = {'award_past_work'          : 1,
              'award_good_match'         : 5,
              'penalty_avoid_tutor'      : 20,
              'penalty_multiple_students': 1,
              'penalty_avoid_student'    : 20,
              'penalty_tutor_on_own'     : 10,
              'penalty_student_on_own'   : 10}

    def __init__(self, **kwargs):
        for param in self.PARAMS:
            val = kwargs[param] if param in kwargs else self.PARAMS[param]
            setattr(self, param, val)
        for kwarg in kwargs:
            if kwarg not in self.PARAMS:
                raise ValueError("Bad score parameter {0}, "
                                 "should be one of {1}".
                                 format(kwarg,
                                        ', '.join(self.PARAMS)))

def get_group_score(hist, tutor, students, params=None, **kwargs):
    if params is None:
        params = ScoreParams(**kwargs)

    annotations = collections.defaultdict(list)
    score = 0
    for student in students:
        prev = hist.get_matches(tutor=tutor, student=student)
        points_past_work = len(prev) * params.award_past_work
        score += points_past_work
        if points_past_work > 0:
            logging.debug("Score %s: Increasing score by %s because %s and %s "
                          "have worked together %s other times",
                          score, points_past_work, tutor, student, len(prev))
            annotations[(tutor, student)].append(
                (points_past_work,
                 "+{0}*{1} because {2} and {3} have worked together".
                 format(len(prev), params.award_past_work, tutor, student)))
        if any([p.avoid_tutor for p in prev]):
            logging.debug("Score %s: Decreasing score by %s because %s should "
                          "avoid tutor %s",
                          score, params.penalty_avoid_tutor, student, tutor)
            score -= params.penalty_avoid_tutor
            annotations[(tutor, student)].append(
                (-params.penalty_avoid_tutor,
                  "-{0} because {1} and {2} shouldn't work together".
                  format(params.penalty_avoid_tutor, tutor, student)))
        if any([p.good_match for p in prev]):
            logging.debug("Score %s: Increasing score by %s because %s is a "
                          "good fit with tutor %s",
                          score, params.award_good_match, student, tutor)
            score += params.award_good_match
            annotations[(tutor, student)].append(
                (params.award_good_match,
                 "+{0} because {1} and {2} are a good match".
                 format(params.award_good_match, tutor, student)))

    n_students = len(students)
    if n_students < 2:
        return (score, annotations)
    # Arbitrarily attach annotations to the first student
    student1 = students[0]
    points_multiple_students = ((n_students - 1)**2 *
                                params.penalty_multiple_students)
    score -= points_multiple_students
    logging.debug("Score %s: Decreasing score by %s because %s is working "
                  "with %s students: %s",
                  score, points_multiple_students, tutor, n_students,
                  students)
    annotations[(tutor, student1)].append(
        (-points_multiple_students,
          "-{0} because {1} is working with {2} students".
          format(points_multiple_students, tutor, n_students)))
    if any([p.tutor_on_own for p in hist.get_matches(tutor=tutor)]):
        logging.debug("Score %s: Decreasing score by %s because tutor %s "
                      "should work alone",
                      score, params.penalty_tutor_on_own, tutor)
        score -= params.penalty_tutor_on_own
        annotations[(tutor, student1)].append(
            (-params.penalty_tutor_on_own,
              "-{0} because tutor {1} should only work on own".
              format(params.penalty_tutor_on_own, tutor)))
    for student in students:
        if any([p.on_own for p in hist.get_matches(student=student)]):
            logging.debug("Score %s: Decreasing score by %s because "
                          "student %s should work alone",
                          score, params.penalty_student_on_own, student)
            score -= params.penalty_student_on_own
            annotations[(tutor, student)].append(
                (-params.penalty_tutor_on_own,
                  "-{0} because student {1} should only work on own".
                  format(params.penalty_tutor_on_own, student)))
    for ii in xrange(n_students):
        for jj in xrange(ii+1, n_students):
            for pairs in hist.get_student_pairings(students[ii],
                                                   students[jj]):
                if any([p.avoid_student for p in pairs]):
                    logging.debug("Score %s: Decreasing score by %s "
                                  "because student %s "
                                  "should not work with student %s",
                                  score, params.penalty_avoid_student,
                                  students[ii], students[jj])
                    score -= params.penalty_avoid_student
                    annotations[(tutor, students[ii])].append(
                        (-params.penalty_avoid_student,
                          "-{0} because students {1} and {2} should "
                          "not work with each other".
                          format(params.penalty_avoid_student,
                                 students[ii],
                                 students[jj])))
                    break
    return (score, annotations)

def get_score(pairing, hist, params=None, **kwargs):
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

    @return Returns a tuple of two values: The first value is the
    score (an integer).  The second value is a dict called
    'annotations' whose keys are (tutor, student), and whose values
    are lists of [(points1, description1), (points2, description2),
    ...]  The sum of the points in the annotations will be the same as
    the score.
    """
    if params is None:
        params = ScoreParams(**kwargs)

    by_tutor = HistoricalData.pairing_by_tutor(pairing)
    score = 0
    annotations = {}
    for tutor in by_tutor:
        group_score, group_ann = get_group_score(hist, tutor, by_tutor[tutor],
                                                 params=params)
        score += group_score
        annotations.update(group_ann)
    return score, annotations

def score_historical(hist, date, session, params=None):
    actual = hist.get_pairing(date, session)
    past_data = hist.get_data_before(date, session)
    return get_score(actual, past_data, params)

# --------------------------------------------------------------------

def good_pairing(hist, students, tutors, params=None):
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
                           reverse=True,
                           key = lambda s: len(hist.get_matches(student=s)))
    pairing = []
    for student in by_attendance:
        best_score = None
        best_pair = None
        for tutor in tutors:
            (this_score, _) = get_score(pairing + [(tutor, student)],
                                        hist, params)
            if best_score is None or this_score > best_score:
                best_score = this_score
                best_pair = (tutor, student)
        pairing.append(best_pair)
    return pairing

def good_historical_score(hist, date, session, params=None):
    actual = hist.get_pairing(date, session)
    students = set([p[1] for p in actual])
    tutors = set([p[0] for p in actual if p[0].strip() != ''])
    past_data = hist.get_data_before(date, session)
    return good_pairing(past_data, students, tutors, params)

# --------------------------------------------------------------------

def print_pairing(pairing, annotations=None):
    by_tutor = HistoricalData.pairing_by_tutor(pairing)
    for tutor in sorted(by_tutor):
        ptutor = tutor
        if tutor.strip() == "":
            ptutor = "<NO TUTOR LISTED>"
        print "{0:20s} : {1:40s}".format(
            ptutor, ' / '.join(sorted(by_tutor[tutor])))
        if annotations is not None:
            for pair in annotations:
                for ann in annotations[pair]:
                    if pair[0] != tutor:
                        continue
                    print "{0:50s}{1}".format(' ', ann[1])

def diff_pairings(pairing1, pairing2, ann1=None, ann2=None):
    """
    Given two pairings (lists of (tutor, student)), print the
    differences, including differences in scores.
    """
    by_tutor1 = HistoricalData.pairing_by_tutor(pairing1)
    by_tutor2 = HistoricalData.pairing_by_tutor(pairing2)

    ptutor = lambda t: "<NO TUTOR LISTED>" if t.strip() == "" else t
    tscore = lambda ann, t: sum(a[0]
                                for pair in ann
                                for a in ann[pair]
                                if pair[0] == t)

    for tutor in by_tutor1:
        if tutor not in by_tutor2:
            print "-{0:20s} {1:44s} {2}".format(ptutor(tutor), "",
                                                "" if ann1 is None
                                                else "(Score Difference: {0})".
                                                format(-tscore(ann1, tutor)))
        elif sorted(by_tutor1[tutor]) != sorted(by_tutor2[tutor]):
            if ann1 is not None and ann2 is not None:
                score1 = tscore(ann1, tutor)
                score2 = tscore(ann2, tutor)
                scorediff = "(Score Difference: {0})".format(score2 - score1)
            else:
                scorediff = ""
            print "{0:20s}: {1:20s} -> {2:20s} {3}".format(
                ptutor(tutor),
                ' / '.join(by_tutor1[tutor]),
                ' / '.join(by_tutor2[tutor]),
                scorediff)
    for tutor in by_tutor2:
        if tutor not in by_tutor1:
            print "+{0:20s} {1:44s} {2}".format(ptutor(tutor), "",
                                                "" if ann2 is None
                                                else "(Score Difference: {0})".
                                                format(tscore(ann2, tutor)))

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

