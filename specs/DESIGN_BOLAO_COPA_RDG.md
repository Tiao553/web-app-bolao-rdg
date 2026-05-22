# DESIGN: Bolao Copa RDG

> Technical design for implementing Bolao Copa RDG with a mock-driven frontend and explicit backend-to-frontend contracts

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | BOLAO_COPA_RDG |
| **Date** | 2026-05-21 |
| **Author** | design-agent |
| **DEFINE** | `~/.config/opencode/sdd/features/bolao-copa-rdg/DEFINE_BOLAO_COPA_RDG.md` |
| **Status** | Built |
| **Design Confidence** | 0.80 — no relevant KB domain loaded; agent matches found for frontend, Python, integration, rules, and tests |

---

## Architecture Overview

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                               SYSTEM DIAGRAM                                 │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Browser                                                                      │
│    │                                                                          │
│    ├── Next.js app (React + UI Kit + mock-driven routes)                      │
│    │     ├── public/auth screens                                              │
│    │     ├── approved member area                                             │
│    │     └── admin console                                                    │
│    │                     │                                                     │
│    │                     └── HTTPS JSON API / screen-shaped DTOs              │
│    ▼                                                                           │
│  FastAPI backend                                                               │
│    ├── auth + session/cookie guards                                           │
│    ├── member/admin routes                                                    │
│    ├── scoring engine                                                         │
│    ├── standings + bracket engine                                             │
│    ├── sync + reconciliation service                                          │
│    └── seed/bootstrap loader                                                  │
│          │                 │                           │                      │
│          │                 │                           ├── Google Sheets API  │
│          │                 ├── PostgreSQL             │   (optional fallback) │
│          │                 │                           │                      │
│          └── Vercel Cron ──┴── POST /admin/sync ──────┴── API-Football       │
│                                                                               │
│  Recalculation flow:                                                           │
│  official result change → persist source data → recompute standings/bracket   │
│  → recompute prediction points → refresh ranking/explore visibility            │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `app/` web client | Login, create-account, pending state, member flows, ranking, results, bracket, Explore, admin UI | Next.js (React + TypeScript) + existing UI Kit |
| `backend/` API service | Auth, authorization, prediction APIs, admin APIs, sync trigger endpoints | FastAPI + Pydantic + SQLAlchemy |
| `backend` frontend-contract layer | DTOs/view models shaped for mock-driven screens and navigation flows | Pydantic response schemas + service mappers |
| `backend` domain engine | Deterministic scoring, standings, bracket propagation, top-scorer resolution | Pure Python service modules |
| `database/` migration layer | Schema lifecycle and seed bootstrap | PostgreSQL + Alembic |
| Seed assets in `data/` | Canonical tournament bootstrap source | Versioned JSON already in repo |
| External providers | Automatic fixtures/results/events/top-scorers and operational fallback | API-Football + optional Google Sheets |

---

## Delivery Boundaries

| Boundary | Owns | Does Not Own |
|----------|------|---------------|
| Frontend (`app/`) | Screens, route guards, optimistic UX, admin forms | Canonical rules, approval authority, score calculation |
| Backend (`backend/`) | Auth, eligibility, sync, recalculation, domain rules, screen-oriented contracts | Browser rendering, UI composition |
| Database (`database/`) | Persistence schema, migrations, bootstrapping | Business orchestration, HTTP contracts |

No shared runtime package is introduced between deployable units; the backend is the sole owner of rule execution and canonical data decisions.

---

## Key Decisions

### Decision 1: React frontend on Next.js, dedicated Python backend, PostgreSQL system of record

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** The MVP must ship a React app on Vercel while preserving a dedicated backend boundary for auth, admin operations, sync jobs, and deterministic rule execution.

**Choice:** Use Next.js in `app/` for the React web experience and a separate FastAPI service in `backend/`, backed by PostgreSQL. The frontend deploys to Vercel; the backend can run independently while Vercel Cron calls its admin sync endpoint.

**Rationale:** This preserves the required dedicated backend, aligns with available build specialists (`frontend-react-agent`, `python.python-developer`), and keeps rules and privileged operations off the client.

**Alternatives Rejected:**
1. React SPA + all logic in client - rejected because auth, ranking eligibility, and sync rules cannot be trusted in the browser.
2. Next.js-only full-stack app - rejected because DEFINE explicitly asks for a dedicated backend layer and operational sync boundaries.

**Consequences:**
- Trade-off: two deployable units instead of one.
- Benefit: clear security boundary and easier rule/test isolation.

---

### Decision 2: Approval status is enforced server-side on every protected read/write path

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** The core product rule is that only `APPROVED` users can participate, influence ranking, or see Explore after release.

**Choice:** Store authenticated session identity in an HTTP-only cookie, resolve the user on the backend, and centralize guard helpers such as `require_authenticated_user`, `require_approved_user`, and `require_admin_user`. Ranking and Explore queries are filtered at query level to exclude non-approved users.

**Rationale:** Centralized backend guards reduce drift between screens, APIs, ranking jobs, and recalculation logic.

**Alternatives Rejected:**
1. Frontend-only route guards - rejected because they do not protect API access or recalculation side effects.
2. Per-route ad hoc checks - rejected because repeated custom checks tend to drift and miss edge cases.

**Consequences:**
- Trade-off: all member endpoints need shared dependency wiring.
- Benefit: AT-002, AT-005, and AT-006 can be enforced consistently.

---

### Decision 3: Deterministic rule engine split into scoring, standings, bracket, and top-scorer modules

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** The application must recompute points, ranking, third-place qualification, and bracket propagation without ambiguity after sync or manual corrections.

**Choice:** Implement pure-Python domain modules:
- `scoring.py` for prediction points
- `standings.py` for group tables and third-place ranking
- `bracket.py` for round-of-32 slot allocation and knockout propagation
- `recalculation_service.py` as orchestration only

**Rationale:** Pure rule modules are easy to unit test exhaustively and prevent API/database concerns from contaminating business correctness.

**Alternatives Rejected:**
1. SQL-heavy stored procedures for all rules - rejected because bracket and top-scorer edge cases become harder to test and evolve.
2. One large service file - rejected because scoring, standings, and bracket logic would become tightly coupled.

**Consequences:**
- Trade-off: more modules to wire.
- Benefit: direct mapping to rules-focused test files and easier validate-phase evidence.

---

### Decision 4: Override-aware sync pipeline with provider adapters and idempotent merges

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** External data imports must not overwrite admin corrections, and the free API quota requires sparse post-match sync.

**Choice:** Implement provider adapters for API-Football and optional Google Sheets, then merge provider payloads via a sync service that checks manual override flags per field/record before writing. Vercel Cron invokes `POST /api/admin/sync/run`, which processes only fixtures eligible by schedule and status (`FT`, `AET`, `PEN`).

**Rationale:** Adapter isolation keeps source contracts replaceable, while the merge layer encodes precedence and auditability once.

**Alternatives Rejected:**
1. Direct route-to-provider writes - rejected because it mixes transport concerns with override logic.
2. Continuous polling - rejected because it conflicts with the quota and MVP operational scope.

**Consequences:**
- Trade-off: additional mapping layer.
- Benefit: reliable idempotency, lower quota consumption, and clearer SyncLog history.

---

### Decision 5: Use a static third-place allocation lookup file, not a heuristic-only algorithm

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** The DEFINE leaves open whether round-of-32 third-place slot allocation should use a full FIFA table or an equivalent algorithm.

**Choice:** Store a canonical lookup file in `backend/app/data/third_place_slot_matrix.json` keyed by the sorted set of 8 advancing third-place groups. `bracket.py` loads the file and fills slots `M74`, `M77`, `M79`, `M80`, `M81`, `M82`, `M85`, `M87` deterministically.

**Rationale:** A static lookup removes ambiguity, avoids subtle bracket bugs, and provides a compact artifact for exhaustive tests.

**Alternatives Rejected:**
1. Greedy exclusion algorithm only - rejected because correctness is harder to prove across all combinations.
2. Manual admin assignment of third-place slots - rejected because it breaks determinism and introduces operational risk.

**Consequences:**
- Trade-off: one curated static data artifact must be maintained.
- Benefit: deterministic bracket allocation with straightforward unit coverage.

---

### Decision 6: Secrets stay in env; tunable rules live in versioned YAML; existing `DATABASE_URL` is reused

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-21 |

**Context:** The user explicitly stated that `.env` already contains `DATABASE_URL`, and the design agent forbids hardcoding operational values.

**Choice:** Do not create a new database secret file. Reuse the existing `DATABASE_URL` from the environment. Keep non-secret tunables such as scoring values, release window defaults, and sync thresholds in `backend/config/app-settings.yaml`.

**Rationale:** This respects current setup, avoids secret duplication, and still keeps rules configurable and reviewable.

**Alternatives Rejected:**
1. Put all config in `.env` - rejected because scoring and tournament rule defaults are not secrets and deserve version control.
2. Hardcode score constants in service modules - rejected because rule review becomes harder and future changes require code edits.

**Consequences:**
- Trade-off: config is split across env and YAML.
- Benefit: secrets remain secret while rule defaults stay auditable.

---

### Decision 7: Treat `mock/*` as the canonical frontend blueprint and expose backend DTOs per screen

| Attribute | Value |
|-----------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-22 |

**Context:** The user requested a new frontend that must follow every mock already created under `mock/` and `mock/admin/`, while ensuring the backend can connect cleanly to that experience.

**Choice:** Map every mock to a concrete route in `app/`, and make the backend return screen-oriented DTOs/view models for member and admin experiences. The frontend remains responsible for rendering and interaction, while the backend owns canonical rules, aggregation, visibility decisions, and payload shaping.

**Rationale:** This reduces ambiguity during build, prevents the frontend from reverse-engineering database structures, and makes traceability from mock → route → API explicit.

**Alternatives Rejected:**
1. Let the frontend infer everything from generic CRUD payloads - rejected because it shifts canonical mapping burden to the client and increases drift from the mocks.
2. Follow mocks visually only, without route/contract traceability - rejected because backend/frontend integration would remain underspecified.

**Consequences:**
- Trade-off: more frontend routes and response schemas to maintain.
- Benefit: direct mapping from approved mock screens to implementation and clearer contract tests.

---

## Frontend Mock Coverage Contract

| Mock Artifact | Planned Route | Backend Contract Expectation |
|---------------|---------------|------------------------------|
| `mock/login-page.html` | `app/src/app/(auth)/login/page.tsx` | session bootstrap, login form submit, auth errors |
| `mock/create-account.html` | `app/src/app/(auth)/create-account/page.tsx` | register form, role/status messaging, post-submit pending state |
| `mock/aguardando-aprovacao.html` | `app/src/app/(pending)/waiting/page.tsx` | current session status + approval guidance |
| `mock/dashborad.html` | `app/src/app/(member)/dashboard/page.tsx` | member dashboard summary, score cards, release windows |
| `mock/palpites-iniciais.html` | `app/src/app/(member)/initial-predictions/page.tsx` | champion/top-scorer options, saved picks, lock state |
| `mock/palpites-fase.html` | `app/src/app/(member)/phase-predictions/page.tsx` | grouped match predictions, phases, lock state |
| `mock/resultados.html` | `app/src/app/(member)/results/page.tsx` | official results + per-match points |
| `mock/ranking.html` | `app/src/app/(member)/ranking/page.tsx` | ranking list, tie-break metadata, participant score cards |
| `mock/chaveamento.html` | `app/src/app/(member)/bracket/page.tsx` | bracket tree, third-place slot fill, winner propagation |
| `mock/explore.html` | `app/src/app/(member)/explore/page.tsx` | gated Explore feed, release-aware visibility |
| `mock/admin/AdminDashboard.html` | `app/src/app/(admin)/dashboard/page.tsx` | admin KPIs, sync health, governance queue |
| `mock/admin/AdminUsers.html` | `app/src/app/(admin)/users/page.tsx` | user moderation table, filters, approval actions |
| `mock/admin/AdminIntegration.html` | `app/src/app/(admin)/integration/page.tsx` | provider health, sync runs, adapter status |
| `mock/admin/AdminMatches.html` | `app/src/app/(admin)/matches/page.tsx` | match registry, manual creation/edit flows |
| `mock/admin/AdminResults.html` | `app/src/app/(admin)/results/page.tsx` | result editor, override metadata, recalculation trigger |
| `mock/admin/AdminPlayers.html` | `app/src/app/(admin)/players/page.tsx` | top-scorer/player stats audit and actions |
| `mock/admin/AdminSettings.html` | `app/src/app/(admin)/settings/page.tsx` | rules configuration, release windows, audit summaries |

Mock fidelity is mandatory for route coverage, layout composition, navigation, and state design. Operational labels and live data values must still reflect the canonical backend decisions already accepted in this feature (for example, API-Football as primary provider).

---

## File Manifest

| # | File | Action | Purpose | Agent | Dependencies |
|---|------|--------|---------|-------|--------------|
| 1 | `app/package.json` | Create | Frontend dependencies/scripts | @frontend-react-agent | None |
| 2 | `app/next.config.mjs` | Create | Next.js runtime config | @frontend-react-agent | 1 |
| 3 | `app/src/app/layout.tsx` | Create | App shell and providers | @frontend-react-agent | 1, 2 |
| 4 | `app/src/app/(auth)/login/page.tsx` | Create | Login screen from `mock/login-page.html` | @frontend-react-agent | 3, 18, 19 |
| 5 | `app/src/app/(auth)/create-account/page.tsx` | Create | Registration screen from `mock/create-account.html` | @frontend-react-agent | 3, 18, 19 |
| 6 | `app/src/app/(pending)/waiting/page.tsx` | Create | Pending/rejected/blocked waiting state from `mock/aguardando-aprovacao.html` | @frontend-react-agent | 3, 19 |
| 7 | `app/src/app/(member)/dashboard/page.tsx` | Create | Approved user home from `mock/dashborad.html` | @frontend-react-agent | 3, 18, 19 |
| 8 | `app/src/app/(member)/initial-predictions/page.tsx` | Create | Champion/top-scorer flow from `mock/palpites-iniciais.html` | @frontend-react-agent | 3, 18, 19 |
| 9 | `app/src/app/(member)/phase-predictions/page.tsx` | Create | Match-by-match predictions from `mock/palpites-fase.html` | @frontend-react-agent | 3, 18, 19 |
| 10 | `app/src/app/(member)/results/page.tsx` | Create | Member results view from `mock/resultados.html` | @frontend-react-agent | 3, 18, 19 |
| 11 | `app/src/app/(member)/ranking/page.tsx` | Create | Ranking view from `mock/ranking.html` | @frontend-react-agent | 3, 18, 19 |
| 12 | `app/src/app/(member)/bracket/page.tsx` | Create | Bracket view from `mock/chaveamento.html` | @frontend-react-agent | 3, 18, 19 |
| 13 | `app/src/app/(member)/explore/page.tsx` | Create | Controlled Explore area from `mock/explore.html` | @frontend-react-agent | 3, 17, 18, 19 |
| 14 | `app/src/app/(admin)/dashboard/page.tsx` | Create | Admin dashboard from `mock/admin/AdminDashboard.html` | @frontend-react-agent | 3, 18, 19 |
| 15 | `app/src/app/(admin)/users/page.tsx` | Create | Admin users screen from `mock/admin/AdminUsers.html` | @frontend-react-agent | 3, 18, 19 |
| 16 | `app/src/app/(admin)/integration/page.tsx` | Create | Admin integration screen from `mock/admin/AdminIntegration.html` | @frontend-react-agent | 3, 18, 19 |
| 17 | `app/src/app/(admin)/matches/page.tsx` | Create | Admin matches screen from `mock/admin/AdminMatches.html` | @frontend-react-agent | 3, 18, 19 |
| 18 | `app/src/app/(admin)/results/page.tsx` | Create | Admin results screen from `mock/admin/AdminResults.html` | @frontend-react-agent | 3, 19 |
| 19 | `app/src/app/(admin)/players/page.tsx` | Create | Admin players screen from `mock/admin/AdminPlayers.html` | @frontend-react-agent | 3, 18 |
| 20 | `app/src/app/(admin)/settings/page.tsx` | Create | Admin settings screen from `mock/admin/AdminSettings.html` | @frontend-react-agent | 3, 19 |
| 21 | `app/src/components/access/access-gate.tsx` | Create | Locked/pending/release-aware UI states | @frontend-react-agent | 3 |
| 22 | `app/src/components/layout/member-shell.tsx` | Create | Shared member navigation aligned to member mocks | @frontend-react-agent | 3 |
| 23 | `app/src/components/layout/admin-shell.tsx` | Create | Shared admin navigation aligned to admin mocks | @frontend-react-agent | 3 |
| 24 | `app/src/lib/api-client.ts` | Create | Typed HTTP client for backend | @frontend-react-agent | 1 |
| 25 | `app/src/lib/session.ts` | Create | Session fetch and route helper | @frontend-react-agent | 24 |
| 26 | `app/src/lib/contracts.ts` | Create | Frontend types mirroring backend screen DTOs | @frontend-react-agent | 24 |
| 27 | `backend/pyproject.toml` | Create | Backend dependencies/scripts | @python.python-developer | None |
| 28 | `backend/app/main.py` | Create | FastAPI entrypoint | @python.python-developer | 27, 29, 31, 32, 33 |
| 29 | `backend/app/core/config.py` | Create | Load env + YAML config | @python.python-developer | 27 |
| 30 | `backend/config/app-settings.yaml` | Create | Versioned non-secret tunables | @python.python-developer | None |
| 31 | `backend/app/core/security.py` | Create | Password hashing, session tokens, guard dependencies | @python.python-developer | 27, 29 |
| 32 | `backend/app/models/schema.py` | Create | ORM models/enums for users, matches, predictions, sync logs | @python.python-developer | 27, 29 |
| 33 | `backend/app/repositories/queries.py` | Create | Query helpers and transaction-safe filters | @python.python-developer | 32 |
| 34 | `backend/app/api/routes/auth.py` | Create | Register/login/logout/session endpoints | @python.python-developer | 31, 32, 33 |
| 35 | `backend/app/api/routes/member.py` | Create | Dashboard/predictions/ranking/results/bracket/explore APIs | @python.python-developer | 31, 32, 33, 38, 39, 40 |
| 36 | `backend/app/api/routes/admin.py` | Create | User moderation, window config, manual overrides, sync trigger | @python.python-developer | 31, 32, 33, 41, 42 |
| 37 | `backend/app/api/schemas/frontend.py` | Create | Pydantic DTOs/view models for mock-driven screens | @python.python-developer | 27 |
| 38 | `backend/app/domain/scoring.py` | Create | Exact/result/Brazil/champion/top-scorer scoring | @rules-qa-agent | 30 |
| 39 | `backend/app/domain/standings.py` | Create | Group table and 12-third-place ranking rules | @rules-qa-agent | 30 |
| 40 | `backend/app/domain/bracket.py` | Create | Third-place slot fill and knockout propagation | @rules-qa-agent | 30, 43 |
| 41 | `backend/app/integrations/api_football.py` | Create | RapidAPI adapter and payload mapping | @external-integration-agent | 29, 32 |
| 42 | `backend/app/integrations/google_sheets.py` | Create | Optional fallback provider adapter | @external-integration-agent | 29, 32 |
| 43 | `backend/app/data/third_place_slot_matrix.json` | Create | Canonical round-of-32 third-place lookup | @rules-qa-agent | None |
| 44 | `backend/app/services/sync_service.py` | Create | Provider selection, idempotent merge, SyncLog writes | @external-integration-agent | 32, 33, 39, 40, 41, 42 |
| 45 | `backend/app/services/recalculation_service.py` | Create | Orchestrate standings/bracket/points/ranking recomputation | @python.python-developer | 32, 33, 38, 39, 40, 44 |
| 46 | `backend/app/services/frontend_contract_service.py` | Create | Compose screen DTOs from canonical domain data | @python.python-developer | 33, 37, 39, 40, 45 |
| 47 | `database/migrations/versions/20260521_0001_init.py` | Create | Initial PostgreSQL schema migration | @python.python-developer | 32 |
| 48 | `database/seeds/load_tournament_seed.py` | Create | Idempotent loader for `data/*.json` canonical seeds | @python.python-developer | 32, 40 |
| 49 | `backend/tests/unit/test_scoring.py` | Create | Rule tests for prediction scoring | @test.test-generator | 38 |
| 50 | `backend/tests/unit/test_standings.py` | Create | Rule tests for groups and best-third ranking | @test.test-generator | 39 |
| 51 | `backend/tests/unit/test_bracket.py` | Create | Lookup and propagation tests | @test.test-generator | 40, 43 |
| 52 | `backend/tests/integration/test_member_access.py` | Create | Pending/approved/explore/ranking/results access tests | @test.test-generator | 34, 35, 36 |
| 53 | `backend/tests/integration/test_admin_sync.py` | Create | Sync override/recalculation integration tests | @test.test-generator | 36, 41, 42, 44, 45 |
| 54 | `backend/tests/contract/test_frontend_contracts.py` | Create | Validate screen DTOs expected by the new frontend mocks | @test.test-generator | 35, 36, 37, 46 |

**Total Files:** 54

---

## Agent Assignment Rationale

> Agents discovered from `~/.config/opencode/agents/**/*.agent.md`. With no relevant KB domain in DEFINE, assignment confidence comes from file purpose and route match.

| Agent | Files Assigned | Why This Agent |
|-------|----------------|----------------|
| @frontend-react-agent | 1-26 | React routes, shared shells, mock-driven screen composition, client contract typing |
| @python.python-developer | 27-37, 45-48 | FastAPI/Pydantic/ORM/config patterns and backend DTO composition |
| @external-integration-agent | 41-44 | Provider adapters, sync design, reconciliation, manual override precedence |
| @rules-qa-agent | 38-40, 43 | High-risk deterministic business rules and bracket correctness |
| @test.test-generator | 49-54 | Pytest unit/integration/contract evidence for validate phase |

**Agent Discovery:**
- Scanned: `~/.config/opencode/agents/**/*.agent.md`
- Matched by: React UI responsibility, Python backend files, sync/integration intent, rules-heavy modules, pytest targets

---

## Code Patterns

### Pattern 1: Backend approval guard

```python
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_session
from app.models.schema import AccessStatus, User


def require_approved_user(user: User = Depends(get_current_session)) -> User:
    if user.access_status is not AccessStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not approved for competition access",
        )
    return user
```

### Pattern 2: Override-aware field merge

```python
def apply_provider_value(current_value, incoming_value, manual_override: bool):
    if manual_override:
        return current_value, "skipped_manual_override"
    if current_value == incoming_value:
        return current_value, "noop"
    return incoming_value, "updated"
```

### Pattern 3: Score calculation from YAML-backed rules

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoreRules:
    exact_points: int
    result_points: int
    brazil_multiplier: int
    champion_points: int
    top_scorer_points: int


def score_match_prediction(prediction, official_result, rules: ScoreRules) -> int:
    if prediction.home_goals == official_result.home_goals and prediction.away_goals == official_result.away_goals:
        base = rules.exact_points
    elif prediction.outcome == official_result.outcome:
        base = rules.result_points
    else:
        base = 0
    return base * rules.brazil_multiplier if official_result.involves_brazil else base
```

### Pattern 4: Frontend release-aware gating

```tsx
type AccessGateProps = {
  approved: boolean;
  released: boolean;
  fallback: React.ReactNode;
  children: React.ReactNode;
};

export function AccessGate({ approved, released, fallback, children }: AccessGateProps) {
  if (!approved || !released) return <>{fallback}</>;
  return <>{children}</>;
}
```

### Pattern 5: Non-secret config structure

```yaml
scoring:
  exact_points: 3
  result_points: 1
  brazil_multiplier: 2
  champion_points: 10
  top_scorer_points: 15

sync:
  post_match_offset_minutes: 115
  allowed_terminal_statuses: [FT, AET, PEN]
  max_runs_per_day: 3

competition:
  prediction_close_key: predictionCloseAt
  explore_release_key: exploreReleaseAt
```

---

## Data Flow

```text
1. User registers or logs in through the React app.
   │
   ▼
2. Backend creates/authenticates the account and stores `access_status`.
   │
   ▼
3. Approved user saves predictions; pending/rejected/blocked users are denied server-side.
   │
   ▼
4. Admin imports or corrects official data through sync/manual override endpoints.
   │
   ▼
5. Sync service merges provider data, preserving manual overrides, then records SyncLog.
   │
   ▼
6. Recalculation service recomputes standings, bracket, top scorers, prediction points, and ranking.
   │
   ▼
7. Frontend reads refreshed ranking, bracket, official results, and Explore visibility.
```

---

## Integration Points

| External System | Integration Type | Authentication |
|-----------------|-----------------|----------------|
| API-Football via RapidAPI | REST API for fixtures/events/top scorers | `X-RapidAPI-Key` + host header |
| Google Sheets API | Optional REST/SDK fallback for manual-maintained data | Service account / OAuth credentials |
| Vercel Cron | Scheduled HTTPS trigger to backend sync endpoint | Shared admin secret token or signed header |
| PostgreSQL | Primary relational store | `DATABASE_URL` from existing env |

---

## Testing Strategy

| Test Type | Scope | Files | Tools | Coverage Goal |
|-----------|-------|-------|-------|---------------|
| Unit | Scoring formulas | `backend/tests/unit/test_scoring.py` | pytest | 100% of score branches |
| Unit | Group standings + best third ranking | `backend/tests/unit/test_standings.py` | pytest | 100% of tie-break ordering branches |
| Unit | Third-place slot allocation + propagation | `backend/tests/unit/test_bracket.py` | pytest | Exhaustive representative slot coverage |
| Integration | Auth/access/ranking/explore gates | `backend/tests/integration/test_member_access.py` | pytest + FastAPI test client | All status transitions |
| Integration | Sync, overrides, and recalculation | `backend/tests/integration/test_admin_sync.py` | pytest + provider mocks | All provider precedence paths |
| UI smoke | Login, pending state, prediction lock, Explore release | Build-phase manual or scripted smoke under `app/` | Playwright or manual smoke | Happy path + locked path |

---

## Error Handling

| Error Type | Handling Strategy | Retry? |
|------------|-------------------|--------|
| External API timeout | Log SyncLog failure, mark run incomplete, allow next scheduled/manual retry | Yes |
| Provider payload mismatch | Reject record, capture validation error context, preserve prior canonical data | No |
| Manual override conflict | Skip provider write and log `skipped_manual_override` | No |
| Unauthorized access | Return 401/403 with stable error payload; never leak admin-only data | No |
| Seed/bootstrap count mismatch | Abort seed transaction and report missing/extra records | No |

---

## Configuration

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `DATABASE_URL` | string | existing env | PostgreSQL connection string already present in `.env` |
| `API_FOOTBALL_KEY` | string | none | RapidAPI credential |
| `SYNC_ADMIN_TOKEN` | string | none | Auth for cron/manual sync trigger |
| `backend.config.app-settings.yaml.scoring.*` | ints | 3/1/2/10/15 | Rule values for score calculation |
| `backend.config.app-settings.yaml.sync.post_match_offset_minutes` | int | 115 | Delay window before processing scheduled matches |

---

## Security Considerations

- All participation rules (`APPROVED`, admin-only actions, Explore release) are enforced on backend reads and writes.
- Sessions use HTTP-only cookies or equivalent server-managed tokens; no rule authority lives in local storage.
- Secrets are never committed; `.env` is reused for `DATABASE_URL`, while new secrets are referenced only by variable name.
- Admin sync and override endpoints require admin auth plus a separate cron/shared secret for unattended execution.
- Provider payloads are validated before persistence to prevent malformed external data from corrupting ranking logic.

---

## Observability

| Aspect | Implementation |
|--------|----------------|
| Logging | Structured JSON logs in backend plus `SyncLog` table for business audit |
| Metrics | Counters for sync runs, skipped overrides, recalculation duration, and protected-route denials |
| Tracing | Request IDs propagated from frontend to backend logs; sync run IDs linked to recalculation events |

---

## Pipeline Architecture

### DAG Diagram

```text
[data/*.json] ─bootstrap─→ [PostgreSQL canonical tables] ──────────────┐
[API-Football] ─extract──→ [provider adapter] ─merge/reconcile─┐       │
[Google Sheets] ─extract→ [fallback adapter] ──────────────────┼─→ [official results/player stats]
[Admin override UI] ─manual fix────────────────────────────────┘       │
                                                                        ▼
                                                          [recalculation service]
                                                           ├─ standings/groups
                                                           ├─ best-third ranking
                                                           ├─ bracket propagation
                                                           ├─ prediction points
                                                           └─ ranking/explore reads
```

### Partition Strategy

| Table | Partition Key | Granularity | Rationale |
|-------|---------------|-------------|-----------|
| `sync_logs` | `created_at` | monthly | Operational history grows over tournament lifecycle |
| `matches` | none | none | MVP volume is low and query patterns are indexed by phase/starts_at |
| `predictions` | none | none | Single competition and <=100 users do not require partitioning |

### Incremental Strategy

| Model | Strategy | Key Column | Lookback |
|-------|----------|------------|----------|
| Tournament seed bootstrap | idempotent upsert | canonical external/code key | full bootstrap rerunnable |
| Official fixture sync | incremental by external id | `external_id` | current sync batch only |
| Ranking recomputation | affected-scope recompute | changed fixture / changed official stat | same transaction |

### Schema Evolution Plan

| Change Type | Handling | Rollback |
|-------------|----------|----------|
| New optional column | Add nullable/defaulted column, backfill separately | Drop column if unused |
| Enum expansion | Add enum value in migration before code path use | Keep old code paths compatible until rollback |
| Manual override granularity increase | Add explicit override metadata columns/tables without removing legacy flags first | Preserve legacy flags and disable new logic |

### Data Quality Gates

| Gate | Tool | Threshold | Action on Failure |
|------|------|-----------|-------------------|
| Seed count validation | pytest/bootstrap assertion | 48 teams, 72 group matches, 32 knockout matches | Block bootstrap |
| Ranking eligibility filter | integration tests | 0 non-approved users in ranking | Block release |
| Third-place slot completeness | unit/integration tests | 0 empty eligible slots after all groups finish | Block release |
| Override protection | integration tests | 0 overwritten manual fields | Block release |

---

## Validation Contract

> This section is read by `/workflow:validate` at Phase 3.5. Requirement IDs below are derived from the DEFINE goals/success criteria because DEFINE does not enumerate standalone REQ IDs.

### Spec Junta Targets (alignment + architecture)

| Requirement ID | Description | Expected Evidence in Code |
|----------------|-------------|---------------------------|
| REQ-001 | New registrations default to `PENDING` | `backend/app/api/routes/auth.py`, `backend/app/models/schema.py` |
| REQ-002 | Only `APPROVED` users can predict, rank, score, or access Explore | `backend/app/core/security.py`, `backend/app/api/routes/member.py`, `backend/tests/integration/test_member_access.py` |
| REQ-003 | Predictions lock at `predictionCloseAt` | `backend/app/api/routes/member.py`, `backend/config/app-settings.yaml`, UI locked state in `app/src/components/access/access-gate.tsx` |
| REQ-004 | Official scoring uses 3/1/0 + Brazil x2 + champion 10 + top scorer 15 | `backend/app/domain/scoring.py`, `backend/tests/unit/test_scoring.py` |
| REQ-005 | Admin can moderate users, configure windows, import data, and apply manual overrides | `backend/app/api/routes/admin.py`, `app/src/app/(admin)/dashboard/page.tsx`, `app/src/app/(admin)/users/page.tsx`, `app/src/app/(admin)/results/page.tsx`, `app/src/app/(admin)/settings/page.tsx` |
| REQ-006 | Official result/stat changes trigger recalculation of points, ranking, and top scorer | `backend/app/services/recalculation_service.py`, `backend/app/services/sync_service.py`, `backend/tests/integration/test_admin_sync.py` |
| REQ-007 | Canonical seeds load from `data/teams-groups.json`, `data/group-stage-matches.json`, `data/bracket-knockout.json` | `database/seeds/load_tournament_seed.py`, seed validation tests |
| REQ-008 | API-Football is primary provider; Google Sheets is optional fallback; admin panel is final fallback | `backend/app/integrations/api_football.py`, `backend/app/integrations/google_sheets.py`, `backend/app/services/sync_service.py` |
| REQ-009 | App calculates group standings, best-third ranking, round-of-32 slot assignment, and knockout propagation | `backend/app/domain/standings.py`, `backend/app/domain/bracket.py`, `backend/tests/unit/test_standings.py`, `backend/tests/unit/test_bracket.py` |
| REQ-010 | Explore only opens after `exploreReleaseAt` and only for approved users | `backend/app/api/routes/member.py`, `app/src/app/(member)/explore/page.tsx`, `backend/tests/integration/test_member_access.py` |
| REQ-011 | Ranking excludes non-approved users from scores, stats, and tie-breaks | `backend/app/repositories/queries.py`, `backend/app/api/routes/member.py`, `backend/tests/integration/test_member_access.py` |
| REQ-012 | Sync runs respect post-match timing and terminal statuses `FT`, `AET`, `PEN` with basic logging | `backend/config/app-settings.yaml`, `backend/app/services/sync_service.py`, `backend/tests/integration/test_admin_sync.py` |
| REQ-013 | All member/admin/public mock screens are implemented as explicit routes and consume backend-shaped DTOs | `app/src/app/(auth)/*`, `app/src/app/(member)/*`, `app/src/app/(admin)/*`, `backend/app/api/schemas/frontend.py`, `backend/tests/contract/test_frontend_contracts.py` |

**Architecture decisions to verify:**

| Decision | Expected Pattern in Code |
|----------|--------------------------|
| Next.js + FastAPI split | Separate `app/` and `backend/` entrypoints; no canonical rules in frontend |
| Server-side approval enforcement | Shared backend guard helpers used by member/admin routes |
| Deterministic rule modules | `scoring.py`, `standings.py`, `bracket.py` are pure rule modules with direct unit tests |
| Override-aware sync | Sync service checks manual override flags before provider writes and logs skipped updates |
| Static third-place lookup | `third_place_slot_matrix.json` loaded by `bracket.py`; tests assert slot mapping |
| Env + YAML config split | `config.py` loads `DATABASE_URL` from env and scoring/sync defaults from YAML |
| Mock-driven frontend contract | Each mock maps to a route and uses DTOs assembled by backend contract services |

---

### Code Junta Targets (quality + devops)

| Dimension | Expectation |
|-----------|-------------|
| Type hints | All Python functions/classes are fully typed; TS files use explicit component prop types |
| Error handling | External provider calls wrapped in typed exceptions; sync failures logged without corrupting canonical data |
| Test coverage | Unit tests for scoring, standings, and bracket; integration tests for auth/access and sync/override flows |
| DevOps | `DATABASE_URL` not duplicated; no secrets committed; backend and app have runnable dependency manifests |
| Security | Inputs validated at backend boundary; admin endpoints require admin auth; Explore/ranking guarded server-side |

---

### Delivery Junta Targets (manifest completeness)

All files in the File Manifest above are expected to exist in the code tree at build time.

| File | Delivery Status at Design Time |
|------|--------------------------------|
| `app/package.json` | Planned |
| `app/next.config.mjs` | Planned |
| `app/src/app/layout.tsx` | Planned |
| `app/src/app/(auth)/login/page.tsx` | Planned |
| `app/src/app/(auth)/create-account/page.tsx` | Planned |
| `app/src/app/(pending)/waiting/page.tsx` | Planned |
| `app/src/app/(member)/dashboard/page.tsx` | Planned |
| `app/src/app/(member)/initial-predictions/page.tsx` | Planned |
| `app/src/app/(member)/phase-predictions/page.tsx` | Planned |
| `app/src/app/(member)/results/page.tsx` | Planned |
| `app/src/app/(member)/ranking/page.tsx` | Planned |
| `app/src/app/(member)/bracket/page.tsx` | Planned |
| `app/src/app/(member)/explore/page.tsx` | Planned |
| `app/src/app/(admin)/dashboard/page.tsx` | Planned |
| `app/src/app/(admin)/users/page.tsx` | Planned |
| `app/src/app/(admin)/integration/page.tsx` | Planned |
| `app/src/app/(admin)/matches/page.tsx` | Planned |
| `app/src/app/(admin)/results/page.tsx` | Planned |
| `app/src/app/(admin)/players/page.tsx` | Planned |
| `app/src/app/(admin)/settings/page.tsx` | Planned |
| `app/src/components/access/access-gate.tsx` | Planned |
| `app/src/components/layout/member-shell.tsx` | Planned |
| `app/src/components/layout/admin-shell.tsx` | Planned |
| `app/src/lib/api-client.ts` | Planned |
| `app/src/lib/session.ts` | Planned |
| `app/src/lib/contracts.ts` | Planned |
| `backend/pyproject.toml` | Planned |
| `backend/app/main.py` | Planned |
| `backend/app/core/config.py` | Planned |
| `backend/config/app-settings.yaml` | Planned |
| `backend/app/core/security.py` | Planned |
| `backend/app/models/schema.py` | Planned |
| `backend/app/repositories/queries.py` | Planned |
| `backend/app/api/routes/auth.py` | Planned |
| `backend/app/api/routes/member.py` | Planned |
| `backend/app/api/routes/admin.py` | Planned |
| `backend/app/api/schemas/frontend.py` | Planned |
| `backend/app/domain/scoring.py` | Planned |
| `backend/app/domain/standings.py` | Planned |
| `backend/app/domain/bracket.py` | Planned |
| `backend/app/integrations/api_football.py` | Planned |
| `backend/app/integrations/google_sheets.py` | Planned |
| `backend/app/data/third_place_slot_matrix.json` | Planned |
| `backend/app/services/sync_service.py` | Planned |
| `backend/app/services/recalculation_service.py` | Planned |
| `backend/app/services/frontend_contract_service.py` | Planned |
| `database/migrations/versions/20260521_0001_init.py` | Planned |
| `database/seeds/load_tournament_seed.py` | Planned |
| `backend/tests/unit/test_scoring.py` | Planned |
| `backend/tests/unit/test_standings.py` | Planned |
| `backend/tests/unit/test_bracket.py` | Planned |
| `backend/tests/integration/test_member_access.py` | Planned |
| `backend/tests/integration/test_admin_sync.py` | Planned |
| `backend/tests/contract/test_frontend_contracts.py` | Planned |

**Acceptance criteria mapping** (from DEFINE → delivery evidence):

| Acceptance Test | Delivered By |
|-----------------|--------------|
| AT-001 Cadastro inicia pendente | `backend/tests/integration/test_member_access.py` |
| AT-002 Usuário pendente vê somente espera | `backend/tests/integration/test_member_access.py`, `app/src/app/(pending)/waiting/page.tsx` |
| AT-003 Aprovação libera participação | `backend/tests/integration/test_member_access.py`, `app/src/app/(member)/initial-predictions/page.tsx`, `app/src/app/(member)/phase-predictions/page.tsx` |
| AT-004 Fechamento bloqueia edição | `backend/tests/integration/test_member_access.py`, `backend/app/api/routes/member.py` |
| AT-004A Frontend público segue mocks de autenticação | `app/src/app/(auth)/login/page.tsx`, `app/src/app/(auth)/create-account/page.tsx`, `backend/tests/contract/test_frontend_contracts.py` |
| AT-005 Explore respeita liberação | `backend/tests/integration/test_member_access.py`, `app/src/app/(member)/explore/page.tsx` |
| AT-005A Frontend membro cobre todos os mocks principais | `app/src/app/(member)/dashboard/page.tsx`, `app/src/app/(member)/initial-predictions/page.tsx`, `app/src/app/(member)/phase-predictions/page.tsx`, `app/src/app/(member)/results/page.tsx`, `app/src/app/(member)/ranking/page.tsx`, `app/src/app/(member)/bracket/page.tsx`, `app/src/app/(member)/explore/page.tsx`, `backend/tests/contract/test_frontend_contracts.py` |
| AT-006 Usuário não aprovado não influencia ranking | `backend/tests/integration/test_member_access.py`, `backend/app/repositories/queries.py` |
| AT-007 Pontuação exata não acumula | `backend/tests/unit/test_scoring.py` |
| AT-008 Multiplicador do Brasil é aplicado | `backend/tests/unit/test_scoring.py` |
| AT-009 Override manual tem precedência | `backend/tests/integration/test_admin_sync.py` |
| AT-010 Mudança de estatística recalcula artilheiro | `backend/tests/integration/test_admin_sync.py` |
| AT-011 Seed inicial do torneio é carregado | `database/seeds/load_tournament_seed.py`, seed validation tests in build phase |
| AT-012 Ranking dos terceiros é calculado | `backend/tests/unit/test_standings.py` |
| AT-013 Slots TBD do Round of 32 são preenchidos | `backend/tests/unit/test_bracket.py` |
| AT-014 Vencedor propaga no mata-mata | `backend/tests/unit/test_bracket.py`, `backend/tests/integration/test_admin_sync.py` |
| AT-015 Sync não processa jogo ainda aberto | `backend/tests/integration/test_admin_sync.py` |
| AT-016 Console admin segue todos os mocks administrativos | `app/src/app/(admin)/dashboard/page.tsx`, `app/src/app/(admin)/users/page.tsx`, `app/src/app/(admin)/integration/page.tsx`, `app/src/app/(admin)/matches/page.tsx`, `app/src/app/(admin)/results/page.tsx`, `app/src/app/(admin)/players/page.tsx`, `app/src/app/(admin)/settings/page.tsx`, `backend/tests/contract/test_frontend_contracts.py` |

---

### Score Targets

| Junta | Minimum Score | Zero Tolerance |
|-------|---------------|----------------|
| Spec (alignment) | ≥ 90 | CRITICAL findings |
| Spec (architecture) | ≥ 90 | CRITICAL findings |
| Code (quality) | ≥ 90 | CRITICAL findings |
| Code (devops) | ≥ 70 | secrets in code |
| Delivery (delta) | ≥ 90 | missing manifest items |
| **Overall** | **≥ 90** | **0 CRITICAL** |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-21 | design-agent | Initial version |
| 1.1 | 2026-05-22 | iterate-agent | Expanded design for mock-driven frontend routes, backend DTO contracts, and full admin/member screen coverage |

---

## Next Step

**Ready for:** `/workflow:build ~/.config/opencode/sdd/features/bolao-copa-rdg/DESIGN_BOLAO_COPA_RDG.md`
