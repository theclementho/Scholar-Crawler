# import sys
# sys.path.append("databases/tables/")

from base import engine, Session, Base
from author import Author
from coauthor import Coauthor
from todo_list import TodoList

Base.metadata.create_all(engine)

session = Session()

session.commit()

session.close()
