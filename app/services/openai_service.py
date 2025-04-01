import requests
from flask import current_app
import logging
import json
import os

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    @staticmethod
    def validate_project_brief(project_data, system_prompt, reference_template):
        """
        Validates a project brief against a reference template using OpenAI.
        
        Args:
            project_data (dict): Project data to validate
            system_prompt (str): System prompt for OpenAI
            reference_template (str): Reference template to compare against
            
        Returns:
            dict: Validation results from OpenAI
        """
        try:
            # Get API key from config
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                logger.error("OpenAI API key not configured")
                return None

            # Instead of using the library, make a direct API request
            # This avoids potential version compatibility issues
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # Prepare user message with project brief and reference template
            user_message = f"""
            Here is the project brief to validate:
            
            {json.dumps(project_data, indent=2)}
            
            Here is the reference template:
            
            {reference_template}
            """
            
            # Prepare API request payload
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1
            }
            
            # Make API request
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {"error": f"OpenAI API error: {response.status_code}"}
            
            # Parse response
            response_data = response.json()
            validation_json = response_data['choices'][0]['message']['content']
            
            # Try to extract JSON from the response
            try:
                # Look for JSON content between triple backticks if present
                if "```json" in validation_json and "```" in validation_json:
                    json_start = validation_json.find("```json") + 7
                    json_end = validation_json.rfind("```")
                    validation_json = validation_json[json_start:json_end].strip()
                
                # Parse the JSON content
                validation_results = json.loads(validation_json)
                return validation_results
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse validation results: {e}")
                return {"error": "Failed to parse validation results", "raw_response": validation_json}
                
        except Exception as e:
            logger.error(f"Error validating project brief: {str(e)}")
            return {"error": f"Error validating project brief: {str(e)}"}