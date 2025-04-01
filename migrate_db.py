#!/usr/bin/env python3
"""
Database Migration Script for adding Projects table

Run this script to migrate your database without losing existing data:
python migrate_db.py
"""

import sys
import os
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("db_migration")

# Add the current directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app
    from app.models import db, Project, Meeting
    from sqlalchemy import text
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    with db.engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
        ))
        return result.scalar()

def migrate_database():
    """Run the database migration"""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting database migration...")
        
        # Check if projects table already exists
        projects_exists = check_table_exists('projects')
        
        if projects_exists:
            logger.info("Projects table already exists, skipping creation")
        else:
            logger.info("Creating projects table...")
            
            # Create the projects table
            db.create_all(tables=[Project.__table__])
            logger.info("Projects table created successfully")
        
        # Get all unique project_ids from meetings
        logger.info("Collecting unique project IDs from meetings...")
        project_ids = db.session.query(Meeting.project_id).distinct().all()
        project_ids = [pid[0] for pid in project_ids]
        
        logger.info(f"Found {len(project_ids)} unique project IDs")
        
        # Create project records for each unique project_id
        projects_created = 0
        for pid in project_ids:
            # Check if project already exists
            existing = Project.query.filter_by(project_id=pid).first()
            if not existing:
                new_project = Project(
                    project_id=pid,
                    created_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                db.session.add(new_project)
                projects_created += 1
        
        if projects_created > 0:
            db.session.commit()
            logger.info(f"Created {projects_created} new project records")
        else:
            logger.info("No new projects needed to be created")
        
        logger.info("Migration completed successfully")
        
if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)