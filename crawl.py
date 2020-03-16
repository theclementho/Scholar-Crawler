import os
import sys
import requests
import csv, json
import time
from datetime import datetime
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly
from collections import deque

# Start with an organization queue, labels queue, and a profile ID queue
# Take all of the authors (automatically sorted by number of citations) from an organization
# From author profile, filter and take all coauthors based on the last date they worked with the author
# Take their interests (searchable, to increase breadth of scraping) and add to queue
# Take the organization and add to queue
# If traversed all the organization numbers, switch to the label queue
# Submit organization and label sets to server, and remove labels and organizations already visited
# Repeat using queues, when organization queue is empty

# Error logging:
def openLogging():
    now = datetime.now().strftime("%d:%m:%Y_%H:%M:%S")
    logf = open("logs/scraping{0}.log".format(now), "w")
    return logf

# TODO: Replace the placeholders with the queues
# Start with UofT
placeholder_orgnum = '8515235176732148308'
# Pretend we also have a label from a queue
placeholder_label = "Debugging"

# deque operations
# queue.append() adds an element to the end, queue.popleft() removes the first thing in it and returns it
label_queue = deque()
organization_queue = deque()

# Next labels to search set -- needs to be verified with the database before every use; also update above queues
# label_set = set()
# organization_set = set()

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
        if auth_profile is None:
            print("Error: Unable to retrieve profile for {0}".format(profileID))
            return auth_profile
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
# Hash set structure: {name: [year, paper_title]}
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
        print("Returning data structure: {0}".format(return_authors))
        return return_authors
    except Exception as e:
        logf = openLogging()
        logf.write(str(e))
        print(str(e))

### TODO: Add to this when the database API is known
def writeToDatabase(profile):
    return

# TODO: Multithread this method
def scrapeListContent(generator):
    """Given a generator function, scrape all authors and return a dictionary of information to send to server"""
    # new_relations: {authID: {'coAuth Name': [year, 'Paper name'], ...}}
    new_profiles = set()
    new_relations = dict()
    label_set = set()
    organization_set = set()
    for profile_array in generator:
        auth_profile = retrieveAuthorPage(profile_array[0])
        new_profiles.add(auth_profile)

        # TODO: Add the coauthors written on their page to a queue "to search"

        coauthor_array = generateCoAuthorDict(auth_profile)
        new_relations[auth_profile.id] = coauthor_array

        # Add the labels and organizations into their sets
        label_set = label_set | profile_array[2]
        if hasattr(auth_profile, 'organization'):
            organization_set.add(auth_profile.organization)

    ## After testing, remove label_set and organization_set from return
    return new_profiles, new_relations, label_set, organization_set

def manageSearchSets():
    """This method spins up new threads to search each label and organization number.
    Start with an organization, and then labels, etc"""

    # These data structures are used to maintain uniqueness
    # Can be converted to a list using list(setname)
    visited_labels = set() # Label [string]
    unvisited_labels = set() # Label [string]
    visited_orgs = set() # IDs [string]
    unvisited_ orgs = set() # IDs [string]
    visited_authors = set() # IDs [string]
    related_coauthors = set() # IDs [string]
    # related_coauthors stores the coauthors that are present in the sidebar of the profile currently being scanned; this will build a secondary list

    # Step 1: Take one label and scrape all of the profiles they produce
    # Let's say number of threads should not be greater than 10

    # Step 2: After searching the labels, we have to search all of the related_coauthors that are on the sidebars of those places
    
    # Step 3: Continue searching the labels until the list is empty, and then try searching all of the organizations, building up labels 

    return

def main():
    # Loop over the whole thing until both are empty
    # while(label_queue or organization_queue):
    """STEP 1: Get the author profiles from every profile in the organization"""
    # Replace placeholder_orgnum with search_query = organization_queue.popleft()
    # Each element in auth_list contains [ID, name, interests]
    auth_list = retrieveAuthorsFromOrgNum(placeholder_orgnum)

    scrapeListContent(auth_list)

    # TODO: Create set of parameters for author profile and coauthor information to send to database

    # TODO: Submit the list of labels and organizations to database to filter the visited ones

    # TODO: append the final organization_set and label_set to their respective queues

    """STEP 2: Take a label and crawl authors related to those"""
    # Replace placeholder_label with search_query = label_queue.popleft()
    auth_list = retrieveAuthorsFromLabels(placeholder_label)

    scrapeListContent(auth_list)
