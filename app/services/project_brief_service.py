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
    def validate_project_brief(project_id, force_validation=False):
        """
        Validates a project brief using OpenAI API.
        
        Args:
            project_id (str): ID of the project to validate
            force_validation (bool): Whether to force validation even if cached validation exists
            
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
            return {"error": "OpenAI API key is not configured", "error_type": "configuration"}
            
        # Get the project data
        project = Project.query.filter_by(project_id=project_id).first()
        
        if not project or not project.requirements:
            logger.error(f"Project {project_id} not found or has no requirements")
            return None
        
        # Check if validation was already done and is not too old (72 hours)
        # Skip this check if force_validation is True
        if not force_validation and project.validation_data and project.last_updated and (datetime.utcnow() - project.last_updated).total_seconds() < 259200:
            try:
                validation_data = json.loads(project.validation_data)
                # Check if the validation data contains an error related to quota
                if isinstance(validation_data, dict) and validation_data.get("error_type") == "quota_exceeded":
                    # If quota was exceeded, return the cached validation with a note
                    logger.info(f"Using cached validation data for project {project_id} despite quota error")
                    validation_data["cached_result"] = True
                return validation_data
            except json