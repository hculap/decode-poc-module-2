import requests
import json
from flask import current_app
import logging
from datetime import datetime
from app.models import db, Project

logger = logging.getLogger(__name__)

class ProjectBriefService:
    """Service for interacting with the external microservice."""
    
    @staticmethod
    def get_project_data(project_id):
        """
        Fetches project data from the external service or database cache.
        
        Args:
            project_id (str): ID of the project to fetch
            
        Returns:
            dict: Project data or None if error
        """
        # First, check if we already have this project in our database
        project = Project.query.filter_by(project_id=project_id).first()
        
        # If we have recent data (less than 1 hour old), return it without calling external service
        if project and project.last_updated and (datetime.utcnow() - project.last_updated).total_seconds() < 3600:
            logger.info(f"Using cached project data for {project_id}")
            return project.to_dict()
        
        # Otherwise, fetch from external service
        external_service_url = current_app.config.get('PROJECT_BRIEF_SERVICE_URL')
        if not external_service_url:
            logger.error("External service URL not configured")
            return None
            
        url = f"{external_service_url}/projects/{project_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Save or update project in database
            if not project:
                project = Project(project_id=project_id)
                db.session.add(project)
            
            project.requirements = data.get('requirements')
            project.questions = data.get('questions')
            project.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Convert to our standard format
            result = project.to_dict()
            
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching project data: {str(e)}")
            # If we have a project in the database but failed to update, use the cached data
            if project:
                logger.info(f"Using existing cached data for project {project_id} due to external service error")
                return project.to_dict()
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting project data: {str(e)}")
            # Same fallback as above
            if project:
                return project.to_dict()
            return None
            
    @staticmethod
    def validate_project_brief(project_id):
        """
        Validates a project brief using OpenAI API.
        
        Args:
            project_id (str): ID of the project to validate
            
        Returns:
            dict: Validation results or None if error
        """
        # Get the project data
        project = Project.query.filter_by(project_id=project_id).first()
        
        if not project or not project.requirements:
            logger.error(f"Project {project_id} not found or has no requirements")
            return None
        
        # Check if validation was already done and is not too old (72 hours)
        if project.validation_data and project.last_updated and (datetime.utcnow() - project.last_updated).total_seconds() < 259200:
            try:
                return json.loads(project.validation_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid validation data for project {project_id}, will re-validate")
        
        # Load the prompt template for OpenAI
        try:
            with open('brief_validation_ai_agent_system_prompt.md', 'r') as f:
                prompt_template = f.read()
                
            # This would be replaced with an actual OpenAI API call 
            # For now, we'll just create a sample validation result
            validation_result = {
                "ValidationReport": {
                    "ExecutiveSummary": {
                        "status": "Partially Addressed",
                        "notes": [
                            "The executive summary provides an overview but lacks details on expected ROI."
                        ]
                    },
                    "ProjectBackground": {
                        "status": "Fully Addressed",
                        "notes": [
                            "All key details are covered."
                        ]
                    },
                    # Other validation sections would be filled here
                }
            }
            
            # Save validation results to database
            project.validation_data = json.dumps(validation_result)
            db.session.commit()
            
            return validation_result
        except Exception as e:
            logger.error(f"Error validating project brief: {str(e)}")
            return None