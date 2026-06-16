# Copa RDG Operating Contract

This repository is a production app. Treat this file as the operating contract for future work in this repo.

## Priority Order

1. Current user request.
2. This `AGENTS.md`.
3. Current code behavior.
4. The latest explicit decisions made in this chat.

If old ideas, stale drafts, or prior assumptions conflict with current code or the latest chat decision, ignore the old material and follow the code plus the latest decision.

## Mandatory Discovery and Tooling

- Inspect the repo first before changing behavior.
- Keep changes minimal and local to the actual bug or feature.
- Never revert or overwrite unrelated user work.
- Never mutate tracked files unless you are implementing the requested change.
- Do not rewrite app behavior from memory when the repo already encodes the contract.
- For any frontend redesign, UI fix, responsive regression, or rendered QA, call `@build-web-apps` directly and use:
  - `Build Web Apps:frontend-app-builder` for new surfaces, redesigns, or substantial UI modernization.
  - `Build Web Apps:frontend-testing-debugging` for browser/Playwright validation loops, desktop/mobile checks, and rendered regressions.
- For auth, admin, tokens, cron, sync, data integrity, or anything that can affect access or production data, call `@codex-security` directly and use the appropriate security skill:
  - `Codex Security:security-scan`
  - `Codex Security:security-diff-scan`
  - `Codex Security:validation`
  - `Codex Security:attack-path-analysis`
  - `Codex Security:threat-model`
  - `Codex Security:fix-finding`
  - `Codex Security:finding-discovery`
- For SQL, scoring, standings, bracket propagation, or contract payload changes, prefer the backend/postgres-oriented skill path instead of guessing from the UI.

## Validation Rules

- Every frontend change must verify both desktop and mobile.
- Every frontend change must verify the first meaningful viewport and at least one core interaction.
- Every frontend change must capture screenshot proof and console health.
- Build success alone is not enough.
- If Browser tooling is unavailable, use Playwright and state the fallback reason explicitly.
- Every backend behavior change needs targeted regression tests on the touched route or service plus the exact failure case the bug exposed.
- For visual or redesign-adjacent work, compare the rendered UI against the intended result before finalizing.
- Temporary screenshots, traces, and QA scripts stay outside the repo unless explicitly requested.

## App Structure

- The app is split into:
  - `app/` Next.js frontend
  - `backend/` FastAPI backend
  - `data/` seed and lookup assets
- The backend is the canonical source for:
  - approval status
  - Explore visibility
  - ranking eligibility
  - score calculation
  - lock semantics
  - sync and audit behavior
- The client only renders contracts. It must not re-implement canonical business rules.

## Member Area Rules

### Shell and Navigation

- Keep the current member nav order stable unless the user explicitly requests a nav change.
- Preserve the admin switch on mobile. Do not hide the toggle just because the viewport is narrow.
- Logout must remain CSRF-protected.
- The member shell must keep the current dark theme and density unless the task explicitly changes the design system.

### Dashboard

- Preserve the overview cards, next matches, ranking snapshot, phase status, and quick actions.
- The `Explore` status shown on the dashboard is derived from session timing.
- Mobile should remain a compact version of the same information architecture, not a different product pattern.
- Do not collapse the dashboard into a generic card grid that loses the current hierarchy.

### Ranking

- Always show the full breakdown explicitly:
  - `exactPoints`
  - `resultPoints`
  - `brazilPoints`
  - `championPoints`
  - `topScorerPoints`
  - `bonusPoints`
  - `totalPoints`
- Avoid ambiguous labels such as `Camp.`.
- Keep the “my points” section legible on mobile.
- If the backend returns a breakdown, render it. Do not hide it behind a generic fallback.

### Standings

- Preserve the group table semantics, qualification highlighting, and standings ordering.
- On mobile, prefer flags and compact team badges over raw numeric emphasis.
- Do not allow side-by-side compression that clips rows or columns.
- Keep the meaning of J/V/E/D/GF/GC/SG/Pts intact.

### Results

- Keep official score versus predicted score visible for each match.
- On mobile, stack vertically instead of compressing into a narrow side-by-side comparison.
- The page should clearly separate per-match outcome from total/breakdown context.

### Phase Predictions

- Lock is per match, not just per round.
- Partial states are valid and must not be flattened into a binary message if the round is mixed.
- Force-lock overrides always win.
- Save controls must only appear when at least one match is editable.
- Messaging must match the real editable state, not a coarse round-level assumption.
- `nextLockAt` and all lock messaging must reflect the actual per-match timing.

### Explore

- `lockAt` and `exploreAt` are separate rules.
- `exploreAt` controls public visibility.
- `lockAt` controls editability.
- Force-locked rounds may still be public in Explore.
- Champion and top-scorer remain public.
- Public match predictions must be listed in date order across all public games.
- Search must operate over the full public set, not only the featured card.
- When the Explore fetch fails, show an explicit unavailable/error state instead of a fake locked state.
- Do not let the featured game card become the search universe.

### Auth Screens

- Login, create-account, register redirect, forgot-password, reset-password, and waiting states must preserve redirect and approval semantics.
- Pending users should never bleed into approved member flows.
- Anonymous users should redirect through the auth flow, not into member content.

## Admin Area Rules

### Admin Shell and Pages

- Keep the admin shell readable and operational on desktop and mobile.
- Preserve the admin navigation and the switch back to the member area.
- The admin console must remain clearly separated from the member shell.

### Admin Dashboard / Users / Matches / Players / Settings

- Keep the operational meaning of each page clear.
- Do not collapse these pages into generic CRUD screens that hide the current task model.
- Settings must preserve the competition window and phase configuration concepts already implemented in code.

### Integration

- `SYNC_ADMIN_TOKEN` and similar secrets stay in environment variables only.
- Never hardcode tokens or provider keys.
- Any automatic sync or cron behavior must be visible in code, testable, and safe to run repeatedly.
- Manual “run now” and scheduled operation are separate concerns.
- The first stable path for sync changes should be code-driven, not platform-click dependent.
- Preserve manual overrides.
- Keep sync idempotent.
- Record auditable skip/success/failure reasons.
- When official results change, recompute derived competition state immediately.

### Results Sync

- Sync logic must preserve manual overrides unless admin explicitly changes them.
- Skip reasons must be explainable from logs or response payloads.
- Any sync path that changes results must be auditable enough to explain what happened after the fact.

## Backend Canon

- Approval is enforced server-side on every protected read/write path.
- Protected reads/writes must not trust the client for eligibility.
- Ranking and Explore queries must exclude non-approved users from the canonical result set.
- Screen DTOs and route-specific payloads should stay explicit and stable.
- Do not let the frontend infer hidden rule logic from raw database rows.
- If a change depends on time windows, the backend is the source of truth.
- If the backend changes a data model, update the contract and the tests together.

## Security and Data Rules

- Use `Codex Security` for auth/admin/sync/token work before merge when the change is security-relevant.
- If a change touches access control, data integrity, or production-facing sync, treat it as security-sensitive by default.
- Keep auditability high for admin-triggered changes to results, users, settings, sync, and visibility.
- Preserve the precedence of manual corrections over provider data unless admin explicitly changes it.

## Page-by-Page Behavior Contract

- `app/src/app/(auth)/login/page.tsx`
  - preserve login redirect behavior and auth error handling.
- `app/src/app/(auth)/create-account/page.tsx`
  - preserve the pending-user creation flow.
- `app/src/app/(pending)/waiting/page.tsx`
  - preserve pending approval messaging and redirect logic.
- `app/src/app/(member)/dashboard/page.tsx`
  - preserve summary cards, ranking snapshot, next matches, quick actions, and Explore timing state.
- `app/src/app/(member)/initial-predictions/page.tsx`
  - preserve champion/top-scorer entry and lock behavior.
- `app/src/app/(member)/phase-predictions/page.tsx`
  - preserve per-match lock/edit behavior and partial round states.
- `app/src/app/(member)/results/page.tsx`
  - preserve score/result comparison and points breakdown.
- `app/src/app/(member)/ranking/page.tsx`
  - preserve explicit breakdown metrics and current-user breakdown.
- `app/src/app/(member)/standings/page.tsx`
  - preserve group standings semantics and mobile identity cues.
- `app/src/app/(member)/bracket/page.tsx`
  - preserve bracket propagation and resolution from standings.
- `app/src/app/(member)/explore/page.tsx`
  - preserve public match visibility, full public search, and explicit error/unavailable state.
- `app/src/app/(admin)/admin/dashboard/page.tsx`
  - preserve operational overview.
- `app/src/app/(admin)/admin/users/page.tsx`
  - preserve approval and moderation workflows.
- `app/src/app/(admin)/admin/matches/page.tsx`
  - preserve match management and sync-adjacent operations.
- `app/src/app/(admin)/admin/results/page.tsx`
  - preserve result import, overrides, and audit state.
- `app/src/app/(admin)/admin/players/page.tsx`
  - preserve player statistics management.
- `app/src/app/(admin)/admin/integration/page.tsx`
  - preserve manual run-now sync control, scheduling knobs, and status visibility.
- `app/src/app/(admin)/admin/settings/page.tsx`
  - preserve competition windows and phase settings.

## Testing Expectations

- For frontend work:
  - verify desktop and mobile
  - verify the first viewport
  - verify at least one interaction
  - verify console health
  - verify screenshots
- For backend work:
  - add or update targeted regression tests for the touched route or service
  - include the exact bug case, not just a happy path
- For Explore/ranking/results/standings/dashboard:
  - verify no unintended copy, ordering, or visibility regression
  - verify the mobile layout remains readable
- For security-sensitive work:
  - run the matching `Codex Security` skill before merge

## Operating Assumptions

- This file is the repo execution contract, not a replacement for product specs.
- The most recent explicit chat decision can override earlier assumptions.
- If a page already works on mobile, prefer surgical corrections over redesign.
- If a new behavior is not obviously supported by the code, inspect the implementation first and do not invent a contract.
