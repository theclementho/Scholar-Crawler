import os
import sys
import requests
import csv, json
import time
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly

# Start with an organization
# Take all the labels
# Take all of the authors (automatically sorted by number of citations)
# From authors, take their coauthors from their works cited,
# also take the authors from their publication list
# If there is an overlap between the coauthor name with the co-author name from the works cited list, then replace the name with an ID

# Error logging:
logf = open("download.log", "w")

# Start with UofT
uoft_org = '8515235176732148308'
org_num = uoft_org

def retrieveAuthorPage(profileID):
    """Takes a string profileID and calls scraper to return AuthorProfile object"""
    start_time = time.time()
    auth_profile = scholarly.auth_all_coauthors(profileID)
    print("--- Retrieving profile {0} seconds ---".format(str(time.time() - start_time)))
    if not hasattr(auth_profile, 'organization'):
        print('No organization found for', auth_profile.name)
        logf.write("No organization found for {0}\n".format(str(auth_profile.name)))
    return auth_profile

def retrieveAuthorList(org_num):
    """Return a generator function to retrieve [ID, name, interests] of an author, given organization number"""
    start_time = time.time()
    search_list_generator = scholarly.search_org(org_num)
    print("--- Retrieving list of org took {0} seconds ---".format(str(time.time() - start_time)))
    # ------------ PROFILE ONLY CONTAINS 3 PARAMETERS. CALL AUTH_ALL_COAUTHORS ON PROFILE TO COMPLETE LIST ------------
    for profile in search_list_generator:
        print("Profile[0]:", profile[0]) # Author ID
        print("Profile[1]:", profile[1]) # Name
        print("Profile[2]:", profile[2]) # Interests
    return search_list_generator

# Create a hash set containing everyone that has worked with the author, and what paper was their most recent one.
# Hash set structure: {name: [year, paper_title]}
def generateCoAuthorDict(profile):
    """Generates a dictionary that contains all of the author's coauthors, the year that they last worked together, and the title of the paper they wrote, given an AuthorProfile object."""
    # papers.bib['author'] is a Set.
    return_authors = dict()
    set_authors = set()
    set_paper_author = set()
    for papers in profile.publications:
        if not hasattr(papers.bib['author']):
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
    # Each element in auth_list contains [ID, name, interests]
    auth_list = retrieveAuthorList(uoft_org)
    
    for profile_array in auth_list:
        auth_profile = retrieveAuthorPage(profile_array[0])
        coauthor_dictionary = generateCoAuthorDict(auth_profile)


if __name__ == "__main__":
    main()