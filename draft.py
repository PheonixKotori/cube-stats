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

import trueskill

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
    
    def parse_report_file(self, filename):
        '''Read a Trollitaire draft report file and return a list of deals to
        process.'''
        raise NotImplementedError

    def process_draft(self, ratings_dict, deal_list):
        '''Apply TrueSkill ratings updates to a series of deals detailed in
        deal_list and return an updated ratings_dict.'''
        raise NotImplementedError

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
        

    def process_deal(self, pick_tuple_list):
        '''Perform a full TrueSkill ratings update on the cards listed
        picked_rating = trueskill.Rating
        '''
        raise NotImplementedError


if __name__ == "__main__":
    pass
