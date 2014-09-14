#!/usr/bin/python2
"""Unit tests for cube-stats."""

import sys
import unittest

import setup


db = None  # Set by configDB

# The cards file currently has 6 lines, 1 duplicate (Swamp), and ends in a newline character.
cards_file = "test_support/test_cardlist.txt"
cards_file2 = "test_support/test_cardlist2.txt"


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
        for table in setup.db.tables:
            setup.db[table].truncate("CASCADE")
        
    def tearDown(self):
        """do stuff to clean up after each test"""
        pass
        
    def testLoadCardList(self):
        """test that loading a test list of cards to an empty database works"""
        # cards_file has 5 cards (6 lines and a duplicate swamp)
        setup.update(cards_file)
        
        cards = setup.db(setup.db.Cards.id > 0).select()
        self.assertEqual(len(cards), 5)
        
        swamp = setup.db(setup.db.Cards.Name == "Swamp").select().first()
        self.assertEqual(swamp.Quantity, 2)
    
        # Ensure the rest are active w/ quantity 1
        for card in cards:
            if card.Name != "Swamp":
                self.assertEqual(card.Quantity, 1)

    def testUpdateCardList(self):
        """test that database is updated properly"""
        setup.update(cards_file)  # Tested via testLoadCardsList
        setup.update(cards_file2)
        
        # cards_list2 should make the following changes against card_list:
        # - 1x Swamp
        # - 1x Faith's Fetters
        # + 1x Island
        cards = setup.db(setup.db.Cards.id > 0).select()

        ff = setup.db(setup.db.Cards.Name == "Faith's Fetters")
        self.assertEqual(ff.count(), 1)

        self.assertEqual(1, setup.db(setup.db.Cards.Name == "Swamp").select().first().Quantity)
        self.assertEqual(0, setup.db(setup.db.Cards.Name == "Faith's Fetters").select().first().Quantity)
        self.assertEqual(1, setup.db(setup.db.Cards.Name == "Island").select().first().Quantity)
        
        
if __name__ == "__main__":
    setup.db = getTempDB(showerr=True)
    unittest.main()
