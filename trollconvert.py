#!/usr/bin/python2
# Executive summary for help page.
DESC = '''cube-stats: convert old-style trollitaire draft files to new.'''

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
    parser.add_argument("draft", help="filename of draft file [trollitaire only]",
                        type=str)
    args = parser.parse_args()
    log.level = LOG_SHORT[args.loglevel]
#------------------------------------------------------------------------------#

TOKENS = {'undo':'***UNDO***', 'sep':'|'}

def convert_draft_file(infile_h, outfile_h):
    """Convert the old-style trollitaire file pointed to by infile_h to a
    new-style file, and write to outfile_h."""
    raw_data = infile_h.readlines()

    # remove [UNDO] lines and the previous line
    undo_found_flag = True
    while undo_found_flag:
        undo_found_flag = False
        for ix, line in enumerate(raw_data):
            if line.startswith(TOKENS['undo']):
                undo_found_flag = True
                raw_data.pop(ix)
                raw_data.pop(ix-1)
                log.warning('%s found, removing previous line',
                            TOKENS['undo'])
                break # reset the flag and restart the for loop

    scrubbed_data = raw_data
    del raw_data
    
    previous_cards = []

    for line in scrubbed_data:

        cards = []
        # Element 1 holds a player number - all others hold a cardname
        for ix, element in enumerate(line.rstrip().split('|')):
            if ix == 1:
                playnum = element
            else:
                cards.append(element)

        # Determine if this is a new deal
        for cardname in cards:
            new_deal = False
            if cardname not in previous_cards:
                    # meaning, this pick has new cards in it...
                    new_deal = True
                    break
            # If we get here, no break was issued - this pick is same deal
            # new_deal should remain false

        if new_deal:
            outline = "[DEAL]"
            for card in cards:
                outline += '|' + card
            outline += '\n'
            outfile_h.write(outline)
            del outline
            previous_cards = cards
            
        outline = "[PICK]|" + playnum + "|" + cards[0] + '\n'
        outfile_h.write(outline)

        

if __name__ == "__main__":
    with open(args.draft, 'r') as f:
        with open('converted_'+args.draft, 'w') as o:
            convert_draft_file(f,o)
