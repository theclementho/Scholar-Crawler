from sqlalchemy import Column, String, Integer
from base import Base


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    gs_profile_id = Column(String, unique=True)
    affiliation = Column(String)
    interest = Column(String)

    def __init__(self, name, gs_profile_id, affiliation, interest):
        self.name = name
        self.gs_profile_id = gs_profile_id
        self.affiliation = affiliation
        self.interest = interest

    def __repr__(self):
        return "<Author(name='{0}', affiliation='{1}', interest='{2}')>" \
            .format(self.name, self.affiliation, self.interest)
            