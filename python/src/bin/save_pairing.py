#!/usr/bin/env python

import inspect
import os
import sys
import traceback

def main():
    try:
        # http://stackoverflow.com/questions/714063/python-importing-modules-from-parent-folder
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        sys.path.insert(0, os.path.join(parentdir, 'lib'))
        import pairing

        pairing.save_pairing()

    except Exception as e:
        print "Error:"
        print
        traceback.print_exc()
        print
        print "Type Control-C to Exit"
        while True:
            pass

if __name__ == "__main__":
    main()
