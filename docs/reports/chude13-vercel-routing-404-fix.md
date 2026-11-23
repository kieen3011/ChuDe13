# ChuDe13 — Vercel FastAPI routing 404 fix

Date: 2026-11-23 (Asia/Saigon)
Branch: `fix/chude13-vercel-integration-audit`
Base commit: `d64ca4cff65d4de23b17d0f7dd3c76f11d8c27c8`

## 1. Exact root cause

The deployed repository had two competing FastAPI entrypoint mechanisms:

- `pyproject.toml` correctly declared `backend.routers.main:app`.
- Root `index.py` was also a filename-based Vercel entrypoint, but its `sys.path` manipulation imported `backend/routers/main.py` as the top-level module `main`. That breaks the relative imports inside `main.py`. A direct import reproduced `ImportError: attempted relative import with no known parent package`.

At the same time, `app.mount("/", StaticFiles(...))` was promoted into Vercel CDN routes. The deployed Resources view showed the resulting Python function at the internal `/fastapi` path, while public `/api/...` paths were not reaching the ASGI application. Directly changing the browser API base to `/fastapi` would be incorrect because `/fastapi` is a Vercel build output detail, and FastAPI would receive the prefixed path.

Vercel's current documentation says a custom module should be selected with `tool.vercel.entrypoint`, and `tool.vercel.fastapi.static.cdn = false` keeps frontend/static requests inside the FastAPI function. The fix therefore uses one entrypoint only and opts out of static CDN promotion so FastAPI owns routing for `/`, `/api/...`, `/openapi.json`, and asset paths.

No `vercel.json` rewrite was added. A rewrite to `/fastapi` would couple source code to an internal function path and, with current Python runtime behavior, could expose the rewritten destination path to the application.

References:

- [Vercel FastAPI entrypoints and static routing](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Python custom entrypoints](https://vercel.com/docs/functions/runtimes/python)
- [Vercel rewrites](https://vercel.com/docs/routing/rewrites)

## 2. Files changed

| File | Change | Reason |
|---|---|---|
| `index.py` | Deleted | Remove the duplicate, invalid filename-based entrypoint |
| `pyproject.toml` | Added `[tool.vercel.fastapi.static] cdn = false` | Ensure all public paths reach FastAPI instead of a root CDN static route |
| `backend/routers/main.py` | Replaced root `StaticFiles` mount with `app.frontend(..., fallback=None)` | Give API routes unconditional priority and keep frontend handling explicit |
| `tests/test_web_api.py` | Added Vercel config and OpenAPI routing regression tests | Prevent reintroducing multiple entrypoints or missing API routes |
| `docs/reports/chude13-vercel-routing-404-fix.md` | Added this report | Record evidence, blockers, commit and redeploy steps |

The pre-existing dirty files `src/expense_service.py`, `-files --others --exclude-standard`, `backend/routers/database.pre-neon.py`, `backend/routers/main.pre-neon.py`, and `src/expense_service.before_restore.py` were not modified.

## 3. Test results

| Test | Result | Evidence |
|---|---|---|
| Custom entrypoint import | PASS | `backend.routers.main:app` imports with isolated SQLite environment |
| Broken root `index.py` reproduction | CONFIRMED | Direct import failed with relative-import error before deletion |
| `/` dashboard | PASS | ASGI integration test returns HTML 200 |
| `/app.js`, `/styles.css` | PASS | ASGI integration tests return 200 |
| `/api/health` | PASS | Returns `{"status":"ok"}` with isolated SQLite DB |
| `/api/demo/state` | PASS | GET/PUT/OCC tests pass |
| `/openapi.json` | PASS | Contains `/api/health`, `/api/demo/state`, `/api/items/` |
| Focused web/API suite | PASS | 13 tests passed |
| Frontend sync suite | PASS | 5 tests passed |
| Non-legacy regression suite | PASS | 46 tests and 13 subtests passed |
| Python/JavaScript syntax | PASS | `compileall`, `node --check` |
| `vercel dev --local` | BLOCKED | Vercel CLI 66.6.0 failed on Windows cache symlink creation with `DEV_SYSCALL_ERROR/EPERM` |
| New Vercel Preview HTTP test | BLOCKED | No push/deploy was authorized or performed |
| Neon Staging connection | BLOCKED | Not exercised during this routing-only fix |

## 4. Unresolved items

- A new Preview deployment must prove that public `/api/...` requests reach FastAPI. Local ASGI tests cannot prove Vercel's deployed routing table.
- `/api/health` includes a database query. If routing is fixed but Neon Staging is unavailable or misconfigured, it should return a database error rather than the old Vercel 404.
- The public mutation API is still unauthenticated; keep Preview protected.
- `vercel dev` requires Windows Developer Mode/administrator symlink permission or a Linux/WSL environment to run locally on this machine.

## 5. Commit only this routing fix

Review first:

```powershell
git diff -- index.py pyproject.toml backend/routers/main.py tests/test_web_api.py docs/reports/chude13-vercel-routing-404-fix.md
```

Stage only the routing fix, excluding all pre-existing dirty/backup files:

```powershell
git add -- index.py pyproject.toml backend/routers/main.py tests/test_web_api.py docs/reports/chude13-vercel-routing-404-fix.md
git diff --cached --check
git diff --cached
git commit -m "fix: route Vercel requests through FastAPI"
```

No push command was run. When approved, push this branch explicitly:

```powershell
git push origin fix/chude13-vercel-integration-audit
```

## 6. Redeploy Vercel Preview

1. Keep Vercel Root Directory at the repository root, not `frontend`.
2. Keep Framework Preset as FastAPI/automatic detection.
3. Keep Build Command and Output Directory empty/default.
4. Confirm Preview has the Neon Staging `DATABASE_URL`; do not copy Production credentials.
5. Push the reviewed commit to `fix/chude13-vercel-integration-audit` and wait for a new Preview deployment.
6. Do not reuse the old deployment; verify the deployment commit SHA is the new routing commit.
7. Test in this order:
   - `GET /openapi.json` — must return OpenAPI JSON and list the API paths.
   - `GET /api/demo/state` — must return JSON, not Vercel `NOT_FOUND`.
   - `GET /api/health` — must return `{"status":"ok"}` when Neon Staging is reachable.
   - `GET /` — must render the dashboard.
   - `GET /app.js` and `GET /styles.css` — must return 200.
8. Inspect runtime logs with:

```powershell
vercel logs --deployment <preview-url> --level error --since "1 h" --expand
```

Do not promote to Production until the new Preview passes these HTTP checks.

## 7. Verdict

**LOCAL_FIX_TESTED — PREVIEW_REDEPLOY_REQUIRED**

The source-level entrypoint and routing conflict is fixed and covered by local regression tests. Vercel deployment success remains unconfirmed until a new Preview is built from the new commit and tested over HTTPS.
