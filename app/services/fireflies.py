import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class FirefliesService:
    """Service for interacting with the Fireflies.ai GraphQL API."""
    
    @staticmethod
    def add_bot_to_meeting(meeting_link, title=None, duration=None):
        """
        Invites the Fireflies AI bot (Fred) to a Google Meet session.
        
        Args:
            meeting_link (str): URL of the Google Meet session
            title (str, optional): Title for the meeting
            duration (int, optional): Duration in minutes
            
        Returns:
            bool: True if successful, False otherwise
        """
        api_key = current_app.config['FIREFLIES_API_KEY']
        if not api_key:
            logger.error("Fireflies API key not configured")
            return False
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        query = """
            mutation AddToLiveMeeting($meetingLink: String!, $title: String, $duration: Int) {
              addToLiveMeeting(meeting_link: $meetingLink, title: $title, duration: $duration) {
                success
              }
            }
        """
        
        variables = {
            "meetingLink": meeting_link,
            "title": title,
            "duration": duration
        }
        
        try:
            resp = requests.post(
                current_app.config['FIREFLIES_API_URL'], 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Check for GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                logger.error(f"GraphQL error: {error_msg}")
                return False
                
            return data.get("data", {}).get("addToLiveMeeting", {}).get("success", False)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error adding bot to meeting: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error adding bot to meeting: {str(e)}")
            return False
    
    @staticmethod
    def get_transcript_by_id(meeting_id):
        """
        Retrieves transcript from Fireflies.ai by meeting ID.
        
        Args:
            meeting_id (str): Fireflies transcript ID
            
        Returns:
            dict: Transcript data or None if error
        """
        api_key = current_app.config['FIREFLIES_API_KEY']
        if not api_key:
            logger.error("Fireflies API key not configured")
            return None
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        query = """
            query GetTranscript($id: String!) {
              transcript(id: $id) {
                title
                meeting_link
                sentences { 
                  text
                  speaker_name
                }
                summary {
                  overview
                  short_summary
                }
              }
            }
        """
        
        variables = {"id": meeting_id}
        
        try:
            resp = requests.post(
                current_app.config['FIREFLIES_API_URL'], 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            print({"query": query, "variables": variables})
            resp.raise_for_status()
            data = resp.json()
            
            # Check for GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                logger.error(f"GraphQL error: {error_msg}")
                return None
                
            return data.get("data", {}).get("transcript")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting transcript: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None
