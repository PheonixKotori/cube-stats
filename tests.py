#!/usr/bin/python2
"""Unit tests for cube-stats."""

import unittest


import setup

db = None  # Set by configDB

# The cards file currently has 6 lines, 1 duplicate (Swamp), and ends in a newline character.
cards_file = "test_cardlist.txt"


def getTempDB(showerr=False):
    """Create temp database by manually executing db setup code."""
    from dal import DAL, Field
    import tempfile
    
    with open('common.py', 'r') as f:
        filelines = f.readlines()

    # Parses db setup module into text, makes a change, & executes code.
    codelines = []
    curline = ""
    for line in filelines:
        line = line.strip()
        if "DAL(" in line:
            # Modify the db path to be in a temp folder
            # Replacing backslashes b/c windoze
            line = line[:line.find('folder')] + " folder=\"" + tempfile.gettempdir().replace("\\", "/") + "\")"
        if len(line) == 0:
            continue
        elif line[0] == "#":
            continue
        else:
            # Join line continuations
            curline += line
            if curline[-1] != "," and curline[-1] != "(":
                codelines.append(curline)
                curline = ""

    for line in codelines:
        try:
            exec(line) in globals(), locals()
        except:
            if showerr:
                print 'err', line

    return db

    
class MainTest(unittest.TestCase):

    """Unit tests for cube-stats. Includes setup of database and calculation of stuff. """

    def setUp(self):
        """do stuff to prepare for each test"""
        for table in rr.db.tables:
            rr.db[table].truncate("CASCADE")
            

if __name__ == "__main__":
    db = getTempDB(showerr=True)
    print db