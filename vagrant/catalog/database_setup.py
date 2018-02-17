import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

class Person(Base):
	__tablename__ = 'people'
	name = Column(String(100))
	email = Column(String(100))
	id = Column(Integer, primary_key = True)

class Idea(Base):
	__tablename__ = 'ideas'
	title = Column(String(300), nullable = False)
	description = Column(String(300), nullable = False)
	id = Column(Integer, primary_key = True)
	person_id = Column(Integer, ForeignKey('people.id'))
	people = relationship(Person)

	@property
	def serialize(self):
		return {
			'title': self.title,
			'description': self.description,
			'id': self.id,
			'person_id': self.person_id,
			'name_person': self.people.name
		}

class Comment(Base):
	__tablename__ = 'comments'
	text = Column(String(300), nullable = False)
	id = Column(Integer, primary_key = True)
	idea_id = Column(Integer, ForeignKey('ideas.id'))
	person_id = Column(Integer, ForeignKey('people.id'))
	people = relationship(Person)
	idea = relationship(Idea)


engine = create_engine('sqlite:///vantage_feedback_users.db')

Base.metadata.create_all(engine)