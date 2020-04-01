import os
import sys
import requests
import csv, json
import time
import traceback
import logging
from datetime import datetime
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly
from collections import deque

# from database import api

# Error logging:
def openLogging():
    now = datetime.now().strftime("%d:%m:%Y_%H:%M:%S")
    logf = open("logs/scraping{0}.log".format(now), "w")
    return logf

def retrieveAuthorsFromOrgNum(org_num):
    """Return a generator function to retrieve [ID, name, interests] of an author, given organization number"""
    start_time = time.time()
    search_list_generator = scholarly.search_org(org_num)
    print("--- Retrieving list from org {0} took {1} seconds ---".format(org_num, str(time.time() - start_time)))
    # ------------ PROFILE ONLY CONTAINS 3 PARAMETERS. CALL AUTH_ALL_COAUTHORS ON PROFILE TO COMPLETE LIST ------------
    return search_list_generator

def retrieveAuthorsFromLabels(label):
    """Return a generator function to retrieve [ID, name, interests] of an author, given label as a string"""
    start_time = time.time()
    search_list_generator = scholarly.search_interests(label)
    print("--- Retrieving list from search label \"{0}\" took {1} seconds ---".format(label, str(time.time() - start_time)))
    # ------------ PROFILE ONLY CONTAINS 3 PARAMETERS. CALL AUTH_ALL_COAUTHORS ON PROFILE TO COMPLETE LIST ------------
    return search_list_generator

def retrieveAuthorPage(profileID):
    """Takes a string profileID and calls scraper to return AuthorProfile object"""
    try:
        start_time = time.time()
        auth_profile = scholarly.auth_all_coauthors(profileID)
        # if auth_profile is None:
        #     print("Error: Unable to retrieve profile for {0}".format(profileID))
        #     return auth_profile
        print("--- Retrieving {0}'s profile took {1} seconds ---".format(auth_profile.name, str(time.time() - start_time)))
        if not hasattr(auth_profile, 'organization'):
            print('No organization found for', auth_profile.name)
            # logf = openLogging()
            # logf.write("No organization found for {0}\n".format(str(auth_profile.name)))
        return auth_profile
    except Exception as e:
        logf = openLogging()
        logf.write(str(e))
        print(str(e))

# Create a hash set containing everyone that has worked with the author, and what paper was their most recent one.
# Hash set structure: {[name, year, paper_title]}
# Also take their coauthors and add it to the end of our to-search queue
def generateCoAuthorDict(profile):
    """Generates a dictionary that contains all of the author's coauthors, the year that they last worked together, and the title of the paper they wrote, given an AuthorProfile object."""
    try:
        # papers['author'] is a Set.
        return_authors = list()
        set_authors = set()
        set_paper_author = set()
        for papers in profile.publications:
            if 'author' not in papers:
                logf = openLogging()
                logf.write('{0}\'s "{1}" is missing authors'.format(str(profile.name), str(papers['title'])))
                print('{0}\'s "{1}" is missing authors'.format(str(profile.name), str(papers['title'])))
                continue

            title = papers['title']
            year = papers['year']
            # Do not consider the authors that are already in return_authors
            # NOTE: The author's name is already removed from this set; added feature in scholarly
            set_paper_author = papers['author'] - set_authors

            # Now that you have the new co-authors, add them to the dictionary of authors, along with its year and title
            for name in set_paper_author:
                return_authors.append([name, year, title])
                set_authors.add(name)
        # print("Returning data structure: {0}".format(return_authors))
        return return_authors
    except Exception as e:
        logf = openLogging()
        logf.write(str(e))
        print(str(e))

def saveNewAuthor(authProfile, mode='file'):
    author_info = dict()
    author_info[authProfile.id] = {
        'name': authProfile.name,
        'gs_profile_id': authProfile.id,
        'affiliation': authProfile.affiliation,
        'interest': list(authProfile.interests),
    }
    if mode == 'file':
        with open("logs/AUTH_{0}.txt".format(authProfile.id), 'w') as saveFile:
            json.dump(author_info, saveFile)
    elif mode == 'database':
        api.add_author(author_info[authProfile.id])
    return

def saveNewRelations(id, relationLists, mode='file'):
    authRelations = dict()
    authRelations[id] = relationLists
    if mode == 'file' or mode == 'both':
        with open("logs/RELATIONS_{0}.txt".format(id), 'w') as saveFile:        
            json.dump(authRelations, saveFile)
    elif mode == 'database' or mode == 'both':
        api.add_relations(id, relationLists)
    return

def saveSets(visited_labels, unvisited_labels, visited_orgs, unvisited_orgs, visited_authors, unvisited_authors):
    with open("logs/visited_labels.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(visited_labels) != 0):
            item = visited_labels.pop()
            wr.writerow([item])
    with open("logs/unvisited_labels.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(unvisited_labels) != 0):
            item = unvisited_labels.pop()
            wr.writerow([item])
    with open("logs/visited_orgs.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(visited_orgs) != 0):
            item = visited_orgs.pop()
            wr.writerow([item])
    with open("logs/unvisited_orgs.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(unvisited_orgs) != 0):
            item = unvisited_orgs.pop()
            wr.writerow([item])
    with open("logs/visited_authors.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(visited_authors) != 0):
            item = visited_authors.pop()
            wr.writerow([item])
    with open("logs/unvisited_authors.csv", 'w') as saveFile:
        wr = csv.writer(saveFile)
        while (len(unvisited_authors) != 0):
            item = unvisited_authors.pop()
            wr.writerow([item])
    return

def readSets():
    try:
        labels = set()
        orgs = set()
        authors = set()
        unvisited_labels = set()
        unvisited_orgs = set()
        unvisited_authors = set()
        with open("logs/visited_labels.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                labels.add(x[0])
        with open("logs/visited_orgs.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                orgs.add(x[0])
        with open("logs/visited_authors.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                authors.add(x[0])
        with open("logs/unvisited_labels.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                unvisited_labels.add(x[0])
        with open("logs/unvisited_orgs.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                unvisited_orgs.add(x[0])
        with open("logs/unvisited_authors.csv") as readFile:
            lis = [line.split() for line in readFile]
            for x in lis:
                unvisited_authors.add(x[0])
    except Exception as e:
        print(str(e))
    finally:
        return labels, orgs, authors, unvisited_labels, unvisited_orgs, unvisited_authors

# TODO: Multithread this method
def scrapeListContent(generator, visited_authors):
    """Given a generator function, scrape all authors and return a dictionary of information to send to server"""
    # new_relations: {authID: {'coAuth Name': [year, 'Paper name'], ...}}
    new_profiles = set()
    label_set = set()
    organization_set = set()
    leftover_profiles = list()
    for profile_array in generator:
        if (profile_array[0] in visited_authors):
            print("Already done ID", profile_array[0])
            continue
        # Try multiple times, sometimes it returns none
        # auth_profile = None
        # for i in range(5):
        auth_profile = retrieveAuthorPage(profile_array[0])
            # if auth_profile is not None:
                # break
        if auth_profile is None:
            print("Cannot find ID",profile_array[0])
            continue
        saveNewAuthor(auth_profile, 'both')
        new_profiles.add(auth_profile.id)

        for id in auth_profile.coauthors:
            leftover_profiles.append(id)

        coauthor_array = generateCoAuthorDict(auth_profile)
        saveNewRelations(auth_profile.id, coauthor_array, 'both')
        # new_relations[auth_profile.id] = coauthor_array

        # Add the labels and organizations into their sets
        label_set = label_set | profile_array[2]
        if hasattr(auth_profile, 'organization'):
            organization_set.add(auth_profile.organization)

    # There are some extra profiles to seach so iterate through those too
    print("Searching leftover profiles")
    while len(leftover_profiles) != 0:
        profile_id = leftover_profiles.pop()
        if (profile_id in visited_authors):
            print("Already done ID", profile_id)
            continue
        auth_profile = retrieveAuthorPage(profile_id)
        if auth_profile is None:
            print("Cannot find ID",profile_id)
            continue
        saveNewAuthor(auth_profile, 'both')
        new_profiles.add(auth_profile.id)

        for id in auth_profile.coauthors:
            leftover_profiles.append(id)
        
        coauthor_array = generateCoAuthorDict(auth_profile)
        saveNewRelations(auth_profile.id, coauthor_array, 'both')

        label_set = label_set | auth_profile.interests
        if hasattr(auth_profile, 'organization'):
            organization_set.add(auth_profile.organization)

    return new_profiles, label_set, organization_set

def manageSearchSets():
    """This method spins up new threads to search each label and organization number.
    Start with an organization, and then labels, etc"""

    # These data structures are used to maintain uniqueness
    # Can be converted to a list using list(setname)
    visited_labels = set() # Label [string]
    unvisited_labels = set() # Label [string]
    visited_orgs = set() # IDs [string]
    unvisited_orgs = set() # IDs [string]
    visited_authors = set() # IDs [string]
    unvisited_authors = set() # IDs [string]
    # related_coauthors stores the coauthors that are present in the sidebar of the profile currently being scanned; this will build a secondary list

    # Step 1: Take one label and scrape all of the profiles they produce
    # Let's say number of threads should not be greater than 10

    # Step 2: After searching the labels, we have to search all of the related_coauthors that are on the sidebars of those places
    
    # Step 3: Continue searching the labels until the list is empty, and then try searching all of the organizations, building up labels

    visited_labels, visited_orgs, visited_authors, unvisited_labels, unvisited_orgs, unvisited_authors= readSets()
    print("Skipping authors:",visited_authors)
    # print("Skipping labels:",visited_labels)
    # print("Skipping orgs:",visited_orgs)

    try:
        generator = None
        while (True):
            if (len(unvisited_labels) != 0):
                # Take a random label off the list, doesn't matter which
                search = unvisited_labels.pop()
                unvisited_labels.discard(search)
                visited_labels.add(search)
                generator = retrieveAuthorsFromLabels(search)
            else:
                if (len(unvisited_orgs) != 0):
                    # Take a random org number off the list, doesn't matter which
                    search = unvisited_orgs.pop()
                    unvisited_orgs.discard(search)
                    visited_orgs.add(search)
                    generator = retrieveAuthorsFromOrgNum(search)
                else:
                    return

            if (generator != None):
                scrapedProfiles, label_set, org_set = scrapeListContent(generator, visited_authors)
                # Add the new profiles to the visited profiles
                visited_authors = visited_authors | scrapedProfiles
                # Exclude the search areas which we've visited already
                new_labels = label_set - visited_labels
                new_orgs = org_set - visited_orgs
                # Add the new set to the unvisited set
                unvisited_labels = unvisited_labels | new_labels
                unvisited_orgs = unvisited_orgs | new_orgs
                # Save the set, so we can see the process.
                saveSets(visited_labels, unvisited_labels, visited_orgs, unvisited_orgs, visited_authors, unvisited_authors)
            else:
                print("Error! generator returned None! Skipping search query", search)
                break
    except Exception as e:
        logging.error(traceback.format_exc())
    finally:
        saveSets(visited_labels, unvisited_labels, visited_orgs, unvisited_orgs, visited_authors, unvisited_authors)

def main():
    # This will start the search as long as there is a label or organization number in unvisited_labels.csv or unvisited_orgs.csv respectively.
    manageSearchSets()

if __name__ == "__main__":
    main()