# -*- coding: utf-8 -*-

# copied from draft.py
DEFAULT_MU = 25.0
DEFAULT_SIGMA = 25.0/3


def index():
    """Main page."""
    colors = 'W U B R G N'.split(' ')
    top_cards = []
    top_cards_by_color = []

    num_top_cards = 20  # How many cards make up the top

    # How to break ties?

    # mostly copied from draft.py
    top_cards = db(db.Cards.Quantity > 0).select(db.Cards.Name,
        db.Transactions.mu.coalesce(DEFAULT_MU).with_alias('mu'),
        db.Transactions.sigma.coalesce(DEFAULT_SIGMA).with_alias('sigma'),
        left=db.Transactions.on(db.Cards.id == db.Transactions.card_id),
        orderby=db.Transactions.mu|db.Transactions.sigma|db.Transactions.timestamp,
        limitby=(0, num_top_cards)
        )

    return dict(colors=colors,
                top_cards=top_cards,
                top_cards_by_color=top_cards_by_color
                )
