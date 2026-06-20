# QA Regression Matrix v2.1

Tujuan: peta baseline QA untuk readiness produksi.  
Aturan: tidak ada row yang jadi PASS sampai benar-benar diverifikasi. Dokumen ini tidak mengklaim runtime sukses.

## Status Legend

- `PASS`: sudah diverifikasi dan ada bukti
- `PARTIAL`: asset/dokumen siap, tapi proof live masih kurang
- `BLOCKED`: fitur harus tetap mati, preview-only, atau butuh approval eksplisit
- `DEFERRED`: fase nanti
- `UNVERIFIED`: belum dicek di batch ini

## Main Regression Matrix

| Area | Check | Production expectation | Verification method | Status now |
| --- | --- | --- | --- | --- |
| Auth | Register | User baru bisa register, tanpa bocor secret | API smoke, response check | PARTIAL |
| Auth | Login | Login valid keluarkan token/session | API smoke, token check | PARTIAL |
| Auth | `auth/me` | Current user balik, tanpa secret | Authenticated API check | PARTIAL |
| Agents | Create agent | Agent bisa dibuat dengan default aman | API smoke | PARTIAL |
| Agents | List agent | List tampil field aman saja | API smoke | PARTIAL |
| Agents | Detail agent | Detail tampil record benar, tanpa secret | API smoke | PARTIAL |
| Agents | Active skills | Active skill terlihat di surface agent | API smoke | PARTIAL |
| Skills | Skill library | Library skill tampil dan attachable flag aman | API smoke | PARTIAL |
| Skills | GitHub skill preview | Preview only, tidak clone/install/execute | API smoke, response review | PARTIAL |
| Skills | Collection preview | Collection preview hanya metadata | API smoke | PARTIAL |
| Skills | Selected import | Import jadi metadata staging saja | API smoke, audit check | PARTIAL |
| Skills | Approve/reject skill | Review ubah state approval saja | API smoke, audit check | PARTIAL |
| Skills | Attach/detach skill | Link skill berubah, execution tidak jalan | API smoke | PARTIAL |
| Providers | Provider key CRUD | Key simpan/lihat/hapus pakai masked only | API smoke, stored payload check | PARTIAL |
| Providers | Provider test-connection | Live provider test tidak jalan di smoke | Negative policy check | BLOCKED |
| Providers | Settings surface | Settings/metadata tampil tanpa raw secret | UI/API smoke | PARTIAL |
| Runtime | Runtime capabilities | Capability metadata saja | API smoke | PARTIAL |
| n8n | n8n workflow guard | Workflow metadata boleh, execution tetap terkunci | Negative test, route check | BLOCKED |
| Monitoring | Activity log read-only | Log hanya baca | API smoke | PARTIAL |
| Monitoring | Audit log read-only | Audit hanya baca | API smoke | PARTIAL |
| Monitoring | Tasks read-only | Tasks hanya baca | API smoke | PARTIAL |
| Monitoring | Approvals read-only | Approvals hanya baca | API smoke | PARTIAL |
| Security | No secret exposure | No API key, token, DB URL, webhook secret, or credential body exposed | UI, API, log review | PARTIAL |
| Security | No GitHub clone/install/execute | Imported GitHub content tetap preview/review only | Negative test, contract review | BLOCKED |
| Security | No tool execution | Tool run path tetap mati atau approval-gated | Negative test, route review | BLOCKED |
| Security | No n8n execution | No workflow/webhook execution path fires | Negative test, route review | BLOCKED |

## Regression Coverage Notes

- Matrix ini baseline readiness, bukan bukti run sukses.
- `BLOCKED` harus fail closed.
- `PARTIAL` berarti asset sudah ada, proof live masih belum lengkap.
- Semua row di file ini map ke `scripts/production_smoke.py` atau ke manual browser check.

## Blocked / Deferred

Blocked now:

- Tool execution
- n8n execution
- GitHub clone/install/execute
- Provider live test-connection

Deferred now:

- Any runtime execution path not explicitly approved
- Any live external side effect from imported GitHub content
- Any workflow activation that implies execution instead of preview

## Still Needs Live Proof

- register
- login
- `auth/me`
- create agent
- list agent
- detail agent
- active skills visible
- skill library
- GitHub skill preview
- collection preview
- selected import
- approve/reject skill
- attach/detach skill
- provider key CRUD masked only
- provider settings surface
- runtime capabilities
- activity log read-only
- audit log read-only
- tasks read-only
- approvals read-only
- no secret exposure

