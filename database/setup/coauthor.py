from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from base import Base


class Coauthor(Base):
    """
        Many-to-one with Author
            e.g. one author may have multiple coauthors
    """
    __tablename__ = 'coauthors'

    id = Column(Integer, primary_key=True)
    person1_id = Column(Integer, ForeignKey('authors.id'))
    person1 = relationship("Author", backref="coauthors")
    person2_name = Column(String)
    most_recent_year = Column(Integer)
    most_recent_paper = Column(String)

    def __init__(self, person1_id, person2_name, most_recent_year, most_recent_paper):
        self.person1_id = person1_id
        self.person2_name = person2_name
        self.most_recent_year = most_recent_year
        self.most_recent_paper = most_recent_paper

    def __repr__(self):
        return "<Coauthor(person1_id='{0}', person2_name='{1}', most_recent_year='{2}', \
            'most_recent_paper='{3}')>" \
            .format(self.person1_id, self.person2_name, self.most_recent_year, self.most_recent_paper)
            