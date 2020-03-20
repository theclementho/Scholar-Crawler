import time
import sys
sys.path.append('..')
sys.path.append('setup/')

from database.setup.base import Session
from database.setup.author import Author
from database.setup.todo_list import TodoList
from sqlalchemy.sql import exists

session = Session()

# Constants
AUTHOR = 0
INTEREST = 1
ORGANIZATION = 2
NEW = 0
ONGOING = 1
DONE = 2


def get_profile(gs_profile_id):
    """Find author using google scholar profile id"""
    author = session.query(Author).filter(Author.gs_profile_id == gs_profile_id).first()
    return author
        
def queue_todo(target, type):
    """Check todo list, queue to todo list if not exists"""
    if isinstance(target, str): # one target
        exists = session.query(TodoList).filter(TodoList.name == target).first()
        if not exists:
            session.add(TodoList(name=target, type=type, status=NEW))
    
    elif isinstance(target, list): #multiple targets
        to_add = []
        for each in target:
            exists = session.query(TodoList).filter(TodoList.name == each['name']).first()
            if not exists:
                to_add.append(TodoList(name=each['name'], type=AUTHOR, status=NEW))
        session.add_all(to_add)

    session.commit()

def add_author(name, gs_profile_id, affiliation, interest):
    """Add a single author"""
    print('Adding... ', name, gs_profile_id, affiliation, interest)
    if session.query(exists().where(Author.gs_profile_id == gs_profile_id)).scalar():
        return
    else:
        author = Author(name=name, gs_profile_id=gs_profile_id, affiliation=affiliation, interest=interest)
        session.add(author)
        queue_todo(name, AUTHOR)
        session.commit()

def add_authors(authors):
    """Add a list of authors"""
    formatted = [Author(name=i['name'], gs_profile_id=i['gs_profile_id'], affiliation=i['affiliation'], \
        interest=i['interest']) for i in authors]
    session.add_all(formatted)
    queue_todo(authors, AUTHOR)
    session.commit()


# test single author insertion
# start = time.time()
# add_author("Different Chris", "akdfjjas", "University of Toronto", "Self isolation, social distancing")
# end = time.time()
# print('Elapsed time: ', end - start)



# test = get_profile("dklfjalejE")
# print(test)

# test adding multiple authors
# multiple_authors = [
    # {
    #     'name': 'Clement',
    #     'gs_profile_id': 'asljel',
    #     'affiliation': 'University of Toronto',
    #     'interest': 'A, B, C'
    # },
#     {
#         'name': 'Keven',
#         'gs_profile_id': 'JEIIsljeliaj',
#         'affiliation': 'University of Toronto',
#         'interest': 'D, E'
#     }
# ]
# add_authors(multiple_authors)

# TEST multiple authors 
# authors = []
# for i in range(100):
#     authors.append({
#         'name': 'Test' + str(i),
#         'gs_profile_id': 'AABB' + str(i),
#         'affiliation': 'Testing',
#         'interest': 'A, B, C'
#     })

# print ('Length of array to be inserted: ', len(authors))

# start = time.time()
# add_authors(authors)
# end = time.time()
# print('Elapsed time: ', end - start)
    
