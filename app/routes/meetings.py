from flask import Blueprint, request, jsonify, current_app
from app.models import db, Meeting
from app.services.fireflies import FirefliesService
from app.utils.webhook import WebhookHandler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route("/meetings", methods=["POST"])
def create_meeting():
    """
    Create a new meeting and invite Fireflies bot.
    
    Expected JSON body:
    {
        "project_id": "1234",
        "google_meet_url": "https://meet.google.com/abc-defg-hij",
        "title": "Optional meeting title",
        "duration": 45  # Optional duration in minutes
    }
    """
    try:
        # Parse and validate request JSON
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400
            
        if 'project_id' not in data:
            return jsonify({"error": "Missing required field: project_id"}), 400
            
        if 'google_meet_url' not in data:
            return jsonify({"error": "Missing required field: google_meet_url"}), 400
            
        project_id = data["project_id"]
        meeting_url = data["google_meet_url"]
        title = data.get("title")
        duration = data.get("duration")
        
        # Check if this is a valid Google Meet URL
        if not meeting_url.startswith("https://meet.google.com/"):
            return jsonify({"error": "Invalid Google Meet URL"}), 400
        
        # Add Fireflies bot to the meeting
        success = FirefliesService.add_bot_to_meeting(meeting_url, title=title, duration=duration)
        if not success:
            return jsonify({"error": "Failed to add Fireflies bot to the meeting"}), 400
        
        # Store meeting record in DB
        new_meeting = Meeting(
            project_id=project_id,
            meeting_url=meeting_url,
            meeting_datetime=datetime.utcnow()
        )
        db.session.add(new_meeting)
        db.session.commit()
        
        return jsonify({
            "status": "ok",
            "id": new_meeting.id,
            "project_id": project_id,
            "meeting_url": meeting_url
        }), 201
    except Exception as e:
        logger.exception("Error creating meeting")
        return jsonify({"error": "Internal server error"}), 500


def process_transcription(fireflies_meeting_id):
    """
    Process a transcription from Fireflies.ai.
    
    Args:
        fireflies_meeting_id (str): The Fireflies transcript ID
        
    Returns:
        tuple: (meeting_record, error_message, status_code)
            - meeting_record: Updated Meeting object or None if error
            - error_message: Error message or None if successful
            - status_code: HTTP status code (404, 500, etc.) or None if successful
    """
    try:
        # Fetch the transcript from Fireflies
        transcript_data = FirefliesService.get_transcript_by_id(fireflies_meeting_id)
        if not transcript_data:
            return None, "Failed to retrieve transcript", 404
            
        # Extract meeting link and sentences
        meeting_link = transcript_data.get("meeting_link")
        sentences = transcript_data.get("sentences", [])
        
        if not meeting_link:
            return None, "Meeting link not found in transcript data", 404
            
        # Format transcription with speaker names
        transcript_lines = []
        for sentence in sentences:
            speaker = sentence.get("speaker", "Unknown")
            text = sentence.get("text", "")
            if text:
                transcript_lines.append(f"{speaker}: {text}")
        
        full_text = "\n".join(transcript_lines)
        
        # Find the corresponding meeting in our database
        meeting_record = Meeting.query.filter(Meeting.meeting_url == meeting_link).first()
        if not meeting_record:
            return None, f"No matching meeting found for URL: {meeting_link}", 404
                
        # Update the meeting record with transcript info
        meeting_record.meeting_id = fireflies_meeting_id
        meeting_record.transcription = full_text
        db.session.commit()
        
        logger.info(f"Successfully processed transcript for meeting: {meeting_record.id}")
        return meeting_record, None, None
    except Exception as e:
        logger.exception(f"Error processing transcription for meeting ID {fireflies_meeting_id}")
        return None, f"Error processing transcription: {str(e)}", 500


@meetings_bp.route("/webhook", methods=["POST"])
def fireflies_webhook():
    """Receive webhook notifications from Fireflies.ai."""
    try:
        # Verify webhook signature
        signature = request.headers.get("X-Hub-Signature", "")
        if not WebhookHandler.verify_signature(request.data, signature):
            return jsonify({"error": "Invalid signature"}), 403
            
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
            
        event_type = data.get("eventType")
        logger.info(f"Received webhook event: {event_type}")
        
        # Only process transcription completed events
        if event_type == "Transcription completed":
            fireflies_meeting_id = data.get("meetingId")
            if not fireflies_meeting_id:
                return jsonify({"error": "Missing meetingId"}), 400
                
            # Process the transcription
            meeting_record, error_message, status_code = process_transcription(fireflies_meeting_id)
            
            if error_message:
                return jsonify({"error": error_message}), status_code
                
            return "OK", 200
        
        # Acknowledge other event types without processing them
        return "OK", 200
    except Exception as e:
        logger.exception("Error processing webhook")
        return jsonify({"error": "Internal server error"}), 500


@meetings_bp.route("/meetings/<meeting_id>", methods=["GET"])
def get_meeting(meeting_id):
    """
    Get meeting transcript by ID.
    
    This endpoint will try to find the meeting by:
    1. Fireflies meeting_id
    2. Internal database ID (if meeting_id is numeric)
    3. If found but has no transcription, will check Fireflies API
    """
    try:
        # Try to find by Fireflies meeting ID first
        meeting_record = Meeting.query.filter(Meeting.meeting_id == meeting_id).first()
        
        # If not found, try looking up by internal database ID (if meeting_id is numeric)
        if not meeting_record and meeting_id.isdigit():
            meeting_record = Meeting.query.get(int(meeting_id))
            
        if not meeting_record:
            return jsonify({"error": "Meeting not found"}), 404
        
        # If we have a meeting record but no transcription and it has a Fireflies meeting ID,
        # try to fetch the transcription from Fireflies
        if (not meeting_record.transcription and meeting_record.meeting_id):
            logger.info(f"Meeting {meeting_id} found but has no transcription. Fetching from Fireflies...")
            updated_meeting, error_message, status_code = process_transcription(meeting_record.meeting_id)
            
            if updated_meeting:
                meeting_record = updated_meeting
            else:
                logger.warning(f"Failed to fetch transcription from Fireflies: {error_message}")
                # Continue with the existing record even if fetching failed
        
        # If we have a meeting record with no transcription and no Fireflies meeting ID,
        # but it matches the provided meeting_id, try to fetch the transcription
        elif (not meeting_record.transcription and not meeting_record.meeting_id 
              and meeting_id != str(meeting_record.id)):
            logger.info(f"Trying to use provided ID as Fireflies meeting ID: {meeting_id}")
            updated_meeting, error_message, status_code = process_transcription(meeting_id)
            
            if updated_meeting:
                meeting_record = updated_meeting
            else:
                logger.warning(f"Failed to fetch transcription using provided ID: {error_message}")
                # Continue with the existing record even if fetching failed
            
        # Return meeting data
        return jsonify(meeting_record.to_dict()), 200
    except Exception as e:
        logger.exception("Error retrieving meeting")
        return jsonify({"error": "Internal server error"}), 500