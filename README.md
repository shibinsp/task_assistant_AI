<p align="center">
  <img src="https://img.shields.io/badge/TaskPulse-AI-gradient?style=for-the-badge&logo=brain&logoColor=white&labelColor=6366f1&color=8b5cf6" alt="TaskPulse AI" height="40"/>
</p>

<h1 align="center">TaskPulse AI</h1>

<p align="center">
  <strong>The Intelligent Task Completion Engine</strong>
</p>

<p align="center">
  Transform your workforce from passive task tracking to active task completion intelligence.
  <br />
  <em>No employee stays stuck for more than 3 hours.</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-docs">API Docs</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-18-61dafb?style=flat-square&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5.3-3178c6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Vite-5.1-646cff?style=flat-square&logo=vite&logoColor=white" alt="Vite"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
</p>

---

## The Problem

Traditional task management tools are **passive observers**. They track what's happening but don't actively help employees complete their work. When someone gets stuck:

- ❌ They waste hours before asking for help
- ❌ Managers only find out during weekly standups
- ❌ Projects slip without early warning
- ❌ Valuable knowledge stays siloed in individuals

## The Solution

**TaskPulse AI** is an **active task completion engine** that:

- ✅ Proactively checks in with employees every 3 hours
- ✅ Uses AI to unblock stuck workers instantly
- ✅ Predicts delivery risks before they become problems
- ✅ Builds organizational knowledge that helps everyone

---

## Features

### 🔄 Smart Check-In Engine

Intelligent, proactive engagement that catches blockers early.

| Feature | Description |
|---------|-------------|
| **3-Hour Loops** | Configurable check-in intervals per team or task type |
| **Friction Detection** | AI identifies when progress is slower than expected |
| **Auto-Escalation** | Missed check-ins trigger manager notifications |
| **Silent Mode** | No interruptions when everything's on track |

### 🧠 AI Unblock Engine

RAG-powered assistance with **zero hallucination** guarantee.

```
Employee: "I'm stuck on the OAuth integration with our legacy system"

TaskPulse AI: Based on your codebase and past solutions:
├── Similar issue solved by @john (PR #234) - 3 weeks ago
├── Internal wiki: "Legacy OAuth Migration Guide"
├── Suggested teammate: @sarah (95% skill match)
└── Estimated unblock time: 45 minutes with pairing
```

- **Knowledge Base Integration** - Upload docs, wikis, and past solutions
- **Skill-Adaptive Responses** - Adjusts explanation complexity to user level
- **Smart Teammate Matching** - Suggests the right person to help

### 📊 Prediction Engine

Machine learning-powered forecasting that sees problems coming.

| Prediction Type | What It Does |
|----------------|--------------|
| **Delivery Forecast** | P25, P50, P90 completion estimates |
| **Risk Cascade** | Shows how one delay affects downstream tasks |
| **Velocity Trends** | Team performance over time |
| **Hiring Forecast** | Predicts when you'll need more capacity |

### 🎯 Skill Graph

Automatic skill inference that grows with your organization.

```
┌─────────────────────────────────────────────────┐
│  Developer: Sarah Chen                          │
├─────────────────────────────────────────────────┤
│  ████████████████████░░░░  React (85%)          │
│  ██████████████░░░░░░░░░░  TypeScript (70%)     │
│  ████████████████████████  Python (95%)         │
│  ████████░░░░░░░░░░░░░░░░  DevOps (40%)         │
├─────────────────────────────────────────────────┤
│  📈 Learning Velocity: +15% this quarter        │
│  🎯 Recommended: "Advanced Kubernetes" course   │
└─────────────────────────────────────────────────┘
```

### 👥 Workforce Intelligence

Data-driven insights for better organizational decisions.

- **Performance Scoring** - Objective, multi-factor employee metrics
- **Manager Effectiveness** - How well leaders enable their teams
- **Org Health Index** - Company-wide productivity dashboard
- **Restructuring Simulator** - Model team changes before making them

### 🤖 Automation Detection

Find and eliminate repetitive work automatically.

1. **Pattern Recognition** - AI identifies repetitive task sequences
2. **Agent Creation** - One-click automation for common workflows
3. **Shadow Mode** - Test automations safely before deployment
4. **ROI Dashboard** - Track hours saved and cost reduction

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Local Development

**1. Clone the repository**

```bash
git clone https://github.com/shibinsp/taskpulse-ai.git
cd taskpulse-ai
```

**2. Backend Setup**

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Or install core dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic-settings python-jose[cryptography] passlib bcrypt python-multipart greenlet

# Configure environment (already set up)
# Edit backend/.env if needed

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**4. Access the Application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Quick Start Script

```bash
# From project root
./start.sh
```

This will start both backend and frontend services automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │Dashboard │ │  Tasks   │ │ Check-ins│ │   Skills & Reports   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API (Vite Proxy)
┌─────────────────────────────▼───────────────────────────────────┐
│                        Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                        API Layer (v1)                        ││
│  │  Auth │ Tasks │ Check-ins │ Skills │ Predictions │ Reports  ││
│  └──────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                      Service Layer                           ││
│  │  AI Service │ Prediction │ Skill Graph │ Automation │ Notif  ││
│  └──────────────────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                       Data Layer                             ││
│  │            SQLAlchemy ORM │ Async SQLite/PostgreSQL          ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌──────────┐
   │   AI    │          │ Database │         │  Cache   │
   │ Provider│          │  SQLite  │         │  (Future)│
   └─────────┘          └──────────┘         └──────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Zustand, Axios |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy, Pydantic |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **AI** | OpenAI / Anthropic Claude / Mock (configurable) |
| **Deployment** | Docker, Docker Compose (coming soon) |

---

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

<details>
<summary><strong>Authentication</strong></summary>

```http
POST /api/v1/auth/register   # Create new account
POST /api/v1/auth/login      # Get access tokens
POST /api/v1/auth/refresh    # Refresh access token
GET  /api/v1/auth/me         # Get current user
```
</details>

<details>
<summary><strong>Tasks</strong></summary>

```http
GET    /api/v1/tasks              # List all tasks
POST   /api/v1/tasks              # Create new task
GET    /api/v1/tasks/{id}         # Get task details
PUT    /api/v1/tasks/{id}         # Update task
DELETE /api/v1/tasks/{id}         # Delete task
POST   /api/v1/tasks/{id}/decompose  # AI task breakdown
```
</details>

<details>
<summary><strong>Check-ins</strong></summary>

```http
GET  /api/v1/checkins              # List check-ins
POST /api/v1/checkins              # Create check-in
GET  /api/v1/checkins/{id}         # Get check-in details
```
</details>

<details>
<summary><strong>AI & Predictions</strong></summary>

```http
POST /api/v1/ai/unblock                    # Get AI help for blockers
GET  /api/v1/predictions/tasks/{id}        # Delivery forecast
GET  /api/v1/predictions/team/{id}/velocity # Velocity trends
```
</details>

<details>
<summary><strong>Workforce & Reports</strong></summary>

```http
GET  /api/v1/workforce/scores       # Employee performance
GET  /api/v1/workforce/org-health   # Organization metrics
POST /api/v1/workforce/simulate     # Restructuring simulation
GET  /api/v1/reports/dashboard      # Dashboard data
POST /api/v1/reports/generate       # Generate report
```
</details>

---

## Role-Based Access Control

| Role | Capabilities |
|------|--------------|
| **Super Admin** | Full system access, multi-org management |
| **Org Admin** | Organization settings, all users |
| **Manager** | Team oversight, reports, escalations |
| **Team Lead** | Team task management, check-ins |
| **Employee** | Personal tasks, respond to check-ins |
| **Viewer** | Read-only dashboard access |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `DATABASE_URL` | Database connection | `sqlite+aiosqlite:///./taskpulse.db` |
| `SECRET_KEY` | JWT signing key | (auto-generated for dev) |
| `AI_PROVIDER` | AI backend | `mock` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |

### AI Provider Setup

**Mock (Default)** - No API keys needed, great for development.

**OpenAI:**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

**Anthropic Claude:**
```env
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

---

## Project Structure

```
taskpulse-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── core/            # Security, middleware
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── agents/          # AI agents
│   │   └── utils/           # Helpers
│   ├── tests/               # Test suite
│   ├── scripts/             # Seed data, utilities
│   ├── .env                 # Environment config
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Route pages
│   │   ├── services/        # API clients
│   │   ├── store/           # State management
│   │   ├── types/           # TypeScript types
│   │   └── lib/             # Utilities
│   ├── package.json
│   └── vite.config.ts
├── start.sh                 # Quick start script
├── INTEGRATION.md           # Integration guide
└── README.md
```

---

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 app/
black app/

# Frontend linting
cd frontend
npm run lint
```

---

## Roadmap

- [x] **Core Task Management** - CRUD operations, status tracking
- [x] **Authentication & Authorization** - JWT-based auth, RBAC
- [x] **Check-in System** - Proactive engagement loops
- [x] **AI Unblock Engine** - RAG-powered assistance
- [x] **Skill Graph** - Automatic skill inference
- [x] **Prediction Engine** - ML-powered forecasting
- [ ] **Slack/Teams Integration** - Check-ins where your team works
- [ ] **Mobile App** - iOS and Android native apps
- [ ] **Advanced Analytics** - Custom report builder
- [ ] **SSO/SAML** - Enterprise authentication
- [ ] **Multi-language Support** - i18n for global teams
- [ ] **API Webhooks** - External integrations

---

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: See [INTEGRATION.md](INTEGRATION.md) for detailed setup
- **Issues**: Report bugs on [GitHub Issues](https://github.com/shibinsp/taskpulse-ai/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/shibinsp/taskpulse-ai/discussions)

---

<p align="center">
  <strong>Built with passion for productive teams everywhere.</strong>
  <br />
  <br />
  <a href="https://github.com/shibinsp/taskpulse-ai/stargazers">
    <img src="https://img.shields.io/github/stars/shibinsp/taskpulse-ai?style=social" alt="Stars"/>
  </a>
  <a href="https://github.com/shibinsp/taskpulse-ai/network/members">
    <img src="https://img.shields.io/github/forks/shibinsp/taskpulse-ai?style=social" alt="Forks"/>
  </a>
</p>
