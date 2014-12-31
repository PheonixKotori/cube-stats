#!/usr/bin/python2
"""Initialize and define cube-stats database."""

# Cube-stats TrueSkill constants


# Construct sqlite database
from dal import DAL, Field

db = DAL('sqlite://storage.sqlite',folder='db')

# Database table definitions -- defined here rather than in the relevant
# modules to allow for reference fields without worrying about the import sequence.
db.define_table(
    'Cards',
    Field('Name', 'string', required=True),
    Field('Quantity', 'integer', required=True),
    Field('Color', 'string'),
    Field('Cardtype', 'string'),
    Field('CMC', 'integer'),
)

db.define_table(
    'Transactions',
    Field('card_id', 'reference Cards', required=True),
    Field('mu', 'float', required=True),
    Field('sigma', 'float', required=True),
    Field('timestamp', 'string', required=True),
)
