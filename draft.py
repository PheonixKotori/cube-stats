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

def get_current_ratings():
    '''Return a dict with a key for each active cardname, and values of tuples
    like (mu, sigma).'''
    return {}

if __name__ == "__main__":
    pass
