# QA Production Smoke v2.1

Tujuan: runbook smoke produksi untuk release gate owner/admin.  
Aturan: stop saat ada failure security. Jangan klaim PASS kalau proof belum ada.

## Asset

- `scripts/production_smoke.py`
- dokumen ini
- `docs/QA_REGRESSION_MATRIX.md`

## Cara Jalan

```powershell
python .\scripts\production_smoke.py
python .\scripts\production_smoke.py --with-mutations
python .\scripts\production_smoke.py --json
```

## Env Wajib

- `SMOKE_API_BASE_URL`

## Env Opsional

- `SMOKE_WEB_BASE_URL`
- `SMOKE_CORS_ORIGIN`
- `SMOKE_LOGIN_EMAIL`
- `SMOKE_LOGIN_PASSWORD`
- `SMOKE_REGISTER_EMAIL`
- `SMOKE_REGISTER_PASSWORD`
- `SMOKE_REGISTER_DISPLAY_NAME`
- `SMOKE_AGENT_NAME`
- `SMOKE_AGENT_SLUG`
- `SMOKE_AGENT_DESCRIPTION`
- `SMOKE_AGENT_ROLE_DESCRIPTION`
- `SMOKE_AGENT_INSTRUCTION_TEXT`
- `SMOKE_MODEL_PROVIDER_ID`
- `SMOKE_MODEL_NAME`
- `SMOKE_GITHUB_REPO_URL`
- `SMOKE_GITHUB_BRANCH`
- `SMOKE_GITHUB_FILE_PATH`
- `SMOKE_GITHUB_COLLECTION_REPO_URL`
- `SMOKE_GITHUB_COLLECTION_BRANCH`
- `SMOKE_GITHUB_SKILL_NAME`
- `SMOKE_GITHUB_SKILL_SLUG`
- `SMOKE_GITHUB_SKILL_VERSION`
- `SMOKE_GITHUB_REVIEW_NOTES`
- `SMOKE_PROVIDER_NAME`
- `SMOKE_PROVIDER_API_KEY`

## Run Order

1. Backend health
2. Frontend load check
3. CORS origin check
4. Auth contract
5. Agent contract
6. GitHub import contract
7. Skill attach/detach contract
8. Provider key contract
9. Logs/tasks/approvals read-only
10. Runtime/n8n guard contract

## Endpoint Yang Diaudit

### Auth

- `GET /auth/me`
- `POST /auth/login`
- `POST /auth/register`

### Agents

- `GET /agents`
- `POST /agents`
- `GET /agents/{agent_id}`
- `GET /agents/{agent_id}/active-skills`
- `POST /agents/{agent_id}/skills/imported/{skill_id}`
- `DELETE /agents/{agent_id}/skills/imported/{skill_id}`

### Skills and GitHub import

- `GET /skills/library`
- `POST /github-imports/skills/preview`
- `POST /github-imports/skills/collection-preview`
- `POST /github-imports/skills/import-selected`
- `POST /github-imports/{import_id}/approve-skill`
- `POST /github-imports/{import_id}/reject`

### Provider

- `GET /model-provider-keys`
- `GET /model-provider-keys/{provider}`
- `PUT /model-provider-keys/{provider}`
- `DELETE /model-provider-keys/{provider}`
- `POST /providers/test-connection` adalah path live provider, tapi tidak dijalankan di smoke ini

### Runtime and guard

- `GET /runtime/capabilities`
- `GET /n8n-workflows`

### Read-only monitor

- `GET /logs/activity`
- `GET /logs/audit`
- `GET /tasks`
- `GET /approvals/pending`

## Safety Contract

- Script default read-only.
- Mutating check hanya jalan kalau `--with-mutations` dipakai.
- Script tidak panggil external model provider.
- Script tidak panggil n8n execution.
- Script tidak clone, install, atau execute GitHub skill/tool.
- Response provider key harus masked only.
- Raw `api_key`, token, password, DB URL, dan secret lain tidak boleh keluar di output.

## Manual Browser Check

Kalau `SMOKE_WEB_BASE_URL` ada, cek ini di browser juga:

- login page load
- register page load
- dashboard load
- agent list/detail load
- provider/settings panel load
- approvals/tasks/logs load

## Failure Rule

- Secret leak = FAIL
- Tool execution path open = FAIL
- n8n execution path open = FAIL
- GitHub code execution path open = FAIL
- Provider live test jalan tanpa approval = FAIL
- Read-only endpoint berubah jadi mutasi = FAIL

## Expected Output

- `PASS`: semua check jalan dan aman
- `PARTIAL`: asset siap, tapi live proof belum lengkap
- `FAIL`: ada leak, open execution path, atau contract rusak

