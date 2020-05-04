from sqlalchemy import Column, String, Integer
from base import Base


class TodoList(Base):
    __tablename__ = 'todo_list'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    status = Column(Integer)

    def __init__(self, name, type, status):
        self.name = name
        self.type = type
        self.status = status

    def __repr__(self):
        return "<TodoList(name='{0}', type='{1}', status='{2}'" \
            .format(self.name, self.type, self.status)
            