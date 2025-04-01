from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Project(db.Model):
    """Database model for storing project information and external service data."""
    
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), nullable=False, index=True, unique=True)
    requirements = db.Column(db.Text, nullable=True)
    questions = db.Column(db.Text, nullable=True)
    validation_data = db.Column(db.Text, nullable=True)  # JSON string from OpenAI validation
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with meetings - one to many
    meetings = db.relationship('Meeting', backref='project_relation', lazy=True, 
                              primaryjoin="Project.project_id == foreign(Meeting.project_id)")
    
    def to_dict(self):
        """Convert project object to dictionary for JSON responses."""
        validation = None
        if self.validation_data:
            try:
                validation = json.loads(self.validation_data)
            except json.JSONDecodeError:
                validation = None
                
        return {
            'id': self.id,
            'project_id': self.project_id,
            'requirements': self.requirements,
            'questions': self.questions,
            'validation': validation,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Meeting(db.Model):
    """Database model for storing meeting information and transcripts."""
    
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), nullable=False, index=True)  # References Project.project_id
    meeting_id = db.Column(db.String(50), nullable=True, index=True)  # Fireflies transcript ID
    meeting_url = db.Column(db.Text, nullable=False, index=True)
    transcription = db.Column(db.Text, nullable=True)
    meeting_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert meeting object to dictionary for JSON responses."""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'meeting_id': self.meeting_id,
            'meeting_url': self.meeting_url,
            'transcription': self.transcription,
            'meeting_datetime': self.meeting_datetime.isoformat() if self.meeting_datetime else None
        }