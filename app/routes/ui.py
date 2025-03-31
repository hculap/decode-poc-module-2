"""
UI routes for the Fireflies Transcription Service.
This module contains routes for serving the web UI.
"""

from flask import Blueprint, render_template

ui_bp = Blueprint('ui', __name__)

@ui_bp.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')