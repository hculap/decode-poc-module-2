import requests
import json
from flask import current_app
import logging
from datetime import datetime
import os
from app.models import db, Project
from app.services.openai_service import OpenAIService

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
        # Check if validation is enabled
        if not current_app.config.get('ENABLE_BRIEF_VALIDATION', False):
            logger.info("Brief validation is disabled")
            return None
            
        # Check if OpenAI API key is configured
        if not current_app.config.get('OPENAI_API_KEY'):
            logger.error("OpenAI API key is not configured")
            return {"error": "OpenAI API key is not configured"}
            
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
        
        try:
            # Load the system prompt
            system_prompt_path = os.path.join('app', 'brief_validation_ai_agent_system_prompt.md')
            if not os.path.exists(system_prompt_path):
                logger.error(f"System prompt file not found at {system_prompt_path}")
                return {"error": "System prompt file not found"}
                
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read()
                
            # Load the reference template
            reference_template_path = os.path.join('app', 'project_brief_reference_template.md')
            if not os.path.exists(reference_template_path):
                logger.error(f"Reference template file not found at {reference_template_path}")
                return {"error": "Reference template file not found"}
                
            with open(reference_template_path, 'r') as f:
                reference_template = f.read()
                
            # Prepare project data for validation
            project_data = {
                "project_id": project.project_id,
                "requirements": project.requirements,
                "questions": project.questions
            }
            
            # Call OpenAI service for validation
            validation_result = OpenAIService.validate_project_brief(
                project_data, 
                system_prompt, 
                reference_template
            )
            
            if validation_result and "error" not in validation_result:
                # Save validation results to database
                project.validation_data = json.dumps(validation_result)
                db.session.commit()
                
            return validation_result
        except Exception as e:
            logger.error(f"Error validating project brief: {str(e)}")
            return {"error": f"Error validating project brief: {str(e)}"}