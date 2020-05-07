#! /usr/bin/env python3
#  -*- coding: utf-8 -*-

"""
traceroute_history is a quick tool to make traceroute / tracert calls, and store it's results into a database if it
differs from last call.

This file contains the SQLAlchemy ORM models

"""

__intname__ = 'traceroute_history'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.4.0'
__build__ = '2020050601'


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Traceroute(Base):
    __tablename__ = 'traceroute'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())  # using func.now() guarantees UTC data
    raw_traceroute = Column(String(2048), nullable=False)
    target_id = Column(Integer, ForeignKey('target.id'))
    target = relationship('Target')

    def __repr__(self):
        return 'Traceroute recorded at {0}:\n {1}'.format(self.creation_date, self.raw_traceroute)


# Many to Many relationship
target_groups_association = Table('target_groups_association', Base.metadata,
                                  Column('target_id', Integer, ForeignKey('target.id')),
                                  Column('group_id', Integer, ForeignKey('group.id')))


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(255), unique=True, nullable=False)
    targets = relationship('Target', secondary=target_groups_association, back_populates='groups')

    def __repr__(self):
        return 'Group "{0}" created on {1}'.format(self.name, self.creation_date)


class Target(Base):
    __tablename__ = 'target'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(255), unique=True, nullable=False)
    address = Column(String(512), nullable=True)
    traceroutes = relationship(Traceroute, backref='traceroutes')
    groups = relationship('Group', secondary=target_groups_association, back_populates='targets')

    def __repr__(self):
        return 'Target {0}: address={1}, created on {2}'.format(self.name, self.address, self.creation_date)


def init_db(db_engine):
    Base.metadata.create_all(db_engine)
