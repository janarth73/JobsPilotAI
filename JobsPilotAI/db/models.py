from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

def get_engine():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'jobs.db')
    return create_engine(f'sqlite:///{db_path}', echo=False)

def get_session():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

class Job(Base):
    __tablename__ = 'jobs'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    job_id      = Column(String(200), unique=True, nullable=False)
    title       = Column(String(300))
    company     = Column(String(200))
    location    = Column(String(200))
    salary      = Column(String(100))
    experience  = Column(String(100))
    description = Column(Text)
    skills      = Column(Text)
    apply_url   = Column(String(500))
    source      = Column(String(50))
    posted_date = Column(String(50))
    scraped_at  = Column(DateTime, default=datetime.utcnow)
    match_score = Column(Float, default=0.0)
    is_applied  = Column(Boolean, default=False)
    applied_at  = Column(DateTime, nullable=True)
    status      = Column(String(50), default='new')

class ApplicationLog(Base):
    __tablename__ = 'application_logs'
    id        = Column(Integer, primary_key=True, autoincrement=True)
    job_id    = Column(Integer)
    action    = Column(String(100))
    note      = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
