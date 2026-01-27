"""
Metadata database (PostgreSQL) integration
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from app.database.db_models import Base, Call
from app.config import get_settings

settings = get_settings()


class MetadataDatabase:
    """PostgreSQL database for storing complete call metadata"""

    def __init__(self):
        self.engine = create_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)



# ------ Create all tables if they don't exist --------------------------------- done
    def init_db(self):
        Base.metadata.create_all(bind=self.engine)


# ------ Get a new database session -------------------------------------------- done
    def get_session(self) -> Session:
        return self.SessionLocal()


# ------ Add call to the database ---------------------------------------------- done
    def create_call(self, call_id: str, full_transcript: str, summary: str,
                    date: datetime, attendants: List[str], topic: Optional[str] = None,
                    meeting_type: Optional[str] = None, duration_minutes: Optional[int] = None,
                    meta: Optional[Dict[str, Any]] = None, chunks_count: int = 0) -> Call:

        session = self.get_session()
        try:
            call = Call(call_id=call_id, full_transcript=full_transcript, summary=summary,
                        date=date, attendants=attendants, meta=meta or {},
                        chunks_count=chunks_count, processed_at=datetime.now()
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            return call
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to create call: {str(e)}")
        finally:
            session.close()


# ------ Get call by id -------------------------------------------------------- done
    def get_call(self, call_id: str) -> Optional[Call]:
        session = self.get_session()
        try:
            call = session.query(Call).filter(Call.call_id == call_id).first()
            return call
        finally:
            session.close()


# ------ Get many call by id --------------------------------------------------------
    def get_calls(self,
                  call_ids: Optional[List[str]] = None,
                  date_from: Optional[datetime] = None,
                  date_to: Optional[datetime] = None,
                  attendants: Optional[List[str]] = None,
                  meeting_type: Optional[str] = None,
                  limit: int = 100,
                  offset: int = 0
                  ) -> List[Call]:
        session = self.get_session()
        try:
            query = session.query(Call)
            if call_ids:
                query = query.filter(Call.call_id.in_(call_ids))
            if date_from:
                query = query.filter(Call.date >= date_from)
            if date_to:
                query = query.filter(Call.date <= date_to)
            if attendants:
                attendant_filters = [Call.attendants.contains([name]) for name in attendants]
                query = query.filter(or_(*attendant_filters))
            # query = query.order_by(Call.date.desc())
            query = query.limit(limit).offset(offset)
            return query.all()
        finally:
            session.close()

# ------ Update call  -------------------------------------------------------- done
    def update_call(self, call_id: str, **kwargs) -> Optional[Call]:
        session = self.get_session()
        try:
            call = session.query(Call).filter(Call.call_id == call_id).first()
            if not call:
                return None

            for key, value in kwargs.items():
                if hasattr(call, key):
                    setattr(call, key, value)

            session.commit()
            session.refresh(call)
            return call
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to update call: {str(e)}")
        finally:
            session.close()

# ------ Delete call by id ------------------------------------------------- done
    def delete_call(self, call_id: str) -> bool:
        session = self.get_session()
        try:
            call = session.query(Call).filter(Call.call_id == call_id).first()
            if not call:
                return False
            session.delete(call)
            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise Exception(f"Failed to delete call: {str(e)}")
        finally:
            session.close()

# ------ Get stats --------------------------------------------------------- done
    def get_stats(self) -> Dict[str, Any]:
        session = self.get_session()
        try:
            total_calls = session.query(Call).count()
            total_chunks = session.query(Call.chunks_count).all()
            total_chunks_sum = sum(c[0] for c in total_chunks if c[0])

            # Get date range
            oldest = session.query(Call.date).order_by(Call.date.asc()).first()
            newest = session.query(Call.date).order_by(Call.date.desc()).first()

            return {
                "total_calls": total_calls,
                "total_chunks": total_chunks_sum,
                "oldest_call": oldest[0].isoformat() if oldest and oldest[0] else None,
                "newest_call": newest[0].isoformat() if newest and newest[0] else None,
            }
        finally:
            session.close()


# Singleton instance
_main_db = None


def get_main_db() -> MetadataDatabase:
    """Get singleton metadata database instance"""
    global _main_db
    if _main_db is None:
        _main_db = MetadataDatabase()
    return _main_db


if __name__ == "__main__":
    """Test database connection and operations"""
    print("🗄️  Testing PostgreSQL connection...")

    try:
        # Initialize database
        db = MetadataDatabase()
        print(f"✅ Connected to PostgreSQL")

        # Create tables
        print(f"📦 Creating tables...")
        db.init_db()
        print(f"✅ Tables created")

        # Test create
        print(f"\n🧪 Testing create operation...")
        test_call = db.create_call(
            call_id="test-call-00",
            full_transcript="Alice: Hello everyone. Bob: Hi Alice. This is a test transcript.",
            summary="Test call to verify database operations",
            date=datetime.now(),
            attendants=["Alice", "Bob"],
            topic="Database Testing",
            meeting_type="internal",
            duration_minutes=15,
            meta={
                "department": "engineering",
                "project": "RAG System"
            },
            chunks_count=3
        )
        print(f"✅ Created call: {test_call.call_id}")

        # Test get
        print(f"\n🔍 Testing get operation...")
        retrieved_call = db.get_call("test-call-001")
        if retrieved_call:
            print(f"✅ Retrieved call: {retrieved_call.call_id}")
            print(f"   Attendants: {retrieved_call.attendants}")
        else:
            print(f"❌ Failed to retrieve call")

        print(f"\n🔍 Testing update operation...")
        for i in range(1, 10):
            result = db.update_call(f"test-call-00{i}", attendants=["Max", "Sava"])
            if result:
                print(f"Result: {result.call_id}")
            else:
                print(f"result: {result}")



        # Test query
        print(f"\n🔍 Testing query operation...")
        calls = db.get_calls(attendants=["Alice"], limit=5)
        print(calls[0].call_id)
        print()
        print(f"✅ Found {len(calls)} call(s) with Alice")

        # Test stats
        print(f"\n📊 Database Statistics:")
        stats = db.get_stats()
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Oldest call: {stats['oldest_call']}")
        print(f"   Newest call: {stats['newest_call']}")

        # Test delete
        print(f"\n🗑️  Testing delete operation...")
        deleted = db.delete_call("test-call-001")
        if deleted:
            print(f"✅ Deleted test call")
        else:
            print(f"❌ Failed to delete call")

        print(f"\n✨ All tests passed! PostgreSQL is working correctly.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
