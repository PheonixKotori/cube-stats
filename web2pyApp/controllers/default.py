# -*- coding: utf-8 -*-

# copied from draft.py
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0/3


def index():
    """Main page."""
    colors = 'W U B R G N'.split(' ')
    top_cards = []
    top_cards_by_color = []

    num_top_cards = 12  # How many cards make up the top

    snapshot = take_snapshot(None)

    top_cards = snapshot[0:num_top_cards]
    
    return dict(colors=colors,
                top_cards=top_cards,
                top_cards_by_color=top_cards_by_color
                )


def take_snapshot(timestamp=None):
    """Return snapshot of cube stats for a given timestamp, or now if None.

    Args:
      timestamp (str): Of the form "2014-12-26 20:09:52.100875".

    Returns:
      list of Storage objects: Objects with properties name, mu, and sigma.

    """
    from gluon.storage import Storage

    if timestamp is None:
        timestamp = db(db.Transactions.id > 0).select(
            db.Transactions.timestamp,
            orderby=~db.Transactions.timestamp,
            limitby=(0,1)).first().timestamp

    active_cards_with_ratings = db(db.Cards.Quantity > 0).select(db.Cards.Name,
        db.Transactions.mu.coalesce(DEFAULT_MU).with_alias('mu'),
        db.Transactions.sigma.coalesce(DEFAULT_SIGMA).with_alias('sigma'),
        left=db.Transactions.on(db.Cards.id == db.Transactions.card_id),
        orderby=db.Transactions.timestamp)

    # Only retains most recent timestamp due to select being ordered by same
    acwrdict = {row['Cards.Name']:(row['mu'], row['sigma'])
                for row in active_cards_with_ratings}

    # Turn dict into ordered list
    data = [Storage(name=name, mu=acwrdict[name][0],
                    sigma=acwrdict[name][1]) for name in acwrdict.keys()]
    data.sort(key=lambda x: x.mu, reverse=True)

    return data
