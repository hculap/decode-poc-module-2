"""
Project routes for the Fireflies Transcription Service.
This module contains routes for accessing project data from the external service.
"""

from flask import Blueprint, jsonify, current_app
from app.services.project_brief_service import ProjectBriefService
from app.models import Project, db
import logging
import json

logger = logging.getLogger(__name__)
projects_bp = Blueprint('projects', __name__)

@projects_bp.route("/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """
    GET: Retrieve project data from database cache or external service
    
    Path parameters:
    - project_id: Project ID to retrieve
    
    Returns:
    - JSON with project data including id, feedback, and requirements
    """
    try:
        # Fetch data (will use cache if available)
        project_data = ProjectBriefService.get_project_data(project_id)
        
        if not project_data:
            return jsonify({"error": "Failed to retrieve project data"}), 404
        
        # If this project doesn't have validation data yet, generate it if enabled
        if current_app.config.get('ENABLE_BRIEF_VALIDATION', False) and current_app.config.get('OPENAI_API_KEY'):
            if 'validation' not in project_data or not project_data.get('validation'):
                # Only validate if we have requirements
                if 'requirements' in project_data and project_data.get('requirements'):
                    logger.info(f"Generating validation for project {project_id}")
                    validation_data = ProjectBriefService.validate_project_brief(project_id)
                    if validation_data and not isinstance(validation_data, dict) or "error" not in validation_data:
                        project_data['validation'] = validation_data
            
        # Return the project data (should contain id, requirements, questions, validation fields)
        return jsonify(project_data), 200
            
    except Exception as e:
        logger.exception(f"Error retrieving project data for project ID {project_id}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@projects_bp.route("/projects/<project_id>/validate", methods=["POST"])
def validate_project(project_id):
    """
    POST: Force validation of a project brief using OpenAI
    
    Path parameters:
    - project_id: Project ID to validate
    
    Returns:
    - JSON with validation results
    """
    try:
        # Check if validation is enabled
        if not current_app.config.get('ENABLE_BRIEF_VALIDATION', False):
            return jsonify({"error": "Brief validation is disabled in configuration"}), 400
            
        # Check if OpenAI API key is configured
        if not current_app.config.get('OPENAI_API_KEY'):
            return jsonify({"error": "OpenAI API key is not configured"}), 400
            
        # First make sure the project exists
        project = Project.query.filter_by(project_id=project_id).first()
        
        if not project:
            # Try to get it from the external service first
            project_data = ProjectBriefService.get_project_data(project_id)
            
            if not project_data:
                return jsonify({"error": "Project not found"}), 404
                
            # Now we should have the project in the database
            project = Project.query.filter_by(project_id=project_id).first()
        
        # Check if the project has requirements
        if not project.requirements:
            return jsonify({"error": "Project has no requirements to validate"}), 400
        
        # Validate the brief regardless of cached validation
        validation_result = ProjectBriefService.validate_project_brief(project_id)
        
        if not validation_result:
            return jsonify({"error": "Failed to validate project brief"}), 500
            
        if isinstance(validation_result, dict) and "error" in validation_result:
            return jsonify(validation_result), 500
            
        # Return the validation results
        return jsonify({"validation": validation_result}), 200
            
    except Exception as e:
        logger.exception(f"Error validating project brief for project ID {project_id}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500