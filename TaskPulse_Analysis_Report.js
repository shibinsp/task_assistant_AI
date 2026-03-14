const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat, TabStopType, TabStopPosition } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function makeCell(text, width, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, font: "Arial", size: 20, ...opts.runOpts })];
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: runs, spacing: { after: 0 } })],
  });
}

function makeRow(cells, widths, opts = {}) {
  return new TableRow({
    children: cells.map((c, i) => makeCell(c, widths[i], { shading: opts.shading, runOpts: opts.runOpts })),
  });
}

function heading(text, level) {
  return new Paragraph({ heading: level, children: [new TextRun({ text, font: "Arial" })], spacing: { before: 240, after: 120 } });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 20, ...opts })],
    spacing: { after: 120 },
  });
}

function boldPara(label, text) {
  return new Paragraph({
    children: [
      new TextRun({ text: label, font: "Arial", size: 20, bold: true }),
      new TextRun({ text, font: "Arial", size: 20 }),
    ],
    spacing: { after: 120 },
  });
}

function bulletItem(text, ref) {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    children: [new TextRun({ text, font: "Arial", size: 20 })],
    spacing: { after: 60 },
  });
}

function severityCell(text, width, level) {
  const colors = { critical: "FFD7D7", high: "FFE8CC", medium: "FFF3CC", low: "D7F0D7", info: "D5E8F0" };
  return makeCell(text, width, { shading: colors[level] || "FFFFFF", runOpts: { bold: true } });
}

// Build document
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1B3A5C" },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5984" },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "3A7AB5" },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets2", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets3", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets4", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets5", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets6", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets7", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets8", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers1", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        children: [
          new TextRun({ text: "TaskPulse AI \u2014 Comprehensive Application Analysis", font: "Arial", size: 16, color: "888888" }),
          new TextRun({ text: "\tMarch 13, 2026", font: "Arial", size: 16, color: "888888" }),
        ],
        tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2E5984", space: 4 } },
      })] }),
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Page ", font: "Arial", size: 16, color: "888888" }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" })],
      })] }),
    },
    children: [
      // ===== TITLE PAGE =====
      new Paragraph({ spacing: { before: 2400 } }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "TaskPulse \u2014 AI Assistant", font: "Arial", size: 48, bold: true, color: "1B3A5C" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Comprehensive Application Analysis Report", font: "Arial", size: 28, color: "2E5984" })],
        spacing: { after: 360 },
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 6, color: "2E5984", space: 8 } },
        children: [new TextRun({ text: "Architecture \u2022 Security \u2022 AI/LLM Integration \u2022 Performance \u2022 Code Quality", font: "Arial", size: 20, color: "666666" })],
        spacing: { before: 240, after: 600 },
      }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Prepared: March 13, 2026", font: "Arial", size: 20, color: "666666" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Analyst: Claude (AI-Assisted Security & Architecture Review)", font: "Arial", size: 20, color: "666666" })], spacing: { after: 120 } }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Codebase: 97 Python files (34,604 LOC) + 105 TypeScript files (25,446 LOC)", font: "Arial", size: 20, color: "666666" })], spacing: { after: 120 } }),

      // ===== EXECUTIVE SUMMARY =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("1. Executive Summary", HeadingLevel.HEADING_1),
      para("TaskPulse AI is a full-stack enterprise workforce productivity platform built with FastAPI (Python 3.14) and React/TypeScript. It combines task management with AI-powered features including intelligent check-ins, unblock suggestions, task decomposition, skill inference, and delivery prediction. The application includes a multi-agent orchestration system with 6 specialized AI agents."),
      para("This analysis covers 202 source files totaling ~60,000 lines of code across backend API, frontend SPA, multi-agent system, and supporting infrastructure. The review was conducted with a focus on enterprise deployment readiness, zero-hallucination AI integration, and security hardening."),

      heading("Overall Assessment", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2800, 1600, 4960],
        rows: [
          makeRow(["Dimension", "Rating", "Summary"], [2800, 1600, 4960], { shading: "2E5984", runOpts: { color: "FFFFFF", bold: true } }),
          makeRow(["Architecture", "B+", "Clean layered design with async-first patterns. Multi-agent system is well-structured."], [2800, 1600, 4960]),
          makeRow(["Security", "B", "Solid foundation (CSRF, rate limiting, RBAC). Several hardening items needed for production."], [2800, 1600, 4960]),
          makeRow(["AI/LLM Safety", "B-", "Input sanitization present. Needs output validation, confidence calibration, and guardrails."], [2800, 1600, 4960]),
          makeRow(["Performance", "C+", "SQLite bottleneck for production. In-memory rate limiting won't scale horizontally."], [2800, 1600, 4960]),
          makeRow(["Code Quality", "B+", "Consistent patterns, good error handling. Some type safety gaps and missing tests."], [2800, 1600, 4960]),
          makeRow(["Production Readiness", "C+", "Several blockers: SECRET_KEY persistence, no migrations, SQLite limitation."], [2800, 1600, 4960]),
        ],
      }),

      // ===== ARCHITECTURE =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("2. Backend Architecture Analysis", HeadingLevel.HEADING_1),

      heading("2.1 Technology Stack", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 6960],
        rows: [
          makeRow(["Component", "Technology"], [2400, 6960], { shading: "D5E8F0", runOpts: { bold: true } }),
          makeRow(["Web Framework", "FastAPI 0.100+ with async/await, Pydantic v2 settings"], [2400, 6960]),
          makeRow(["Database", "SQLAlchemy 2.0 async + SQLite (aiosqlite) with WAL mode"], [2400, 6960]),
          makeRow(["Authentication", "JWT (HS256) via python-jose, bcrypt password hashing"], [2400, 6960]),
          makeRow(["AI Providers", "Mock, Mistral, Kimi (Moonshot), Ollama (OpenAI-compatible)"], [2400, 6960]),
          makeRow(["Frontend", "React 18 + TypeScript + Vite + Zustand + React Query + Chakra UI"], [2400, 6960]),
          makeRow(["API Client", "Axios with CSRF interceptor and 401 token refresh queue"], [2400, 6960]),
        ],
      }),

      heading("2.2 API Design", HeadingLevel.HEADING_2),
      para("The API follows RESTful conventions with 16 router modules mounted under /api/v1/. Each module covers a distinct domain: auth, users, organizations, tasks, checkins, AI, skills, predictions, automation, workforce, notifications, integrations, reports, admin, agents, and chat."),

      heading("Strengths", HeadingLevel.HEADING_3),
      bulletItem("Clean separation of concerns with service layer pattern (e.g., AuthService, AIService)", "bullets"),
      bulletItem("Consistent error handling via TaskPulseException with error codes and request IDs", "bullets"),
      bulletItem("RBAC dependency injection with require_roles() factory pattern", "bullets"),
      bulletItem("Organization-scoped data access via OrgAccessChecker dependency", "bullets"),
      bulletItem("Pydantic v2 settings with env file support and production validation", "bullets"),

      heading("Issues Found", HeadingLevel.HEADING_3),
      bulletItem("DB commit timing: get_db() commits after yield, but HTTP response sends before cleanup. Registration flow required explicit await db.commit() to prevent login failures (already fixed).", "bullets2"),
      bulletItem("No database migration system (Alembic not configured). Schema changes require manual DB recreation.", "bullets2"),
      bulletItem("datetime.utcnow() used throughout (deprecated in Python 3.12+). Should use datetime.now(timezone.utc).", "bullets2"),
      bulletItem("failed_login_attempts stored as string (should be integer column).", "bullets2"),

      heading("2.3 Multi-Agent System", HeadingLevel.HEADING_2),
      para("The application includes a sophisticated multi-agent orchestration system with 6 agents: ChatAgent, UnblockAgent, DecomposerAgent, PredictorAgent, SkillMatcherAgent, and CoachAgent."),
      bulletItem("Event bus with publish/subscribe pattern and priority-based routing", "bullets3"),
      bulletItem("Pipeline execution (sequential) and parallel execution modes", "bullets3"),
      bulletItem("Chain depth limiting (max 5) to prevent infinite agent loops", "bullets3"),
      bulletItem("Execution history tracking with bounded buffer (1000 records)", "bullets3"),
      bulletItem("Graceful degradation: agent initialization failures are non-fatal warnings", "bullets3"),

      // ===== SECURITY =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("3. Security Audit", HeadingLevel.HEADING_1),

      heading("3.1 Findings Summary", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 1400, 4560, 2600],
        rows: [
          makeRow(["#", "Severity", "Finding", "Status"], [800, 1400, 4560, 2600], { shading: "2E5984", runOpts: { color: "FFFFFF", bold: true } }),
          new TableRow({ children: [
            makeCell("S1", 800), severityCell("CRITICAL", 1400, "critical"),
            makeCell("SECRET_KEY regenerated on every restart, invalidating all sessions", 4560),
            makeCell("Fix: Add to .env", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S2", 800), severityCell("HIGH", 1400, "high"),
            makeCell("JWT tokens in localStorage vulnerable to XSS (no httpOnly cookies)", 4560),
            makeCell("Documented tradeoff", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S3", 800), severityCell("HIGH", 1400, "high"),
            makeCell("No Content-Security-Policy header (CSP) configured", 4560),
            makeCell("Not implemented", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S4", 800), severityCell("MEDIUM", 1400, "medium"),
            makeCell("In-memory rate limiting lost on restart, no distributed support", 4560),
            makeCell("Needs Redis", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S5", 800), severityCell("MEDIUM", 1400, "medium"),
            makeCell("Password reset tokens are JWT-based, not single-use DB tokens", 4560),
            makeCell("Design gap", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S6", 800), severityCell("MEDIUM", 1400, "medium"),
            makeCell("Email enumeration partially mitigated (reset OK, registration leaks)", 4560),
            makeCell("Partial fix", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S7", 800), severityCell("LOW", 1400, "low"),
            makeCell("CORS origins hardcoded to localhost; needs env-based config for deploy", 4560),
            makeCell("Config needed", 2600),
          ]}),
          new TableRow({ children: [
            makeCell("S8", 800), severityCell("LOW", 1400, "low"),
            makeCell("API docs auto-enabled in development (correct), but no auth gate", 4560),
            makeCell("Acceptable", 2600),
          ]}),
        ],
      }),

      heading("3.2 Security Controls Implemented", HeadingLevel.HEADING_2),
      boldPara("CSRF Protection (SEC-006): ", "Double-submit cookie pattern with hmac.compare_digest validation. State-changing methods (POST/PUT/PATCH/DELETE) require X-CSRF-Token header matching csrf_token cookie. Auth endpoints exempted. SameSite=strict in production."),
      boldPara("Rate Limiting (SEC-002): ", "Three-tier sliding window: auth endpoints (10 req/60s), AI endpoints (30 req/60s), general (100 req/60s). Per-IP tracking with stale entry eviction."),
      boldPara("Account Lockout (SEC-014): ", "Progressive lockout: 5 failures = 15 min, 10 = 1 hour, 15+ = 4 hours. Resets on successful login."),
      boldPara("Input Sanitization (SEC-004): ", "sanitize_user_input() strips control characters and common prompt injection patterns before AI provider calls."),
      boldPara("Security Headers: ", "X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection, Referrer-Policy, HSTS (production only)."),
      boldPara("RBAC: ", "6-tier role hierarchy (super_admin through viewer) with dependency-based enforcement. OrgAccessChecker ensures cross-org isolation."),
      boldPara("Production Validation: ", "Rejects startup without explicit SECRET_KEY, enforces DEBUG=False, warns on SQLite usage."),

      // ===== AI/LLM SECURITY =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("4. AI/LLM Integration Security & Hallucination Analysis", HeadingLevel.HEADING_1),

      para("Given your requirement for 0% hallucination in enterprise AI, this section is critical. TaskPulse uses AI for task decomposition, unblock suggestions, skill inference, and delivery predictions."),

      heading("4.1 Current Safeguards", HeadingLevel.HEADING_2),
      bulletItem("Input sanitization: sanitize_user_input() removes control characters and injection patterns (e.g., 'ignore previous instructions', 'system:', prompt delimiters)", "bullets4"),
      bulletItem("Confidence scores: All AI outputs include confidence values (0.0-1.0) for downstream filtering", "bullets4"),
      bulletItem("Mock provider: Default AI_PROVIDER='mock' ensures the app works without any LLM configured", "bullets4"),
      bulletItem("Graceful degradation: Provider failures fall back to mock responses with clear indicators", "bullets4"),
      bulletItem("Cache with bounded size: LRU cache (max 1000 entries) with SHA-256 keys prevents unbounded memory growth", "bullets4"),

      heading("4.2 Critical Gaps for Enterprise Zero-Hallucination", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 1200, 5160, 2200],
        rows: [
          makeRow(["#", "Severity", "Gap", "Recommendation"], [800, 1200, 5160, 2200], { shading: "2E5984", runOpts: { color: "FFFFFF", bold: true } }),
          new TableRow({ children: [
            makeCell("A1", 800), severityCell("CRITICAL", 1200, "critical"),
            makeCell("No output validation/guardrails. AI responses are passed directly to clients without schema validation or factuality checks.", 5160),
            makeCell("Add output schema validation + content filter", 2200),
          ]}),
          new TableRow({ children: [
            makeCell("A2", 800), severityCell("CRITICAL", 1200, "critical"),
            makeCell("No grounding/RAG verification. Unblock suggestions claim to be RAG-powered but don't verify against source documents.", 5160),
            makeCell("Implement source attribution with citation verification", 2200),
          ]}),
          new TableRow({ children: [
            makeCell("A3", 800), severityCell("HIGH", 1200, "high"),
            makeCell("Confidence scores are AI-self-reported, not calibrated. A model saying '0.85 confidence' doesn't mean 85% accuracy.", 5160),
            makeCell("Add calibration layer or use separate validator model", 2200),
          ]}),
          new TableRow({ children: [
            makeCell("A4", 800), severityCell("HIGH", 1200, "high"),
            makeCell("No prompt injection defense on output side. AI could be tricked into generating harmful instructions in responses.", 5160),
            makeCell("Add output scanning for injection artifacts", 2200),
          ]}),
          new TableRow({ children: [
            makeCell("A5", 800), severityCell("MEDIUM", 1200, "medium"),
            makeCell("AI cache keyed by input hash only. Same question always returns cached answer even if context has changed.", 5160),
            makeCell("Add context-aware cache invalidation", 2200),
          ]}),
          new TableRow({ children: [
            makeCell("A6", 800), severityCell("MEDIUM", 1200, "medium"),
            makeCell("No rate limiting per user for AI endpoints (only per IP). Shared offices could hit limits unfairly.", 5160),
            makeCell("Add per-user token bucket for AI calls", 2200),
          ]}),
        ],
      }),

      heading("4.3 Recommendations for Zero-Hallucination", HeadingLevel.HEADING_2),
      new Paragraph({
        numbering: { reference: "numbers1", level: 0 },
        children: [new TextRun({ text: "Output Schema Validation: ", bold: true, font: "Arial", size: 20 }), new TextRun({ text: "Validate all AI responses against Pydantic schemas before returning to clients. Reject responses that don't match expected structure.", font: "Arial", size: 20 })],
        spacing: { after: 80 },
      }),
      new Paragraph({
        numbering: { reference: "numbers1", level: 0 },
        children: [new TextRun({ text: "Citation Verification: ", bold: true, font: "Arial", size: 20 }), new TextRun({ text: "For RAG-powered suggestions, verify that cited sources actually exist and contain the claimed information. Return 'unable to verify' rather than ungrounded claims.", font: "Arial", size: 20 })],
        spacing: { after: 80 },
      }),
      new Paragraph({
        numbering: { reference: "numbers1", level: 0 },
        children: [new TextRun({ text: "Confidence Calibration: ", bold: true, font: "Arial", size: 20 }), new TextRun({ text: "Replace self-reported confidence with calibrated scores based on historical accuracy. Track prediction vs. outcome and adjust calibration curves.", font: "Arial", size: 20 })],
        spacing: { after: 80 },
      }),
      new Paragraph({
        numbering: { reference: "numbers1", level: 0 },
        children: [new TextRun({ text: "Human-in-the-Loop: ", bold: true, font: "Arial", size: 20 }), new TextRun({ text: "For high-stakes AI actions (task decomposition, automation triggers), require explicit user confirmation. Never auto-execute AI-generated actions.", font: "Arial", size: 20 })],
        spacing: { after: 80 },
      }),
      new Paragraph({
        numbering: { reference: "numbers1", level: 0 },
        children: [new TextRun({ text: "Audit Trail: ", bold: true, font: "Arial", size: 20 }), new TextRun({ text: "Log all AI inputs/outputs with timestamps, user IDs, and provider metadata. This enables post-hoc analysis of hallucination incidents.", font: "Arial", size: 20 })],
        spacing: { after: 80 },
      }),

      // ===== PERFORMANCE =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("5. Performance & Scalability Analysis", HeadingLevel.HEADING_1),

      heading("5.1 Database Layer", HeadingLevel.HEADING_2),
      boldPara("Current: ", "SQLite with WAL journal mode and foreign keys enabled. Async via aiosqlite."),
      boldPara("Issue: ", "SQLite has a single-writer lock. Under concurrent load, write operations serialize. WAL mode helps reads but doesn't solve write contention. The config warns about this in production validation but doesn't block deployment."),
      boldPara("Recommendation: ", "Migrate to PostgreSQL with asyncpg for production. The config already supports DATABASE_URL override. Add Alembic for schema migrations."),

      heading("5.2 Rate Limiting", HeadingLevel.HEADING_2),
      boldPara("Current: ", "In-memory sliding window per IP. Timestamps stored in Python lists."),
      boldPara("Issues: ", "Lost on server restart. Doesn't work across multiple workers/instances. No per-user limiting. Lists grow unbounded within windows (no pre-allocation)."),
      boldPara("Recommendation: ", "Replace with Redis-backed sliding window (e.g., redis-py with MULTI/EXEC). Add per-user token buckets for AI endpoints."),

      heading("5.3 AI Service", HeadingLevel.HEADING_2),
      boldPara("Current: ", "Synchronous HTTP calls to AI providers within async handlers. LRU cache with SHA-256 keys."),
      boldPara("Issues: ", "No request timeouts on AI provider calls (could hang indefinitely). Cache eviction is O(n) scan. No circuit breaker for provider failures."),
      boldPara("Recommendation: ", "Add httpx timeouts (connect=5s, read=30s). Implement circuit breaker pattern. Consider async streaming for long AI responses."),

      heading("5.4 Frontend", HeadingLevel.HEADING_2),
      bulletItem("React Query provides automatic caching, deduplication, and background refetching", "bullets5"),
      bulletItem("Token refresh queue prevents thundering herd on 401 responses", "bullets5"),
      bulletItem("Zustand stores are lightweight and don't cause unnecessary re-renders", "bullets5"),
      bulletItem("Consider: Code splitting for the 17 route pages (currently all bundled)", "bullets5"),
      bulletItem("Consider: Virtual scrolling for task lists that could grow large", "bullets5"),

      // ===== CODE QUALITY =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("6. Code Quality & Optimization", HeadingLevel.HEADING_1),

      heading("6.1 Strengths", HeadingLevel.HEADING_2),
      bulletItem("Consistent SEC-XXX security annotation system throughout codebase (17+ annotated items)", "bullets6"),
      bulletItem("Clean dependency injection via FastAPI Depends() with composable security chains", "bullets6"),
      bulletItem("Well-structured error hierarchy with domain-specific exception classes", "bullets6"),
      bulletItem("API client with proper interceptor pattern for auth token lifecycle", "bullets6"),
      bulletItem("Multi-agent system with clean separation: base, context, event bus, orchestrator", "bullets6"),
      bulletItem("Request ID tracing through entire request lifecycle for debugging", "bullets6"),

      heading("6.2 Issues & Optimization Opportunities", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 1200, 4960, 2400],
        rows: [
          makeRow(["#", "Priority", "Issue", "Fix"], [800, 1200, 4960, 2400], { shading: "2E5984", runOpts: { color: "FFFFFF", bold: true } }),
          new TableRow({ children: [
            makeCell("C1", 800), severityCell("HIGH", 1200, "high"),
            makeCell("No test suite. Zero unit/integration tests found in the codebase.", 4960),
            makeCell("Add pytest + httpx for API tests", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C2", 800), severityCell("HIGH", 1200, "high"),
            makeCell("No database migrations (Alembic). Schema changes require manual DB recreation.", 4960),
            makeCell("Initialize Alembic with autogenerate", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C3", 800), severityCell("MEDIUM", 1200, "medium"),
            makeCell("datetime.utcnow() deprecated in Python 3.12+. Used throughout codebase.", 4960),
            makeCell("Replace with datetime.now(timezone.utc)", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C4", 800), severityCell("MEDIUM", 1200, "medium"),
            makeCell("failed_login_attempts stored as string type instead of integer.", 4960),
            makeCell("Change to Integer column", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C5", 800), severityCell("MEDIUM", 1200, "medium"),
            makeCell("Consent data stored as JSON string, not structured columns.", 4960),
            makeCell("Add typed JSON column or separate table", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C6", 800), severityCell("LOW", 1200, "low"),
            makeCell("Missing .env.example with documented configuration variables.", 4960),
            makeCell("Create from Settings class", 2400),
          ]}),
          new TableRow({ children: [
            makeCell("C7", 800), severityCell("LOW", 1200, "low"),
            makeCell("Organization slug generation has unbounded while loop for uniqueness.", 4960),
            makeCell("Add max iterations or UUID suffix fallback", 2400),
          ]}),
        ],
      }),

      // ===== PRODUCTION READINESS =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("7. Production Deployment Checklist", HeadingLevel.HEADING_1),

      para("Based on the analysis, here are the items required before production deployment, ordered by priority:"),

      heading("7.1 Blockers (Must Fix)", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 5960, 2600],
        rows: [
          makeRow(["#", "Item", "Effort"], [800, 5960, 2600], { shading: "FFD7D7", runOpts: { bold: true } }),
          makeRow(["P0", "Set SECRET_KEY in .env (sessions invalidate on restart without this)", "30 minutes"], [800, 5960, 2600]),
          makeRow(["P0", "Replace SQLite with PostgreSQL for concurrent write support", "2-4 hours"], [800, 5960, 2600]),
          makeRow(["P0", "Add Alembic database migrations", "2-3 hours"], [800, 5960, 2600]),
          makeRow(["P0", "Configure CORS_ORIGINS for production domain", "30 minutes"], [800, 5960, 2600]),
          makeRow(["P0", "Add AI output validation schemas (prevent hallucinated structure)", "4-6 hours"], [800, 5960, 2600]),
        ],
      }),

      heading("7.2 High Priority (Should Fix)", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 5960, 2600],
        rows: [
          makeRow(["#", "Item", "Effort"], [800, 5960, 2600], { shading: "FFE8CC", runOpts: { bold: true } }),
          makeRow(["P1", "Add Content-Security-Policy header", "2-3 hours"], [800, 5960, 2600]),
          makeRow(["P1", "Replace in-memory rate limiter with Redis", "3-4 hours"], [800, 5960, 2600]),
          makeRow(["P1", "Add pytest test suite (minimum: auth, task CRUD, AI endpoints)", "8-16 hours"], [800, 5960, 2600]),
          makeRow(["P1", "Add httpx timeouts for AI provider calls", "1-2 hours"], [800, 5960, 2600]),
          makeRow(["P1", "Implement AI output scanning for injection artifacts", "3-4 hours"], [800, 5960, 2600]),
        ],
      }),

      heading("7.3 Medium Priority (Plan For)", HeadingLevel.HEADING_2),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [800, 5960, 2600],
        rows: [
          makeRow(["#", "Item", "Effort"], [800, 5960, 2600], { shading: "FFF3CC", runOpts: { bold: true } }),
          makeRow(["P2", "Migrate from localStorage JWT to httpOnly cookies", "4-6 hours"], [800, 5960, 2600]),
          makeRow(["P2", "Add confidence calibration for AI predictions", "8-16 hours"], [800, 5960, 2600]),
          makeRow(["P2", "Replace datetime.utcnow() with timezone-aware calls", "2-3 hours"], [800, 5960, 2600]),
          makeRow(["P2", "Add circuit breaker for AI provider failures", "2-3 hours"], [800, 5960, 2600]),
          makeRow(["P2", "Implement code splitting for frontend routes", "2-4 hours"], [800, 5960, 2600]),
          makeRow(["P2", "Add AI input/output audit logging", "3-4 hours"], [800, 5960, 2600]),
        ],
      }),

      // ===== CONCLUSION =====
      new Paragraph({ children: [new PageBreak()] }),
      heading("8. Conclusion", HeadingLevel.HEADING_1),
      para("TaskPulse AI demonstrates solid architectural foundations with clean separation of concerns, a well-designed multi-agent system, and thoughtful security annotations throughout the codebase. The SEC-XXX annotation system shows security was considered during development, not bolted on afterward."),
      para("The primary concerns for enterprise deployment center on three areas: (1) infrastructure readiness (SQLite to PostgreSQL, persistent SECRET_KEY, database migrations), (2) AI safety for zero-hallucination requirements (output validation, grounding verification, confidence calibration), and (3) horizontal scalability (Redis-backed rate limiting, distributed session management)."),
      para("The codebase is well-organized and follows consistent patterns, making the recommended changes straightforward to implement. The estimated total effort for all P0 blockers is approximately 1-2 developer days, with P1 items requiring an additional 2-3 days. This positions TaskPulse well for a production deployment within a 1-2 week hardening sprint."),

      new Paragraph({ spacing: { before: 480 } }),
      new Paragraph({
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "2E5984", space: 8 } },
        children: [new TextRun({ text: "End of Report", font: "Arial", size: 20, italics: true, color: "888888" })],
        alignment: AlignmentType.CENTER,
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/wizardly-modest-johnson/mnt/task_assistant_AI/TaskPulse_Analysis_Report.docx", buffer);
  console.log("Report created successfully");
});
