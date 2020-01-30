import os
import sys
import requests
import csv, json
import time
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly

# History location
save_location = 'scholarly_sandbox.txt'

# Ding Yuan Profile ID
DY_id = 'g7PHxIYAAAAJ'

# Check database for saved ID
cache = 0
if cache:
    if (os.stat(save_location).st_size != 0):
        with open(save_location) as history_json:
            data = json.load(history_json)

        print(data[DY_id]['name'])
        print(data[DY_id]['id'])
        print(data[DY_id]['coauthors']['mkq2kWsAAAAJ']['name'])
        print(data[DY_id]['coauthors']['mkq2kWsAAAAJ']['id'])
        
        sys.exit(0)

# Failsafe, in case the ID gets deleted and we don't get anything
# Currently it just exits the program
# Good URL: g7PHxIYAAAAJ
# Bad ID: g7PIxIYAAAAJ
try:
    start_time = time.time()
    author_downloaded = scholarly.auth_all_coauthors('g7PHxIYAAAAJ')
    print("--- %s seconds ---" % (time.time() - start_time))
except Exception as e:
    print ("Invalid ID. Exception ", e)
    sys.exit(0)
else:
    print ("Valid ID")

start_time = time.time()
next(scholarly.search_author("Ding Yuan")).fill()
print("--- %s seconds ---" % (time.time() - start_time))

if cache:
    print(author_downloaded.name)
    print(author_downloaded.id)
    for id, item,  in author_downloaded.coauthors.items():
        print("Name: ", item['name'], ", ID: ", id)

    author_info = {}
    author_info[author_downloaded.id] = {
        'name': author_downloaded.name,
        'id': author_downloaded.id,
        'coauthors':author_downloaded.coauthors
    }

    # Save the file
    with open(save_location, mode='w') as historical_info:
        json.dump(author_info, historical_info)