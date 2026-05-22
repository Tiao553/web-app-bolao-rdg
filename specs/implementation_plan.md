# Implementation Plan — BOLAO_COPA_RDG

## Build Reference

- Workflow command: `~/.config/opencode/skills/workflow-commands/commands/build.md`
- Contract: `~/.config/opencode/sdd/architecture/WORKFLOW_CONTRACTS.yaml`
- Design: `~/.config/opencode/sdd/features/bolao-copa-rdg/DESIGN_BOLAO_COPA_RDG.md`
- Define: `~/.config/opencode/sdd/features/bolao-copa-rdg/DEFINE_BOLAO_COPA_RDG.md`
- Output root confirmed by user: `~/bolao-copa-rdg/`

## Build Strategy

This build is executed in chunks because the command contract requires implementation of the next pending chunk, immediate verification, report persistence, and a stop point for user-controlled continuation.

### Architectural Guardrails

1. All implementation files are written under `/home/tiao553/bolao-copa-rdg/`.
2. Frontend remains a presentation shell only; canonical rules stay in backend domain modules.
3. Secrets remain in `.env`; only non-secret tunables are versioned in YAML.
4. Backend foundation is typed, validation-first, and ready for FastAPI + SQLAlchemy wiring.
5. Every delegated specialist must produce evidence for the build report.

## Chunk Plan

| Chunk | Name | Scope | Files | Reason |
|---|---|---|---|---|
| 1 | Foundation manifests and config | Runtime entry manifests and config loading | 1, 2, 13, 15, 16 | Unlocks frontend/backend scaffolding without forcing business logic yet |
| 2 | Frontend shell and client utilities | layout, access gate, API/session libs | 3, 10, 11, 12 | Establishes app-shell and auth-aware client foundation |
| 3 | Backend auth/data core | security, schema, queries, main | 17, 18, 19, 14 | Creates backend backbone for route wiring |
| 4 | Product routes and member/admin UI | frontend pages and backend routes | 4-9, 20-22 | Delivers visible product flows |
| 5 | Rules and integrations | scoring, standings, bracket, provider adapters, sync, recalculation, lookup | 23-30 | Encodes critical tournament logic and sync behavior |
| 6 | Persistence and evidence | migration, seed loader, unit/integration tests | 31-37 | Provides validation evidence and seed bootstrap |

## Completed Chunk

### Chunk 1 — Foundation manifests and config

| Manifest # | File | Specialist | Dependency Basis | Implementation Notes |
|---|---|---|---|---|
| 1 | `app/package.json` | `frontend-react-agent` | none | Minimal Next.js TypeScript runtime/scripts |
| 2 | `app/next.config.mjs` | `frontend-react-agent` | 1 | Production-safe frontend runtime flags |
| 13 | `backend/pyproject.toml` | `python.python-developer` | none | Backend dependency, lint, type-check, and test tooling |
| 16 | `backend/config/app-settings.yaml` | `python.python-developer` | none | Versioned non-secret defaults per design decision 6 |
| 15 | `backend/app/core/config.py` | `python.python-developer` | 13, 16 | Typed env + YAML settings loader with validation |

## Agent Assignments

| File | Agent | Agent File |
|---|---|---|
| `app/package.json` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| `app/next.config.mjs` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| `backend/pyproject.toml` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| `backend/config/app-settings.yaml` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| `backend/app/core/config.py` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |

## Edge Cases Considered for Chunk 1

1. Missing `DATABASE_URL` must fail clearly.
2. YAML root must be a mapping and reject malformed config.
3. Competition release timestamp cannot precede prediction close timestamp.
4. Sync terminal statuses cannot be empty or duplicated.
5. Frontend foundation must not imply client-owned authorization.

## Verification Plan for Chunk 1

1. `ruff check backend/app/core/config.py`
2. `mypy backend/app/core/config.py`
3. `python -m compileall backend/app/core/config.py`
4. Optional tooling presence check for Node/Python package managers if needed

## Completed Chunks

### Chunk 2 — Frontend shell and client utilities

| Manifest # | File | Specialist | Dependency Basis | Implementation Notes |
|---|---|---|---|---|
| 3 | `app/src/app/layout.tsx` | `frontend-react-agent` | 1, 2 | Root shell with metadata and provider-ready body wrapper |
| 10 | `app/src/components/access/access-gate.tsx` | `frontend-react-agent` | 3 | Release-aware presentation gate for loading, pending, blocked, rejected, error, and locked states |
| 11 | `app/src/lib/api-client.ts` | `frontend-react-agent` | 1 | Typed cookie-friendly backend client with stable error shape |
| 12 | `app/src/lib/session.ts` | `frontend-react-agent` | 11 | Session normalization and view-state helpers based on backend payloads |

## Agent Assignments for Chunk 2

| File | Agent | Agent File |
|---|---|---|
| `app/src/app/layout.tsx` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| `app/src/components/access/access-gate.tsx` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| `app/src/lib/api-client.ts` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| `app/src/lib/session.ts` | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |

## Edge Cases Considered for Chunk 2

1. Session payload may be anonymous or partially populated.
2. Explore release and prediction close timestamps may be absent or invalid.
3. UI must represent pending, rejected, blocked, locked, loading, and error states distinctly.
4. Frontend must not become the source of truth for approval or admin authorization.
5. Backend error payload shapes may vary between `message`, `detail`, or `error` fields.

## Verification Plan for Chunk 2

1. `npm exec --yes --package esbuild@0.25.5 -- esbuild src/app/layout.tsx src/components/access/access-gate.tsx src/lib/api-client.ts src/lib/session.ts --outdir=/tmp/opencode/bolao-copa-rdg-chunk2 --bundle --format=esm --platform=browser --external:next --external:react`
2. Manual review against DESIGN Pattern 4 and frontend agent quality gate

## Completed Chunk

### Chunk 3 — Backend auth/data core

| Manifest # | File | Specialist | Dependency Basis | Implementation Notes |
|---|---|---|---|---|
| 17 | `backend/app/core/security.py` | `python.python-developer` | 13, 15 | Password hashing, session cookies, opaque token storage, and centralized auth guards |
| 18 | `backend/app/models/schema.py` | `python.python-developer` | 13, 15 | Typed SQLAlchemy schema for users, sessions, matches, predictions, sync logs, and competition windows |
| 19 | `backend/app/repositories/queries.py` | `python.python-developer` | 18 | DB session dependency, approved-user filters, session lookup, and visibility query builders |
| 14 | `backend/app/main.py` | `python.python-developer` | 13, 15, 17, 18, 19 | FastAPI factory, CORS, health endpoints, and stable error envelopes without future route imports |

## Agent Assignments for Chunk 3

| File | Agent | Agent File |
|---|---|---|
| `backend/app/core/security.py` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| `backend/app/models/schema.py` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| `backend/app/repositories/queries.py` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| `backend/app/main.py` | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |

## Edge Cases Considered for Chunk 3

1. New users must remain `PENDING` by default at the schema level.
2. Session cookies must resolve users on the backend and invalidate blocked or expired sessions.
3. Ranking and Explore visibility must be filterable at query level to exclude non-approved users.
4. The backend app must import safely before future route modules exist.
5. Local verification must work while secrets continue to come only from repo `.env`.

## Verification Plan for Chunk 3

1. `ruff check app/core/security.py app/models/schema.py app/repositories/queries.py app/main.py`
2. `mypy --explicit-package-bases app/core/security.py app/models/schema.py app/repositories/queries.py app/main.py`
3. `python3 -m compileall app/core/security.py app/models/schema.py app/repositories/queries.py app/main.py`
4. `PYTHONPATH="backend" python3 -c "from app.main import app; print(app.title)"`

## Completed Chunks

### Chunks 4 and 5 — Product routes, rules, and integrations

These chunks were executed together because route behavior, sync orchestration, and rule modules are coupled by the DESIGN manifest and endpoint contracts.

| Manifest # | File | Specialist | Dependency Basis | Implementation Notes |
|---|---|---|---|---|
| 4-9 | `app/src/app/(auth|pending|member)/**/page.tsx` | `frontend-react-agent` | 3, 10, 11, 12 | Presentation-only screens wired to backend session and release-state contracts |
| 20-22 | `backend/app/api/routes/{auth,member,admin}.py` | `python.python-developer` | 17, 18, 19, 24-27 | Cookie auth, approved/admin guards, moderation, windows, and sync trigger routes |
| 23-25 | `backend/app/domain/{scoring,standings,bracket}.py` | `rules-qa-agent` | 16, 28 | Deterministic rule modules for score, standings, best-third ranking, and bracket propagation |
| 26-29 | `backend/app/integrations/{api_football,google_sheets}.py`, `backend/app/services/sync_service.py` | `external-integration-agent` | 15, 18, 24, 25 | Provider adapters, idempotent merge logic, override protection, SyncLog writes |
| 28 | `backend/app/data/third_place_slot_matrix.json` | `rules-qa-agent` | none | Deterministic full allocation matrix generated from documented slot constraints |
| 30 | `backend/app/services/recalculation_service.py` | `python.python-developer` | 18, 19, 23, 24, 25, 29 | Recompute standings, bracket mirrors, prediction points, and ranking snapshots |
| 14 | `backend/app/main.py` | `python.python-developer` | 20-22 | Backend entrypoint updated to register auth/member/admin routers |

## Agent Assignments for Chunks 4 and 5

| File Group | Agent | Agent File |
|---|---|---|
| Frontend pages | `frontend-react-agent` | `~/.config/opencode/agents/frontend-react-agent.agent.md` |
| Backend routes and recalculation | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| Rule modules and matrix | `rules-qa-agent` | `~/.config/opencode/agents/rules-qa-agent.agent.md` |
| Provider adapters and sync service | `external-integration-agent` | `~/.config/opencode/agents/external-integration-agent.agent.md` |

## Edge Cases Considered for Chunks 4 and 5

1. Anonymous session reads must not crash member-facing pages.
2. Register/login must support current HTML form posts while preserving backend authority.
3. Sync cannot overwrite manual overrides and must skip non-terminal matches.
4. Third-place slot allocation must be deterministic across all 495 combinations.
5. Backend imports must stay safe even when database drivers are unavailable until runtime session usage.

## Verification Plan for Chunks 4 and 5

1. `npm exec --yes --package esbuild@0.25.5 -- esbuild src/app/(auth)/login/page.tsx src/app/(pending)/waiting/page.tsx src/app/(member)/dashboard/page.tsx src/app/(member)/predictions/page.tsx src/app/(member)/ranking/page.tsx src/app/(member)/explore/page.tsx --outdir=/tmp/opencode/bolao-copa-rdg-chunk45-frontend --bundle --format=esm --platform=browser --external:next --external:next/link --external:next/navigation --external:react`
2. `ruff check app/api/routes/auth.py app/api/routes/member.py app/api/routes/admin.py app/domain/scoring.py app/domain/standings.py app/domain/bracket.py app/integrations/api_football.py app/integrations/google_sheets.py app/services/sync_service.py app/services/recalculation_service.py app/repositories/queries.py app/main.py`
3. `mypy --explicit-package-bases app/api/routes/auth.py app/api/routes/member.py app/api/routes/admin.py app/domain/scoring.py app/domain/standings.py app/domain/bracket.py app/integrations/api_football.py app/integrations/google_sheets.py app/services/sync_service.py app/services/recalculation_service.py app/repositories/queries.py app/main.py`
4. `python3 -m compileall app/api/routes/auth.py app/api/routes/member.py app/api/routes/admin.py app/domain/scoring.py app/domain/standings.py app/domain/bracket.py app/integrations/api_football.py app/integrations/google_sheets.py app/services/sync_service.py app/services/recalculation_service.py app/repositories/queries.py app/main.py`
5. `PYTHONPATH="backend" python3 -c "from app.main import app; print(app.title); print(len(app.routes))"`
6. `python3 -c "import json, pathlib; json.loads(pathlib.Path('backend/app/data/third_place_slot_matrix.json').read_text())"`

## Current Chunk

### Chunk 6 — Persistence and evidence

| Manifest # | File | Specialist | Dependency Basis | Implementation Notes |
|---|---|---|---|---|
| 31 | `database/migrations/versions/20260521_0001_init.py` | `python.python-developer` | 18 | Initial PostgreSQL migration aligned with current SQLAlchemy schema |
| 32 | `database/seeds/load_tournament_seed.py` | `python.python-developer` | 18, 25 | Idempotent tournament bootstrap from `data/*.json` |
| 33-35 | `backend/tests/unit/test_{scoring,standings,bracket}.py` | `test.test-generator` | 23-25 | Unit evidence for core rule modules |
| 36-37 | `backend/tests/integration/test_{member_access,admin_sync}.py` | `test.test-generator` | 20-22, 26-30 | Integration evidence for access and sync flows |

## Agent Assignments for Current Chunk

| File Group | Agent | Agent File |
|---|---|---|
| Migration and seed loader | `python.python-developer` | `~/.config/opencode/agents/python.python-developer.agent.md` |
| Unit and integration tests | `test.test-generator` | `~/.config/opencode/agents/test.test-generator.agent.md` |

## Edge Cases Considered for Chunk 6

1. Migration must create enums and tables in safe downgrade order.
2. Seed loader must be idempotent and tolerate missing source timestamps by falling back to configured competition windows.
3. Tests must run without depending on production Postgres or external provider credentials.
4. Integration tests must authenticate through cookie-backed flows instead of bypassing backend authority.
5. Build completion requires evidence that chunks 1-6 are now covered by runnable verification.

## Verification Plan for Chunk 6

1. `ruff check ../database/migrations/versions/20260521_0001_init.py ../database/seeds/load_tournament_seed.py tests/unit/test_scoring.py tests/unit/test_standings.py tests/unit/test_bracket.py tests/integration/test_member_access.py tests/integration/test_admin_sync.py app/api/routes/member.py`
2. `mypy --explicit-package-bases tests/unit/test_scoring.py tests/unit/test_standings.py tests/unit/test_bracket.py tests/integration/test_member_access.py tests/integration/test_admin_sync.py`
3. `python3 -m compileall ../database/migrations/versions/20260521_0001_init.py ../database/seeds/load_tournament_seed.py tests/unit/test_scoring.py tests/unit/test_standings.py tests/unit/test_bracket.py tests/integration/test_member_access.py tests/integration/test_admin_sync.py`
4. `DATABASE_URL="sqlite+pysqlite://" PYTHONPATH="." pytest tests/unit/test_scoring.py tests/unit/test_standings.py tests/unit/test_bracket.py tests/integration/test_member_access.py tests/integration/test_admin_sync.py -q`

## Next Step

Build complete. Proceed to `/workflow:validate ~/.config/opencode/sdd/features/bolao-copa-rdg/DESIGN_BOLAO_COPA_RDG.md`.
