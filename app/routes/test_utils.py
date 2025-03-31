"""
Test utility routes for the Fireflies Transcription Service.
This module contains routes that should ONLY be enabled in the testing environment.
"""

from flask import Blueprint, request, jsonify
from app.models import db, Meeting

test_utils_bp = Blueprint('test_utils', __name__, url_prefix='/test-utils')

@test_utils_bp.route('/reset-db', methods=['POST'])
def reset_database():
    """
    WARNING: This endpoint drops and recreates all database tables.
    It should only be enabled in a testing environment.
    """
    try:
        db.drop_all()
        db.create_all()
        return jsonify({"status": "Database reset successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_utils_bp.route('/meetings/<int:meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    """
    Updates a meeting record for testing purposes.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        meeting = Meeting.query.get(meeting_id)
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
            
        # Update fields if provided
        if 'meeting_id' in data:
            meeting.meeting_id = data['meeting_id']
            
        if 'transcription' in data:
            meeting.transcription = data['transcription']
            
        if 'meeting_url' in data:
            meeting.meeting_url = data['meeting_url']
            
        db.session.commit()
        return jsonify({"status": "Meeting updated", "meeting": meeting.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@test_utils_bp.route('/inject-transcript', methods=['POST'])
def inject_transcript():
    """
    Injects a test transcript for a meeting identified by URL.
    """
    try:
        data = request.json
        if not data or 'meeting_url' not in data or 'meeting_id' not in data or 'transcription' not in data:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Find meeting by URL
        meeting = Meeting.query.filter(Meeting.meeting_url == data['meeting_url']).first()
        if not meeting:
            return jsonify({"error": "Meeting not found with provided URL"}), 404
            
        # Update the meeting with test data
        meeting.meeting_id = data['meeting_id']
        meeting.transcription = data['transcription']
        db.session.commit()
        
        return jsonify({
            "status": "Transcript injected successfully",
            "meeting": meeting.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
