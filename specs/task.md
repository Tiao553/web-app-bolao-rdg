# Task Breakdown — BOLAO_COPA_RDG

## Active Target

Target: Chunk 6 - Persistence and evidence

## Sub-tasks

- [x] 1.1 `[workflow.build-agent]` Confirm build output path and persist it in `specs/BUILD_OUTPUT_PATH.txt`
- [x] 1.2 `[workflow.build-agent]` Load workflow contract, build command, routing, DESIGN, DEFINE, and assigned specialist instructions
- [x] 1.3 `[frontend-react-agent]` Create `app/package.json`
- [x] 1.4 `[frontend-react-agent]` Create `app/next.config.mjs`
- [x] 1.5 `[python.python-developer]` Create `backend/pyproject.toml`
- [x] 1.6 `[python.python-developer]` Create `backend/config/app-settings.yaml`
- [x] 1.7 `[python.python-developer]` Create `backend/app/core/config.py`
- [x] 1.8 `[workflow.build-agent]` Run verification commands for Chunk 1
- [x] 1.9 `[workflow.build-agent]` Persist global `BUILD_REPORT_BOLAO_COPA_RDG.md` and copy it flat to `./specs/`
- [x] 1.10 `[workflow.build-agent]` Stop and hand off next chunk recommendation

## Chunk 2 Sub-tasks

- [x] 2.1 `[workflow.build-agent]` Resume active build context and confirm Chunk 2 is the next pending chunk
- [x] 2.2 `[frontend-react-agent]` Create `app/src/app/layout.tsx`
- [x] 2.3 `[frontend-react-agent]` Create `app/src/components/access/access-gate.tsx`
- [x] 2.4 `[frontend-react-agent]` Create `app/src/lib/api-client.ts`
- [x] 2.5 `[frontend-react-agent]` Create `app/src/lib/session.ts`
- [x] 2.6 `[workflow.build-agent]` Run verification commands for Chunk 2
- [x] 2.7 `[workflow.build-agent]` Persist global `BUILD_REPORT_BOLAO_COPA_RDG.md` and copy it flat to `./specs/`
- [x] 2.8 `[workflow.build-agent]` Stop and hand off next chunk recommendation

## Chunk 3 Sub-tasks

- [x] 3.1 `[workflow.build-agent]` Resume active build context and confirm Chunk 3 is the next pending chunk
- [x] 3.2 `[python.python-developer]` Create `backend/app/core/security.py`
- [x] 3.3 `[python.python-developer]` Create `backend/app/models/schema.py`
- [x] 3.4 `[python.python-developer]` Create `backend/app/repositories/queries.py`
- [x] 3.5 `[python.python-developer]` Create `backend/app/main.py`
- [x] 3.6 `[workflow.build-agent]` Run verification commands for Chunk 3
- [x] 3.7 `[workflow.build-agent]` Persist global `BUILD_REPORT_BOLAO_COPA_RDG.md` and copy it flat to `./specs/`
- [x] 3.8 `[workflow.build-agent]` Stop and hand off next chunk recommendation

## Chunk 4 and 5 Sub-tasks

- [x] 4.1 `[workflow.build-agent]` Reclassified remaining work as coupled Chunks 4 and 5
- [x] 4.2 `[frontend-react-agent]` Create auth, waiting, dashboard, predictions, ranking, and explore pages
- [x] 4.3 `[python.python-developer]` Create backend auth, member, and admin route files
- [x] 5.1 `[rules-qa-agent]` Create scoring, standings, bracket, and third-place slot matrix artifacts
- [x] 5.2 `[external-integration-agent]` Create API-Football adapter, Google Sheets fallback adapter, and sync service
- [x] 5.3 `[python.python-developer]` Create recalculation service and wire backend entrypoint routers
- [x] 5.4 `[workflow.build-agent]` Run verification commands for Chunks 4 and 5
- [x] 5.5 `[workflow.build-agent]` Persist global `BUILD_REPORT_BOLAO_COPA_RDG.md` and copy it flat to `./specs/`
- [x] 5.6 `[workflow.build-agent]` Stop and hand off next chunk recommendation

## Pending Later Chunks

## Chunk 6 Sub-tasks

- [x] 6.1 `[workflow.build-agent]` Resume active build context and confirm Chunk 6 is the only remaining chunk
- [x] 6.2 `[python.python-developer]` Create initial migration file `database/migrations/versions/20260521_0001_init.py`
- [x] 6.3 `[python.python-developer]` Create idempotent seed loader `database/seeds/load_tournament_seed.py`
- [x] 6.4 `[test.test-generator]` Create unit tests for scoring, standings, and bracket modules
- [x] 6.5 `[test.test-generator]` Create integration tests for member access and admin sync flows
- [x] 6.6 `[workflow.build-agent]` Run verification commands for Chunk 6`
- [x] 6.7 `[workflow.build-agent]` Persist global `BUILD_REPORT_BOLAO_COPA_RDG.md` and copy it flat to `./specs/`
- [x] 6.8 `[workflow.build-agent]` Mark build complete and hand off to `/workflow:validate`

## Pending Later Chunks

- [x] No pending build chunks remain
