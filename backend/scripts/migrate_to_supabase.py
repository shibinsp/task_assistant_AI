#!/usr/bin/env python3
"""
TaskPulse AI - SQLite to Supabase (PostgreSQL + Auth) Migration Script

Migrates all data from the existing SQLite database to Supabase PostgreSQL,
creates Supabase Auth users, and preserves all relationships.

Usage:
    python -m scripts.migrate_to_supabase \
        --sqlite-url sqlite+aiosqlite:///./taskpulse.db \
        --pg-url postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres \
        --supabase-url https://xxx.supabase.co \
        --service-role-key eyJ... \
        [--dry-run] [--skip-auth] [--batch-size 500]

Tables are inserted in topological order to satisfy FK constraints.
Self-referential FKs use a two-pass strategy (insert with NULL, then update).
"""

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Optional

import aiosqlite

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("migrate")

# ---------------------------------------------------------------------------
# Topological table ordering (FK-dependency sorted)
# ---------------------------------------------------------------------------

# Phase 1: No FK dependencies (root tables)
PHASE_1_TABLES = [
    "organizations",
    "system_health",
]

# Phase 2: Depends only on organizations
PHASE_2_TABLES = [
    "users",            # FK: organizations; self-ref: manager_id (deferred)
    "skills",           # FK: organizations
]

# Phase 3: Depends on users + organizations
PHASE_3_TABLES = [
    # "sessions" removed — Supabase Auth manages sessions now; table no longer exists
    "tasks",                   # FK: organizations, users x2; self-ref: parent_task_id (deferred)
    "agents",                  # FK: organizations
    "automation_patterns",     # FK: organizations, users
    "integrations",            # FK: organizations, users
    "webhooks",                # FK: organizations, users
    "notification_preferences",# FK: users, organizations
    "workforce_scores",        # FK: users, organizations
    "manager_effectiveness",   # FK: users, organizations
    "org_health_snapshots",    # FK: organizations
    "restructuring_scenarios", # FK: organizations, users
    "user_skills",             # FK: users, skills, organizations
    "skill_gaps",              # FK: users, skills, organizations
    "skill_metrics",           # FK: users, organizations
    "learning_paths",          # FK: users, organizations
    "audit_logs",              # FK: organizations
    "gdpr_requests",           # FK: organizations, users x2
    "api_keys",                # FK: organizations, users x2
    "velocity_snapshots",      # FK: organizations
]

# Phase 4: Depends on tasks, agents, etc.
PHASE_4_TABLES = [
    "task_dependencies",    # FK: tasks x2
    "task_history",         # FK: tasks, users
    "task_comments",        # FK: tasks, users
    "checkins",             # FK: tasks, users, organizations
    "checkin_configs",      # FK: organizations, users, tasks
    "documents",            # FK: organizations
    "ai_agents",            # FK: organizations, automation_patterns, users x2
    "predictions",          # FK: organizations, tasks, users
    "notifications",        # FK: users, organizations, tasks, checkins
    "webhook_deliveries",   # FK: webhooks, organizations
    "agent_executions",     # FK: agents, organizations, users, tasks; self-ref: parent_execution_id
    "agent_conversations",  # FK: organizations, users
    "agent_schedules",      # FK: agents, organizations
]

# Phase 5: Depends on documents, checkins
PHASE_5_TABLES = [
    "document_chunks",   # FK: documents
    "unblock_sessions",  # FK: organizations, users, tasks, checkins
    "checkin_reminders", # FK: checkins, users
    "agent_runs",        # FK: ai_agents, organizations
]

ALL_PHASES = [
    ("Phase 1: Root tables", PHASE_1_TABLES),
    ("Phase 2: Orgs → Users/Skills", PHASE_2_TABLES),
    ("Phase 3: Users → dependent tables", PHASE_3_TABLES),
    ("Phase 4: Tasks/Agents → dependent tables", PHASE_4_TABLES),
    ("Phase 5: Deep dependencies", PHASE_5_TABLES),
]

# Self-referential FK columns that must be set to NULL on first pass
# then updated in a second pass
SELF_REF_COLUMNS = {
    "users": "manager_id",
    "tasks": "parent_task_id",
    "agent_executions": "parent_execution_id",
}

# Columns that store JSON as TEXT in SQLite and need to be parsed to dicts/lists
# for JSONB insertion into PostgreSQL.  Maps table -> list of column names.
JSON_TEXT_COLUMNS: dict[str, list[str]] = {
    "users": ["consent_data"],
    "organizations": ["settings_data"],
    "tasks": ["tools", "tags", "skills_required"],
    "task_history": ["details"],
    "documents": ["team_ids", "tags", "categories"],
    "document_chunks": ["chunk_metadata"],
    "unblock_sessions": ["sources"],
    "automation_patterns": ["automation_recipe", "triggers", "actions"],
    "ai_agents": ["config", "permissions"],
    "agent_runs": ["input_data", "output_data", "human_action"],
    "notifications": ["action_data"],
    "integrations": ["config", "credentials"],
    "webhooks": ["events", "headers"],
    "webhook_deliveries": ["payload"],
    "predictions": ["risk_factors", "features"],
    "audit_logs": ["old_value", "new_value", "audit_metadata"],
    "api_keys": ["scopes"],
    "system_health": ["active_alerts"],
    "restructuring_scenarios": ["config", "risk_factors"],
    "skills": ["aliases", "related_skills", "prerequisites"],
    "user_skills": ["level_history"],
    "skill_gaps": ["learning_resources"],
    "learning_paths": ["skills_data", "milestones"],
    "agents": ["capabilities", "config", "permissions"],
    "agent_executions": ["context_data", "output_data"],
    "agent_conversations": ["messages", "context_data"],
    "agent_schedules": ["config"],
}

# Columns that were stored as TEXT-encoded floats list in SQLite (embeddings)
EMBEDDING_COLUMNS: dict[str, str] = {
    "document_chunks": "embedding",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_json_value(value: Any) -> Any:
    """Parse a JSON string value into a Python object."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value  # Already parsed
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value  # Return as-is if not valid JSON
    return value


def parse_embedding(value: Any) -> Optional[list[float]]:
    """Parse an embedding stored as JSON text into a list of floats."""
    if value is None:
        return None
    if isinstance(value, list):
        return [float(v) for v in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [float(v) for v in parsed]
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def coerce_uuid(value: Any) -> Optional[str]:
    """Ensure a value is a valid UUID string or None."""
    if value is None:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError):
        return str(value)


def transform_row(
    table_name: str,
    row: dict[str, Any],
    self_ref_col: Optional[str] = None,
) -> dict[str, Any]:
    """
    Transform a SQLite row dict for PostgreSQL insertion.

    - Parses JSON TEXT columns to Python objects (for JSONB).
    - Parses embedding columns to float lists (for pgvector).
    - Nullifies self-referential FK columns for first-pass insert.
    - Coerces UUID columns.
    """
    result = dict(row)

    # Parse JSON text columns
    json_cols = JSON_TEXT_COLUMNS.get(table_name, [])
    for col in json_cols:
        if col in result:
            result[col] = parse_json_value(result[col])

    # Parse embedding columns
    emb_col = EMBEDDING_COLUMNS.get(table_name)
    if emb_col and emb_col in result:
        result[emb_col] = parse_embedding(result[emb_col])

    # Nullify self-referential FK for first pass
    if self_ref_col and self_ref_col in result:
        # Store original value for second pass
        result[f"_orig_{self_ref_col}"] = result[self_ref_col]
        result[self_ref_col] = None

    return result


# ---------------------------------------------------------------------------
# SQLite reader
# ---------------------------------------------------------------------------

async def read_sqlite_table(
    sqlite_path: str,
    table_name: str,
) -> list[dict[str, Any]]:
    """Read all rows from a SQLite table as dicts."""
    async with aiosqlite.connect(sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        try:
            cursor = await db.execute(f"SELECT * FROM {table_name}")  # noqa: S608
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.warning("Could not read table '%s': %s", table_name, e)
            return []


async def get_sqlite_tables(sqlite_path: str) -> list[str]:
    """Get list of all tables in the SQLite database."""
    async with aiosqlite.connect(sqlite_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


# ---------------------------------------------------------------------------
# PostgreSQL writer (via asyncpg)
# ---------------------------------------------------------------------------

async def insert_rows_pg(
    pg_pool,
    table_name: str,
    rows: list[dict[str, Any]],
    batch_size: int = 500,
) -> int:
    """
    Insert rows into a PostgreSQL table using asyncpg.

    Returns the number of rows inserted.
    """
    if not rows:
        return 0

    # Get column names from first row (excluding our temp _orig_ columns)
    columns = [c for c in rows[0].keys() if not c.startswith("_orig_")]

    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]

        # Build INSERT statement with ON CONFLICT DO NOTHING
        placeholders = ", ".join(
            f"${j + 1}" for j in range(len(columns))
        )
        col_names = ", ".join(f'"{c}"' for c in columns)
        sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        async with pg_pool.acquire() as conn:
            for row in batch:
                values = []
                for col in columns:
                    val = row.get(col)
                    # Convert Python dicts/lists to JSON strings for asyncpg JSONB
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val)
                    # Convert embedding lists to the pgvector string format
                    if col == EMBEDDING_COLUMNS.get(table_name) and isinstance(val, list):
                        val = "[" + ",".join(str(f) for f in val) + "]"
                    values.append(val)
                try:
                    await conn.execute(sql, *values)
                    inserted += 1
                except Exception as e:
                    logger.error(
                        "Failed to insert row into %s (id=%s): %s",
                        table_name,
                        row.get("id", "?"),
                        e,
                    )
    return inserted


async def update_self_refs(
    pg_pool,
    table_name: str,
    self_ref_col: str,
    rows: list[dict[str, Any]],
) -> int:
    """Second-pass: update self-referential FK columns that were nulled on insert."""
    updated = 0
    sql = f'UPDATE "{table_name}" SET "{self_ref_col}" = $1 WHERE "id" = $2'

    async with pg_pool.acquire() as conn:
        for row in rows:
            orig_val = row.get(f"_orig_{self_ref_col}")
            if orig_val is not None:
                row_id = row.get("id")
                try:
                    await conn.execute(sql, orig_val, row_id)
                    updated += 1
                except Exception as e:
                    logger.error(
                        "Failed to update %s.%s for id=%s: %s",
                        table_name,
                        self_ref_col,
                        row_id,
                        e,
                    )
    return updated


# ---------------------------------------------------------------------------
# Supabase Auth user creation
# ---------------------------------------------------------------------------

async def create_supabase_auth_users(
    supabase_url: str,
    service_role_key: str,
    users: list[dict[str, Any]],
    pg_pool,
) -> dict[str, str]:
    """
    Create Supabase Auth users for each local user.

    Uses the Supabase Admin API to create users with their existing
    bcrypt password hashes (Supabase supports importing bcrypt hashes).

    Returns a mapping of local user.id -> supabase auth user.id
    """
    import httpx

    id_map: dict[str, str] = {}
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
        "Content-Type": "application/json",
    }
    admin_url = f"{supabase_url}/auth/v1/admin/users"

    async with httpx.AsyncClient(timeout=30) as client:
        for user in users:
            email = user.get("email")
            if not email:
                continue

            local_id = user.get("id")
            password_hash = user.get("password_hash")

            # Build request body
            body: dict[str, Any] = {
                "email": email,
                "email_confirm": True,  # Auto-confirm since they're migrated users
                "user_metadata": {
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                },
                "app_metadata": {
                    "provider": "email",
                    "local_user_id": str(local_id),
                },
            }

            # Import existing bcrypt hash if available
            if password_hash and password_hash.startswith("$2"):
                body["password_hash"] = password_hash

            try:
                resp = await client.post(admin_url, json=body, headers=headers)
                if resp.status_code in (200, 201):
                    auth_user = resp.json()
                    supabase_auth_id = auth_user.get("id")
                    id_map[str(local_id)] = supabase_auth_id
                    logger.info(
                        "Created auth user for %s (local=%s, auth=%s)",
                        email,
                        local_id,
                        supabase_auth_id,
                    )
                elif resp.status_code == 422 and "already been registered" in resp.text:
                    # User already exists in Supabase Auth — fetch their ID
                    logger.info("Auth user %s already exists, fetching ID...", email)
                    list_resp = await client.get(
                        f"{admin_url}?filter={email}",
                        headers=headers,
                    )
                    if list_resp.status_code == 200:
                        auth_users = list_resp.json().get("users", [])
                        for au in auth_users:
                            if au.get("email") == email:
                                id_map[str(local_id)] = au["id"]
                                break
                else:
                    logger.error(
                        "Failed to create auth user %s: %s %s",
                        email,
                        resp.status_code,
                        resp.text[:200],
                    )
            except Exception as e:
                logger.error("Error creating auth user %s: %s", email, e)

    # Update local users table with supabase_auth_id
    if id_map:
        sql = 'UPDATE "users" SET "supabase_auth_id" = $1 WHERE "id" = $2'
        async with pg_pool.acquire() as conn:
            for local_id, auth_id in id_map.items():
                try:
                    await conn.execute(sql, auth_id, local_id)
                except Exception as e:
                    logger.error(
                        "Failed to set supabase_auth_id for user %s: %s",
                        local_id,
                        e,
                    )

    return id_map


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

async def migrate(
    sqlite_path: str,
    pg_dsn: str,
    supabase_url: str,
    service_role_key: str,
    dry_run: bool = False,
    skip_auth: bool = False,
    batch_size: int = 500,
) -> None:
    """Run the full migration."""
    import asyncpg

    logger.info("=" * 60)
    logger.info("TaskPulse AI - SQLite → Supabase Migration")
    logger.info("=" * 60)
    logger.info("SQLite: %s", sqlite_path)
    logger.info("PostgreSQL: %s", pg_dsn.split("@")[-1] if "@" in pg_dsn else "(local)")
    logger.info("Dry run: %s", dry_run)
    logger.info("")

    # Verify SQLite tables exist
    sqlite_tables = await get_sqlite_tables(sqlite_path)
    logger.info("Found %d tables in SQLite: %s", len(sqlite_tables), ", ".join(sorted(sqlite_tables)))

    # Connect to PostgreSQL
    # Convert SQLAlchemy-style URL to asyncpg-compatible DSN
    pg_dsn_clean = pg_dsn.replace("postgresql+asyncpg://", "postgresql://")
    pg_pool = await asyncpg.create_pool(pg_dsn_clean, min_size=2, max_size=10)
    logger.info("Connected to PostgreSQL")

    stats = {
        "tables_migrated": 0,
        "rows_inserted": 0,
        "rows_failed": 0,
        "self_refs_updated": 0,
        "auth_users_created": 0,
    }

    # Track rows with self-referential FKs for second pass
    self_ref_rows: dict[str, list[dict[str, Any]]] = {}

    try:
        for phase_name, tables in ALL_PHASES:
            logger.info("")
            logger.info("─" * 40)
            logger.info(phase_name)
            logger.info("─" * 40)

            for table_name in tables:
                if table_name not in sqlite_tables:
                    logger.info("  ⏭  %s — not found in SQLite, skipping", table_name)
                    continue

                # Read from SQLite
                rows = await read_sqlite_table(sqlite_path, table_name)
                if not rows:
                    logger.info("  ⏭  %s — empty, skipping", table_name)
                    continue

                # Transform rows
                self_ref_col = SELF_REF_COLUMNS.get(table_name)
                transformed = [
                    transform_row(table_name, row, self_ref_col)
                    for row in rows
                ]

                # Store for second pass if needed
                if self_ref_col:
                    self_ref_rows[table_name] = transformed

                if dry_run:
                    logger.info(
                        "  📋 %s — %d rows (dry run, not inserted)",
                        table_name,
                        len(transformed),
                    )
                    continue

                # Insert into PostgreSQL
                inserted = await insert_rows_pg(
                    pg_pool, table_name, transformed, batch_size
                )
                stats["rows_inserted"] += inserted
                stats["rows_failed"] += len(transformed) - inserted
                stats["tables_migrated"] += 1
                logger.info(
                    "  ✅ %s — %d/%d rows inserted",
                    table_name,
                    inserted,
                    len(transformed),
                )

        # Second pass: update self-referential FKs
        if self_ref_rows and not dry_run:
            logger.info("")
            logger.info("─" * 40)
            logger.info("Second pass: self-referential FK updates")
            logger.info("─" * 40)

            for table_name, rows in self_ref_rows.items():
                self_ref_col = SELF_REF_COLUMNS[table_name]
                rows_with_refs = [
                    r for r in rows if r.get(f"_orig_{self_ref_col}") is not None
                ]
                if not rows_with_refs:
                    logger.info("  ⏭  %s.%s — no self-refs to update", table_name, self_ref_col)
                    continue

                updated = await update_self_refs(
                    pg_pool, table_name, self_ref_col, rows_with_refs
                )
                stats["self_refs_updated"] += updated
                logger.info(
                    "  ✅ %s.%s — %d/%d rows updated",
                    table_name,
                    self_ref_col,
                    updated,
                    len(rows_with_refs),
                )

        # Create Supabase Auth users
        if not skip_auth and not dry_run:
            logger.info("")
            logger.info("─" * 40)
            logger.info("Creating Supabase Auth users")
            logger.info("─" * 40)

            user_rows = await read_sqlite_table(sqlite_path, "users")
            if user_rows:
                id_map = await create_supabase_auth_users(
                    supabase_url, service_role_key, user_rows, pg_pool
                )
                stats["auth_users_created"] = len(id_map)
                logger.info("  ✅ Created %d Supabase Auth users", len(id_map))
            else:
                logger.info("  ⏭  No users to migrate")

    finally:
        await pg_pool.close()

    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info("  Tables migrated:      %d", stats["tables_migrated"])
    logger.info("  Rows inserted:        %d", stats["rows_inserted"])
    logger.info("  Rows failed:          %d", stats["rows_failed"])
    logger.info("  Self-refs updated:    %d", stats["self_refs_updated"])
    logger.info("  Auth users created:   %d", stats["auth_users_created"])
    logger.info("")

    if stats["rows_failed"] > 0:
        logger.warning("⚠️  Some rows failed to insert. Check logs above for details.")
    else:
        logger.info("🎉 Migration completed successfully!")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate TaskPulse AI data from SQLite to Supabase PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview what would be migrated)
  python -m scripts.migrate_to_supabase \\
      --sqlite-url ./taskpulse.db \\
      --pg-url postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres \\
      --supabase-url https://xxx.supabase.co \\
      --service-role-key eyJ... \\
      --dry-run

  # Full migration
  python -m scripts.migrate_to_supabase \\
      --sqlite-url ./taskpulse.db \\
      --pg-url postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres \\
      --supabase-url https://xxx.supabase.co \\
      --service-role-key eyJ...

  # Skip auth user creation (if already done)
  python -m scripts.migrate_to_supabase \\
      --sqlite-url ./taskpulse.db \\
      --pg-url postgresql+asyncpg://postgres:pass@db.xxx.supabase.co:5432/postgres \\
      --supabase-url https://xxx.supabase.co \\
      --service-role-key eyJ... \\
      --skip-auth
        """,
    )
    parser.add_argument(
        "--sqlite-url",
        required=True,
        help="Path to the SQLite database file (e.g., ./taskpulse.db)",
    )
    parser.add_argument(
        "--pg-url",
        required=True,
        help="PostgreSQL connection URL (e.g., postgresql+asyncpg://user:pass@host:5432/db)",
    )
    parser.add_argument(
        "--supabase-url",
        required=True,
        help="Supabase project URL (e.g., https://xxx.supabase.co)",
    )
    parser.add_argument(
        "--service-role-key",
        required=True,
        help="Supabase service role key for admin API access",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without inserting data",
    )
    parser.add_argument(
        "--skip-auth",
        action="store_true",
        help="Skip creating Supabase Auth users (useful if already created)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of rows to insert per batch (default: 500)",
    )

    args = parser.parse_args()

    asyncio.run(
        migrate(
            sqlite_path=args.sqlite_url,
            pg_dsn=args.pg_url,
            supabase_url=args.supabase_url,
            service_role_key=args.service_role_key,
            dry_run=args.dry_run,
            skip_auth=args.skip_auth,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
