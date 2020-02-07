import os
import sys
import requests
import csv, json
import time
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly

# Test label search functionality
test_label_search = 0
if test_label_search:
    search_list_generator = scholarly.search_interests('failure_diagnosis')

    for profile in search_list_generator:
        profile.fill()
        print(profile.name)
        print(profile.affiliation)
        if hasattr(profile, 'organization'):
            print(profile.organization)
        else:
            print('No organization found for', profile.name)
        for interest in profile.interests:
            print(interest)
            break
        break
    sys.exit(0)

# History location
save_location = 'scholarly_sandbox.txt'

# Ding Yuan Profile ID
DY_id = 'g7PHxIYAAAAJ'

# Check database for saved ID
cache = 1
if cache:
    if (os.stat(save_location).st_size != 0):
        with open(save_location) as history_json:
            data = json.load(history_json)

        # How to read data from the cache; you need to know the ID
        print(data[DY_id]['name'])
        print(data[DY_id]['id'])
        print(data[DY_id]['coauthors']['mkq2kWsAAAAJ']['name'])
        print(data[DY_id]['coauthors']['mkq2kWsAAAAJ']['id'])
        sys.exit(0)

# Failsafe, in case the ID gets deleted and we don't get anything
# Currently it just exits the program
# Good URL: g7PHxIYAAAAJ
# Bad ID: g7PIxIYAAAAJ

# Performance testing
perf_test = 0
if perf_test:
    try:
        start_time = time.time()
        author_downloaded = scholarly.auth_all_coauthors('g7PHxIYAAAAJ')
        print("--- %s seconds ---" % (time.time() - start_time))
    except Exception as e:
        print ("Invalid ID. Exception ", e)
        sys.exit(0)
    else:
        print ("Valid ID")

    # Comparing Scholarly.py to custom scraper
    start_time = time.time()
    next(scholarly.search_author("Ding Yuan")).fill()
    print("--- %s seconds ---" % (time.time() - start_time))


    # Save the data we scraped into a .txt file
    if cache:
        # for id, item, in author_downloaded.coauthors.items():
        #     print("Name: ", item['name'], ", ID: ", id)
        # print("Name: ", author_downloaded[DY_id].name, ", Affiliation: ", author_downloaded[DY_id].affiliation, ", Interests: ", author_downloaded[DY_id].interests)

        author_info = {}
        author_info[author_downloaded.id] = {
            'name': author_downloaded.name,
            'id': author_downloaded.id,
            'affiliation': author_downloaded.affiliation,
            'interests': author_downloaded.interests,
            'coauthors':author_downloaded.coauthors
        }
        if hasattr(author_downloaded, 'organization'):
            author_info[author_downloaded.id]['organization'] = author_downloaded.organization
            print(author_downloaded.organization)
        else:
            print("No organization ID found with author")
        print(author_info[author_downloaded.id]['name'])
        print(author_info[author_downloaded.id]['affiliation'])
        print(author_info[author_downloaded.id]['interests'])

        # Save the file
        with open(save_location, mode='w') as historical_info:
            json.dump(author_info, historical_info)