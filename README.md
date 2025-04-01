# DeCode PoC meeting Module 🎙️

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)

A Flask-based web application that integrates with Fireflies.ai to provide automated meeting transcription services. The application allows you to schedule meetings, automatically add Fireflies' AI bot to your Google Meet calls, and retrieve searchable, formatted transcripts afterward.

## ✨ Features

- **Meeting Management**: Create, track, and manage meeting transcriptions by project
- **Automatic Bot Integration**: Seamlessly add Fireflies.ai bot to Google Meet sessions
- **Webhook Support**: Receive real-time notifications when transcriptions are complete
- **Transcript Retrieval**: Access and view meeting transcripts with speaker identification
- **Project Organization**: Group meetings by project for better organization
- **AI-Powered Brief Validation**: Optional validation of project briefs using OpenAI
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL (for production, SQLite for development)
- Fireflies.ai API key
- OpenAI API key (optional, for project brief validation)

## 🚀 Installation


### Manual Installation (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fireflies-transcription-service.git
   cd fireflies-transcription-service
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and update with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   # or
   python migrate_db.py
   ```

6. Start the Flask development server:
   ```bash
   flask run
   # or
   python wsgi.py
   ```

7. Access the application at `http://localhost:5000`

### Using Docker (Experimental)

1. Clone the repository:
   ```bash
   git clone git@github.com:hculap/decode-poc-module-2.git
   cd decode-poc-module-2
   ```

2. Copy the example environment file and update with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Start the service using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application at `http://localhost:5000`

## ⚙️ Configuration

The application is configured through environment variables, which can be set in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URI` | Database connection string | `sqlite:///fireflies.db` |
| `FIREFLIES_API_KEY` | Your Fireflies.ai API key (required) | None |
| `FIREFLIES_WEBHOOK_SECRET` | Secret for verifying webhook signatures | None |
| `FLASK_ENV` | Flask environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | `INFO` |
| `PROJECT_BRIEF_SERVICE_URL` | URL for external project brief service | `http://localhost:8001` |
| `OPENAI_API_KEY` | OpenAI API key for brief validation | None |
| `ENABLE_BRIEF_VALIDATION` | Enable project brief validation | `false` |

## 🔍 Usage

### Creating a New Meeting

1. Navigate to the main interface
2. Enter your Project ID
3. Provide the Google Meet URL
4. Click "Start Debriefing Meeting"

The application will:
1. Add the Fireflies.ai bot to your meeting
2. Create a new meeting record in the database
3. Wait for the webhook callback when transcription is complete

### Viewing Transcripts

1. Navigate to your project's meeting list
2. Click on a completed meeting to view the transcript
3. Transcripts are formatted with speaker identification

## 🏗️ Project Structure

```
fireflies-transcription-service/
├── app/                        # Main application package
│   ├── __init__.py             # Application factory
│   ├── config.py               # Configuration settings
│   ├── models.py               # Database models
│   ├── routes/                 # API route modules
│   │   ├── meetings.py         # Meeting-related routes
│   │   ├── projects.py         # Project-related routes
│   │   ├── test_utils.py       # Test utility routes
│   │   └── ui.py               # UI routes
│   ├── services/               # Service modules
│   │   ├── fireflies.py        # Fireflies.ai API interactions
│   │   ├── openai_service.py   # OpenAI API service
│   │   └── project_brief_service.py # Project brief service
│   ├── static/                 # Static files (JS, CSS)
│   │   └── js/app.js           # Frontend JavaScript
│   ├── templates/              # HTML templates
│   │   └── index.html          # Main application template
│   └── utils/                  # Utility modules
│       └── webhook.py          # Webhook verification utilities
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker configuration
├── migrate_db.py               # Database migration script
├── requirements.txt            # Python dependencies
└── wsgi.py                     # WSGI entry point
```

## 📡 API Endpoints

### Meetings API

- `GET /projects/<project_id>/meetings` - List meetings for a project
- `POST /projects/<project_id>/meetings` - Create a new meeting
- `GET /projects/<project_id>/meetings/<meeting_id>` - Get a specific meeting/transcript

### Projects API

- `GET /projects/<project_id>` - Get project details
- `POST /projects/<project_id>/validate` - Validate a project brief

### Webhook API

- `POST /webhooks/meetings` - Webhook endpoint for Fireflies.ai

### Health Check

- `GET /health` - Health check endpoint

## 🧪 Testing

The repository includes a test script that can validate your installation and configuration:

```bash
python test_fireflies_service.py --host=http://localhost:5000
```

For development environments, test utility endpoints are available:

- `POST /test-utils/reset-db` - Reset the database
- `POST /test-utils/inject-transcript` - Inject a test transcript for a meeting

## 📚 Project Brief Validation

When enabled, the service can validate project briefs against a reference template using OpenAI:

1. Set `ENABLE_BRIEF_VALIDATION=true` in your `.env` file
2. Provide your `OPENAI_API_KEY`
3. Project briefs will be validated automatically when retrieved

The validation provides a comprehensive analysis of project requirements against best practices.

## 🛠️ Development

### Setting up a Development Environment

1. Follow the manual installation steps above
2. Enable development mode in the `.env` file:
   ```
   FLASK_ENV=development
   ```

3. Run the application with:
   ```bash
   flask run --reload
   ```

### Running Tests

Use the included test script to validate functionality:

```bash
python test_fireflies_service.py
```

## 📞 Support & Contact

For issues or questions:
- Open a GitHub issue
- Contact the maintainers at [kontakt@szymonpaluch.com]

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Fireflies.ai](https://fireflies.ai) for their transcription API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [OpenAI](https://openai.com) for the brief validation capabilities