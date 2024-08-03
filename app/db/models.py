from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from .session import Base


# Association table for the many-to-many relationship between parts and tags
part_tags = Table(
    'part_tags', Base.metadata,
    Column('part_id', Integer, ForeignKey('parts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Plate(Base):
    __tablename__ = 'plates'

    plate_number = Column(String(10), primary_key=True, index=True)
    is_flagged = Column(Boolean, default=False)

class Part(Base):
    __tablename__ = 'parts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String(10), index=True)
    part = Column(String(10))
    reason = Column(String(255))
    confidence_rating = Column(Integer)
    tags = relationship('Tag', secondary=part_tags, back_populates='parts')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag = Column(String(50))
    parts = relationship('Part', secondary=part_tags, back_populates='tags')