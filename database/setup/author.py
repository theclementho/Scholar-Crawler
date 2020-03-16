from sqlalchemy import Column, String, Integer
from base import Base


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    affiliation = Column(String)
    interest = Column(String)

    def __init__(self, name, affiliation, interest):
        self.name = name
        self.affiliation = affiliation
        self.interest = interest

    def __repr__(self):
        return "<Author(name='{0}', affiliation='{1}', interest='{2}')>" \
            .format(self.name, self.affiliation, self.interest)