"""
Script to add generated txt to database
"""
import argparse
import os
import json
from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
sys.path.append("database/setup/")
from author import Author
from coauthor import Coauthor
import dbconfig as cfg

# determine whether run on local or RDS database server
parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument('-rds', '--rds', action='store_true', help="run on rds server")
args = parser.parse_args()

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

import glob
os.chdir("logs")

if __name__ == "__main__":
    t = time()

    engine = create_engine(url)
    session = sessionmaker()
    session.configure(bind=engine)
    s = session()

    for file in glob.glob("*.txt"):
        with open(file, 'r') as readFile:
            print("reading file ", file)
            data = json.load(readFile)
            id = list(data.keys())[0]
            info = data[id]
            if len(info) == 0:
                continue

            if file[0] == 'A':  # import author  
                name = info['name']
                gs_profile_id = info['gs_profile_id']
                affiliation = info['affiliation']
                interest = ', '.join(info['interest'])
                
                author = Author(
                    name=name, 
                    gs_profile_id=gs_profile_id, 
                    affiliation=affiliation, 
                    interest=interest)
                s.add(author)
            
            elif file[0] == 'R':    # import relation
                relations = [Coauthor(
                    person1_id = id,
                    person2_name = i[0],
                    most_recent_year = i[1],
                    most_recent_paper = i[2]
                ) for i in info]
                s.add_all(relations)
    try:
        s.commit()
    except:
        s.rollback()
    finally:
        s.close()    

    print("=== Importing CSV took: " + str(time() - t) + " s.")
