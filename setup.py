#!/usr/bin/python2
# Executive summary for help page.
DESC = '''cube-stats: Verify database structure and update cube lists.'''




import argparse
import logging
log = logging.getLogger(__name__)
LOG_SHORT ={'d':'DEBUG', 'i':'INFO', 'w':'WARNING', 'e':'ERROR', 'c':'CRITICAL'}

def main():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = DESC)
    parser.add_argument("-l", "--loglevel",
                        help="set log level (default=WARNING)", type=str,
                        choices = list(LOG_SHORT.keys()), default='w')
    args = parser.parse_args()
    logging.basicConfig(level = LOG_SHORT[args.loglevel])

    main()
