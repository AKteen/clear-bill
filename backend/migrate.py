from sqlalchemy import text
from database import engine

def migrate_database():
    """Add missing columns to tables if they don't exist"""
    
    with engine.connect() as conn:
        # Check if severity column exists in audit_policies
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'audit_policies' 
            AND column_name = 'severity'
        """))
        
        if not result.fetchone():
            # Add severity column
            conn.execute(text("""
                ALTER TABLE audit_policies 
                ADD COLUMN severity VARCHAR(20) DEFAULT 'medium'
            """))
            conn.commit()
            print("Added severity column to audit_policies table")
        
        # Check if audit_result column exists in documents
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            AND column_name = 'audit_result'
        """))
        
        if not result.fetchone():
            # Add audit_result column
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN audit_result JSON
            """))
            conn.commit()
            print("Added audit_result column to documents table")
        
        print("Database migration completed")

if __name__ == "__main__":
    migrate_database()