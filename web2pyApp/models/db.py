# -*- coding: utf-8 -*-

# this is the database used by web2py. i've made a symlink connecting ./databases to /db.
# auto_import makes web2py use whatever table schema is defined in /db/*.table, so we don't
# need to define the tables here. this may have some drawbacks, though, TBD.
db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=None,auto_import=True)

response.generic_patterns = ['*'] if request.is_local else []
