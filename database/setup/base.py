import sys
import argparse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# determine whether run on local or RDS database server
parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument('-rds', '--rds', action='store_true', help="run on rds server")
args = parser.parse_args()

configPath = 'database/setup/'
sys.path.append(configPath)
import dbconfig as cfg
if args.rds:
    USER = cfg.rds['username']
    PASS = cfg.rds['password']
    HOST = cfg.rds['host']
    DB = cfg.rds['db']
else:
    USER = cfg.local['username']
    PASS = cfg.local['password']
    HOST = cfg.local['host']
    DB = cfg.local['db']

url = 'postgresql://{0}:{1}@{2}:5432/{3}'.format(USER, PASS, HOST, DB)

engine = create_engine(url)
Session = sessionmaker(bind=engine)

Base = declarative_base()
