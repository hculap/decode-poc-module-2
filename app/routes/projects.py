"""
Project routes for the Fireflies Transcription Service.
This module contains routes for accessing project data from the external service.
"""

from flask import Blueprint, jsonify, current_app
from app.services.project_brief_service import ProjectBriefService
from app.services.openai_service import OpenAIService
import logging
import os

logger = logging.getLogger(__name__)
projects_bp = Blueprint('projects', __name__)

@projects_bp.route("/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """
    GET: Retrieve project data from external service
    
    Path parameters:
    - project_id: Project ID to retrieve
    
    Returns:
    - JSON with project data including id, feedback, and requirements
    """
    try:
        # Fetch data from external service
        project_data = ProjectBriefService.get_project_data(project_id)
        
        if not project_data:
            return jsonify({"error": "Failed to retrieve project data"}), 404
            
        # If validation is enabled, perform validation
        if current_app.config.get('ENABLE_BRIEF_VALIDATION', False):
            try:
                # Load system prompt from file
                system_prompt_path = os.path.join(current_app.root_path, 'brief_validation_ai_agent_system_prompt.md')
                with open(system_prompt_path, 'r') as f:
                    system_prompt = f.read()
                
                # Load reference template from file
                template_path = os.path.join(current_app.root_path, 'project_brief_reference_template.md')
                with open(template_path, 'r') as f:
                    reference_template = f.read()
                
                # Validate project data
                validation_results = OpenAIService.validate_project_brief(
                    project_data, 
                    system_prompt,
                    reference_template
                )
                
                # Add validation results to the response
                if validation_results:
                    project_data['validation'] = validation_results
            except Exception as e:
                logger.exception(f"Error during brief validation: {str(e)}")
                # Continue without validation if it fails
        
        # Return the project data (should contain id, feedback, requirements fields)
        return jsonify(project_data), 200
            
    except Exception as e:
        logger.exception(f"Error retrieving project data for project ID {project_id}")
        return jsonify({"error": "Internal server error"}), 500