#!/usr/bin/python2
"""Unit tests for cube-stats."""

import sys
import unittest

import setup
import draft

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

    """Unit tests for cube-stats. Includes setup of db and calculation of stuff. """

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
        setup.update(cards_file)  # Tested via testLoadCardList
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

    def testNewCardRatings(self):
        """test that cards with no transactions can be loaded from the db"""
        setup.update(cards_file) # Tested via testLoadCardList
        setup.update(cards_file2) # Tested via testUpdateCardList
        ratings = draft.get_current_ratings()

        # Do get all active cards (Qty != 0)
        self.assertEqual(len(ratings), 5)

        # Do not get any inactive cards (Qty == 0)
        self.assertTrue("Faith's Fetters" not in ratings)

        # No transactions yet; check that all mu,sigma are (25.0,25.0/3)
        for entry in ratings.values():
            self.assertAlmostEqual(entry[0], 25.0)
            self.assertAlmostEqual(entry[1], 25.0/3)

    def testPartialUpdateCoeffs(self):
        """verify that update coeffs are created correctly for n>0 deals."""
        t = draft.Trollitaire()

        self.assertRaises(ValueError, t.generate_partial_update_coeffs, 'a')
        self.assertRaises(ValueError, t.generate_partial_update_coeffs, 0)

        for x in range(1, 150):
            a = t.generate_partial_update_coeffs(x)
            self.assertEqual(len(a), x) # Critical - len(list) == num_deals.
            self.assertAlmostEqual(a[0], 1.0) # First deal is always 1.0.
            if x > 1: # Check that the last element is 0.1 for >1 deal.
                self.assertAlmostEqual(a[-1], 0.1)
            if x == 11: # Check an arbitrary point on the line for 11 deals.
                self.assertAlmostEqual(a[5], 0.6)
            if x == 21: # Check anther arbitrary point at x = 21.
                self.assertAlmostEqual(a[7], 0.75)

    def testTrollitaireDeal(self):
        """Test that a Trollitaire deal can be correctly processed.""" 
        pass
        # do stuff

    def testTransactionWrite(self):
        """Test that transactions can be written to the db correctly."""
        pass

if __name__ == "__main__":
    setup.db = draft.db = getTempDB(showerr=True)
    unittest.main()
