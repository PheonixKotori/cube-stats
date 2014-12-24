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
    parser.add_argument("draft", help="filename of draft file [trollitaire only]",
                        type=str)
    args = parser.parse_args()
    log.level = LOG_SHORT[args.loglevel]
#------------------------------------------------------------------------------#

# DAL setup/database init
from common import db

import trueskill
import datetime

# Define starting mu-sigma in case there are no existing transactions
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0/3

def get_current_ratings():
    '''Return a dict with a key for each active cardname, and values of tuples
    like (mu, sigma).'''
    active_cards_with_ratings = db(db.Cards.Quantity > 0).select(db.Cards.Name,
        db.Transactions.mu.coalesce(DEFAULT_MU).with_alias('mu'),
        db.Transactions.sigma.coalesce(DEFAULT_SIGMA).with_alias('sigma'),
        left=db.Transactions.on(db.Cards.id == db.Transactions.card_id),
        orderby=db.Transactions.timestamp)

    # Only retains most recent timestamp due to select being ordered by same
    acwrdict = {row['Cards.Name']:(row['mu'], row['sigma'])
                for row in active_cards_with_ratings}
    return acwrdict

def write_updated_ratings(transactions):
    '''Given a cardname:(mu, sigma) dictonary, write each entry to the database as a new transaction. Each entry in a given call to this function should have an identical timestamp.

    inputs

    outputs

    '''
    timestamp = datetime.datetime.utcnow()

    for cardname in transactions:
        db.Transactions.insert(card_id = db.Cards(db.Cards.Name==cardname).id,
                               mu = transactions[cardname][0],
                               sigma = transactions[cardname][1],
                               timestamp = timestamp)

    db.commit()

class Trollitaire(object):
    '''A collection of methods specific to processing Trollitaire drafts.

    The Trollitaire draft format is modeled as a series of free-for-alls (deals)
    in which one or more out of 3+ cards is picked in order, and the rest are
    passed (undrafted). In each deal, the first card picked wins 1st place, the
    second card picked 2nd, etc., and all undrafted cards draw for last place.

    In addition, as the draft winds on, draft picks are made less on the
    absolute strengths of the cards and more on the synergy with prior draft
    picks. The resultant loss in card-strength information is modeled by
    reducing the ratings adjustments in a linear fashion after the first 10% of
    the draft.
    '''

    def __init__(self):
        '''Initialize a Trollitaire TrueSkill environment.'''

        # Trollitaire uses default values except for draw probability.
        self.env = trueskill.TrueSkill(draw_probability = 0.25)
    
    def generate_partial_update_coeffs(self, num_deals):
        '''Generate a list of coefficients to apply to updates based on their
        position in the draft.

        Coeffs will be 1 for the first 10% of deals, and decrease linearly from
        1.0 at 10% to 0.1 at 100%. This calculation is broken out into a
        separate method to allow for easy adjustment later if necessary.
        
        Input:
        num_deals (int): indicates the total number of deals in the draft.

        Output:
        coeff_list (list of floats): each entry is a deal coefficient.
        '''
        num_deals = int(num_deals)

        if num_deals < 1:
            raise ValueError("num_deals must be greater than 0.")

        coeff_list = [1.0 for x in range(num_deals/10)]

        coeff_list += [1 - 0.9*x*(1./(max(num_deals - num_deals/10 - 1,1)))
                                for x in range(num_deals - num_deals/10)]

        log.debug("Update-coeffs list length is %s", len(coeff_list))

        return coeff_list

    def parse_report_file(self, filename):
        '''Read a Trollitaire draft report file and return a list of deals to
        process.

        Input
        -----

        filename - path to the draft report

        Output (copied from process_draft's inputs)
        -------------------------------------------
        deal_list - [{'cardname':N, 'cardname':N, 'cardname':N ...}, ...]

        where each list entry is a dict with a deal and N is the card's place
        in said deal (0 for first-picked, 1 for second, up to a tie of N for
        undrafted).


        '''
        TOKENS = {'deal':'[DEAL]',
                  'pick':'[PICK]',
                  'undo':'[UNDO]',
                  'sep':'|'}
        
        with open(filename, 'r') as f:
            raw_data = f.readlines()

            # Quick check for basic formatting
            for ix, line in enumerate(raw_data):
                if not (line.startswith('[') or line.startswith('#')):
                    raise ValueError('Invalid input read on line %s', ix)

            # remove comment lines and trailing newlines
            no_cmts = [line.rstrip('\n') for line in raw_data if not\
                       line.startswith('#')]
            del raw_data
            
            # remove [UNDO] lines and the previous line
            undo_found_flag = True
            while undo_found_flag:
                undo_found_flag = False
                for ix, line in enumerate(no_cmts):
                    if line.startswith(TOKENS['undo']):
                        undo_found_flag = True
                        no_cmts.pop(ix)
                        no_cmts.pop(ix-1)
                        log.warning('%s found, removing previous line',
                                    TOKENS['undo'])
                        break # reset the flag and restart the for loop
                
            # build list of deals/picks
            
            # Warn if deal has no picks - proceed, but don't count the deal.
            # This behavior is based on data seen in the wild - could be changed
            # later if needed.
            
            deal_list = []

            # Warning flags
            first_line_flag = True
            last_line_was_deal_flag = False
            
            for line in no_cmts:
                if first_line_flag:
                    if not line.startswith(TOKENS['deal']):
                        raise ValueError("First line didn't contain %s!",
                                         TOKENS['deal'])
                    first_line_flag = False
                if line.startswith(TOKENS['deal']):
                    if last_line_was_deal_flag:
                        log.warning("Deal with no picks detected!")
                        continue
                    # Remove deal flag and initial separator
                    # Rest of string is cardnames found in the deal
                    cards = line[len(TOKENS['deal']+TOKENS['sep']):].split(TOKENS['sep'])
                    deal_list.append({cardname:0 for cardname in cards})
                    picked_cards_this_deal = []
                    last_line_was_deal_flag = True
                    
                elif line.startswith(TOKENS['pick']):
                    last_line_was_deal_flag = False
                    
                    # [PICK] lines have 2 fields including a single cardname
                    #TODO add error-checking based on player field??
                    
                    # Add picked card to list of 'safe' cards
                    this_picked_card = line.split(TOKENS['sep'])[-1]
                    picked_cards_this_deal.append(this_picked_card)
                    
                    # Increment the placing of cards not on safe list
                    picked_card_found_flag = False
                    for k in deal_list[-1]:
                        if k not in picked_cards_this_deal:
                            deal_list[-1][k] += 1
                        else:
                            if k == this_picked_card:
                                picked_card_found_flag = True
                    if not picked_card_found_flag:
                        raise ValueError("Picked card %s not found in deal!",
                                         line.split(TOKENS['sep'])[-1])

            # return completed deal_list
            return deal_list
    
    def process_deal(self, ratings, placement):
        '''Perform a full TrueSkill ratings update on the cards listed.
        ratings is a dictionary with name:(mu,sigma) values.
        placement is a dictionary with name:place values.

        Because only partial adjustments are made for later draft picks,
        TrueSkill.Rating objects are not passed around - they are created
        locally inside the Trollitaire environment and not passed back to the
        calling method.

        Inputs
        -----
        ratings - {'cardname':(mu, sigma), 'cardname':(mu,sigma), ...}
        placement - {'cardname':place, 'cardname':place, ...}

        ratings & placement must have the same keys or KeyError will be raised.


        Outputs

        Returns the **change** in both mu and sigma for each card.
        Return format is a dictionary with keys = cardnames and values = tuples
        with the mu/sigma deltas.
        -----
        rating_deltas - {'cardname':(mu_d, sigma_d), 'cardname':(mu_d, sigma_d),
                         'cardname':(mu_d, sigma_d), ... }
        '''

        if ratings.keys().sort() != placement.keys().sort():
            raise KeyError("Ratings and placement must have the same keys.\n\
                            Ratings keys: %s\n\
                            Placement keys: %s", ratings.keys(), placement.keys())

        for k in ratings:
            if type(ratings[k]) is not tuple:
                raise TypeError("Ratings must be tuples")
            if type(placement[k]) is not int:
                raise TypeError("Placing must be integer")

        rating_list, place_list = [], []
        for k in ratings:
            rating_list += [{k:self.env.create_rating(ratings[k])}]
            place_list += [placement[k]]

        new_ratings = {}
        for entry in self.env.rate(rating_list, place_list):
            new_ratings.update(entry)

        rating_deltas = {k:(new_ratings[k].mu - ratings[k][0], 
                            new_ratings[k].sigma - ratings[k][1])
                         for k in ratings}

        return rating_deltas

    def process_draft(self, ratings, deal_list):
        '''
        Apply TrueSkill ratings updates to a series of deals detailed in
        deal_list and return an updated ratings dict.

        Inputs
        ------
        ratings - {'cardname':(mu,sigma), 'cardname':(mu, sigma), ...}

        for at least all cards in the draft - all cards in the cube will be
        typical.

        deal_list - [{'cardname':N, 'cardname':N, 'cardname':N ...}, ...]

        where each list entry is a dict with a deal and N is the card's place
        in said deal (0 for first-picked, 1 for second, up to a tie of N for
        undrafted).

        Outputs
        -------
        new_ratings - dictionary of same format as ratings, but only including
        cards that had rating changes. (These cards will have new transactions
        written to the database.)
        '''

        # Input validation
        pass

        new_ratings = ratings.copy() # Make a copy for comparison
        
        # Get partial update coefficients
        update_coeffs = self.generate_partial_update_coeffs(len(deal_list))
        
        # Process deals
        for ix, deal in enumerate(deal_list):
            # deal_list should be able to pass the placement data through
            # unchanged. Need to grab the appropriate ratings to pass in,
            # and retain to add/subtract the deltas * the update coefficient.
            cards = {key:new_ratings[key] for key in deal.keys()}

            r_delta = self.process_deal(cards, deal)
            for card in r_delta:
                # ratings gets updated so that multiple-copy cards have their
                # updates applied immediately in case they come up again in the
                # same draft.
                new_ratings[card] = (new_ratings[card][0] + r_delta[card][0] *
                                 update_coeffs[ix],
                                 new_ratings[card][1] + r_delta[card][1] *
                                 update_coeffs[ix])

        # Run a comparison and only return cards that have changed
        return {k:new_ratings[k] for k in new_ratings if new_ratings[k] != ratings[k]}

        
                
if __name__ == "__main__":
    t = Trollitaire()
    deals = t.parse_report_file(args.draft)
    ratings = t.process_draft(get_current_ratings(), deals)
    write_updated_ratings(ratings)
