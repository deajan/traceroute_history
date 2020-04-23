
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Traceroute(Base):
    __tablename__ = 'traceroute'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())  # using func.now() guarantees UTC data
    # update_date = Column(DateTime(timezone=True), onupdate=func.now())
    traceroute = Column(String(255), nullable=False)
    target_id = Column(Integer, ForeignKey('target.id'))
    target = relationship('Target')

    def __repr__(self):
        return f'Traceroute recorded at {self.creation_date}:\n {self.traceroute}'


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(255), nullable=False)
    target_id = Column(Integer, ForeignKey('target.id'))
    target = relationship('Target')

    def __repr(self):
        return f'Group name: {self.name}'


class Target(Base):
    __tablename__ = 'target'

    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    name = Column(String(255), unique=True, nullable=False)
    address = Column(String(255), nullable=True)
    traceroutes = relationship(Traceroute, backref='traceroutes')
    groups = relationship(Traceroute, backref='groups' )

    def __repr__(self):
        return f'Target {self.name}: fqdn={self.fqdn}, ipv4={self.ipv4}, ipv6={self.ipv6}'


def init_db(db_engine):
    Base.metadata.create_all(db_engine)

