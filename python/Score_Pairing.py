#!/usr/bin/env python

if __name__ == "__main__":
    try:
        # http://stackoverflow.com/questions/714063/python-importing-modules-from-parent-folder
        import inspect
        import os
        import sys
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        sys.path.insert(0, os.path.join(parentdir, 'src'))
        import pairing

        pairing.score_pairing()

    except Exception as e:
        print "Error:"
        print
        print e
        print
        print "Type Control-C to Exit"
        while True:
            pass
