# TaskPulse AI - Project Workflow

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Development Workflow](#development-workflow)
6. [Backend Workflow](#backend-workflow)
7. [Frontend Workflow](#frontend-workflow)
8. [AI Agent System](#ai-agent-system)
9. [Authentication Flow](#authentication-flow)
10. [Task Lifecycle](#task-lifecycle)
11. [API Reference](#api-reference)
12. [Database Schema](#database-schema)
13. [Deployment](#deployment)

---

## Architecture Overview

```
                    +-------------------+
                    |   React Frontend  |
                    |  (Vite + TS)      |
                    +--------+----------+
                             |
                        HTTP / WebSocket
                             |
                    +--------v----------+
                    |   FastAPI Backend  |
                    |   (Python 3.11+)  |
                    +--------+----------+
                             |
              +--------------+--------------+
              |              |              |
     +--------v---+  +------v------+  +----v--------+
     | SQLite/     |  | AI Providers|  | Scheduler   |
     | PostgreSQL  |  | (Multi)     |  | (APScheduler)|
     +-------------+  +-------------+  +-------------+
```

**Frontend** (port 5173) communicates with **Backend** (port 8000) via REST API with `/api/v1` prefix. Vite dev server proxies `/api` requests to the backend.

---

## Tech Stack

| Layer          | Technology                                            |
|----------------|-------------------------------------------------------|
| Frontend       | React 19, TypeScript 5.9, Vite 7.2, Tailwind CSS     |
| UI Components  | Radix UI, shadcn/ui, Framer Motion, Recharts          |
| State          | Zustand 5 (auth, theme, UI), TanStack React Query     |
| Backend        | FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy 2.0    |
| Database       | SQLite (dev) / PostgreSQL (prod), Alembic migrations  |
| AI Providers   | OpenAI, Anthropic, Ollama, Mistral, Kimi (pluggable)  |
| Auth           | JWT (access + refresh tokens), Google OAuth 2.0       |
| Real-time      | WebSocket (check-in prompts, notifications)           |
| Deployment     | Docker, Docker Compose                                |

---

## Project Structure

```
task_assistant_AI/
├── Frontend/
│   ├── src/
│   │   ├── pages/              # Route page components (18 pages)
│   │   ├── components/
│   │   │   ├── layout/         # DashboardLayout, Sidebar, Header
│   │   │   └── ui/             # shadcn/ui components
│   │   ├── services/           # API client services (17 services)
│   │   ├── store/              # Zustand stores (auth, theme, ui)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── types/              # TypeScript types & mappers
│   │   ├── lib/                # API client config, utilities
│   │   ├── App.tsx             # Root component, routing, ErrorBoundary
│   │   └── main.tsx            # Entry point
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── app/
│   │   ├── api/v1/             # Route handlers (18 route files)
│   │   ├── services/           # Business logic (17 services)
│   │   ├── models/             # SQLAlchemy ORM models (12 models)
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── agents/             # AI agent system
│   │   │   ├── conversation/   # Chat agent, conversation manager
│   │   │   ├── integrations/   # External system integrations
│   │   │   ├── orchestrator.py # Agent coordination
│   │   │   └── *.py            # Specialized agents
│   │   ├── core/               # Security, permissions, middleware
│   │   ├── utils/              # Validators, helpers, file extractor
│   │   ├── config.py           # Settings (Pydantic Settings)
│   │   ├── database.py         # Async DB session management
│   │   └── main.py             # FastAPI app entry point
│   ├── scripts/seed_data.py    # Demo data seeder
│   ├── tests/                  # Pytest test suite
│   ├── requirements.txt
│   ├── run.py
│   └── .env
│
├── docker-compose.yml
├── workflow.md                 # This file
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt

# Configure environment
cp .env.example .env            # Edit with your API keys

# Initialize database & seed data
python scripts/seed_data.py

# Start server
python run.py                   # Runs on http://localhost:8000
```

### Frontend Setup

```bash
cd Frontend
npm install

# Start dev server
npm run dev                     # Runs on http://localhost:5173
```

### Docker (Alternative)

```bash
docker-compose up --build       # Starts both frontend and backend
```

### Environment Variables (`backend/.env`)

```
GOOGLE_CLIENT_ID=<google-oauth-client-id>
AI_PROVIDER=ollama              # mock | openai | anthropic | ollama | mistral | kimi
OLLAMA_MODEL=<model-name>
MISTRAL_API_KEY=<key>
KIMI_API_KEY=<key>
KIMI_MODEL=<model>
```

---

## Development Workflow

### Daily Development Cycle

```
1. Start backend     →  cd backend && python run.py
2. Start frontend    →  cd Frontend && npm run dev
3. Open browser      →  http://localhost:5173
4. Login             →  admin@acme.com / demo123
5. Make changes      →  Hot reload (Vite) / Auto-restart (uvicorn)
6. Type check        →  cd Frontend && npx tsc --noEmit
7. Build check       →  cd Frontend && npx vite build
8. Commit            →  git add <files> && git commit
```

### Adding a New Feature

```
Backend:
  1. Define schema       →  backend/app/schemas/<feature>.py
  2. Create model        →  backend/app/models/<feature>.py
  3. Write service       →  backend/app/services/<feature>_service.py
  4. Add route           →  backend/app/api/v1/<feature>.py
  5. Register router     →  backend/app/main.py

Frontend:
  1. Add API types       →  Frontend/src/types/api.ts
  2. Create service      →  Frontend/src/services/<feature>.service.ts
  3. Add query keys      →  Frontend/src/hooks/useApi.ts
  4. Build page          →  Frontend/src/pages/<Feature>Page.tsx
  5. Add route           →  Frontend/src/App.tsx
  6. Add sidebar link    →  Frontend/src/components/layout/DashboardLayout.tsx
```

---

## Backend Workflow

### Request Lifecycle

```
Client Request
    │
    v
FastAPI Router (api/v1/*.py)
    │  - Path validation
    │  - Auth dependency injection (get_current_user)
    │  - Request schema validation (Pydantic)
    v
Service Layer (services/*_service.py)
    │  - Business logic
    │  - Database operations (SQLAlchemy async)
    │  - AI agent calls (if needed)
    v
Response Schema (schemas/*.py)
    │  - Response serialization
    v
JSON Response → Client
```

### Key Backend Services

| Service                | Responsibility                                      |
|------------------------|-----------------------------------------------------|
| `auth_service`         | Login, signup, JWT tokens, Google OAuth              |
| `task_service`         | Task CRUD, status transitions, AI decomposition      |
| `checkin_service`      | Proactive check-in scheduling and responses          |
| `ai_service`           | Multi-provider AI calls (OpenAI/Anthropic/Ollama)    |
| `skill_service`        | Skill graph inference, gap analysis, learning paths  |
| `prediction_service`   | Delivery forecasting, velocity trends, risk scoring  |
| `unblock_service`      | RAG-powered blocker resolution                       |
| `automation_service`   | Pattern detection, rule creation                     |
| `workforce_service`    | Employee scoring, org health, simulations            |
| `notification_service` | Push notifications, email dispatch                   |
| `analytics_service`    | Metrics aggregation, reporting                       |

### AI Provider Configuration

The backend supports multiple AI providers via `AI_PROVIDER` env var:

```python
# backend/app/config.py
AI_PROVIDER = "ollama"  # Options: mock, openai, anthropic, ollama, mistral, kimi
```

Each provider implements the same interface in `ai_service.py`, making them interchangeable.

---

## Frontend Workflow

### Page → Service → API Flow

```
Page Component (React)
    │
    │  useQuery / useMutation (TanStack Query)
    v
Service (services/*.service.ts)
    │
    │  apiClient.get/post/put/delete (Axios)
    v
API Client (lib/api-client.ts)
    │  - Base URL: /api/v1
    │  - Auth header injection
    │  - Token refresh on 401
    v
Backend API
```

### State Management

| Store        | Purpose                          | Persistence       |
|--------------|----------------------------------|--------------------|
| `authStore`  | User auth, tokens, login/logout  | localStorage       |
| `themeStore` | Light/dark mode                  | localStorage       |
| `uiStore`    | Sidebar state, modals            | In-memory          |

### Frontend Pages

| Page                    | Route                | Purpose                              |
|-------------------------|----------------------|--------------------------------------|
| LandingPage             | `/`                  | Public marketing page                |
| LoginPage               | `/login`             | User authentication                  |
| SignupPage               | `/signup`            | User registration                    |
| Dashboard               | `/dashboard`         | Overview metrics, charts, widgets    |
| TasksPage               | `/tasks`             | Kanban/List/Timeline + inline AI creation |
| CheckInsPage            | `/checkins`          | Check-in management and responses    |
| AICommandCenter         | `/ai`                | General AI help, issue resolution    |
| SkillsPage              | `/skills`            | Skill graphs, gaps, learning paths   |
| PredictionsPage         | `/predictions`       | Delivery forecasts, risk analysis    |
| WorkforcePage           | `/workforce`         | Employee scores, org health          |
| AutomationPage          | `/automation`        | Automation rules, pattern detection  |
| AnalyticsPage           | `/analytics`         | Advanced reporting and analytics     |
| KnowledgeBasePage       | `/knowledge`         | Document management for RAG          |
| TeamPage                | `/team`              | Team member management               |
| IntegrationsPage        | `/integrations`      | Third-party connections              |
| OrganizationSettingsPage| `/organization`      | Organization configuration           |
| AdminPage               | `/admin`             | System administration                |
| SettingsPage            | `/settings`          | User preferences                     |

---

## AI Agent System

### Agent Architecture

```
User Request
    │
    v
Chat Router (api/v1/chat.py)
    │
    v
ChatAgent (agents/conversation/chat_agent.py)
    │  - Conversation state management
    │  - Multi-turn dialog
    │  - Task creation flow
    v
Orchestrator (agents/orchestrator.py)
    │
    ├── DecomposerAgent    → Breaks tasks into subtasks
    ├── PredictorAgent     → Estimates delivery timelines
    ├── SkillMatcherAgent  → Matches skills to assignments
    ├── CoachAgent         → Provides mentoring guidance
    └── UnblockAgent       → Resolves blockers via RAG
```

### Two AI Surfaces

1. **Tasks Page (Inline Dialog)** - For **creating tasks only**
   - User describes a task via text or file upload
   - AI asks follow-up questions (deadline, priority, dependencies)
   - AI creates the task with subtasks automatically
   - All happens inside a dialog on the Tasks page

2. **AI Command Center (`/ai`)** - For **general assistance**
   - Ask about task status, get summaries
   - Get help resolving blockers
   - Analyze team productivity
   - Schedule meetings, manage automations
   - Proactive check-in prompts via WebSocket

### Conversational Task Creation Flow

```
User opens "Describe Your Task" dialog on Tasks page
    │
    v
User enters description (text or file upload)
    │
    v
AI asks: "What's the deadline?"
    │  (clickable suggestion badges)
    v
User replies
    │
    v
AI asks: "What priority level?"
    │
    v
AI asks: "Working hours per day?"
    │
    v
AI creates task with subtasks
    │
    v
Task list auto-refreshes via queryClient.invalidateQueries
```

---

## Authentication Flow

### Email/Password Login

```
1. User submits email + password
2. POST /api/v1/auth/login
3. Backend verifies credentials (bcrypt)
4. Returns { access_token, refresh_token, user }
5. Frontend stores tokens in authStore (localStorage)
6. Axios interceptor attaches Bearer token to all requests
7. On 401 → auto-refresh using refresh_token
```

### Google OAuth Login

```
1. Google Identity Services SDK loads on Login/Signup page
2. User clicks "Sign in with Google"
3. Google returns JWT credential
4. POST /api/v1/auth/google with { token: credential }
5. Backend verifies with google-auth library
6. Creates/finds user, returns access + refresh tokens
7. Frontend stores tokens, redirects to /dashboard
```

### Role-Based Access Control (RBAC)

```
Roles (hierarchical):
  SUPER_ADMIN  → Full system access
  ORG_ADMIN    → Organization-level admin
  MANAGER      → Team management
  TEAM_LEAD    → Team coordination
  EMPLOYEE     → Standard access
  VIEWER       → Read-only access
```

---

## Task Lifecycle

```
                 ┌─────────┐
                 │  CREATED │  (via AI or manual)
                 └────┬─────┘
                      │
                 ┌────v─────┐
                 │   TO DO  │
                 └────┬─────┘
                      │
              ┌───────v────────┐
              │  IN PROGRESS   │
              └───┬────────┬───┘
                  │        │
          ┌───────v──┐  ┌──v───────┐
          │ BLOCKED  │  │  REVIEW  │
          └───────┬──┘  └──┬───────┘
                  │        │
                  └───┬────┘
                 ┌────v─────┐
                 │   DONE   │
                 └──────────┘
```

### Status Transitions

- **To Do** → In Progress (developer starts)
- **In Progress** → Review (ready for review)
- **In Progress** → Blocked (hit a blocker → AI agent analyzes)
- **Blocked** → In Progress (blocker resolved)
- **Review** → Done (approved)
- **Review** → In Progress (changes requested)

### AI-Powered Task Decomposition

When a task is created via AI:
1. User describes the task in natural language
2. `DecomposerAgent` breaks it into subtasks
3. `PredictorAgent` estimates hours per subtask
4. `SkillMatcherAgent` suggests assignments
5. All subtasks are created as children of the parent task

---

## API Reference

### Base URL: `http://localhost:8000/api/v1`

### Authentication

| Method | Endpoint                | Description              |
|--------|-------------------------|--------------------------|
| POST   | `/auth/register`        | Create new account       |
| POST   | `/auth/login`           | Email/password login     |
| POST   | `/auth/google`          | Google OAuth login       |
| POST   | `/auth/refresh`         | Refresh access token     |
| POST   | `/auth/forgot-password` | Send password reset email|
| GET    | `/auth/me`              | Get current user profile |

### Tasks

| Method | Endpoint                       | Description                  |
|--------|--------------------------------|------------------------------|
| GET    | `/tasks`                       | List tasks (filter, search)  |
| POST   | `/tasks`                       | Create task                  |
| GET    | `/tasks/{id}`                  | Get task details             |
| PUT    | `/tasks/{id}`                  | Update task                  |
| DELETE | `/tasks/{id}`                  | Delete task                  |
| PATCH  | `/tasks/{id}/status`           | Update task status           |
| GET    | `/tasks/{id}/subtasks`         | Get subtasks                 |
| GET    | `/tasks/{id}/comments`         | Get task comments            |
| POST   | `/tasks/{id}/decompose`        | AI decompose into subtasks   |

### Chat

| Method | Endpoint                              | Description                    |
|--------|---------------------------------------|--------------------------------|
| POST   | `/chat`                               | Send chat message              |
| POST   | `/chat/with-file`                     | Send message with file upload  |
| GET    | `/chat/conversations`                 | List conversations             |
| GET    | `/chat/conversations/{id}`            | Get conversation details       |
| DELETE | `/chat/conversations/{id}`            | Delete conversation            |
| POST   | `/chat/conversations/{id}/end`        | End conversation               |
| WS     | `/chat/ws`                            | WebSocket for real-time events |

### Check-Ins

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/checkins`                 | List check-ins                 |
| POST   | `/checkins`                 | Create check-in                |
| POST   | `/checkins/{id}/respond`    | Respond to check-in            |

### Skills

| Method | Endpoint                   | Description                    |
|--------|----------------------------|--------------------------------|
| GET    | `/skills/graph`            | Get skill graph                |
| GET    | `/skills/gaps`             | Identify skill gaps            |
| GET    | `/skills/learning-path`    | Get learning recommendations   |
| GET    | `/skills/velocity`         | Get learning velocity metrics  |

### Predictions

| Method | Endpoint                   | Description                    |
|--------|----------------------------|--------------------------------|
| GET    | `/predictions/forecast`    | Get delivery forecasts         |
| GET    | `/predictions/velocity`    | Get velocity trends            |
| GET    | `/predictions/risks`       | Identify project risks         |

### Workforce

| Method | Endpoint                     | Description                    |
|--------|------------------------------|--------------------------------|
| GET    | `/workforce/scores`          | Employee engagement scores     |
| GET    | `/workforce/org-health`      | Organization health metrics    |
| GET    | `/workforce/simulations`     | Run workforce simulations      |

### Other Endpoints

| Module       | Endpoint Prefix     | Description                    |
|--------------|---------------------|--------------------------------|
| Automation   | `/automation`       | Rules, patterns, triggers      |
| AI Unblock   | `/ai/unblock`       | Blocker resolution             |
| Admin        | `/admin`            | System administration          |
| Organizations| `/organizations`    | Org management                 |
| Users        | `/users`            | User management                |
| Notifications| `/notifications`    | Notification management        |
| Integrations | `/integrations`     | Third-party connections        |
| Reports      | `/reports`          | Report generation              |
| Agents       | `/agents`           | AI agent management            |

---

## Database Schema

### Core Models

```
User
  ├── id (UUID, PK)
  ├── email (unique)
  ├── hashed_password
  ├── name
  ├── role (enum: SUPER_ADMIN, ORG_ADMIN, MANAGER, TEAM_LEAD, EMPLOYEE, VIEWER)
  ├── organization_id (FK)
  └── is_active, created_at, updated_at

Task
  ├── id (UUID, PK)
  ├── title, description
  ├── status (enum: TODO, IN_PROGRESS, REVIEW, BLOCKED, DONE)
  ├── priority (enum: LOW, MEDIUM, HIGH, URGENT)
  ├── assigned_to (FK → User)
  ├── created_by (FK → User)
  ├── parent_id (FK → Task, self-referential for subtasks)
  ├── deadline, estimated_hours
  ├── tags (JSON)
  └── created_at, updated_at

CheckIn
  ├── id (UUID, PK)
  ├── user_id (FK → User)
  ├── task_id (FK → Task)
  ├── status, response
  ├── friction_level
  └── scheduled_at, responded_at

Skill
  ├── id (UUID, PK)
  ├── name, category
  ├── user_id (FK → User)
  ├── level (float)
  └── verified, last_assessed_at

Organization
  ├── id (UUID, PK)
  ├── name, slug
  ├── settings (JSON)
  └── created_at
```

**Database:** SQLite for development (auto-created at `backend/taskpulse.db`), PostgreSQL for production.

---

## Deployment

### Docker Compose

```bash
docker-compose up --build
```

Services:
- **backend**: FastAPI on port 8000
- **frontend**: Vite build served via nginx on port 80

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Set a strong `SECRET_KEY` (min 32 chars)
- [ ] Configure `DATABASE_URL` for PostgreSQL
- [ ] Set `AI_PROVIDER` and corresponding API keys
- [ ] Configure `GOOGLE_CLIENT_ID` with production origins
- [ ] Set `CORS_ORIGINS` to production domain
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Build frontend: `cd Frontend && npm run build`

### Default Demo Credentials

| Role       | Email             | Password |
|------------|-------------------|----------|
| Admin      | admin@acme.com    | demo123  |
| Manager    | sarah@acme.com    | demo123  |
| Developer  | mike@acme.com     | demo123  |
| Developer  | emily@acme.com    | demo123  |

---

## Useful Commands

```bash
# Backend
cd backend
python run.py                          # Start server
python scripts/seed_data.py            # Seed demo data
pytest                                 # Run tests
pytest --cov=app                       # Run with coverage

# Frontend
cd Frontend
npm run dev                            # Start dev server (port 5173)
npx vite build                         # Production build
npx tsc --noEmit                       # Type check (no output)

# Git
git status
git log --oneline -10
```
