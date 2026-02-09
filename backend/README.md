# TaskPulse - AI Assistant - Backend

**The Intelligent Task Completion Engine**

An AI-native workforce productivity platform that transforms task management from passive tracking to active task completion intelligence.

## Core Philosophy

> "No employee should stay stuck for more than 3 hours without intelligent intervention."

## Key Features

### Smart Check-In Engine
- Proactive 3-hour check-in loops with friction detection
- Configurable intervals per team/task
- Automatic escalation for missed check-ins
- Silent mode when progress is on track

### AI Unblock Engine
- RAG-powered contextual help with 0% hallucination
- Knowledge base integration
- Adaptive skill-level responses
- Smart teammate suggestions

### Prediction Engine
- ML-powered delivery forecasting (P25, P50, P90)
- Risk cascade modeling
- Team velocity prediction
- Hiring needs forecasting

### Skill Graph
- Automatic skill inference from task completions
- Learning velocity tracking
- Skill gap detection
- Personalized learning paths

### Workforce Intelligence
- Employee performance scoring
- Manager effectiveness ranking
- Organization health index
- Restructuring simulator

### Automation Detection
- Pattern recognition for repetitive tasks
- AI agent creation and management
- Shadow mode for validation
- ROI dashboard

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLite with SQLAlchemy ORM (async)
- **Authentication**: JWT with refresh tokens
- **AI**: Mock provider (switchable to OpenAI/Anthropic)
- **Testing**: pytest with async support

## Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone repository
git clone https://github.com/shibinsp/taskpulse-ai.git
cd taskpulse-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the application
python run.py
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## API Documentation

Once running, access the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Tasks
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{id}` - Get task details
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/decompose` - AI decomposition

### Check-ins
- `GET /api/v1/checkins` - List check-ins
- `POST /api/v1/checkins/{id}/respond` - Respond to check-in
- `GET /api/v1/checkins/config` - Get configuration

### Skills
- `GET /api/v1/skills/{user_id}/graph` - Get skill graph
- `GET /api/v1/skills/{user_id}/gaps` - Get skill gaps
- `GET /api/v1/skills/{user_id}/learning-path` - Get learning path

### AI
- `POST /api/v1/ai/unblock` - Get AI help for blockers
- `POST /api/v1/ai/knowledge-base/upload` - Upload documents

### Predictions
- `GET /api/v1/predictions/tasks/{id}` - Task delivery prediction
- `GET /api/v1/predictions/team/{id}/velocity` - Velocity forecast

### Workforce
- `GET /api/v1/workforce/scores` - Employee scores
- `GET /api/v1/workforce/org-health` - Organization health
- `POST /api/v1/workforce/simulate` - Restructuring simulation

### Automation
- `GET /api/v1/automation/patterns` - Detected patterns
- `POST /api/v1/automation/agents` - Create AI agent
- `GET /api/v1/automation/roi` - ROI dashboard

### Reports
- `GET /api/v1/reports/dashboard` - Dashboard metrics
- `POST /api/v1/reports/generate` - Generate report
- `GET /api/v1/reports/executive-summary` - Executive summary

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## Seed Data

Populate database with demo data:

```bash
# Seed database
python scripts/seed_data.py

# Clear and reset database
python scripts/seed_data.py --clear
```

Demo credentials (password: `demo123`):
- Admin: admin@acme.com
- Manager: manager@acme.com
- Employee: dev1@acme.com

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API routes
│   ├── core/            # Security, permissions, middleware
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── utils/           # Utilities
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Role-Based Access Control

| Role | Description |
|------|-------------|
| Super Admin | Full system access |
| Org Admin | Organization-wide management |
| Manager | Team oversight and reports |
| Team Lead | Team task management |
| Employee | Personal tasks and check-ins |
| Viewer | Read-only access |

## Environment Variables

Key configuration options (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | Database connection string | sqlite:///./taskpulse.db |
| `SECRET_KEY` | Application secret key | - |
| `AI_PROVIDER` | AI provider (mock/openai/anthropic) | mock |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |

## AI Provider Configuration

### Mock (Default)
No configuration needed. Useful for development.

### OpenAI
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

### Anthropic (Claude)
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

---

Built with FastAPI and Python
