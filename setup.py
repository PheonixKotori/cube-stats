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
import common


def update(filename):
    '''Change the cube list to reflect the contents of FILENAME.'''
    log.debug(filename)
    f = open(filename, 'r')
    cardData = f.readlines()
    for i in range(len(cardData)):
        cardData[i] = cardData[i].strip()
    log.debug(cardData)

# These functions currently act as placeholders and will be implemented should
# the need arise.
def add(filename):
    '''Add cards found in FILENAME to the cube (increase quantity).'''
    raise NotImplementedError

def drop(filename):
    '''Remove cards found in FILENAME from the cube. (set qty to 0?)'''
    raise NotImplementedError

if __name__ == "__main__":
    add(args.cards)
