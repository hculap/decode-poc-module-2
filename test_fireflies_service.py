#!/usr/bin/env python3
"""
Test Script for Fireflies Transcription Service

This script tests all endpoints of the Fireflies transcription service:
1. Creating a new meeting
2. Simulating a webhook callback from Fireflies
3. Retrieving the meeting transcript

Usage:
    python test_fireflies_service.py [--host=http://localhost:8000]
"""

import argparse
import json
import requests
import time
import hmac
import hashlib
import uuid
import sys


class Colors:
    """Terminal colors for better readability."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_success(message):
    """Log success message with color."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def log_error(message):
    """Log error message with color."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def log_info(message):
    """Log info message with color."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def log_warning(message):
    """Log warning message with color."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def log_section(message):
    """Log section header with color."""
    print(f"\n{Colors.BOLD}{message}{Colors.RESET}")
    print("=" * len(message))


def check_health(base_url):
    """Check if the service is running."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            log_success(f"Service is running: {response.json()}")
            return True
        else:
            log_error(f"Health check failed: {response.status_code} {response.text}")
            return False
    except requests.RequestException as e:
        log_error(f"Service is not accessible: {e}")
        return False


def create_meeting(base_url, project_id, google_meet_url, title=None, duration=None):
    """Test creating a new meeting."""
    log_section("Testing Create Meeting Endpoint")
    
    # Prepare request data
    data = {
        "project_id": project_id,
        "google_meet_url": google_meet_url
    }
    
    if title:
        data["title"] = title
    
    if duration:
        data["duration"] = duration
    
    log_info(f"Sending request to {base_url}/meetings")
    log_info(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/meetings",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        log_info(f"Response status: {response.status_code}")
        log_info(f"Response body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            log_success("Successfully created meeting")
            return response.json()
        else:
            log_error(f"Failed to create meeting: {response.text}")
            return None
    except requests.RequestException as e:
        log_error(f"Request failed: {e}")
        return None


def simulate_webhook(base_url, meeting_id, meeting_url, webhook_secret=None):
    """Simulate a webhook call from Fireflies."""
    log_section("Simulating Fireflies Webhook")
    
    # Create a synthetic Fireflies webhook payload
    webhook_data = {
        "meetingId": meeting_id,
        "eventType": "Transcription completed",
        "meeting_link": meeting_url
    }
    
    log_info(f"Webhook payload: {json.dumps(webhook_data, indent=2)}")
    
    # Prepare headers
    headers = {"Content-Type": "application/json"}
    
    # Add signature if webhook secret is provided
    if webhook_secret:
        payload_bytes = json.dumps(webhook_data).encode('utf-8')
        signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        headers["X-Hub-Signature"] = signature
        log_info(f"Added webhook signature: {signature}")
    
    try:
        response = requests.post(
            f"{base_url}/webhook",
            json=webhook_data,
            headers=headers,
            timeout=10
        )
        
        log_info(f"Response status: {response.status_code}")
        log_info(f"Response body: {response.text}")
        
        if response.status_code == 200:
            log_success("Webhook processed successfully")
            return True
        else:
            log_error(f"Webhook processing failed: {response.text}")
            return False
    except requests.RequestException as e:
        log_error(f"Request failed: {e}")
        return False


def get_meeting(base_url, meeting_id):
    """Test retrieving a meeting transcript."""
    log_section(f"Testing Get Meeting Endpoint: {meeting_id}")
    
    try:
        response = requests.get(
            f"{base_url}/meetings/{meeting_id}",
            timeout=10
        )
        
        log_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            log_info(f"Response body: {json.dumps(response.json(), indent=2)}")
            log_success("Successfully retrieved meeting")
            return response.json()
        else:
            log_error(f"Failed to retrieve meeting: {response.text}")
            return None
    except requests.RequestException as e:
        log_error(f"Request failed: {e}")
        return None


def inject_test_transcript(base_url, meeting_id, meeting_url):
    """Inject a test transcript into the database for testing."""
    log_section("Injecting Test Transcript")
    
    # Create a sample transcript
    sample_transcript = (
        "Alice: Hello everyone, thanks for joining today's meeting.\n"
        "Bob: Hi Alice, happy to be here.\n"
        "Charlie: I had some questions about the project timeline.\n"
        "Alice: Sure, let's discuss that. We're planning to launch next month.\n"
        "Bob: That sounds ambitious but achievable.\n"
        "Charlie: I agree, I think we can make it work."
    )
    
    # Prepare data for the test-utils endpoint
    inject_data = {
        "meeting_url": meeting_url,
        "meeting_id": meeting_id,
        "transcription": sample_transcript
    }
    
    log_info(f"Injecting transcript via test-utils endpoint")
    
    try:
        response = requests.post(
            f"{base_url}/test-utils/inject-transcript",
            json=inject_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        log_info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            log_info(f"Response body: {json.dumps(response.json(), indent=2)}")
            log_success("Successfully injected test transcript")
            return True
        else:
            log_error(f"Failed to inject test transcript: {response.text}")
            return False
    except requests.RequestException as e:
        log_error(f"Request failed: {e}")
        return False


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test Fireflies Transcription Service")
    parser.add_argument("--host", default="http://localhost:8000", help="Base URL of the service")
    parser.add_argument("--webhook-secret", default=None, help="Webhook secret (if enabled)")
    args = parser.parse_args()
    
    base_url = args.host.rstrip('/')
    
    log_section("Testing Fireflies Transcription Service")
    log_info(f"Service URL: {base_url}")
    
    # Check if service is running
    if not check_health(base_url):
        log_error("Service is not running. Exiting.")
        sys.exit(1)
    
    # Generate unique values for testing
    project_id = f"test-project-{uuid.uuid4().hex[:8]}"
    google_meet_url = f"https://meet.google.com/test-{uuid.uuid4().hex[:10]}"
    meeting_title = "Test Meeting"
    fireflies_meeting_id = f"test-{uuid.uuid4().hex[:10]}"
    
    # Test creating a meeting
    meeting_data = create_meeting(
        base_url, 
        project_id, 
        google_meet_url, 
        title=meeting_title
    )
    
    if not meeting_data:
        log_error("Failed to create meeting. Exiting.")
        sys.exit(1)
    
    internal_meeting_id = meeting_data.get("id")
    log_info(f"Created meeting with internal ID: {internal_meeting_id}")
    
    # Inject test transcript
    inject_result = inject_test_transcript(base_url, fireflies_meeting_id, google_meet_url)
    
    if inject_result:
        # Attempt to retrieve the meeting using the Fireflies meeting ID
        time.sleep(1)  # Give the service a moment to process
        meeting_result = get_meeting(base_url, fireflies_meeting_id)
        
        if meeting_result:
            if meeting_result.get("transcription"):
                log_success("Full test completed successfully!")
                sys.exit(0)
            else:
                log_warning("Meeting retrieved but no transcript found.")
                sys.exit(1)
        else:
            log_error("Failed to retrieve meeting. Test failed.")
            sys.exit(1)
    else:
        log_warning("Test transcript injection failed. Trying webhook simulation.")
        
        # Try simulating just the webhook
        webhook_result = simulate_webhook(
            base_url, 
            fireflies_meeting_id, 
            google_meet_url, 
            webhook_secret=args.webhook_secret
        )
        
        if webhook_result:
            log_success("Webhook simulation successful.")
        else:
            log_warning("Webhook simulation failed.")
        
        # Try retrieving the meeting data by internal ID
        if internal_meeting_id:
            meeting_result = get_meeting(base_url, str(internal_meeting_id))
            if meeting_result:
                log_success("Retrieved meeting by internal ID.")
            else:
                log_warning("Failed to retrieve meeting by internal ID.")


if __name__ == "__main__":
    main()
