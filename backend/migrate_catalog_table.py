#!/usr/bin/env python3
"""
Migration script to add 'size' and 'type' columns to catalog_files table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_database():
    """Add size and type columns to catalog_files table"""
    
    # Get database URL from environment
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    # Convert SQLAlchemy URL to asyncpg format if needed
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("Connected to database successfully!")
        
        # Check if columns already exist
        existing_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'catalog_files' 
            AND column_name IN ('size', 'type')
        """)
        
        existing_column_names = [row['column_name'] for row in existing_columns]
        
        # Add size column if it doesn't exist
        if 'size' not in existing_column_names:
            print("Adding 'size' column...")
            await conn.execute("""
                ALTER TABLE catalog_files 
                ADD COLUMN size INTEGER;
            """)
            print("✓ 'size' column added successfully!")
        else:
            print("✓ 'size' column already exists")
        
        # Add type column if it doesn't exist
        if 'type' not in existing_column_names:
            print("Adding 'type' column...")
            await conn.execute("""
                ALTER TABLE catalog_files 
                ADD COLUMN type VARCHAR;
            """)
            print("✓ 'type' column added successfully!")
        else:
            print("✓ 'type' column already exists")
        
        # Update existing records with default values
        print("Updating existing records with default values...")
        result = await conn.execute("""
            UPDATE catalog_files 
            SET size = 0, type = 'application/octet-stream' 
            WHERE size IS NULL OR type IS NULL
        """)
        print(f"✓ Updated {result.split()[-1]} existing records")
        
        # Make columns NOT NULL
        if 'size' not in existing_column_names:
            print("Making 'size' column NOT NULL...")
            await conn.execute("""
                ALTER TABLE catalog_files 
                ALTER COLUMN size SET NOT NULL;
            """)
            print("✓ 'size' column is now NOT NULL")
        
        if 'type' not in existing_column_names:
            print("Making 'type' column NOT NULL...")
            await conn.execute("""
                ALTER TABLE catalog_files 
                ALTER COLUMN type SET NOT NULL;
            """)
            print("✓ 'type' column is now NOT NULL")
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        if 'conn' in locals():
            await conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    asyncio.run(migrate_database())
