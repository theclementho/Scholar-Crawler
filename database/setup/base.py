from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import dbconfig as cfg

USER = cfg.local['username']
PASS = cfg.local['password']
HOST = cfg.local['host']
DB = cfg.local['db']

url = 'postgresql://{0}:{1}@{2}:5432/{3}'.format(USER, PASS, HOST, DB)

engine = create_engine(url)
Session = sessionmaker(bind=engine)

Base = declarative_base()
