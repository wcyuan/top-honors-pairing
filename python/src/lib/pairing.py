#!/usr/bin/env python
"""
Functions to deal with historical data in Top Honors pairing

Run doctests with:
  python -m doctest pairing.py
or
  python -m doctest -v pairing.py

Terminology:

A Pair is a (date, tutor, student) tuple, which represents a tutor
matched to a single student for a single week.  If, one week, a tutor
is matched with 3 students, that is stored as three separate Pairs.

A Pairing is a set of Pairs that matches all the students to tutors
for a particular week.  The goal of the Pairing Algorithm is to find
the best Pairing for a week, given the Pairings for all previous weeks.

HistoricalData is the set of all past Pairings.

 - API ('-' means run a script, '.' means use excel to edit a csv file)
   - create blank attendance sheet, including the previous topic for
     each student -- prompts for the date
   . (set current attendance for tutors and students, including current topics)
   - run pairing for this week (overwriting anything that's there)
   . (modify the pairing)
   - score the given pairing
   . (set compatibility information)
   - save the given pairing to historical data

 - Extended API
   - Given a past date, populate the 'input attendance' and 'current
     pairing' with the data from that date (with the score and explanation)
   - Rename a student or tutor

 - Data layout: many separate files
   - score parameters
   - historical data
   - input attendance
   - current pairing
   - list of students -- including initial assessment, gender, etc.
   - list of tutors -- including gender, etc.
   - a run log
 - code:
   - a bitbucket git repo inside of a dropbox shared folder (?)
     - stores everything (including data)?  or just the code?
       or just the code and the historical data?
       is the data sensitive?
   - a directory for each session
     a py script for each command
     csv files for input and output
     data directory -- holds historical data and log
   - the py scripts get session from cwd
   - date comes from the actual date, or from a line in the Attendance sheet?

 - plan:
 [x] figure out the new data layout
 [x] put things on dropbox/git
 [x] create classes for reading/writing data files
   [x] score parameters
   [x] historical data
   [x] student and tutor lists
     [x] confirm that all students and tutors in the historical data are valid
   [x] attendance (including topic)
   [x] Add 'topic' to attendance and historical data
   [x] create layout for pairings
 [x] Use topic in scoring (untested)
 [ ] create sample data from last year's historical data
 [ ] create scripts to run on the sample data, test each step in the API
 [ ] validate PairingFile

 - next steps:
 [ ] Address issues in parsing the old manual file
 [ ] clean up code organization (break into several files,
     separate main from functions)
 [ ] add comments, docstrings

 - maybe/somday?
 python gui?
 http://farhadi.ir/projects/html5sortable/

"""
# -------------------------------------------------------
# Imports and Constants
#

from __future__ import absolute_import, division, with_statement

import collections
import datetime
import inspect
import itertools
import logging
import operator
import optparse
import os.path
import re

# Input
ATTENDANCE_FILE = 'Attendance.csv'

# Output
PAIRING_FILE = 'Pairing.csv'

# Auxiliary Data
STUDENT_FILE = os.path.join('data', 'Students.csv')
TUTOR_FILE   = os.path.join('data', 'Tutors.csv')
HIST_FILE    = os.path.join('data', 'HistoricalPairings.csv')
PARAM_FILE   = os.path.join('data', 'Parameters.csv')

# -------------------------------------------------------
# Main + command line parsing
#

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

def main():
    opts = getopts()
    if opts.make_files:
        make_files()
    elif opts.run_2012:
        given_params = dict((k, getattr(opts, k))
                            for k in ScoreParams.PARAMS
                            if hasattr(opts, k))
        params = ScoreParams(**given_params)
        hist = get_2012_data()
        run_pairing_code(opts.date,
                         opts.session,
                         hist=hist,
                         params=params,
                         show_details=opts.verbose)

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
    parser.add_option('--make_files',
                      action='store_true',
                      help='make initial csv files')
    parser.add_option('--run_2012',
                      action='store_true',
                      help='run for 2012, expecting data to be in the cwd')
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
# These functions capture the API for running pairing
#

def make_attendance_sheet(date=None):
    Attendance.to_csv(ATTENDANCE_FILE,
                      Students().from_csv(STUDENT_FILE),
                      Tutors().from_csv(TUTOR_FILE),
                      HistoricalData().from_csv(HIST_FILE),
                      date=date)

def run_pairing():
    hist = HistoricalData().from_csv(HIST_FILE)
    stds = Students().from_csv(STUDENT_FILE)
    tuts = Tutors().from_csv(TUTOR_FILE)
    params = ScoreParams.from_csv(PARAM_FILE)
    (tutors, students, date) = Attendance.from_csv(ATTENDANCE_FILE)
    Attendance.validate(tutors, students, tuts, stds, ATTENDANCE_FILE)

    # XXX Confirm that the historical data has only recognized tutors and
    # students
    # XXX Confirm that we have valid topics
    pairing = good_pairing(hist, students.keys(), tutors, students, params)
    # get score
    (score, annotations) = get_score(pairing, hist, students, params=params)
    # output to a file
    PairingFile.to_csv(PAIRING_FILE, pairing, students, annotations, date=date)

def save_pairing():
    session = os.path.basename(os.path.abspath(os.path.curdir))
    pairs = PairingFile.from_csv(PAIRING_FILE, session)
    hist = HistoricalData().from_csv(HIST_FILE)
    hist.add_list(pairs)
    with open(HIST_FILE, 'w') as fd:
        fd.write(hist.to_csv())
        fd.write("\n")

def score_pairing():
    hist = HistoricalData().from_csv(HIST_FILE)
    stds = Students().from_csv(STUDENT_FILE)
    tuts = Tutors().from_csv(TUTOR_FILE)
    params = ScoreParams.from_csv(PARAM_FILE)
    (tutors, students, date) = Attendance.from_csv(ATTENDANCE_FILE)
    Attendance.validate(tutors, students, tuts, stds, ATTENDANCE_FILE)
    pairs = PairingFile.from_csv(PAIRING_FILE, session)
    PairingFile.validate(pairs)
    pairing = [(pair.student, pair.tutor) for pair in pairs]
    (score, annotations) = get_score(pairing, hist, students, params=params)
    PairingFile.to_csv(PAIRING_FILE, pairing, students, annotations, date=date)


# -------------------------------------------------------
# These functions capture the real main code.  Main is just a switch
# around either run_pairing_code or make_files
#

def make_files():
    """
    Make the initial version of the following files:
     - score parameters
     - historical data
     - input attendance
     - current pairing
    """
    params = ScoreParams()
    hist = get_2012_data()

    with open(PARAM_FILE, 'w') as fd:
        fd.write(params.to_csv())
        fd.write("\n")
    if (params != ScoreParams.from_csv(PARAM_FILE)):
        print ScoreParams.from_csv(PARAM_FILE).to_csv()
        raise RuntimeError("Error dumping parameters")
    with open(HIST_FILE, 'w') as fd:
        fd.write(hist.to_csv())
        fd.write("\n")
    if (hist != HistoricalData().from_csv(HIST_FILE)):
        raise RuntimeError("Error dumping historical data")
    with open(STUDENT_FILE, 'w') as fd:
        stds = Students(Student(name=n) for n in hist.all_students)
        fd.write(stds.to_csv())
        fd.write("\n")
    if stds != Students().from_csv(STUDENT_FILE):
        raise RuntimeError("Error dumping student data")
    with open(TUTOR_FILE, 'w') as fd:
        tuts = Tutors(Tutor(first=t[0], last=t[1])
                      for t in set((p.tutor_first, p.tutor_last)
                                   for p in hist.data))
        fd.write(tuts.to_csv())
        fd.write("\n")
    if tuts != Tutors().from_csv(TUTOR_FILE):
        raise RuntimeError("Error dumping tutor data")

# -------------------------------------------------------

def run_pairing_code(date=20130413,
                     session='am_purple',
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
    recent = hist.most_recent(by_student=True, date=date)
    student_topics = dict((s, recent[s].topic) for s in recent)
    (best_score, best_ann) = get_score(
        best, hist.get_data_before(date, session),
        student_topics)

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

# -------------------------------------------------------
# Pair and HistoricalData
#
# These are the heart of the data representation
#

class CsvObject(object):
    """
    A CsvObject is an abstract base class for an object that can be
    serialized to a csv file.
    """
    INT_FIELDS  = ()
    STR_FIELDS  = ()
    BOOL_FIELDS = ()
    FIELDS = INT_FIELDS + STR_FIELDS + BOOL_FIELDS
    DEFAULTS = {}

    def __init__(self, *args, **kwargs):
        for (fld, val) in zip(self.FIELDS, args):
            setattr(self, fld, val)
        for fld in kwargs:
            setattr(self, fld, kwargs[fld])
        for fld in self.FIELDS:
            if not hasattr(self, fld):
                if fld in self.DEFAULTS:
                    setattr(self, fld, self.DEFAULTS[fld])
                else:
                    raise ValueError("No value provided for field "
                                     "{0} ({1} {2})".
                                     format(fld, args, kwargs))

    def __eq__(self, other):
        if self.FIELDS != other.FIELDS:
            logging.debug("list of fields doesn't match")
            return False
        for f in self.FIELDS:
            mine = getattr(self, f)
            theirs = getattr(other, f)
            if mine != theirs:
                logging.debug("Field %s: mine %s != theirs %s",
                              f, mine, theirs)
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        """
        This returns a string which, when evaluated, returns an object
        that is equivalent to self
        """
        return ('{cn}(' + 
                ',\n{pd} '.join('{0} = {{self.{0}!r}}'.format(f) for f in self.FIELDS) +
                ')').format(cn=self.__class__.__name__,
                            pd=' ' * len(self.__class__.__name__),
                            self=self)

    @classmethod
    def to_header(cls, fieldname):
        return ' '.join(f.title() for f in fieldname.split('_'))

    @classmethod
    def from_header(cls, fieldname):
        return '_'.join(f.lower() for f in fieldname.split(' '))

    @classmethod
    def csv_header(cls, delim=','):
        return delim.join(cls.to_header(f) for f in cls.FIELDS)

    @classmethod
    def csv_bool(cls, val):
        return 'TRUE' if val else ''

    def to_csv(self, delim=','):
        return delim.join(
            str(self.csv_bool(getattr(self, f))
                if f in self.BOOL_FIELDS
                else getattr(self, f))
            for f in self.FIELDS)

    @classmethod
    def from_csv_field(cls, fld, val):
        if fld in cls.BOOL_FIELDS:
            return val == 'TRUE'
        if fld in cls.INT_FIELDS:
            return int(val)
        return val

    @classmethod
    def from_csv(cls, header, line, delim=','):
        flds = {}
        header = header.rstrip()
        line = line.rstrip()
        for (fld, val) in zip(header.split(delim), line.split(delim)):
            fld = cls.from_header(fld)
            val = cls.from_csv_field(fld, val)
            flds[fld] = val
        return cls(**flds)

class Pair(CsvObject):
    """
    A Pair represents one student paired with one tutor on one week.
    (If the same tutor has N students at once, that would be
    represented as N Pairs)
    """
    INT_FIELDS  = ('date',)
    STR_FIELDS  = ('session', 'tutor_first', 'tutor_last',
                   'student', 'topic')
    # Instead of avoid_student being a boolean, should it be a list of
    # the names students to avoid?
    BOOL_FIELDS = ('tutor_on_own', 'on_own', 'avoid_student',
                   'avoid_tutor', 'good_match')
    FIELDS = INT_FIELDS + STR_FIELDS + BOOL_FIELDS
    DEFAULTS = {'topic' : ''}

    @property
    def tutor(self):
        return '{0} {1}'.format(self.tutor_first, self.tutor_last)

class CsvList(object):
    OBJ_CLASS = CsvObject
    ORDER = OBJ_CLASS.FIELDS
    BY_KEY = False
    KEY_UNIQUE = False

    def __init__(self, data=None):
        self.data = [] if data is None else list(data)
        self._data_by_key = None

    def __eq__(self, other):
        return (sorted(self.data, key=operator.attrgetter(*self.ORDER)) ==
                sorted(other.data, key=operator.attrgetter(*self.ORDER)))

    def __ne__(self, other):
        return not (self == other)

    def to_csv(self):
        return '\n'.join([self.OBJ_CLASS.csv_header()] +
                         [obj.to_csv()
                          for obj in
                          sorted(self.data,
                                 key=operator.attrgetter(*self.ORDER))])

    def from_csv(self, filename):
        with open(filename) as fd:
            header = None
            for line in fd:
                line = line.rstrip()
                if header is None:
                    header = line
                    continue
                self.add(self.OBJ_CLASS.from_csv(header, line))
        return self

    def get_matches(self, **kwargs):
        return [d for d in self.data
                if all(getattr(d, fld) == kwargs[fld]
                       for fld in kwargs)]

    def best_matches(self, sort_by, key_func, skip_if=None):
        """
        If you divide the objects into classes, then return a dict
        which, for each class, maps to the 'best' object in that class,
        where 'best' means 'comes last when sorted by the sort_by field'.

        The best example is if sort_by = date and key_func = lambda p:
        p.student, then this returns the most recent pairing for each
        student.

        @param sort_by: the name of a field, or a list of fields

        @param key: a function which, given an instance of OBJ_CLASS,
        returns the group to put that object into

        @param skip_if: a function which, given an instance of OBJ_CLASS
        returns True if we should skip that object
        """
        return dict((key_func(obj), obj)
                    for obj in
                    sorted(self.data, key=operator.attrgetter(sort_by))
                    if skip_if is None or not skip_if(obj))

    def add(self, obj):
        self._data_by_key = None
        self.data.append(obj)

    def add_list(self, obj_list):
        self._data_by_key = None
        self.data.extend(obj_list)

    @classmethod
    def key_func(self, obj):
        # Not implemented
        return None

    @property
    def data_by_key(self):
        if not self.BY_KEY:
            return None
        if self._data_by_key is None:
            if self.KEY_UNIQUE:
                self._data_by_key = {}
            else:
                self._data_by_key = collections.defaultdict(list)
            for obj in self.data:
                key = self.key_func(obj)
                if self.KEY_UNIQUE:
                    if key in self._data_by_key:
                        raise ValueError(
                            "Multiple {0} objects with the same key {1}".
                            format(self.OBJ_CLASS.__name__, key))
                    self._data_by_key[key] = obj
                else:
                    self._data_by_key[key].append(obj)
        return self._data_by_key

class HistoricalData(CsvList):
    """
    Historical Data captures all past pairings.  It is basically just
    a list of Pairs.
    """
    OBJ_CLASS = Pair
    ORDER = ('session', 'date', 'tutor', 'student')
    BY_KEY = True

    def __init__(self, data=None):
        super(HistoricalData, self).__init__(data)

    @classmethod
    def key_func(self, pair):
        return (pair.date, pair.tutor)

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

    def add_pairs(self, pairs):
        self.add_list(pairs)

    @property
    def data_by_tutor(self):
        return self.data_by_key

    def get_pairing(self, date, session):
        return [(d.tutor, d.student)
                for d in self.data
                if d.date == date and d.session == session]

    def get_data_before(self, date, session):
        return HistoricalData([d for d in self.data
                               if d.date < date and d.session == session])

    # This get_matches has the same functionality as
    # CsvList.get_matches, but it's much faster.  This gets called a
    # lot, so speeding it up a little makes a big difference.
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

    @property
    def previous_date(self, date=None):
        dates = sorted(set([p.date for p in self.data]), reverse=True)
        if date is None:
            return dates[0]
        else:
            return (d for d in dates if d < date).next()

    def most_recent(self, by_student=False, by_tutor=False, date=None,
                    criteria=None):
        """
        Returns a dict from student -> most recent pair for that student
        or from tutor -> most recent pair for that tutor
        or from <any key> -> most recent pair for that key
        """
        recent = {}
        for pair in sorted(self.data, key=operator.attrgetter('date')):
            if date is not None and pair.date >= date:
                continue
            if by_student:
                key = pair.student
            elif by_tutor:
                key = pair.tutor
            elif criteria is not None:
                key = criteria(pair)
            recent[key] = pair
        return recent

    def validate(self, students, tutors):
        for pair in self.data:
            if pair.tutor not in tutors.data_by_key:
                raise ValueError("Invalid Tutor in {0}".format(pair))
            if pair.student not in students.data_by_key:
                raise ValueError("Invalid Student in {0}".format(pair))

# --------------------------------------------------------------------

class Student(CsvObject):
    STR_FIELDS  = ('name', 'initial_assessment', 'gender', 'grade')
    BOOL_FIELDS = ('is_active',)
    FIELDS = STR_FIELDS + BOOL_FIELDS
    DEFAULTS = {'initial_assessment' : '',
                'gender' : '',
                'grade' : '',
                'is_active' : True}

class Students(CsvList):
    OBJ_CLASS = Student
    ORDER = Student.FIELDS
    BY_KEY = True
    KEY_UNIQUE = True
    @classmethod
    def key_func(cls, s):
        return s.name

class Tutor(CsvObject):
    STR_FIELDS  = ('first', 'last')
    BOOL_FIELDS = ('is_active',)
    FIELDS = STR_FIELDS + BOOL_FIELDS
    DEFAULTS = {'is_active' : True}
    @property
    def full_name(self):
        return ' '.join((self.first, self.last))

class Tutors(CsvList):
    OBJ_CLASS = Tutor
    ORDER = Tutor.FIELDS
    BY_KEY = True
    KEY_UNIQUE = True
    @classmethod
    def key_func(cls, t):
        return t.full_name

# --------------------------------------------------------------------

class Attendance(object):
    @classmethod
    def to_csv(cls, filename, students, tutors, hist, date=None):
        recent = hist.most_recent(by_student=True, date=date)
        with open(filename, 'w') as fd:
            if date is not None:
                fd.write(','.join(('Date', date)))
                fd.write("\n")
            fd.write(','.join(('Tutor', '', 'Student', '', 'Topic')))
            fd.write("\n")
            for (student, tutor) in itertools.izip_longest(
                    students.get_matches(is_active=True),
                    tutors.get_matches(is_active=True),
                    fillvalue=''):
                topic = recent[student].topic if student in recent else ''
                fd.write(','.join((tutor.full_name, '',
                                   student.name, '',
                                   topic)))
                fd.write("\n")

    @classmethod
    def not_present(cls, string):
        return string.lower() in ('', 'no', 'false', 'n')

    @classmethod
    def from_csv(cls, filename):
        tutors = []
        students = {}
        date = None
        with open(filename) as fd:
            header = None
            for line in fd:
                line = line.rstrip()
                if line.lower().startswith("date"):
                    date = int(line.split(',', 1)[1])
                    continue
                if header is None:
                    header = line
                    continue
                (tutor, tutor_present, student,
                 student_present, topic) = line.split(',')
                if tutor in tutors:
                    raise ValueError("Tutor {0} appears multiple times!".
                                     format(tutor))
                if not cls.not_present(tutor_present):
                    tutors.append(tutor)
                if student in students:
                    raise ValueError("Student {0} appears multiple times!".
                                     format(student))
                if not cls.not_present(student_present):
                    students[student] = topic
        return (tutors, students, date)

    @classmethod
    def validate(cls, tutors, students, tutor_list, student_list, filename):
        # Confirm that these are recognized tutors and students
        for tutor in tutors:
            if tutor not in tutor_list.data_by_key:
                raise ValueError("Invalid Tutor {0} in {1}".
                                 format(tutor, filename))
        for student in students:
            if student not in student_list.data_by_key:
                raise ValueError("Invalid Student {0} in {1}".
                                 format(student, filename))

class PairingFile(object):
    @classmethod
    def to_csv(cls, filename, pairing, student_topics, annotations, date=None):
        with open(filename, 'w') as fd:
            if date is not None:
                fd.write(','.join(('Date', date)))
                fd.write("\n")
            fd.write(','.join(('Tutor', 'Student',
                               'Topic', 'TUTOR_ON_OWN', 'STUDENT_ON_OWN',
                               'AVOID_TUTOR', 'AVOID_STUDENT', 'GOOD_MATCH',
                               'Reason',)))
        by_tutor = HistoricalData.pairing_by_tutor(pairing)
        for tutor in sorted(by_tutor):
            for student in by_tutor[tutor]:
                ann = (' | '.join(annotations[(tutor, student)])
                       if (tutor, student) in annotations
                       else '')
                fd.write(','.join((tutor, student, student_topics[student],
                                   '', '', '', '', '', ann)))
                fd.write("\n")

    @classmethod
    def from_csv(cls, filename, session):
        pairing = []
        date = int(datetime.date.today().strftime('%Y%m%d'))
        with open(filename) as fd:
            header = None
            for line in fd:
                line = line.rstrip()
                if line.lower().startswith('date'):
                    date = int(line.split(',', 1)[1])
                if header is None:
                    header = line
                    continue
                (tutor, student, topic, tutor_on_own,
                 student_on_own, avoid_tutor, avoid_student,
                 good_match, reason) = line.split(',')
                tname = tutor.split()
                tutor_first = tname[0]
                tutor_last = ' '.join(tname[1:]) if len(tname) > 1 else ''
                # XXX validate all fields
                # XXX make the reason optional
                # XXX allow columns to move?
                pairing.append(Pair(date=date,
                                    session=session,
                                    tutor_first=tutor_first,
                                    tutor_last=tutor_last,
                                    student=student,
                                    tutor_on_own=tutor_on_own,
                                    on_own=on_own,
                                    avoid_student=avoid_student,
                                    avoid_tutor=avoid_tutor,
                                    good_match=good_match))
        return pairing

    @classmethod
    def validate(cls, pairs):
        return True

# --------------------------------------------------------------------
# ParseManualFile
#

class ParseManualFile(object):
    """
    Class for parsing the old excel spreadsheet.  This doesn't work
    perfectly because nothing validated the old format.
    """
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
        lines = [l.replace('"', '').split(',') for l in open(fn).readlines()]
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
                            logging.info('Missed one? "{0}" -- {1}, {2} '
                                         '{3} {4} {5}'.
                                         format(student, val, session,
                                                tutor_first, tutor_last, date))
                        data.append(Pair(date=date,
                                         session=session,
                                         tutor_first=tutor_first,
                                         tutor_last=tutor_last,
                                         student=student,
                                         tutor_on_own=tutor_on_own,
                                         on_own=on_own,
                                         avoid_student=avoid_student,
                                         avoid_tutor=avoid_tutor,
                                         good_match=good_match))
                last_fld = fld
        return data

def get_2012_data():
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe())))
    data_dir = os.path.join(os.path.dirname(os.path.dirname(currentdir)), 'data', '2012')
    data = []
    data.extend(ParseManualFile.read_file(os.path.join(data_dir, 'am_purple.csv'),
                                          'am_purple', 2012))
    data.extend(ParseManualFile.read_file(os.path.join(data_dir, 'am_orange.csv'),
                                          'am_orange', 2012))
    data.extend(ParseManualFile.read_file(os.path.join(data_dir, 'pm.csv'), 'pm', 2012))
    return HistoricalData(data)

# --------------------------------------------------------------------
# Functions to score a pairing
#

class ScoreParams(object):
    PARAMS = {'award_past_work'          : 1,
              'award_good_match'         : 5,
              'penalty_avoid_tutor'      : 20,
              'penalty_multiple_students': 1,
              'penalty_avoid_student'    : 20,
              'penalty_tutor_on_own'     : 10,
              'penalty_student_on_own'   : 10,
              'penalty_different_topics' : 10}

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

    def to_csv(self):
        return '\n'.join(
            ','.join((param, str(getattr(self, param))))
            for param in self.PARAMS)

    @classmethod
    def from_csv(cls, filename):
        with open(filename) as fd:
            vals = {}
            for line in fd:
                (fld, val) = line.split(',')
                vals[fld] = int(val)
        return cls(**vals)

    def __eq__(self, other):
        if self.PARAMS != other.PARAMS:
            logging.debug("list of params doesn't match")
            return False
        for p in self.PARAMS:
            mine = getattr(self, p)
            theirs = getattr(other, p)
            if mine != theirs:
                logging.debug("Param %s: mine %s != theirs %s",
                              p, mine, theirs)
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

def get_group_score(hist, tutor, students, topics, params=None, **kwargs):
    if params is None:
        params = ScoreParams(**kwargs)

    annotations = collections.defaultdict(list)
    score = 0
    for student in students:
        prev = hist.get_matches(tutor=tutor, student=student)
        points_past_work = len(prev) * params.award_past_work
        if points_past_work > 0:
            score += points_past_work
            logging.debug("Score %s: Increasing score by %s because %s and %s "
                          "have worked together %s other times",
                          score, points_past_work, tutor, student, len(prev))
            annotations[(tutor, student)].append(
                (points_past_work,
                 "+{0}*{1} because {2} and {3} have worked together".
                 format(len(prev), params.award_past_work, tutor, student)))
        if any([p.avoid_tutor for p in prev]):
            score -= params.penalty_avoid_tutor
            logging.debug("Score %s: Decreasing score by %s because %s should "
                          "avoid tutor %s",
                          score, params.penalty_avoid_tutor, student, tutor)
            annotations[(tutor, student)].append(
                (-params.penalty_avoid_tutor,
                  "-{0} because {1} and {2} shouldn't work together".
                  format(params.penalty_avoid_tutor, tutor, student)))
        if any([p.good_match for p in prev]):
            score += params.award_good_match
            logging.debug("Score %s: Increasing score by %s because %s is a "
                          "good fit with tutor %s",
                          score, params.award_good_match, student, tutor)
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
    if any([t != topics[0] for t in topics[1:]]):
        score -= params.penalty_different_topics
        logging.debug("Score %s: Decreasing score by %s because students "
                      "%s with tutor %s are working on different topics %s",
                      score, params.penalty_different_topics, students, tutor,
                      topics)
        annotations[(tutor, student1)].append(
            -params.penalty_different_topics,
            "-{0} because students {1} working with tutor {2} are working "
            "on different topics {3}".format(
                params.penalty_different_topics,
                students, tutor, topics))
    if any([p.tutor_on_own for p in hist.get_matches(tutor=tutor)]):
        score -= params.penalty_tutor_on_own
        logging.debug("Score %s: Decreasing score by %s because tutor %s "
                      "should work alone",
                      score, params.penalty_tutor_on_own, tutor)
        annotations[(tutor, student1)].append(
            (-params.penalty_tutor_on_own,
              "-{0} because tutor {1} should only work on own".
              format(params.penalty_tutor_on_own, tutor)))
    for student in students:
        if any([p.on_own for p in hist.get_matches(student=student)]):
            score -= params.penalty_student_on_own
            logging.debug("Score %s: Decreasing score by %s because "
                          "student %s should work alone",
                          score, params.penalty_student_on_own, student)
            annotations[(tutor, student)].append(
                (-params.penalty_tutor_on_own,
                  "-{0} because student {1} should only work on own".
                  format(params.penalty_tutor_on_own, student)))
    for ii in xrange(n_students):
        for jj in xrange(ii+1, n_students):
            for pairs in hist.get_student_pairings(students[ii],
                                                   students[jj]):
                if any([p.avoid_student for p in pairs]):
                    score -= params.penalty_avoid_student
                    logging.debug("Score %s: Decreasing score by %s "
                                  "because student %s "
                                  "should not work with student %s",
                                  score, params.penalty_avoid_student,
                                  students[ii], students[jj])
                    annotations[(tutor, students[ii])].append(
                        (-params.penalty_avoid_student,
                          "-{0} because students {1} and {2} should "
                          "not work with each other".
                          format(params.penalty_avoid_student,
                                 students[ii],
                                 students[jj])))
                    break
    return (score, annotations)

def get_score(pairing, hist, student_topics, params=None, **kwargs):
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
        group = by_tutor[tutor]
        topics = [student_topics[s] for s in group]
        group_score, group_ann = get_group_score(hist, tutor, group, topics,
                                                 params=params)
        score += group_score
        annotations.update(group_ann)
    return score, annotations

def score_historical(hist, date, session, params=None):
    actual = hist.get_pairing(date, session)
    past_data = hist.get_data_before(date, session)
    recent = hist.most_recent(by_student=True, date=date)
    student_topics = dict((s, recent[s].topic) for s in recent)
    return get_score(actual, past_data, student_topics, params)

# --------------------------------------------------------------------
# Functions to find the pairing with the highest score, either for a
# list of students and tutors, or for a historical date
#

def good_pairing(hist, students, tutors, student_topics, params=None):
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
                                        hist, student_topics,
                                        params)
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
    recent = hist.most_recent(by_student=True, date=date)
    student_topics = dict((s, recent[s].topic) for s in recent)
    return good_pairing(past_data, students, tutors, student_topics, params)

# --------------------------------------------------------------------
# Functions to print or compare pairings
#

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
