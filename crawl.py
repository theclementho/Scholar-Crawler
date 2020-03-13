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
now = datetime.now().strftime("%d/%m/%Y_%H:%M:%S")
logf = open("scraping{0}.log".format(now), "w")

# TODO: Replace the placeholders with the queues
# Start with UofT
placeholder_orgnum = '8515235176732148308'
# Pretend we also have a label from a queue
placeholder_label = "Debugging"

# deque operations
# queue.append() adds an element to the end, queue.popleft() removes the first thing in it and returns it
label_queue = deque()
organization_queue = deque()

# Next labels to search set -- needs to be verified with the database before every use
label_set = set()
organization_set = set()

def retrieveAuthorsFromOrgNum(org_num):
    """Return a generator function to retrieve [ID, name, interests] of an author, given organization number"""
    start_time = time.time()
    search_list_generator = scholarly.search_org(org_num)
    print("--- Retrieving list from org number took {0} seconds ---".format(str(time.time() - start_time)))
    # ------------ PROFILE ONLY CONTAINS 3 PARAMETERS. CALL AUTH_ALL_COAUTHORS ON PROFILE TO COMPLETE LIST ------------
    for profile in search_list_generator:
        print("Profile[0]:", profile[0]) # Author ID
        print("Profile[1]:", profile[1]) # Name
        print("Profile[2]:", profile[2]) # Interests
    return search_list_generator

def retrieveAuthorsFromLabels(label):
    """Return a generator function to retrieve [ID, name, interests] of an author, given label as a string"""
    start_time = time.time()
    search_list_generator = scholarly.search_interests(label):
    print("--- Retrieving list from interests took {0} seconds ---".format(str(time.time() - start_time)))
    # ------------ PROFILE ONLY CONTAINS 3 PARAMETERS. CALL AUTH_ALL_COAUTHORS ON PROFILE TO COMPLETE LIST ------------
    for profile in search_list_generator:
        print("Profile[0]:", profile[0]) # Author ID
        print("Profile[1]:", profile[1]) # Name
        print("Profile[2]:", profile[2]) # Interests
    return search_list_generator

def retrieveAuthorPage(profileID):
    """Takes a string profileID and calls scraper to return AuthorProfile object"""
    start_time = time.time()
    auth_profile = scholarly.auth_all_coauthors(profileID)
    print("--- Retrieving profile {0} seconds ---".format(str(time.time() - start_time)))
    if not hasattr(auth_profile, 'organization'):
        print('No organization found for', auth_profile.name)
        logf.write("No organization found for {0}\n".format(str(auth_profile.name)))
    return auth_profile

# Create a hash set containing everyone that has worked with the author, and what paper was their most recent one.
# Hash set structure: {name: [year, paper_title]}
def generateCoAuthorDict(profile):
    """Generates a dictionary that contains all of the author's coauthors, the year that they last worked together, and the title of the paper they wrote, given an AuthorProfile object."""
    # papers.bib['author'] is a Set.
    return_authors = dict()
    set_authors = set()
    set_paper_author = set()
    for papers in profile.publications:
        if 'author' not in papers.bib:
            logf.write('{0}\'s {1} is missing a year'.format(str(profile.name), str(papers.bib['title'])))
            continue

        title = papers.bib['title']
        year = papers.bib['year']
        # Do not consider the authors that are already in return_authors
        # NOTE: The author's name is already removed from this set; added feature in scholarly
        set_paper_author = papers.bib['author'] - set_authors

        # Now that you have the new co-authors, add them to the dictionary of authors, along with its year and title
        for name in set_paper_author:
            return_authors[name] = [year, papers.bib['title']]
            set_authors.add(name)
    
    return return_authors

### TODO: Add to this when the database API is known
def writeToDatabase(profile):
    return

def main():
    # Loop over the whole thing until both are empty
    # while(label_queue or organization_queue):
    """STEP 1: Get the author profiles from every profile in the organization"""
    # Replace placeholder_orgnum with search_query = organization_queue.popleft()
    # Each element in auth_list contains [ID, name, interests]
    auth_list = retrieveAuthorsFromOrgNum(placeholder_orgnum)

    # Generate the coauthor dictionary
    # Generate the set of labels 
    for profile_array in auth_list:
        auth_profile = retrieveAuthorPage(profile_array[0]) # Contains organization too
        coauthor_dictionary = generateCoAuthorDict(auth_profile)
        
        # Add the labels and organizations into their sets
        label_set = label_set | profile_array[2]
        if 'organization' in auth_profile:
            organization_set = organization_set | auth_profile.organization

    # TODO: Create set of parameters for author profile and coauthor information to send to database

    # TODO: Submit the list of labels and organizations to database to filter the visited ones

    # TODO: append the final organization_set and label_set to their respective queues

    """STEP 2: Take a label and crawl authors related to those"""
    # Replace placeholder_label with search_query = label_queue.popleft()
    auth_list = retrieveAuthorsFromLabels(placeholder_label)
    for profile_array in auth_list:
        auth_profile = retrieveAuthorPage(profile_array[0])
        coauthor_dictionary = generateCoAuthorDict(auth_profile)

        label_set = label_set | profile_array[2]
        if 'organization' in auth_profile:
            organization_set = organization_set | auth_profile.organization


if __name__ == "__main__":
    main()