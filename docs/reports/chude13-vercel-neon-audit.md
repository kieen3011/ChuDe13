# ChuDe13 — Vercel + FastAPI + Neon audit

Audit date: 2026-11-23 (Asia/Saigon)
Audit branch: `fix/chude13-vercel-integration-audit`
Base commit: `6a22cdf0f1b2f79baffd5d51d64ff437014a7530` (`update-new-version`)
Final verdict: **READY_FOR_STAGING_ONLY**

## A. Executive Summary

The starting branch contained the most complete frontend/backend integration, but it could not work as a single Vercel deployment: the browser called `http://127.0.0.1:8000`, FastAPI did not serve the static frontend, and the Vercel project had previously used `frontend` as its Root Directory. The original OCC implementation also allowed `expected_version > 0` to insert a missing record and could discard a newer browser mutation after a 409 response.

The implementation now serves the HTML/CSS/JS from the FastAPI app, uses same-origin `/api/...` requests, validates persisted state, performs atomic compare-and-update OCC, preserves the newest local snapshot on conflicts/errors, and prevents the demo reset action from writing to Neon. Open CORS was removed; cross-origin access is opt-in through `CORS_ORIGINS`.

The configured local `DATABASE_URL` was inspected without printing or connecting to it. It is present, uses PostgreSQL, points to a Neon pooled endpoint, and includes a TLS option. PostgreSQL JSONB DDL compiles successfully. No read or write was sent to Neon Production.

Staging is still blocked from a final deployment PASS because no Vercel Preview was deployed or inspected, no isolated Neon test branch was provided for an end-to-end PostgreSQL write test, and the public write/delete API has no user authentication. Production should not be exposed until authentication/authorization is added or the whole deployment is protected at the Vercel edge.

The working tree was already dirty before this audit. The pre-existing modification to `src/expense_service.py` and pre-existing untracked backup files were preserved and are not part of this fix.

## B. Findings Matrix

| ID | Severity | File | Root cause | Evidence | Remediation | Status |
|---|---|---|---|---|---|---|
| F-01 | Critical | `frontend/app.js` | Production browser called localhost | Original line used `http://127.0.0.1:8000` | Use empty base URL and same-origin `/api` | TESTED |
| F-02 | Critical | `backend/routers/main.py` | No route served the frontend in the FastAPI project | `/` returned JSON and static files were not mounted | Mount `frontend/` with `StaticFiles` after API routes | TESTED |
| F-03 | High | `backend/routers/demo.py` | The upsert path inserted a row when `expected_version > 0` and row `id=1` was absent | Regression test uses `expected_version=7` on an empty DB | Replace upsert with conditional `UPDATE ... WHERE version = expected_version RETURNING` | TESTED |
| F-04 | High | `frontend/app.js` | A 409 cleared a newer queued snapshot and resolved the conflict with the older in-flight snapshot | Node regression test mutates while PUT is pending | Resolve with queued/localStorage latest snapshot before clearing the queue | TESTED |
| F-05 | High | `frontend/app.js` | “Server record exists” was inferred from a non-empty groups array | A valid versioned record can contain `groups: []` | Use `version > 0` to identify record existence | TESTED |
| F-06 | High | `frontend/app.js` | Demo reset could overwrite the shared Neon state | Reset used the normal server persistence pipeline | Make reset local-only, clear pending write, require later explicit reconciliation | TESTED |
| F-07 | High | `backend/routers/main.py` | CORS allowed every origin and credentials | `allow_origins=["*"]`, `allow_credentials=True` | Same-origin by default; exact opt-in `CORS_ORIGINS` only | TESTED |
| F-08 | High | `backend/routers/demo.py`, `backend/routers/items.py` | PUT/POST/DELETE endpoints have no authentication or ownership model | Any caller reaching the deployment can mutate shared data | Protect Preview with Vercel Deployment Protection; design app authentication before public Production | BLOCKED |
| F-09 | High | Vercel/Neon external systems | No authorized Preview deployment or isolated Neon test branch was available | Vercel CLI is absent; Production DB writes were prohibited | Deploy a protected Preview and test against a Neon Preview branch | BLOCKED |
| F-10 | Medium | `pyproject.toml` | UTF-8 BOM made TOML parsing fail | Initial pytest run: `Invalid statement (line 1, column 1)` | Recreate file as BOM-free UTF-8 | TESTED |
| F-11 | Medium | `requirements.txt`, `pyproject.toml` | Runtime dependencies were unpinned and Python version unspecified | Original files used bare package names | Pin tested versions and declare Python 3.13 | TESTED |
| F-12 | Medium | `backend/routers/schemas.py` | Demo state accepted arbitrary nested dictionaries | Invalid member references reached persistence | Add bounded structured state models and reference validation | TESTED |
| F-13 | Medium | `frontend/app.js` | Startup handlers could accept edits before local/server reconciliation completed | `handleStartupResolution()` was not awaited | Await reconciliation before registering mutation handlers | TESTED |
| F-14 | Medium | `frontend/app.js` | Failed writes were removed from the in-memory queue | Network/500 branch did not restore the failed snapshot | Retain latest snapshot and retry on later mutation/online event | TESTED |
| F-15 | Medium | legacy SQLite tests | Nine tests require the absent `database/group_expense.db` fixture and fixed IDs | Full suite: 9 failed, 42 passed before the final added test | Provide a disposable fixture instead of relying on a developer DB | BLOCKED |
| F-16 | Low | `.gitignore`, tracked files | Secret handling needed verification | `.env` is ignored; tracked credential-pattern scan returned no files | Keep `DATABASE_URL` only in environment settings | TESTED |

## C. Changed Files

| File | Change | Compatibility risk |
|---|---|---|
| `backend/routers/database.py` | Psycopg 3 normalization, pre-ping/recycle settings, isolated SQLite test support | Production should use the Neon pooled URL; no schema/data deletion |
| `backend/routers/demo.py` | Atomic OCC insert/update, rollback, non-leaking 500 handling | Concurrent stale writers now receive 409 consistently |
| `backend/routers/items.py` | Preserves CRUD routes while removing detailed database-error logging | Public mutation remains an authentication blocker |
| `backend/routers/main.py` | Lifespan table creation, health route, restricted CORS, static frontend mount | `/` now serves the website; health moved to `/api/health` |
| `backend/routers/schemas.py` | Structured and bounded demo state validation | Previously stored malformed states may fail response validation and need manual review |
| `frontend/app.js` | Same-origin API, timeout/error handling, safe queue/conflict/startup logic, local-only reset | Users who explicitly select local-only must click “Bật lại đồng bộ” to reconcile |
| `frontend/index.html` | Adds the “Bật lại đồng bộ” action | Minimal UI addition only |
| `pyproject.toml` | BOM removal, Python/runtime pins, Vercel entrypoint, pytest discovery | Requires Python 3.12–3.13; `.python-version` selects 3.13 |
| `requirements.txt` | Exact tested runtime versions | Upgrades must be intentional and retested |
| `.python-version` | Selects Python 3.13 | Vercel must use a currently supported 3.13 runtime |
| `requirements-dev.txt` | Reproducible test dependencies | Development only |
| `tests/test_web_api.py` | Static/API/OCC/422/500/CORS regression tests | Uses SQLite in-memory only |
| `tests/frontend_sync.test.mjs` | Browser-state pipeline regression tests with Node VM | Simulates browser APIs; not a real browser E2E test |

Not changed by this audit: `src/expense_service.py`, `-files --others --exclude-standard`, `backend/routers/*.pre-neon.py`, root `index.py`, and `src/expense_service.before_restore.py`. They were already modified/untracked and must be reviewed separately before commit.

## D. Test Results

| Test ID | Scope | Result | Evidence |
|---|---|---|---|
| T-01 | Python syntax/import | PASS | `compileall`; FastAPI entrypoint import with SQLite environment |
| T-02 | JavaScript syntax | PASS | `node --check frontend/app.js` |
| T-03 | Frontend queue, rapid PUT, 409, network failure, local reload | PASS | 5/5 Node tests |
| T-04 | Static frontend, health, items CRUD, GET/PUT, persistence, OCC, 409, 422, 500 rollback, CORS | PASS | 11/11 API tests on SQLite in-memory |
| T-05 | Repository tests not dependent on missing legacy DB | PASS | 44 tests and 13 subtests passed |
| T-06 | Complete legacy suite | BLOCKED | 9 failures require absent `database/group_expense.db`; other 42 tests passed in that run |
| T-07 | PostgreSQL model compatibility | PASS | `demo_state` DDL compiled with PostgreSQL dialect and contains JSONB |
| T-08 | Neon URL safety/config | PASS | Configured, PostgreSQL, Neon host, pooled endpoint, TLS option; values not printed |
| T-09 | Neon Preview GET/PUT and real transaction race | BLOCKED | No isolated Neon test credentials; Production was intentionally untouched |
| T-10 | Vercel Preview build/runtime/routing | BLOCKED | No deployment authorization/access; Vercel CLI not installed |
| T-11 | Secret baseline | PASS | `.env` ignored; tracked credential-pattern scan empty; `pip check` clean |
| T-12 | Real browser refresh/persistence | BLOCKED | Reload behavior is unit-tested through localStorage, but no browser E2E runtime was available |

## E. Vercel Deployment Instructions

These settings follow Vercel's current [Python runtime and custom entrypoint documentation](https://vercel.com/docs/functions/runtimes/python) and its support for [FastAPI StaticFiles on the CDN](https://vercel.com/changelog/fastapi-frontends-and-static-files-served-from-the-cdn). Neon recommends a pooled endpoint for request-driven/serverless applications; its FastAPI example uses Psycopg 3 with `pool_recycle=300` and a pooled TLS URL in [Neon's FastAPI guide](https://neon.com/blog/deploy-a-serverless-fastapi-app-with-neon-postgres-and-aws-app-runner-at-any-scale).

### Project settings

- Branch for Preview: `fix/chude13-vercel-integration-audit`, after reviewing/committing only the intended files and pushing the branch.
- Root Directory: repository root (`.` / leave the field empty). Do **not** use `frontend`.
- Framework Preset: FastAPI (automatic detection is acceptable).
- Build Command: leave empty/default.
- Output Directory: leave empty/default.
- Install Command: leave empty/default; dependencies come from `pyproject.toml`/`requirements.txt`.
- Python: 3.13 from `.python-version`.
- Environment variables:
  - `DATABASE_URL` — required; use a pooled Neon **Preview branch** URL with TLS for Preview.
  - `CORS_ORIGINS` — optional; leave unset for this same-origin deployment.
- Protect the Preview deployment with Vercel Deployment Protection because write endpoints are unauthenticated.
- Place the Vercel Function region near the Neon region when possible.

### Preview verification

1. Open `/`; confirm HTML, `/styles.css`, and `/app.js` return 200 over HTTPS.
2. Open `/api/health`; expect `{"status":"ok"}`.
3. GET `/api/demo/state`; on a fresh isolated Neon branch expect version 0 and an empty groups array.
4. PUT a disposable state with `expected_version: 0`; expect version 1.
5. Repeat the stale PUT with `expected_version: 0`; expect HTTP 409.
6. Reload the browser; confirm the state is restored and version is displayed.
7. Simulate offline mode, make a local change, reconnect, and resolve the explicit conflict dialog.
8. Confirm `/api/items/` still returns the expected response.
9. Inspect runtime errors with `vercel logs --deployment <preview-url> --level error --since "1 h" --expand` and build logs with `vercel inspect <preview-url> --logs`. The current CLI syntax is documented in [Vercel logs](https://vercel.com/docs/cli/logs).

Do not run PUT tests against the existing Production Neon record. Create a Neon Preview branch or a separate test database first.

### Redeploy and rollback

1. Commit only intended audit files; exclude all pre-existing dirty/untracked files listed above.
2. Push the audit branch and let Vercel create a Preview deployment.
3. Run every Preview verification step before any Production promotion.
4. Promote only after authentication/protection is approved and the blocker tests pass.
5. If Production fails, use Deployments → previous eligible deployment → **Instant Rollback**, or `vercel rollback [deployment-id-or-url]`. Verify with `vercel rollback status`. See [Vercel Instant Rollback](https://vercel.com/docs/instant-rollback).

## F. Final Verdict

**READY_FOR_STAGING_ONLY**

The code path is locally tested and structurally compatible with Vercel FastAPI + same-origin static serving + Neon PostgreSQL. It is not `READY_FOR_DEPLOYMENT` to public Production because Vercel Preview, isolated Neon PostgreSQL writes, real browser E2E, and API authentication remain unresolved.
