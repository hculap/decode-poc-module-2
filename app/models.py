from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Meeting(db.Model):
    """Database model for storing meeting information and transcripts."""
    
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), nullable=False, index=True)
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
