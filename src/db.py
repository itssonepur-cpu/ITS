from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
import os

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    name = Column(String(120))
    phone = Column(String(20), unique=True, index=True)
    tags = Column(String(255), default="")
    unsubscribed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MessageLog(Base):
    __tablename__ = "message_logs"
    id = Column(Integer, primary_key=True)
    direction = Column(String(10))  # inbound/outbound
    phone = Column(String(20), index=True)
    content = Column(Text)
    status = Column(String(30), default="queued")
    extra = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    segment = Column(String(255))  # tag query
    template = Column(Text)
    media_url = Column(String(500), default="")
    schedule = Column(String(50), default="once")  # once/daily/weekly
    next_run = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def make_session(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
