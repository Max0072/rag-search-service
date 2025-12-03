"""
Database initialization script

This script creates the database tables and can be used to set up the database initially.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.main_db import MetadataDatabase, get_main_db
from app.database.db_models import Base


def init_database():
    """Initialize the database by creating all tables"""
    print("🗄️  Initializing database...")

    try:
        # Get database instance
        db = get_main_db()

        # Create all tables
        print("📦 Creating tables...")
        db.init_db()

        print("✅ Database initialized successfully!")
        print(f"   Tables created: {', '.join(Base.metadata.tables.keys())}")

        # Show current stats
        print("\n📊 Current database stats:")
        stats = db.get_stats()
        print(f"   Total calls: {stats['total_calls']}")
        print(f"   Total chunks: {stats['total_chunks']}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)