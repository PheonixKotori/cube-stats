#!/usr/bin/python2
# Executive summary for help page.
DESC = '''cube-stats: Manage the cube list.'''

#------------------------------------------------------------------------------#
# Parse command-line arguments and (if called directly) set up logging.
import argparse
import logging
import logging.config
# Change root logger level in logging.config to view debug/info from modules.
logging.config.fileConfig('logging.config')

log = logging.getLogger("setup")
LOG_SHORT ={'d':logging.DEBUG,
            'i':logging.INFO,
            'w':logging.WARNING,
            'e':logging.ERROR,
            'c':logging.CRITICAL}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = DESC)
    parser.add_argument("-l", "--loglevel",
                        help="set log level (default=WARNING)", type=str,
                        choices = list(LOG_SHORT.keys()), default='w')
    parser.add_argument("cards", help="filename of add/change file", type=str)
    args = parser.parse_args()
    log.level = LOG_SHORT[args.loglevel]
#------------------------------------------------------------------------------#

# DAL setup/database init
from common import db


def update(filename):
    '''Change the cube list to reflect the contents of FILENAME.
    FILENAME: a list of cardnames, one per line. No quantity data - multiples
    must be listed separately for each instance. This matches CubeTutor's output
    as of August 2014.
    
    This function:
    1. Iterates through the list and builds a {name: quantity} dictionary.
    2. Iterates through the cards table, setting quantities to 0 on all cards
    not appearing in the dictionary.
    3. Iterates through the dictionary, creating or updating rows as needed.

    This function does not add, update, or change card attributes (color etc.).
    '''

    log.debug("Reading from %s", filename)
    with open(filename, 'r') as f:
        cardData = f.readlines()
    log.info("cardData indicates a %s-card cube.", len(cardData))

    # Step 1

    newCards = {} # empty dictionary to hold name:qty keypairs
    for i in range(len(cardData)):
        cardData[i] = cardData[i].strip()
        if cardData[i] in newCards:    # Duplicate cardname found...
            newCards[cardData[i]] += 1 # so increment the quantity.
        else:
            newCards[cardData[i]] = 1  # Otherwise add a key with qty=1.
    log.warning("newCards indicates a %s-card cube.", sum(newCards.values()))

    # Step 2

    cut_cards = added_cards = 0 # Count number of changed cards for logging.
    for row in db().select(db.Cards.Name, db.Cards.Quantity):
        if row.Name not in newCards and row.Quantity != 0: # Card has been cut
            db(db.Cards.Name == row.Name).update(Quantity = 0)
            cut_cards += row.Quantity
        else:
            added_cards -= row.Quantity
            # This subtracts out the existing records' quantities. The total
            # number of added cards is the sum of this (negative or 0) and the
            # update_or_insert quantity sum in step 3.

    log.warning("Cutting %s cards...", cut_cards)

    # Step 3

    for cardname in newCards:
        db.Cards.update_or_insert(db.Cards.Name == cardname, Name = cardname,
                                  Quantity = newCards[cardname])
        added_cards += newCards[cardname]

    log.warning("Adding %s cards...", added_cards)

    db.commit()

    return

# These functions currently act as placeholders and will be implemented should
# the need arise.
def add(filename):
    '''Add cards found in FILENAME to the cube (increase quantity).'''
    raise NotImplementedError

def drop(filename):
    '''Remove cards found in FILENAME from the cube. (set qty to 0?)'''
    raise NotImplementedError

if __name__ == "__main__":
    update(args.cards)
