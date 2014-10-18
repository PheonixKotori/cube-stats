#!/usr/bin/python2
# Executive summary for help page.
DESC = '''cube-stats: import draft data and update card ratings'''

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
    parser.add_argument("draft", help="filename of draft file", type=str)
    args = parser.parse_args()
    log.level = LOG_SHORT[args.loglevel]
#------------------------------------------------------------------------------#

# DAL setup/database init
from common import db

# Define starting mu-sigma in case there are no existing transactions
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0/3

def get_current_ratings():
    '''Return a dict with a key for each active cardname, and values of tuples
    like (mu, sigma).'''
    active_cards_with_ratings = db(db.Cards.Quantity > 0).select(db.Cards.Name, db.Transactions.mu.coalesce(DEFAULT_MU).with_alias('mu'), db.Transactions.sigma.coalesce(DEFAULT_SIGMA).with_alias('sigma'), left=db.Transactions.on(db.Cards.id == db.Transactions.card_id))
    aacdict = {row['Cards.Name']:(row['mu'], row['sigma']) for row in active_cards_with_ratings}

    return aacdict

if __name__ == "__main__":
    pass
