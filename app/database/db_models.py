"""
SQLAlchemy database models for metadata storage
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Call(Base):
    """
    Conference call metadata and full transcript storage

    This is the "cold storage" for complete call data.
    Vector DB stores chunks for fast retrieval, this stores the source of truth.
    """
    __tablename__ = "calls"

    # Primary key
    call_id = Column(String, primary_key=True, index=True)

    # Core data
    full_transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Metadata
    date = Column(DateTime, nullable=False, index=True)
    attendants = Column(ARRAY(String), nullable=True, index=True)


    # Additional metadata (flexible JSON field)
    meta = Column(JSON, nullable=True, default={})
    # meta can contain:
    # - department
    # - project
    # - client_name
    # - language
    # - recording_url
    # - custom fields

    # Statistics
    chunks_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "call_id": self.call_id,
            "full_transcript": self.full_transcript,
            "summary": self.summary,
            "date": self.date.isoformat() if self.date else None,
            "attendants": self.attendants,
            "meta": self.meta,
            "chunks_count": self.chunks_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }



def main():
    class1 = Call()
    print(class1.to_dict())

if __name__ == "__main__":
    main()
