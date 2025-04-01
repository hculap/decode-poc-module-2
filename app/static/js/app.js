// Configuration
const API_BASE_URL = ''; // Leave empty for relative URLs, or set to your API server URL if different

// State management
let currentMeetingId = null;
let pollingInterval = null;
let meetingData = {};
let projectId = null;
let projectData = null;
let allMeetings = [];
let currentFilter = 'all';

// DOM Elements
const loaderScreen = document.getElementById('loaderScreen');
const inputScreen = document.getElementById('inputScreen');
const waitingScreen = document.getElementById('waitingScreen');
const transcriptScreen = document.getElementById('transcriptScreen');
const meetingListScreen = document.getElementById('meetingListScreen');
const errorMessageEl = document.getElementById('errorMessage');
const meetingForm = document.getElementById('meetingForm');

const displayMeetingUrl = document.getElementById('displayMeetingUrl');
const displayProjectId = document.getElementById('displayProjectId');

const transcriptMeetingUrl = document.getElementById('transcriptMeetingUrl');
const transcriptProjectId = document.getElementById('transcriptProjectId');
const transcriptMeetingDate = document.getElementById('transcriptMeetingDate');
const transcriptContent = document.getElementById('transcriptContent');

const listProjectId = document.getElementById('listProjectId');
const meetingsList = document.getElementById('meetingsList');
const statusSummary = document.getElementById('statusSummary');
const filterControls = document.getElementById('filterControls');

// Project detail containers
const projectDetailsList = document.getElementById('projectDetailsList');
const projectDetailsInput = document.getElementById('projectDetailsInput');
const projectDetailsWaiting = document.getElementById('projectDetailsWaiting');
const projectDetailsTranscript = document.getElementById('projectDetailsTranscript');

const checkStatusButton = document.getElementById('checkStatusButton');
const startNewButton = document.getElementById('startNewButton');
const newTranscriptionButton = document.getElementById('newTranscriptionButton');
const startNewFromListButton = document.getElementById('startNewFromListButton');
const backToListButton = document.getElementById('backToListButton');
const backToListFromTranscriptButton = document.getElementById('backToListFromTranscriptButton');

const notification = document.getElementById('notification');

// Helper functions
function showScreen(screenId) {
    // Hide all screens
    loaderScreen.classList.remove('active');
    inputScreen.classList.remove('active');
    waitingScreen.classList.remove('active');
    transcriptScreen.classList.remove('active');
    meetingListScreen.classList.remove('active');

    // Show the requested screen
    document.getElementById(screenId).classList.add('active');
}

function showError(message) {
    errorMessageEl.textContent = message;
    errorMessageEl.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorMessageEl.style.display = 'none';
    }, 5000);
}

function clearError() {
    errorMessageEl.style.display = 'none';
}

function showNotification(message) {
    notification.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
        hour12: true
    }).format(date);
}

function startPolling(projectId, meetingId) {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Set up polling every 10 seconds
    pollingInterval = setInterval(() => {
        checkMeetingStatus(projectId, meetingId);
    }, 10000);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// Get parameters from URL
function getProjectIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('project_id') || null;
}

function getMeetingIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('meeting_id') || null;
}

// Calculate status summary
function updateStatusSummary(meetings) {
    // Count meetings by status
    let totalCount = meetings.length;
    let completedCount = 0;
    let pendingCount = 0;
    
    meetings.forEach(meeting => {
        if (meeting.transcription) {
            completedCount++;
        } else {
            pendingCount++;
        }
    });
    
    // Update summary display
    statusSummary.innerHTML = `
        <div class="status-summary-item">
            <div class="status-count">${totalCount}</div>
            <div>Total Meetings</div>
        </div>
        <div class="status-summary-item">
            <div class="status-count">${completedCount}</div>
            <div><span class="status-indicator status-complete"></span>Completed</div>
        </div>
        <div class="status-summary-item">
            <div class="status-count">${pendingCount}</div>
            <div><span class="status-indicator status-pending"></span>Pending</div>
        </div>
    `;
}

// Filter meetings
function filterMeetings(filter) {
    currentFilter = filter;
    
    // Update filter button states
    const filterButtons = filterControls.querySelectorAll('.filter-button');
    filterButtons.forEach(button => {
        if (button.dataset.filter === filter) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Apply filter to meetings list
    const filteredMeetings = allMeetings.filter(meeting => {
        if (filter === 'all') return true;
        if (filter === 'completed') return !!meeting.transcription;
        if (filter === 'pending') return !meeting.transcription;
        return true;
    });
    
    // Update the display with filtered meetings
    renderMeetingsList(filteredMeetings);
}

// Render the meetings list
function renderMeetingsList(meetings) {
    // Clear the meetings list
    meetingsList.innerHTML = '';
    
    if (meetings.length === 0) {
        meetingsList.innerHTML = '<p>No meetings found matching the selected filter.</p>';
        return;
    }
    
    // Add each meeting to the list
    meetings.forEach(meeting => {
        const meetingCard = document.createElement('div');
        meetingCard.className = 'meeting-card';
        meetingCard.dataset.meetingId = meeting.id;
        
        // Create meeting title (use URL if no title available)
        const title = document.createElement('h3');
        let meetingTitle = "Meeting";
        if (meeting.meeting_url) {
            // Extract the meeting code from URL as a simple title
            const urlParts = meeting.meeting_url.split('/');
            meetingTitle = `Meeting ${urlParts[urlParts.length - 1]}`;
        }
        
        title.textContent = meetingTitle;
        
        // Add prominent status badge
        const hasTranscript = !!meeting.transcription;
        const statusBadge = document.createElement('div');
        statusBadge.className = `status-badge ${hasTranscript ? 'status-completed' : 'status-pending'}`;
        statusBadge.textContent = hasTranscript ? 'Completed' : 'Pending';
        meetingCard.appendChild(statusBadge);
        
        // Add meeting details
        const details = document.createElement('div');
        details.innerHTML = `
            <p><strong>Date:</strong> ${formatDate(meeting.meeting_datetime)}</p>
            <p><strong>URL:</strong> ${meeting.meeting_url}</p>
            <p><strong>Status:</strong> 
                <span class="status-indicator ${hasTranscript ? 'status-complete' : 'status-pending'}"></span>
                ${hasTranscript ? 'Completed' : 'Pending'}
            </p>
        `;
        
        // Build the card
        meetingCard.appendChild(title);
        meetingCard.appendChild(details);
        
        // Add click handler to view the meeting
        meetingCard.addEventListener('click', () => {
            // Stop any existing polling
            stopPolling();
            
            // Set the current meeting
            currentMeetingId = meeting.id;
            meetingData = meeting;
            
            // Show the appropriate screen based on meeting status
            if (hasTranscript) {
                displayTranscript(meeting);
            } else {
                // Meeting is in progress
                displayMeetingUrl.textContent = meeting.meeting_url;
                displayProjectId.textContent = meeting.project_id;
                showScreen('waitingScreen');
                
                // Display project details
                renderProjectDetails('waiting');
                
                startPolling(meeting.project_id, currentMeetingId);
            }
        });
        
        meetingsList.appendChild(meetingCard);
    });
}

// Get meetings by project ID
async function getMeetingsByProjectId(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/meetings`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to retrieve meetings for project');
        }

        return await response.json();
    } catch (error) {
        console.error('Error retrieving meetings for project:', error);
        throw error;
    }
}

// Get project details
async function getProjectDetails(projectId) {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to retrieve project details');
        }

        return await response.json();
    } catch (error) {
        console.error('Error retrieving project details:', error);
        throw error;
    }
}

// Render project details in the specified container
function renderProjectDetails(screenType) {
    // Select the appropriate container based on screen type
    let container;
    switch (screenType) {
        case 'list':
            container = projectDetailsList;
            break;
        case 'input':
            container = projectDetailsInput;
            break;
        case 'waiting':
            container = projectDetailsWaiting;
            break;
        case 'transcript':
            container = projectDetailsTranscript;
            break;
        default:
            console.error('Invalid screen type for project details');
            return;
    }
    
    // Clear current content
    container.innerHTML = '';
    
    // If no project data, show loading state
    if (!projectData) {
        container.innerHTML = `
            <div class="project-details-skeleton">
                <div class="skeleton-loader h-6 w-3/4 bg-gray-200 rounded mb-3"></div>
                <div class="skeleton-loader h-4 w-full bg-gray-200 rounded mb-2"></div>
                <div class="skeleton-loader h-4 w-full bg-gray-200 rounded mb-2"></div>
            </div>
        `;
        return;
    }
    
    // Create sections for Requirements and Feedback/Questions
    const requirementsSection = document.createElement('div');
    requirementsSection.className = 'project-details mb-4';
    
    const questionsSection = document.createElement('div');
    questionsSection.className = 'project-details';
    
    // Requirements Section
    const requirementsHeader = document.createElement('div');
    requirementsHeader.className = 'project-details-header';
    requirementsHeader.innerHTML = `
        <h3>Project Requirements</h3>
        <button class="project-details-toggle" data-target="requirements-content">Show/Hide</button>
    `;
    
    const requirementsContent = document.createElement('div');
    requirementsContent.id = 'requirements-content';
    requirementsContent.className = 'project-details-content';
    requirementsContent.innerHTML = marked.parse(projectData.requirements || 'No requirements specified.');
    
    requirementsSection.appendChild(requirementsHeader);
    requirementsSection.appendChild(requirementsContent);
    
    // Questions/Feedback Section
    const questionsHeader = document.createElement('div');
    questionsHeader.className = 'project-details-header';
    questionsHeader.innerHTML = `
        <h3>Followup Questions</h3>
        <button class="project-details-toggle" data-target="questions-content">Show/Hide</button>
    `;
    
    const questionsContent = document.createElement('div');
    questionsContent.id = 'questions-content';
    questionsContent.className = 'project-details-content';
    questionsContent.innerHTML = marked.parse(projectData.questions || 'No questions specified.');
    
    questionsSection.appendChild(questionsHeader);
    questionsSection.appendChild(questionsContent);
    
    // Add everything to container
    container.appendChild(requirementsSection);
    container.appendChild(questionsSection);
    
    // Add toggle functionality to show/hide buttons
    container.querySelectorAll('.project-details-toggle').forEach(button => {
        button.addEventListener('click', () => {
            const targetId = button.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.classList.toggle('collapsed');
                
                // Update button text based on state
                button.textContent = targetElement.classList.contains('collapsed') ? 'Show' : 'Hide';
            }
        });
    });
}

// Function to display the meetings list
function displayMeetingsList(meetings, projectId) {
    // Save all meetings for filtering
    allMeetings = meetings;
    
    // Update project ID display
    listProjectId.textContent = projectId;
    
    // Update status summary
    updateStatusSummary(meetings);
    
    // Display project details
    renderProjectDetails('list');
    
    // Apply current filter
    filterMeetings(currentFilter);
    
    // Show the meetings list screen
    showScreen('meetingListScreen');
}

// API interaction functions
async function createMeeting(projectId, meetingData) {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/meetings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(meetingData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create meeting');
        }

        return await response.json();
    } catch (error) {
        console.error('Error creating meeting:', error);
        throw error;
    }
}

async function getMeeting(projectId, meetingId) {
    try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/meetings/${meetingId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to retrieve meeting');
        }

        return await response.json();
    } catch (error) {
        console.error('Error retrieving meeting:', error);
        throw error;
    }
}

async function checkMeetingStatus(projectId, meetingId) {
    try {
        const meetingData = await getMeeting(projectId, meetingId);
        
        // If we have a transcription, show it
        if (meetingData.transcription) {
            displayTranscript(meetingData);
            stopPolling();
            
            // Update the meeting in the list if we're polling for status
            const meetingIndex = allMeetings.findIndex(m => m.id === meetingData.id);
            if (meetingIndex !== -1) {
                allMeetings[meetingIndex] = meetingData;
            }
            
            return true;
        }
        
        return false;
    } catch (error) {
        console.warn('Error checking meeting status:', error);
        return false;
    }
}

// Refresh all meetings data
async function refreshMeetings() {
    if (!projectId) return;
    
    try {
        const meetings = await getMeetingsByProjectId(projectId);
        
        if (meetings && Array.isArray(meetings)) {
            // Update our meetings list
            allMeetings = meetings;
            
            // Update displays
            updateStatusSummary(meetings);
            filterMeetings(currentFilter);
            
            return true;
        }
        
        return false;
    } catch (error) {
        console.error('Error refreshing meetings:', error);
        return false;
    }
}

// Load project details
async function loadProjectDetails(projectId) {
    try {
        const data = await getProjectDetails(projectId);
        projectData = data;
        
        // Update all project detail containers
        renderProjectDetails('list');
        renderProjectDetails('input');
        renderProjectDetails('waiting');
        renderProjectDetails('transcript');
        
        return true;
    } catch (error) {
        console.error('Error loading project details:', error);
        showError(`Failed to load project details: ${error.message}`);
        return false;
    }
}

function displayTranscript(meetingData) {
    // Update the transcript screen with meeting details
    transcriptMeetingUrl.textContent = meetingData.meeting_url;
    transcriptProjectId.textContent = meetingData.project_id;
    transcriptMeetingDate.textContent = formatDate(meetingData.meeting_datetime);
    
    // Display project details
    renderProjectDetails('transcript');
    
    // Parse and display the transcript
    const transcription = meetingData.transcription || 'No transcript available yet.';
    
    // Clear the transcript container
    transcriptContent.innerHTML = '';
    
    if (transcription === 'No transcript available yet.') {
        transcriptContent.textContent = transcription;
    } else {
        // Split by new lines and format each line
        const lines = transcription.split('\n');
        lines.forEach(line => {
            if (!line.trim()) return; // Skip empty lines
            
            const lineDiv = document.createElement('div');
            lineDiv.className = 'transcript-line';
            
            // Try to separate speaker from text
            const colonIndex = line.indexOf(':');
            if (colonIndex > 0) {
                const speaker = line.substring(0, colonIndex).trim();
                const text = line.substring(colonIndex + 1).trim();
                
                const speakerSpan = document.createElement('span');
                speakerSpan.className = 'transcript-speaker';
                speakerSpan.textContent = speaker + ': ';
                
                const textSpan = document.createElement('span');
                textSpan.className = 'speaker-text';
                textSpan.textContent = text;
                
                lineDiv.appendChild(speakerSpan);
                lineDiv.appendChild(textSpan);
            } else {
                // If no colon, just use the whole line
                lineDiv.textContent = line;
            }
            
            transcriptContent.appendChild(lineDiv);
        });
    }
    
    // Show the transcript screen
    showScreen('transcriptScreen');
}

// Event Handlers
meetingForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    clearError();
    
    const googleMeetUrl = document.getElementById('googleMeetUrl').value.trim();
    const meetingTitle = document.getElementById('meetingTitle').value.trim();
    
    // Get project ID from URL
    projectId = getProjectIdFromUrl();
    
    // Validate Google Meet URL
    if (!googleMeetUrl.startsWith('https://meet.google.com/')) {
        showError('Please enter a valid Google Meet URL (starting with https://meet.google.com/)');
        return;
    }
    
    // Validate project ID
    if (!projectId) {
        showError('Please provide a project ID in the URL (e.g., ?project_id=your_project_id)');
        return;
    }
    
    // Prepare meeting data
    const meetingData = {
        google_meet_url: googleMeetUrl
    };
    
    if (meetingTitle) {
        meetingData.title = meetingTitle;
    }
    
    try {
        // Show loader while creating meeting
        showScreen('loaderScreen');
        
        // Create the meeting
        const response = await createMeeting(projectId, meetingData);
        
        // Save the meeting ID and data
        currentMeetingId = response.id;
        meetingData.id = response.id;
        
        // Update the waiting screen
        displayMeetingUrl.textContent = googleMeetUrl;
        displayProjectId.textContent = projectId;
        
        // Refresh meetings list
        await refreshMeetings();
        
        // Render project details
        renderProjectDetails('waiting');
        
        // Switch to waiting screen
        showScreen('waitingScreen');
        
        // Start polling for updates
        startPolling(projectId, currentMeetingId);
        
        showNotification('Meeting transcription started');
    } catch (error) {
        showError(error.message || 'Failed to start meeting transcription');
        showScreen('inputScreen');
    }
});

checkStatusButton.addEventListener('click', async function() {
    if (!currentMeetingId || !projectId) {
        showError('No active meeting to check');
        return;
    }
    
    try {
        // Show loader while checking status
        showScreen('loaderScreen');
        
        const hasTranscript = await checkMeetingStatus(projectId, currentMeetingId);
        
        if (!hasTranscript) {
            showNotification('Transcript not ready yet. Still waiting...');
            showScreen('waitingScreen');
        }
    } catch (error) {
        showError(error.message || 'Failed to check meeting status');
        showScreen('waitingScreen');
    }
});

startNewButton.addEventListener('click', function() {
    stopPolling();
    currentMeetingId = null;
    meetingData = {};
    
    // Display project details
    renderProjectDetails('input');
    
    showScreen('inputScreen');
});

newTranscriptionButton.addEventListener('click', function() {
    currentMeetingId = null;
    meetingData = {};
    
    // Display project details
    renderProjectDetails('input');
    
    showScreen('inputScreen');
});

startNewFromListButton.addEventListener('click', function() {
    currentMeetingId = null;
    meetingData = {};
    
    // Display project details
    renderProjectDetails('input');
    
    showScreen('inputScreen');
});

backToListButton.addEventListener('click', async function() {
    stopPolling();
    showScreen('loaderScreen');
    await refreshMeetings();
    showScreen('meetingListScreen');
});

backToListFromTranscriptButton.addEventListener('click', async function() {
    showScreen('loaderScreen');
    await refreshMeetings();
    showScreen('meetingListScreen');
});

// Set up filter button event listeners
filterControls.addEventListener('click', function(e) {
    if (e.target.classList.contains('filter-button')) {
        const filter = e.target.dataset.filter;
        if (filter) {
            filterMeetings(filter);
        }
    }
});

// Auto-refresh meeting list every 30 seconds
setInterval(async () => {
    if (meetingListScreen.classList.contains('active')) {
        await refreshMeetings();
    }
}, 30000);

// Initialize the app with project data loading
document.addEventListener('DOMContentLoaded', async function() {
    // Always start with the loader screen
    showScreen('loaderScreen');
    
    try {
        // Get parameters from URL
        projectId = getProjectIdFromUrl();
        const urlMeetingId = getMeetingIdFromUrl();
        
        // Load project details if project ID is available
        if (projectId) {
            try {
                await loadProjectDetails(projectId);
            } catch (error) {
                console.warn(`Could not load project details: ${error.message}`);
                // Continue with app initialization even if project details fail to load
            }
        }
        
        // First priority: Check if a specific meeting ID is provided
        if (projectId && urlMeetingId) {
            try {
                const meeting = await getMeeting(projectId, urlMeetingId);
                
                if (meeting) {
                    // Save the meeting data
                    currentMeetingId = meeting.id;
                    meetingData = meeting;
                    
                    // Check if meeting has transcription
                    if (meeting.transcription) {
                        displayTranscript(meeting);
                    } else {
                        // Meeting is in progress
                        displayMeetingUrl.textContent = meeting.meeting_url;
                        displayProjectId.textContent = meeting.project_id;
                        
                        // Display project details
                        renderProjectDetails('waiting');
                        
                        showScreen('waitingScreen');
                        startPolling(projectId, currentMeetingId);
                    }
                    return; // Exit initialization
                }
            } catch (error) {
                console.warn(`Could not find meeting with ID: ${urlMeetingId}`, error);
                // Continue with project_id check
            }
        }
        
        // Second priority: Check for project_id and show meeting list
        if (projectId) {
            try {
                // Get meetings for this project
                const projectMeetings = await getMeetingsByProjectId(projectId);
                
                if (projectMeetings && projectMeetings.length > 0) {
                    // Display the meetings list
                    displayMeetingsList(projectMeetings, projectId);
                    return; // Exit initialization
                }
            } catch (error) {
                console.warn(`Could not find meetings for project: ${projectId}`, error);
                // If we can't find meetings, will show the input form
            }
        }
        
        // If we get here, show the input form
        if (projectId) {
            // Display project details
            renderProjectDetails('input');
        }
        
        showScreen('inputScreen');
        
    } catch (error) {
        console.error('Error during initialization:', error);
        showError('Failed to load application data. Please refresh the page.');
        showScreen('inputScreen');
    }
});