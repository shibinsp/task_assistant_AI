# TaskPulse AI - Project Rules

## Issue & PR Workflow (Mandatory)

**Every bug fix, feature, or improvement MUST follow this workflow:**

1. **Create a GitHub Issue first** - Describe the problem/feature with clear title and details
2. **Create a feature branch** from `main` (e.g., `fix/issue-42-redact-secrets`)
3. **Fix the issue** on the branch
4. **Create a Pull Request** linking the issue (use `Fixes #<number>` in the PR body)
5. **Never push directly to `main`** - all changes go through PRs

### Branch Naming Convention
- Bug fixes: `fix/<issue-number>-<short-description>`
- Features: `feat/<issue-number>-<short-description>`
- Refactors: `refactor/<issue-number>-<short-description>`

### Commit Message Format
```
<type>: <short summary>

<optional detailed description>

Fixes #<issue-number>
```

Types: `fix`, `feat`, `refactor`, `docs`, `test`, `chore`

### Git Author Rules
- **Author name**: Always `shibinsp` — never use any other name
- **NEVER** add `Co-Authored-By` lines in commits — no Claude, no AI co-author tags
- Local git config must be: `user.name = shibinsp`

### PR Description Format
- Summary section with bullet points
- Test plan section
- Reference the issue with `Fixes #<number>`

## GitHub Configuration
- Remote: `shibinsp/task_assistant_AI`
- Push access requires `shibinsp` account (use `gh auth switch --user shibinsp` before pushing)
- Default branch: `main`

## Tech Stack
- **Frontend**: React 19, TypeScript 5.9, Vite 7, Tailwind CSS, Radix UI/shadcn
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0 async, SQLite (dev) / PostgreSQL (prod)
- **Auth**: JWT + bcrypt + Google OAuth 2.0
- **AI**: Multi-provider (OpenAI, Anthropic, Mistral, Kimi, Ollama, mock)

## Security Rules
- Never expose secrets (passwords, tokens, API keys) in API responses - always redact
- All automation endpoints require appropriate permission checks (AUTOMATION_VIEW, AUTOMATION_MANAGE)
- System audit fields (triggered_by, trigger_type) must not be overridable by user input
- Always add logging imports when using logger in exception handlers
