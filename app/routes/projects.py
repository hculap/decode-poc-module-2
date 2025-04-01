"""
Project routes for the Fireflies Transcription Service.
This module contains routes for accessing project data from the external service.
"""

from flask import Blueprint, jsonify
from app.services.project_brief_service import ProjectBriefService
import logging

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
            
        # Return the project data (should contain id, feedback, requirements fields)
        return jsonify(project_data), 200
            
    except Exception as e:
        logger.exception(f"Error retrieving project data for project ID {project_id}")
        return jsonify({"error": "Internal server error"}), 500