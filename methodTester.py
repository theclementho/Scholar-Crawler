import crawl
import time
import json

import sys
scholarlypath = "scholarly-master/scholarly/"
sys.path.append(scholarlypath)
import scholarly

# Generate fake data to test each method on
# Functions to test:
# retrieveAuthorsFromOrgNum
# retrieveAuthorsFromLabels
# retrieveAuthorPage
# generateCoAuthorDict
# writeToDatabase       (later)
# scrapeListContent

uoft_org = '8515235176732148308'
example_label = "Debugging"
DY_id = 'g7PHxIYAAAAJ'

def printAuthorInfoFromGenerator(generator):
    try:
        for author in generator:
            print("Author ID: ", author[0])
            print("Name: ", author[1])
            print("Interests Set: ", author[2])
    except Exception as e:
        logf = crawl.openLogging()
        logf.write(str(e))

def printAuthorProfile(authorProfile):
    try:
        print("Name: ", authorProfile.name)
        print("ID: ", authorProfile.id)
        print("Affiliation: ", authorProfile.affiliation)
        print("Interests: ", authorProfile.interests)
        print("Coauthors: ", authorProfile.coauthors)
        if hasattr('organization', authorProfile):
            print("Organization number: ", authorProfile.organization)

        if hasattr('publications', authorProfile):
            print ("Publications:")
            for row in authorProfile.publications:
                print("Title: ", row['title'])
                print("Author: ", row['author'])
                print("Year: ", row['year'])

    except Exception as e:
        logf = crawl.openLogging()
        logf.write(str(e))

def test_retrieveAuthorsFromOrgNum(): 
    generator = crawl.retrieveAuthorsFromOrgNum(uoft_org)
    printAuthorInfoFromGenerator(generator)

def test_retrieveAuthorsFromLabels():
    generator = crawl.retrieveAuthorsFromLabels(example_label)
    printAuthorInfoFromGenerator(generator)

def test_retrieveAuthorPage():
    authorProfile = crawl.retrieveAuthorPage(DY_id)
    printAuthorProfile(authorProfile)

def test_generateCoAuthorDict():
    """This test assumes that test_retrieveAuthorPage() 
    works as expected."""
    authorProfile = crawl.retrieveAuthorPage(DY_id)
    coauthors = crawl.generateCoAuthorDict(authorProfile)
    print (coauthors)

def test_scrapeListContent():
    test_start = time.time()
    # generator = crawl.retrieveAuthorsFromOrgNum(uoft_org)
    generator = crawl.retrieveAuthorsFromLabels(example_label)
    newProfiles, newRelations, label_set, org_set = crawl.scrapeListContent(generator)
    print("New Author Profiles:")
    for author in newProfiles:
        # printAuthorProfile(author)
        print(author.name)
    print("New Relations:")
    for coauthor in newRelations:
        print(coauthor,": ",newRelations[coauthor])
    print("New Labels:")
    print(label_set)
    print("New org numbers:")
    print(org_set)

    # Save dict
    with open("uoft_org.txt", mode='w') as scraped:
        json.dump(newRelations, scraped)

    print("Total test took {0} seconds.".format(str(time.time()-test_start)))
    

if __name__ == '__main__':
    # test_retrieveAuthorsFromOrgNum()
    # test_retrieveAuthorsFromLabels()
    # test_retrieveAuthorPage()
    # test_generateCoAuthorDict()
    test_scrapeListContent()