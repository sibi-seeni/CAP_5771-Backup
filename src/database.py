import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Setting up Database Connection
DATABASE_URL = "sqlite:///arc_raiders_sentiment.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Defining Schema
class Video(Base):
    __tablename__ = "videos"
    
    video_id = Column(String, primary_key=True)  # unique ID
    title = Column(String)
    description = Column(Text)
    channel_id = Column(String)
    published_at = Column(DateTime)
    keyword_matched = Column(String)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    comments_disabled = Column(Boolean, default=False)  # For skipping videos that have their comments disabled

    # Relationship to comments
    comments = relationship("Comment", back_populates="video")

class Comment(Base):
    __tablename__ = "comments"
    
    comment_id = Column(String, primary_key=True)  # deduplication
    video_id = Column(String, ForeignKey("videos.video_id"))
    parent_id = Column(String, nullable=True)  # reply threading
    author_hash = Column(String)  # anonymized for ethics
    text = Column(Text)
    published_at = Column(DateTime)
    last_updated_at = Column(DateTime)
    
    video = relationship("Video", back_populates="comments")

class CollectionState(Base):
    __tablename__ = "collection_state"
    
    keyword = Column(String, primary_key=True)
    last_search_time = Column(DateTime)  # For incremental search

# Initializing Database
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Phase 1: Database and tables created successfully.")

if __name__ == "__main__":
    init_db()