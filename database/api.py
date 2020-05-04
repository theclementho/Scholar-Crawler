import time
import sys
sys.path.append('database/setup/')

from base import Session
from author import Author
from coauthor import Coauthor
from todo_list import TodoList
# sys.path.append('..')
# sys.path.append('setup/')

# from database.setup.base import Session
# from database.setup.author import Author
# from database.setup.coauthor import Coauthor
# from database.setup.todo_list import TodoList

# from .setup.base import Session
# from .setup.author import Author
# from .setup.coauthor import Coauthor
# from .setup.todo_list import TodoList

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
                to_add.append(TodoList(name=each['name'], type=type, status=NEW))
        session.add_all(to_add)

    session.commit()

def add_author(authProfile):
    """Add a single author"""
    name = authProfile['name']
    gs_profile_id = authProfile['gs_profile_id']
    affiliation = authProfile['affiliation']
    interest = ', '.join(authProfile['interest'])

    if session.query(exists().where(Author.gs_profile_id == gs_profile_id)).scalar():
        return
    else:
        author = Author(name=name, gs_profile_id=gs_profile_id, affiliation=affiliation, interest=interest)
        print('WRITE: author %s to database...' % gs_profile_id)
        session.add(author)
        queue_todo(name, AUTHOR)
        session.commit()

def add_authors(authProfiles):
    """Add a list of authors"""
    formatted = [Author(
        name=i['name'], 
        gs_profile_id=i['gs_profile_id'], 
        affiliation=i['affiliation'], 
        interest=', '.join(i['interest'])
        ) for i in authProfiles]
    print('WRITE: %d authors to database...' % len(authProfiles))
    session.add_all(formatted)
    queue_todo(formatted, AUTHOR)
    session.commit()

def add_relations(profile_id, relationLists):
    """Add relations of an author"""
    formatted = [Coauthor(
        person1_id = profile_id,
        person2_name = i[0],
        most_recent_year = i[1],
        most_recent_paper = i[2]
    ) for i in relationLists]
    print('WRITE: %d relations of %s to database...' % (len(relationLists), profile_id))
    session.add_all(formatted)
    # queue_todo(formatted, AUTHOR) #FIXME: necessary?
    session.commit()

# test single author insertion
# start = time.time()
# add_author("Different Chris", "akdfjjas", "University of Toronto", "Self isolation, social distancing")
# end = time.time()
# print('Elapsed time: ', end - start)


# time.sleep(0.5)

# test get profile
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
    
