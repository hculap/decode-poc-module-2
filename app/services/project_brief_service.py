import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ProjectBriefService:
    """Service for interacting with the external microservice."""
    
    @staticmethod
    def get_project_data(project_id):
        """
        Fetches project data from the external service.
        
        Args:
            project_id (str): ID of the project to fetch
            
        Returns:
            dict: Project data or None if error
        """
        external_service_url = current_app.config.get('PROJECT_BRIEF_SERVICE_URL')
        if not external_service_url:
            logger.error("External service URL not configured")
            return None
            
        url = f"{external_service_url}/projects/{project_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching project data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting project data: {str(e)}")
            return None