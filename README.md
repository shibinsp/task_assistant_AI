<p align="center">
  <img src="https://img.shields.io/badge/TaskPulse-AI-gradient?style=for-the-badge&logo=brain&logoColor=white&labelColor=D4A017&color=B8860B" alt="TaskPulse AI" height="40"/>
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
  <a href="https://github.com/shibinsp/task_assistant_AI/actions/workflows/ci-cd.yml">
    <img src="https://github.com/shibinsp/task_assistant_AI/actions/workflows/ci-cd.yml/badge.svg?branch=main" alt="CI/CD"/>
  </a>
  <a href="https://relaxed-gates.vercel.app">
    <img src="https://img.shields.io/badge/Vercel-Deployed-000?style=flat-square&logo=vercel" alt="Vercel"/>
  </a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-5.9-3178c6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Vite-7-646cff?style=flat-square&logo=vite&logoColor=white" alt="Vite"/>
</p>

<p align="center">
  <a href="#live-demo">Live Demo</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#tech-stack">Tech Stack</a> &bull;
  <a href="#getting-started">Getting Started</a> &bull;
  <a href="#api-endpoints">API Docs</a> &bull;
  <a href="#contributing">Contributing</a>
</p>

---

## Live Demo

**Production**: [https://relaxed-gates.vercel.app](https://relaxed-gates.vercel.app)

| Email | Password | Role |
|-------|----------|------|
| `admin@taskpulse.demo` | `TaskPulse2024` | Super Admin |
| `orgadmin@taskpulse.demo` | `TaskPulse2024` | Org Admin |
| `manager@taskpulse.demo` | `TaskPulse2024` | Manager |
| `lead@taskpulse.demo` | `TaskPulse2024` | Team Lead |
| `dev@taskpulse.demo` | `TaskPulse2024` | Employee |
| `viewer@taskpulse.demo` | `TaskPulse2024` | Viewer |

---

## Features

### Task Management
- **Full CRUD** with priority, status, assignments, due dates, and subtasks
- **Kanban Board** / **List** / **Grid** views with drag-and-drop
- **AI Task Decomposition** - break complex tasks into subtasks automatically
- **Bulk Operations** - update multiple tasks at once
- **Task Dependencies** - link related tasks together
- **Comments & History** - full audit trail on every task

### Smart Check-In Engine
- **3-Hour Loops** - configurable proactive check-in intervals
- **Friction Detection** - AI identifies when progress stalls
- **Auto-Escalation** - missed check-ins notify managers
- **Manager Feed** - centralized view of team responses

### AI Command Center
- **AI Unblock Engine** - RAG-powered help with blockers
- **Knowledge Base** - upload and search internal docs
- **Conversational Task Creation** - create tasks via natural language
- **Multi-Provider** - OpenAI, Anthropic, Mistral, Kimi, Ollama support

### Prediction & Analytics
- **Delivery Forecasts** - P25/P50/P90 completion estimates
- **Velocity Trends** - team performance over time
- **Productivity Heatmap** - hourly productivity patterns
- **Dashboard Metrics** - real-time task statistics

### Skill Graph
- **Skill Tracking** - catalog and rate team skills
- **Gap Analysis** - identify missing skills for roles
- **Learning Paths** - personalized development plans
- **Team Composition** - visualize collective strengths

### Workforce Intelligence
- **Performance Scoring** - multi-factor employee metrics
- **Manager Rankings** - leadership effectiveness comparison
- **Org Health Index** - company-wide health dashboard
- **Attrition Risk** - identify at-risk employees
- **Restructuring Simulator** - model team changes before committing

### Automation Detection
- **Pattern Recognition** - AI finds repetitive workflows
- **Agent Creation** - one-click automation for common tasks
- **Shadow Mode** - test automations safely before activation
- **ROI Dashboard** - track hours saved and cost reduction

### Integrations
- **OAuth Flows** - connect Slack, Jira, and other tools
- **Webhooks** - real-time event notifications
- **API Keys** - programmatic access management

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind CSS, Radix UI/shadcn |
| **State** | Zustand 5, TanStack React Query |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy 2.0 (async) |
| **Database** | SQLite (dev) / PostgreSQL + Supabase (prod) |
| **Auth** | JWT + bcrypt + Google OAuth 2.0 + Supabase Auth |
| **AI** | OpenAI, Anthropic, Mistral, Kimi, Ollama, Mock |
| **Testing** | Playwright (E2E), pytest (unit) |
| **CI/CD** | GitHub Actions + Vercel |
| **Infra** | Docker, Docker Compose |

---

## Architecture

```
                            ┌──────────────────────────────┐
                            │     Vercel (Production)      │
                            │  relaxed-gates.vercel.app    │
                            └──────────────┬───────────────┘
                                           │
               ┌───────────────────────────┼───────────────────────────┐
               │                           │                           │
    ┌──────────▼──────────┐    ┌──────────▼──────────┐    ┌──────────▼──────────┐
    │   Frontend (Vite)   │    │   API (Serverless)   │    │   Supabase Auth     │
    │   React 19 + TS     │───▶│   FastAPI + Python   │    │   OAuth + JWT       │
    │   Port: 5173        │    │   Port: 8000         │    │                     │
    └─────────────────────┘    └──────────┬───────────┘    └─────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
             ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
             │  PostgreSQL │      │ AI Providers │      │  Supabase   │
             │  (Supabase) │      │ OpenAI/etc   │      │  Storage    │
             └─────────────┘      └─────────────┘      └─────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1. Clone

```bash
git clone https://github.com/shibinsp/task_assistant_AI.git
cd task_assistant_AI
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the server
python run.py
# Or: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

### 4. Seed Demo Data

```bash
cd backend
python scripts/seed_data.py
```

### 5. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

**Default login**: `admin@acme.com` / `demo123`

---

## E2E Testing

13 Playwright test suites covering 113 test cases.

```bash
cd Frontend

# Run against local dev server
npm run test:e2e

# Run against deployed app
npm run test:e2e:deployed

# Run with visible browser
npm run test:e2e:headed

# Interactive UI mode
npm run test:e2e:ui

# View HTML report
npx playwright show-report
```

### Latest Results (Deployed App)

| Suite | Tests | Status |
|-------|-------|--------|
| Landing Page | 7 | Pass |
| Authentication | 8 | Pass |
| Dashboard | 9 | 8 Pass / 1 Fail |
| Task Creation | 6 | Pass |
| AI Task Creator | 6 | Pass |
| Task Management | 5 | Pass |
| Navigation | 7 | Pass |
| Settings | 3 | Pass |
| Task Detail | 11 | Pass |
| Filters & Sort | 12 | Pass |
| Check-Ins | 13 | Pass |
| AI Command | 9 | Pass |
| Settings Logic | 15 | Pass |
| **Total** | **113** | **110 Pass / 1 Fail / 2 Skip** |

---

## CI/CD Pipeline

Every push to `main` triggers automatic deployment:

```
Push to main
    │
    ├── Detect Changes (frontend/backend)
    │
    ├── Frontend: Lint & Build (ESLint + tsc + Vite)
    │
    ├── Backend: Unit Tests (pytest)
    │
    └── Deploy to Vercel Production
```

- **Preview deploys** on every PR with auto-comment
- **Manual trigger** via GitHub Actions UI (`workflow_dispatch`)
- **Concurrency control** — new pushes cancel in-progress runs

---

## Project Structure

```
task_assistant_AI/
├── Frontend/
│   ├── src/
│   │   ├── pages/              # 19 route pages
│   │   ├── components/         # UI components (shadcn + custom)
│   │   ├── services/           # 17 API service modules
│   │   ├── store/              # Zustand stores (auth, theme, ui)
│   │   ├── types/              # TypeScript types + mappers
│   │   ├── hooks/              # React Query hooks
│   │   └── lib/                # API client, Supabase, utils
│   ├── e2e/                    # 13 Playwright spec files
│   ├── playwright.config.ts
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/v1/             # 18 route modules
│   │   ├── core/               # Security, middleware, permissions
│   │   ├── models/             # 12 SQLAlchemy models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # 17 business logic services
│   │   └── agents/             # 5 AI agents
│   ├── tests/                  # pytest test suite
│   ├── scripts/                # Seed data scripts
│   └── requirements.txt
├── api/
│   └── index.py                # Vercel serverless entry point
├── .github/workflows/
│   └── ci-cd.yml               # CI/CD pipeline
├── docs/
│   ├── reports/                # Test & audit reports
│   └── screenshots/            # UI screenshots
├── vercel.json                 # Vercel deploy config
├── docker-compose.yml          # Docker services
└── CLAUDE.md                   # Development rules
```

---

## API Endpoints

<details>
<summary><strong>Authentication</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create new account |
| `POST` | `/api/v1/auth/login` | Get access tokens |
| `GET` | `/api/v1/auth/me` | Get current user |
| `POST` | `/api/v1/auth/google` | Google OAuth login |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `POST` | `/api/v1/auth/logout` | Logout current session |
| `POST` | `/api/v1/auth/change-password` | Change password |
| `GET` | `/api/v1/auth/sessions` | List active sessions |

</details>

<details>
<summary><strong>Tasks</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List tasks (filterable) |
| `POST` | `/api/v1/tasks` | Create task |
| `GET` | `/api/v1/tasks/{id}` | Get task details |
| `PUT` | `/api/v1/tasks/{id}` | Update task |
| `DELETE` | `/api/v1/tasks/{id}` | Delete task |
| `POST` | `/api/v1/tasks/{id}/decompose` | AI decomposition |
| `POST` | `/api/v1/tasks/{id}/subtasks` | Create subtask |
| `POST` | `/api/v1/tasks/{id}/comments` | Add comment |
| `GET` | `/api/v1/tasks/{id}/history` | Task change history |
| `POST` | `/api/v1/tasks/bulk/update` | Bulk update |

</details>

<details>
<summary><strong>Check-Ins</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/checkins` | List check-ins |
| `GET` | `/api/v1/checkins/pending` | Pending check-ins |
| `POST` | `/api/v1/checkins/{id}/respond` | Submit response |
| `POST` | `/api/v1/checkins/{id}/skip` | Skip check-in |
| `POST` | `/api/v1/checkins/{id}/escalate` | Escalate blocker |
| `GET` | `/api/v1/checkins/config` | Get config |
| `GET` | `/api/v1/checkins/statistics` | Check-in stats |

</details>

<details>
<summary><strong>AI & Chat</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ai/unblock` | AI unblock assistance |
| `GET` | `/api/v1/ai/documents` | Knowledge base docs |
| `POST` | `/api/v1/chat` | Send chat message |
| `GET` | `/api/v1/chat/conversations` | List conversations |

</details>

<details>
<summary><strong>Skills, Predictions, Workforce</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/skills` | Skill catalog |
| `GET` | `/api/v1/skills/{userId}/graph` | Skill graph |
| `GET` | `/api/v1/skills/{userId}/gaps` | Skill gaps |
| `GET` | `/api/v1/predictions/tasks/{id}` | Delivery forecast |
| `GET` | `/api/v1/predictions/team/{id}/velocity` | Velocity forecast |
| `GET` | `/api/v1/workforce/scores` | Performance scores |
| `GET` | `/api/v1/workforce/org-health` | Org health index |
| `POST` | `/api/v1/workforce/simulations` | Restructuring sim |

</details>

<details>
<summary><strong>Automation & Integrations</strong></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/automation/patterns` | Detected patterns |
| `POST` | `/api/v1/automation/agents` | Create agent |
| `GET` | `/api/v1/automation/roi` | ROI dashboard |
| `GET` | `/api/v1/integrations` | List integrations |
| `POST` | `/api/v1/integrations` | Create integration |
| `POST` | `/api/v1/integrations/{id}/test` | Test connection |
| `GET` | `/api/v1/webhooks` | List webhooks |

</details>

---

## Security

- **JWT Authentication** with refresh token rotation
- **bcrypt Password Hashing** with complexity requirements (8+ chars, uppercase, etc.)
- **Role-Based Access Control** (6 roles: Super Admin to Viewer)
- **Permission Guards** on all API endpoints
- **Secret Redaction** in API responses (SMTP passwords, tokens)
- **CORS Protection** with configurable origins
- **Rate Limiting** on authentication endpoints
- **Input Validation** via Pydantic schemas
- **SQL Injection Prevention** via SQLAlchemy ORM
- **XSS Protection** via React's built-in escaping

---

## Role-Based Access Control

| Role | Tasks | Check-Ins | Team | Reports | Admin |
|------|-------|-----------|------|---------|-------|
| **Super Admin** | Full | Full | Full | Full | Full |
| **Org Admin** | Full | Full | Full | Full | Org Settings |
| **Manager** | Team | Team | View | Full | - |
| **Team Lead** | Team | Team | View | Team | - |
| **Employee** | Own | Own | - | Own | - |
| **Viewer** | Read | Read | - | Read | - |

---

## Contributing

All changes follow the **Issue -> Branch -> PR** workflow:

1. **Create a GitHub Issue** describing the change
2. **Create a branch**: `fix/issue-42-description` or `feat/issue-43-feature`
3. **Implement** the fix/feature
4. **Create a PR** with `Fixes #<issue-number>` in the body
5. **CI passes** -> **Merge** to `main` -> **Auto-deploy** to Vercel

---

<p align="center">
  <strong>Built by <a href="https://github.com/shibinsp">shibinsp</a> &bull; Powered by Beeax</strong>
</p>
