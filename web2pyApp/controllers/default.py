# -*- coding: utf-8 -*-

# copied from draft.py
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0/3


def index():
    """Main page."""
    num_top_cards = 12  # How many cards make up the top
    color = request.vars.color
    cardtype = request.vars.cardtype
    cmc = request.vars.cmc

    snapshot = take_snapshot(None)

    if color is None:
        if cardtype is None:
            if cmc is None:
                cards = snapshot
                group_name = 'All cards'
            else:
                if cmc == "6":
                    cards = filter(lambda x: int(x.cmc) >= 6, snapshot)
                    group_name = 'CMC >= 6'
                else:
                    cards = filter(lambda x: str(x.cmc) == str(cmc), snapshot)
                    group_name = 'CMC = {0}'.format(cmc)
        else:
            cards = filter(lambda x: cardtype in x.cardtype, snapshot)
            group_name = 'Cardtype = {0}'.format(cardtype.title())
    elif color == "MULTI":
        cards = filter(lambda x: x.color not in (
            'WHITE', 'BLUE', 'BLACK', 'RED', 'GREEN', 'COLOURLESS'), snapshot)
        group_name = color.title()
    else:
        cards = filter(lambda x: x.color == color, snapshot)
        group_name = color.title()

    draft_count = count_drafts_in_snapshot(None)

    untouched_cards = [c for c in snapshot if c.mu == 25]

    return dict(cards=cards,
                group_name=group_name,
                num_top_cards=num_top_cards,
                cube_size=len(snapshot),
                draft_count=draft_count,
                untouched_cards=untouched_cards
                )


def count_drafts_in_snapshot(timestamp=None):
    """Return number of drafts represented in a snapshot based on timestamp."""
    if timestamp is None:
        import datetime
        timestamp = datetime.datetime.utcnow()

    data = db(db.Transactions.timestamp <= timestamp).count(
        distinct=db.Transactions.timestamp)
    return data


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
            limitby=(0,1)).first()#.timestamp

    # TODO make use of timestamp arg
    active_cards_with_ratings = db(db.Cards.Quantity > 0).select(
        db.Cards.Name, db.Cards.Color, db.Cards.Cardtype, db.Cards.CMC,
        db.Transactions.mu.coalesce(DEFAULT_MU).with_alias('mu'),
        db.Transactions.sigma.coalesce(DEFAULT_SIGMA).with_alias('sigma'),
        left=db.Transactions.on(db.Cards.id == db.Transactions.card_id),
        orderby=db.Transactions.timestamp)

    # Only retains most recent timestamp due to select being ordered by same
    acwrdict = {row['Cards.Name']:(row['mu'], row['sigma'], row['Cards.Color'],
                                   row['Cards.Cardtype'], row['Cards.CMC'])
                for row in active_cards_with_ratings}

    # Turn dict into ordered list
    data = [Storage(name=name,
                    mu=acwrdict[name][0],
                    sigma=acwrdict[name][1],
                    color=acwrdict[name][2],
                    cardtype=acwrdict[name][3],
                    cmc=acwrdict[name][4]) for name in acwrdict.keys()]
    data.sort(key=lambda x: x.mu, reverse=True)

    return data
